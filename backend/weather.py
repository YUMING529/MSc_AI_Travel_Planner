"""Daily Open-Meteo forecasts; failures never block planning. No user notes are sent."""
import copy
import json
import math
import threading
import time
from http.client import HTTPException
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from urllib.request import urlopen

CITIES = {
    'London': (51.5074, -0.1278), 'Edinburgh': (55.9533, -3.1883),
    'Manchester': (53.4808, -2.2426), 'Birmingham': (52.4862, -1.8904),
    'Liverpool': (53.4084, -2.9916), 'Glasgow': (55.8642, -4.2518),
    'Bristol': (51.4545, -2.5879), 'Leeds': (53.8008, -1.5491),
    'Cardiff': (51.4816, -3.1791), 'Belfast': (54.5973, -5.9301),
    'Newcastle': (54.9783, -1.6178), 'Nottingham': (52.9548, -1.1581),
    'Sheffield': (53.3811, -1.4701), 'Oxford': (51.7520, -1.2577),
    'Cambridge': (52.2053, 0.1218), 'Bath': (51.3811, -2.3590), 'York': (53.9590, -1.0815),
}
FIELDS = ['weather_code', 'temperature_2m_max', 'temperature_2m_min',
          'precipitation_probability_max', 'wind_speed_10m_max']
_cache = {}
_lock = threading.Lock()


def recommendation(code, rain, wind):
    # Product heuristics, not official warnings or safety guarantees.
    if code in (95, 96, 99) or wind >= 40 or code in (56, 57, 66, 67, 75, 86):
        return 'indoor', 'Prefer indoor activities; storm, freezing precipitation, snow or strong wind is forecast. Check official warnings.'
    if rain >= 60 or code in (63, 65, 82):
        return 'indoor', 'Prefer indoor activities because rain is likely or substantial rain is forecast.'
    if rain < 30 and wind < 25 and code in (0, 1, 2, 3):
        return 'outdoor', 'Outdoor activities may suit the forecast; keep an indoor backup.'
    return 'mixed', 'Keep plans flexible and provide indoor alternatives.'


def description(code):
    if code == 0: return 'Clear sky'
    if code in (1, 2, 3): return 'Partly cloudy / overcast'
    if code in (45, 48): return 'Fog'
    if code in (51, 53, 55, 56, 57): return 'Drizzle'
    if code in (61, 63, 65, 66, 67, 80, 81, 82): return 'Rain / showers'
    if code in (71, 73, 75, 77, 85, 86): return 'Snow'
    if code in (95, 96, 99): return 'Thunderstorm'
    return 'Variable weather'


def number(value, low, high):
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def get_weather(preferences, enabled=True, now=None):
    now = now or datetime.now(ZoneInfo('Europe/London'))
    today = now.astimezone(ZoneInfo('Europe/London')).date()
    start = datetime.fromisoformat(preferences['start']).date()
    end = datetime.fromisoformat(preferences['end']).date()
    dates = [(start+timedelta(days=i)).isoformat() for i in range((end-start).days+1)]
    days = [{'date': d, 'status': 'out_of_range', 'recommendation': 'unknown',
             'reason': 'No forecast for this date. Keep an indoor alternative; check again nearer departure.'} for d in dates]
    result = {'source': 'Open-Meteo', 'sourceUrl': 'https://open-meteo.com/',
              'timezone': 'Europe/London', 'fetchedAt': None, 'status': 'unavailable', 'days': days}
    eligible = [d for d in dates if today.isoformat() <= d <= (today+timedelta(days=15)).isoformat()]
    if not enabled:
        for d in days: d.update(status='disabled', reason='Weather lookup is disabled. Indoor alternatives are still available.')
        return result
    if not eligible:
        result['status'] = 'out_of_range'
        return result
    for d in days:
        if d['date'] in eligible:
            d.update(status='unavailable', reason='Weather forecast unavailable. Planning continues with indoor alternatives.')
    cache_key = (preferences['destination'], today.isoformat())
    with _lock:
        cached = _cache.get(cache_key)
    if cached and time.monotonic()-cached[0] < 1800:
        body, fetched = copy.deepcopy(cached[1]), cached[2]
    else:
        try:
            lat, lon = CITIES[preferences['destination']]
            query = urlencode({'latitude': lat, 'longitude': lon, 'daily': ','.join(FIELDS),
                               'timezone': 'Europe/London', 'forecast_days': 16,
                               'temperature_unit': 'celsius', 'wind_speed_unit': 'kmh'})
            with urlopen('https://api.open-meteo.com/v1/forecast?'+query, timeout=8) as response:
                raw = response.read(131073)
            if len(raw) > 131072: return result
            body = json.loads(raw)
            if not isinstance(body, dict) or not isinstance(body.get('daily'), dict): return result
            fetched = now.isoformat()
            with _lock:
                _cache.clear() if len(_cache) > 40 else None
                _cache[cache_key] = (time.monotonic(), copy.deepcopy(body), fetched)
        except (OSError, ValueError, KeyError, TypeError, HTTPException):
            return result
    daily = body.get('daily', {})
    times = daily.get('time')
    if not isinstance(times, list): return result
    for day in days:
        if day['date'] not in eligible or day['date'] not in times: continue
        try:
            i = times.index(day['date'])
            code, high, low, rain, wind = [daily[f][i] for f in FIELDS]
            if not (type(code) is int and number(code, 0, 99) and number(high, -80, 65)
                    and number(low, -80, 65) and low <= high and number(rain, 0, 100) and number(wind, 0, 400)):
                continue
            tendency, reason = recommendation(code, rain, wind)
            day.update(status='available', summary=description(code), weatherCode=code,
                       temperatureMax=high, temperatureMin=low, rainProbability=rain,
                       windSpeed=wind, recommendation=tendency, reason=reason)
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    available = sum(d['status']=='available' for d in days)
    result.update(status='available' if available==len(days) else 'partial' if available else 'unavailable',
                  fetchedAt=fetched if available else None)
    return result


def attach_weather(trip, weather):
    """Keep forecast claims authoritative, even if the model invents weather in its rationale."""
    trip['itinerary']['weather'] = weather
    daily = {d['date']: d for d in weather['days']}
    for day in trip['itinerary'].get('days', []):
        forecast = daily.get(day['date'])
        for activity in day['activities']:
            if activity.get('setting'):
                activity['weatherReason'] = forecast['reason'] if forecast else 'Forecast unavailable. Keep an indoor backup.'
    return trip
