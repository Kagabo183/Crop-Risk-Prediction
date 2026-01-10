import React, { useState, useEffect, useCallback } from 'react';
import { fetchWeatherForecast } from '../api';
import './Weather.css';

// --- SVG Components for Professional Data ---
const SunIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="12" cy="12" r="5" fill="#FFD700" stroke="#FFD700" fillOpacity="0.4" />
    <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="#FFD700" />
  </svg>
);

const CloudIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" fill="#fff" stroke="#fff" fillOpacity="0.8" />
  </svg>
);

const RainIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25" fill="#fff" stroke="#fff" fillOpacity="0.8" />
    <path d="M8 19l-2 3" stroke="#60A5FA" strokeLinecap="round" />
    <path d="M12 19l-2 3" stroke="#60A5FA" strokeLinecap="round" />
    <path d="M16 19l-2 3" stroke="#60A5FA" strokeLinecap="round" />
  </svg>
);

const SnowIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25" fill="#fff" stroke="#fff" fillOpacity="0.8" />
    <path d="M8 19h.01M12 19h.01M16 19h.01" stroke="#fff" strokeWidth="3" strokeLinecap="round" />
  </svg>
);

const StormIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25" fill="#555" stroke="#555" fillOpacity="0.8" />
    <path d="M13 14l-2 4h3l-2 4" stroke="#FFD700" strokeWidth="2" />
  </svg>
);

const FogIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M4 14h16" stroke="#ccc" />
    <path d="M4 17h16" stroke="#ccc" />
    <path d="M4 20h16" stroke="#ccc" />
    <path d="M8 10h8" stroke="#ccc" strokeOpacity="0.5" />
  </svg>
);

