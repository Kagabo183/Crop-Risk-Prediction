"""Remote sensing diagnostics

This module provides *best-effort* inference from Sentinel-derived NDVI signals.

Important: Sentinel NDVI alone cannot reliably identify exact crop species nor
confirm a specific disease. What we can do without labeled crop/disease imagery
is:
1) Detect vegetation condition signals (cover, stress, trend)
2) Combine those signals with weather-driven disease models to rank likely risks
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.models.data import SatelliteImage
from app.models.disease import Disease
from app.models.farm import Farm
from app.services.disease_intelligence import DiseaseModelEngine
from app.services.weather_service import WeatherDataIntegrator


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        v = float(value)
        if np.isnan(v):
            return None
        return v
    except Exception:
        return None


def _extract_ndvi_from_meta(meta: Any) -> Optional[float]:
    if not isinstance(meta, dict):
        return None
    # Common keys across this repo's different ingestion paths
    for key in ("ndvi_value", "mean_ndvi", "mean", "ndvi"):
        v = _safe_float(meta.get(key))
        if v is not None:
            return v
    return None


def _extract_farm_id_from_meta(meta: Any) -> Optional[int]:
    if not isinstance(meta, dict):
        return None
    raw = meta.get("farm_id")
    try:
        if raw is None:
            return None
        return int(raw)
    except Exception:
        return None


def _clamp01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def _ndvi_cover_class(current_ndvi: Optional[float]) -> str:
    if current_ndvi is None:
        return "unknown"
    if current_ndvi < 0.2:
        return "bare_or_harvested"
    if current_ndvi < 0.4:
        return "sparse_vegetation"
    if current_ndvi < 0.6:
        return "moderate_vegetation"
    return "dense_vegetation"


@dataclass
class NdviSignals:
    count: int
    current: Optional[float]
    mean: Optional[float]
    trend: float
    anomaly_from_baseline: float
    stress_score: float
    cover_class: str


class RemoteSensingDiagnosticsService:
    def __init__(self):
        self.weather = WeatherDataIntegrator()
        self.disease_engine = DiseaseModelEngine()

    def _compute_ndvi_signals(self, ndvi_series: List[float]) -> NdviSignals:
        if not ndvi_series:
            return NdviSignals(
                count=0,
                current=None,
                mean=None,
                trend=0.0,
                anomaly_from_baseline=0.0,
                stress_score=0.0,
                cover_class="unknown",
            )

        arr = np.array(ndvi_series, dtype=float)
        current = float(arr[-1])
        mean = float(np.mean(arr))

        # Trend as slope of NDVI values over time index (unitless per step)
        if len(arr) >= 2:
            x = np.arange(len(arr))
            trend = float(np.polyfit(x, arr, 1)[0])
        else:
            trend = 0.0

        # Baseline: in absence of location-specific seasonal baseline,
        # use a conservative healthy vegetation baseline.
        baseline = 0.70
        anomaly = float(current - baseline)

        # Stress score: blend low NDVI, negative anomaly, and declining trend.
        # This is intentionally conservative and capped to [0,1].
        low_ndvi = _clamp01((0.65 - current) / 0.65)  # near 0 when healthy
        neg_anom = _clamp01(max(0.0, -anomaly) / 0.35)
        neg_trend = _clamp01(max(0.0, -trend) / 0.05)

        stress = _clamp01(0.45 * low_ndvi + 0.35 * neg_anom + 0.20 * neg_trend)
        cover = _ndvi_cover_class(current)

        return NdviSignals(
            count=int(len(arr)),
            current=round(current, 4),
            mean=round(mean, 4),
            trend=round(trend, 6),
            anomaly_from_baseline=round(anomaly, 4),
            stress_score=round(stress, 3),
            cover_class=cover,
        )

    def _predict_disease_for_name(self, disease_name: str, weather_data: Dict[str, Any], crop_hint: str) -> Dict[str, Any]:
        name = (disease_name or "").lower()
        if "late blight" in name or "phytophthora" in name:
            return self.disease_engine.predict_late_blight(weather_data, crop_hint)
        if "septoria" in name:
            return self.disease_engine.predict_septoria_leaf_spot(weather_data, crop_hint)
        if "powdery" in name:
            return self.disease_engine.predict_powdery_mildew(weather_data, crop_hint)
        if "bacterial spot" in name:
            return self.disease_engine.predict_bacterial_spot(weather_data, crop_hint)
        if "fusarium" in name:
            return self.disease_engine.predict_fusarium_wilt(weather_data, crop_hint)

        # Default: treat unknown diseases as low-risk unless weather is extreme.
        return {
            "disease_name": disease_name,
            "risk_score": 0.0,
            "risk_level": "low",
            "confidence_score": 0.3,
            "recommended_actions": ["Add a pathogen-specific model configuration."],
            "research_source": "unconfigured",
        }

    def diagnose_farm(
        self,
        farm_id: int,
        db: Session,
        days: int = 30,
        top_n: int = 3,
    ) -> Dict[str, Any]:
        farm = db.query(Farm).filter(Farm.id == farm_id).first()
        if not farm:
            raise ValueError("Farm not found")

        # Pull recent images and filter by farm_id stored in extra_metadata.
        # (There is no farm_id column on the table in this project.)
        start_date = (datetime.utcnow() - timedelta(days=days)).date()
        images = (
            db.query(SatelliteImage)
            .filter(SatelliteImage.date >= start_date)
            .order_by(SatelliteImage.date)
            .all()
        )

        ndvi_series: List[float] = []
        recent_points: List[Dict[str, Any]] = []

        for img in images:
            meta = img.extra_metadata
            if _extract_farm_id_from_meta(meta) != farm_id:
                continue
            ndvi = _extract_ndvi_from_meta(meta)
            if ndvi is None:
                continue
            ndvi_series.append(float(ndvi))
            recent_points.append(
                {
                    "date": img.date.isoformat() if img.date else None,
                    "ndvi": round(float(ndvi), 4),
                    "image_type": img.image_type,
                    "cloud_coverage": meta.get("cloud_coverage") if isinstance(meta, dict) else None,
                }
            )

        signals = self._compute_ndvi_signals(ndvi_series)

        # Weather snapshot for risk models
        if farm.latitude is not None and farm.longitude is not None:
            weather_data = self.weather.integrate_multi_source_data(
                lat=farm.latitude,
                lon=farm.longitude,
                start_date=datetime.utcnow() - timedelta(days=1),
                end_date=datetime.utcnow(),
            )
            try:
                weather_data["disease_risk_factors"] = self.weather.calculate_disease_risk_factors(weather_data)
            except Exception:
                # If some fields are missing, keep base weather
                pass
        else:
            weather_data = {}

        diseases = db.query(Disease).limit(200).all()

        # Crop hint: prefer a persisted farm crop_type; otherwise fall back to a neutral default.
        farm_crop_type = (getattr(farm, "crop_type", None) or "").strip() or None
        crop_hint = (farm_crop_type or "mixed").lower()
        if signals.cover_class in ("bare_or_harvested", "unknown"):
            crop_hint = "unknown"

        ranked: List[Dict[str, Any]] = []
        stress_multiplier = 1.0 + (signals.stress_score * 0.25)

        for disease in diseases:
            pred = self._predict_disease_for_name(disease.name, weather_data, crop_hint)
            base_score = _safe_float(pred.get("risk_score")) or 0.0
            adjusted_score = float(min(100.0, base_score * stress_multiplier))
            ranked.append(
                {
                    "disease": disease.name,
                    "risk_score": round(adjusted_score, 2),
                    "risk_level": pred.get("risk_level", "low"),
                    "confidence": round(float(_safe_float(pred.get("confidence_score")) or 0.0), 2),
                    "recommended_actions": pred.get("recommended_actions") or [],
                    "research_source": pred.get("research_source"),
                }
            )

        ranked.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
        top = ranked[: max(0, int(top_n))]

        # Human-readable drivers
        drivers: List[str] = []
        if signals.count == 0:
            drivers.append("No recent NDVI points for this farm (satellite linkage missing)")
        else:
            if (signals.trend or 0.0) < -0.01:
                drivers.append("NDVI is declining (stress signal)")
            if (signals.current or 0.0) < 0.45:
                drivers.append("Low NDVI (weaker vegetation cover)")
            if signals.anomaly_from_baseline < -0.10:
                drivers.append("NDVI below baseline (negative anomaly)")

        rf = weather_data.get("disease_risk_factors") if isinstance(weather_data, dict) else None
        if isinstance(rf, dict):
            if rf.get("high_humidity"):
                drivers.append("High humidity (favors fungal diseases)")
            if rf.get("recent_rain"):
                drivers.append("Recent rainfall (spore spread / leaf wetness)")
            if rf.get("leaf_wetness"):
                drivers.append("Leaf wetness present")

        return {
            "farm_id": farm_id,
            "farm_name": farm.name,
            "farm_crop_type": farm_crop_type,
            "cover_class": signals.cover_class,
            "ndvi": {
                "points": signals.count,
                "current": signals.current,
                "mean": signals.mean,
                "trend": signals.trend,
                "anomaly_from_baseline": signals.anomaly_from_baseline,
            },
            "stress_score": signals.stress_score,
            "drivers": drivers,
            "top_disease_risks": top,
            "ndvi_history": recent_points[-30:],
            "note": (
                "These are risk signals (not lab-confirmed disease detection). "
                "To identify exact crop species/disease from imagery, the system needs labeled training data."
            ),
        }
