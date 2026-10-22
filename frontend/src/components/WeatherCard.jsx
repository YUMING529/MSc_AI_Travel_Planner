import React from 'react';

export default function WeatherCard({weather,date}) {
  if (!weather) return <div className="weather-card"><strong>Weather not recorded</strong><p>Generate a new plan to include a forecast where available.</p></div>;
  const day=weather.days?.find(d=>d.date===date);
  const available=day?.status==='available';
  const labels={indoor:'Indoor activities preferred',outdoor:'Outdoor options possible',mixed:'Keep plans flexible',unknown:'Indoor backup recommended'};
  return <section className="weather-card" aria-label={`Weather for ${date}`}>
    <div className="weather-heading"><strong>{available?day.summary:'Forecast unavailable'}</strong><span>{labels[day?.recommendation||'unknown']}</span></div>
    {available&&<p>{day.temperatureMin}–{day.temperatureMax} °C · Rain chance {day.rainProbability}% · Max wind {day.windSpeed} km/h</p>}
    <p>{day?.reason||'No weather data saved for this date.'}</p>
    <small>Daily planning guidance, not an official weather warning. {weather.fetchedAt&&<>Retrieved {new Date(weather.fetchedAt).toLocaleString('en-GB',{timeZone:'Europe/London'})} (UK time). Saved forecast; not refreshed automatically. </>}<a href="https://open-meteo.com/" target="_blank" rel="noreferrer">Weather data: Open-Meteo</a></small>
  </section>;
}