// Map codes to Icon Component
const getWeatherIcon = (code) => {
  // Clear
  if (code === 0 || code === 1) return SunIcon;
  // Cloud
  if (code === 2 || code === 3) return CloudIcon;
  // Fog
  if (code === 45 || code === 48) return FogIcon;
  // Drizzle / Rain
  if ([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return RainIcon;
  // Snow
  if ([71, 73, 75, 77, 85, 86].includes(code)) return SnowIcon; // Fallback for 77/85/86 if missing
  // Storm
  if ([95, 96, 99].includes(code)) return StormIcon;
  
  // Default to Cloud if unknown
  return CloudIcon;
};

const getWeatherText = (code) => {
  const map = {
    0: 'Clear Sky', 1: 'Mainly Clear', 2: 'Partly Cloudy', 3: 'Overcast',
    45: 'Fog', 48: 'Fog',
    51: 'Light Drizzle', 53: 'Drizzle', 55: 'Dense Drizzle',
    56: 'Freezing Drizzle', 57: 'Freezing Drizzle',
    61: 'Light Rain', 63: 'Rain', 65: 'Heavy Rain',
    66: 'Freezing Rain', 67: 'Heavy Freezing Rain',
    71: 'Light Snow', 73: 'Snow', 75: 'Heavy Snow', 77: 'Snow Grains',
    80: 'Rain Showers', 81: 'Rain Showers', 82: 'Violent Showers',
    85: 'Snow Showers', 86: 'Heavy Snow Showers',
    95: 'Thunderstorm', 96: 'Storm & Hail', 99: 'Heavy Hail Storm'
  };
  return map[code] || 'Cloudy'; // Safe fallback
};

const getBackgroundClass = (code) => {
   if (code <= 1) return 'weather-bg-clear';
   if (code <= 3) return 'weather-bg-cloudy';
   if ([45, 48].includes(code)) return 'weather-bg-fog';
   if (code >= 95) return 'weather-bg-storm';
   if (code >= 71 && code <= 77) return 'weather-bg-rainy'; // Snow looks cool on purple too
   if (code >= 85) return 'weather-bg-rainy';
   return 'weather-bg-rainy'; // Default rain/drizzle
};

const AnimatedIcon = ({ code }) => {
  const type = getBackgroundClass(code); // Reuse mapping logic for simplification
  if (code <= 1) return <div className="anim-icon icon-sunny"></div>;
  if (code <= 3) return <div className="anim-icon icon-cloudy"></div>;
  if (code >= 50 && code < 70) return (
    <div className="anim-icon icon-rainy">
      <div className="rain-drop"></div>
      <div className="rain-drop"></div>
      <div className="rain-drop"></div>
    </div>
  );
  if (code >= 70) return <div className="anim-icon icon-rainy"></div>; // Snow/Storm fallback
  return <div className="anim-icon icon-cloudy"></div>;
};

const Weather = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [locationName, setLocationName] = useState('Kigali'); 
  const [coords, setCoords] = useState({ lat: -1.9441, lon: 30.0619 });

  const loadWeather = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWeatherForecast(coords.lat, coords.lon);
      setWeatherData(data);
    } catch (err) {
      setError('Failed to fetch weather data.');
    } finally {
      setLoading(false);
    }
  }, [coords]);

  useEffect(() => {
    loadWeather();
  }, [loadWeather]);

  const handleUseLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCoords({
            lat: position.coords.latitude,
            lon: position.coords.longitude
          });
          setLocationName('Current Location');
        },
        () => alert('Could not get your location.')
      );
    }
  };

  if (loading && !weatherData) {
    return <div className="weather-container">Loading...</div>;
  }

  if (error) {
    return <div className="weather-container error">{error}</div>;
  }

  const current = weatherData?.current;
  const currentCode = current?.weather_code;
  const bgClass = getBackgroundClass(currentCode);
  const currentText = getWeatherText(currentCode);
  
  return (
    <div className={`weather-container ${bgClass}`}>
      <div className="weather-header">
        <div className="location-info">
          <h2>{locationName}</h2>
        </div>
        <button className="location-btn" onClick={handleUseLocation}>
          My Location 🎯
        </button>
      </div>

      {weatherData && (
        <>
          {/* Main Hero */}
          <div className="current-weather">
            <div className="current-header">{currentText}</div>
            <div className="current-main">
              <AnimatedIcon code={currentCode} />
              <div className="temp-large">{Math.round(current.temperature_2m)}°</div>
            </div>
            
            <div className="weather-details">
              <div className="detail-item">
                <span className="detail-label">Wind</span>
                <span className="detail-value">{current.wind_speed_10m} km/h</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Humidity</span>
                <span className="detail-value">{current.relative_humidity_2m}%</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Precip</span>
                <span className="detail-value">{current.precipitation} mm</span>
              </div>
            </div>
          </div>

          {/* Hourly Forecast */}
          <div className="forecast-section">
            <h3>Hourly Forecast</h3>
            <div className="forecast-scroll">
              {weatherData.hourly.time.slice(0, 24).map((time, index) => {
                const date = new Date(time);
                const hour = date.getHours().toString().padStart(2, '0') + ':00';
                const code = weatherData.hourly.weather_code[index];
                const temp = weatherData.hourly.temperature_2m[index];
                const IconComp = getWeatherIcon(code);
                
                return (
                  <div key={index} className="hourly-item">
                    <span className="hour-time">{hour}</span>
                    <span className="hour-icon">
                      <IconComp className="w-icon-sm" />
                    </span>
                    <span className="hour-temp">{Math.round(temp)}°</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 7-Day Forecast */}
          <div className="forecast-section">
            <h3>7-Day Forecast</h3>
            <div className="daily-list">
              {weatherData.daily.time.map((time, index) => {
                const date = new Date(time);
                const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
                const code = weatherData.daily.weather_code[index];
                const max = weatherData.daily.temperature_2m_max[index];
                const min = weatherData.daily.temperature_2m_min[index];
                const IconComp = getWeatherIcon(code);

                return (
                  <div key={time} className="daily-item">
                    <span className="day-name">{dayName}</span>
                    <span className="day-icon">
                      <IconComp className="w-icon-md" />
                    </span>
                    <div className="day-temp">
                      <span className="max-temp">{Math.round(max)}°</span>
                      <span className="min-temp">{Math.round(min)}°</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Weather;
