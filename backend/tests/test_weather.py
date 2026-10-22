import copy
import json
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
from backend.weather import get_weather, recommendation, _cache, CITIES
from backend.validation import DESTINATIONS
from backend.app import create_app


class WeatherTests(unittest.TestCase):
    def setUp(self):
        _cache.clear()
        self.now=datetime(2026,10,21,12,tzinfo=ZoneInfo('Europe/London'))
        self.prefs=dict(destination='London',start='2026-10-21',end='2026-10-22')
        self.daily=dict(time=['2026-10-21','2026-10-22'],weather_code=[63,1],
            temperature_2m_max=[15,17],temperature_2m_min=[10,12],
            precipitation_probability_max=[80,10],wind_speed_10m_max=[20,12])

    def response(self, mock, daily=None):
        mock.return_value.__enter__.return_value.read.return_value=json.dumps({'daily':daily or self.daily}).encode()

    @patch('backend.weather.urlopen')
    def test_forecast_rules_cache_and_copy(self, mock):
        self.response(mock)
        result=get_weather(self.prefs,now=self.now)
        self.assertEqual(result['status'],'available')
        self.assertEqual([d['recommendation'] for d in result['days']],['indoor','outdoor'])
        self.assertIn('timezone=Europe%2FLondon',mock.call_args.args[0])
        result['days'][0]['rainProbability']=0
        self.assertEqual(get_weather(self.prefs,now=self.now)['days'][0]['rainProbability'],80)
        self.assertEqual(mock.call_count,1)

    @patch('backend.weather.urlopen')
    def test_far_future_past_and_disabled_skip_network(self, mock):
        for changes in ({'start':'2026-12-01','end':'2026-12-02'}, {'start':'2026-10-01','end':'2026-10-02'}):
            self.assertEqual(get_weather({**self.prefs,**changes},now=self.now)['status'],'out_of_range')
        get_weather(self.prefs,enabled=False,now=self.now)
        mock.assert_not_called()

    @patch('backend.weather.urlopen')
    def test_partial_and_missing_values(self,mock):
        self.response(mock)
        result=get_weather({**self.prefs,'start':'2026-10-20'},now=self.now)
        self.assertEqual(result['status'],'partial')
        self.assertEqual(result['days'][0]['status'],'out_of_range')
        _cache.clear()
        bad=copy.deepcopy(self.daily);bad['precipitation_probability_max'][0]=None
        self.response(mock,bad)
        result=get_weather(self.prefs,now=self.now)
        self.assertEqual(result['status'],'partial')
        self.assertNotIn('rainProbability',result['days'][0])

    @patch('backend.weather.urlopen')
    def test_timeout_and_malformed_fail_open(self,mock):
        mock.side_effect=TimeoutError()
        self.assertEqual(get_weather(self.prefs,now=self.now)['status'],'unavailable')
        mock.side_effect=None
        mock.return_value.__enter__.return_value.read.return_value=b'null'
        self.assertEqual(get_weather(self.prefs,now=self.now)['status'],'unavailable')

    def test_all_cities_and_wind_override(self):
        self.assertEqual(set(CITIES),set(DESTINATIONS))
        self.assertEqual(recommendation(0,0,45)[0],'indoor')
        self.assertEqual(recommendation(95,10,5)[0],'indoor')
        self.assertEqual(recommendation(3,45,10)[0],'mixed')

    @patch('backend.app.generate_qwen')
    @patch('backend.app.get_weather')
    def test_weather_attached_from_backend_not_model(self, weather, qwen):
        weather.return_value={'status':'unavailable','days':[]}
        qwen.return_value={'itinerary':{'weather':{'status':'invented'}}}
        client=create_app({'TRIP_PROVIDER':'qwen','WEATHER_ENABLED':True}).test_client()
        prefs={**self.prefs,'currency':'GBP','budget':500,'travellers':1,'interests':[]}
        response=client.post('/api/trips/generate',json={**prefs,'weather':{'status':'fake'}})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['trip']['itinerary']['weather']['status'],'unavailable')
        self.assertEqual(qwen.call_args.args[1]['WEATHER_CONTEXT'],weather.return_value)
        weather.assert_called_once()

    def test_model_weather_claims_are_replaced(self):
        from backend.weather import attach_weather
        trip={'itinerary':{'days':[{'date':'2026-10-22','activities':[{'setting':'indoor','weatherReason':'Sunny 99 C'}]}]}}
        weather={'days':[{'date':'2026-10-22','reason':'Forecast unavailable.'}]}
        attach_weather(trip, weather)
        self.assertEqual(trip['itinerary']['days'][0]['activities'][0]['weatherReason'],'Forecast unavailable.')

    def test_outdoor_alternative_validated_and_preserved(self):
        from backend.qwen import validate_output, PlannerError
        from backend.planner import generate_sample
        prefs={**self.prefs,'currency':'GBP','budget':500,'travellers':1,'interests':[]}
        output=generate_sample(prefs)['itinerary']
        activity=output['days'][0]['activities'][0]
        activity.update(setting='outdoor',weatherReason='Keep a backup.',indoorAlternative='Visit a local museum; verify entry.')
        days,_=validate_output(output,prefs)
        self.assertIn('museum',days[0]['activities'][0]['indoorAlternative'])
        activity['indoorAlternative']=''
        with self.assertRaises(PlannerError): validate_output(output,prefs)
