#!/usr/bin/env python3
"""
Compute mean NDVI from a GeoTIFF and store the value in the `satellite_images` table's
`extra_metadata` JSON column (as `mean_ndvi`).

Usage:
  python scripts/ndvi_mean_to_db.py --file C:/data/sentinel2/ndvi_test.tif --db-url "postgresql://user:pass@host:5432/dbname"

If `--db-url` is omitted the script uses the `DATABASE_URL` environment variable.
If a row with the same `file_path` exists the script updates its `extra_metadata` adding `mean_ndvi`.
If no row exists the script will insert a new row; in that case you must provide `--date` and `--region`.
"""
from pathlib import Path
import argparse
import json
import os
import numpy as np
import rasterio
from sqlalchemy import create_engine, text


def compute_mean_ndvi(tif_path: Path) -> float:
    with rasterio.open(tif_path) as src:
        arr = src.read(1).astype('float32')
        nodata = src.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)
        # Some datasets use negative values; keep as is, user can interpret
        mean = float(np.nanmean(arr))
    return mean


def load_row_by_path(conn, file_path):
    q = text('SELECT id, extra_metadata FROM satellite_images WHERE file_path = :fp')
    res = conn.execute(q, {'fp': file_path}).fetchone()
    return res


def update_row_extra_metadata(conn, row_id, extra_metadata: dict):
    q = text('UPDATE satellite_images SET extra_metadata = :meta WHERE id = :id')
    conn.execute(q, {'meta': json.dumps(extra_metadata), 'id': row_id})


def insert_row(conn, date, region, image_type, file_path, extra_metadata: dict):
    q = text('''INSERT INTO satellite_images (date, region, image_type, file_path, extra_metadata)
                VALUES (:date, :region, :image_type, :file_path, :extra_metadata)
                RETURNING id''')
    res = conn.execute(q, {
        'date': date,
        'region': region,
        'image_type': image_type,
        'file_path': file_path,
        'extra_metadata': json.dumps(extra_metadata)
    })
    return res.fetchone()[0]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--file', required=True, help='Path to NDVI GeoTIFF')
    p.add_argument('--db-url', help='SQLAlchemy DB URL (overrides DATABASE_URL env)')
    p.add_argument('--date', help='Date for new record (YYYY-MM-DD)')
    p.add_argument('--region', help='Region name for new record (e.g., Rwanda)')
    p.add_argument('--out-json', help='Path to write JSON fallback with mean NDVI results')
    p.add_argument('--image-type', default='NDVI', help='Image type to use when inserting (default NDVI)')
    args = p.parse_args()

    tif_path = Path(args.file)
    if not tif_path.exists():
        raise SystemExit(f"File not found: {tif_path}")

    mean_ndvi = compute_mean_ndvi(tif_path)
    print(f"Mean NDVI for {tif_path}: {mean_ndvi:.6f}")

    db_url = args.db_url or os.environ.get('DATABASE_URL')
    out_json = args.out_json

    if not db_url:
        # Fallback: write to JSON if provided, else exit with message
        if not out_json:
            print('DATABASE_URL not provided and --out-json not set. Will write to stdout.')
            print(json.dumps({'file': str(tif_path).replace('\\', '/'), 'mean_ndvi': mean_ndvi}))
            return

        # write/append to JSON file as an object mapping file_path -> mean_ndvi
        out_path = Path(out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if out_path.exists():
            try:
                with out_path.open('r', encoding='utf-8') as fh:
                    data = json.load(fh)
            except Exception:
                data = {}
        data[str(tif_path).replace('\\', '/')] = mean_ndvi
        with out_path.open('w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2)
        print(f"Wrote mean NDVI to JSON: {out_path}")
        return

    # If we have a DB URL, attempt to write to DB
    try:
        engine = create_engine(db_url)
        conn = engine.connect()
    except Exception as e:
        if out_json:
            out_path = Path(out_json)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            if out_path.exists():
                try:
                    with out_path.open('r', encoding='utf-8') as fh:
                        data = json.load(fh)
                except Exception:
                    data = {}
            data[str(tif_path).replace('\\', '/')] = mean_ndvi
            with out_path.open('w', encoding='utf-8') as fh:
                json.dump(data, fh, indent=2)
            print(f"DB connection failed; wrote mean NDVI to JSON: {out_path}")
            return
        else:
            raise

    try:
        row = load_row_by_path(conn, str(tif_path).replace('\\', '/'))
        if row:
            row_id = row[0]
            existing_meta = row[1] or {}
            if isinstance(existing_meta, str):
                try:
                    existing_meta = json.loads(existing_meta)
                except Exception:
                    existing_meta = {}
            existing_meta['mean_ndvi'] = mean_ndvi
            update_row_extra_metadata(conn, row_id, existing_meta)
            print(f"Updated satellite_images id={row_id} with mean_ndvi")
        else:
            if not args.date or not args.region:
                raise SystemExit('No existing DB row found for this file. Provide --date and --region to insert a new row.')
            extra = {'mean_ndvi': mean_ndvi}
            new_id = insert_row(conn, args.date, args.region, args.image_type, str(tif_path).replace('\\', '/'), extra)
            print(f"Inserted new satellite_images id={new_id} with mean_ndvi")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
