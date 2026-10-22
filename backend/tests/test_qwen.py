import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError

from backend.app import create_app
from backend.qwen import validate_output, PlannerError
from backend.planner import generate_sample


class QwenAPI(unittest.TestCase):
    def setUp(self):
        self.preferences = dict(destination='London', start='2026-11-02', end='2026-11-03',
                                currency='GBP', budget=500, travellers=1,
                                interests=['History', 'Food'], notes='Relaxed pace')
        self.output = generate_sample(self.preferences)['itinerary']
        self.config = dict(QUALITY_FIELDS_REQUIRED=False, WEATHER_ENABLED=False, TRIP_PROVIDER='qwen', DASHSCOPE_API_KEY='test-secret',
                           QWEN_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1',
                           QWEN_MODEL='qwen-plus', RECORD_LLM_EXPERIMENTS=False)
        self.client = create_app(self.config).test_client()

    def post(self, client=None):
        return (client or self.client).post('/api/trips/generate', json=self.preferences)

    def response(self, opener, output=None, finish='stop'):
        body = {'choices': [{'finish_reason': finish, 'message': {'content': json.dumps(output or self.output)}}], 'usage': {'total_tokens': 100}}
        opener.return_value.open.return_value.__enter__.return_value.read.return_value = json.dumps(body).encode()

    @patch('backend.qwen.build_opener')
    def test_success_contract_and_request(self, opener):
        self.response(opener)
        response = self.post()
        self.assertEqual(response.status_code, 200)
        trip = response.json['trip']
        self.assertEqual(trip['itinerary']['mode'], 'qwen')
        self.assertEqual(trip['itinerary']['total'], 340)
        self.assertFalse(trip['itinerary']['checks']['factsVerified'])
        request = opener.return_value.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload['model'], 'qwen-plus')
        self.assertFalse(payload['enable_thinking'])
        self.assertIn('Relaxed pace', payload['messages'][1]['content'])
        self.assertEqual(payload['response_format'], {'type': 'json_object'})
        self.assertTrue(request.full_url.endswith('/chat/completions'))
        self.assertNotIn('test-secret', response.get_data(as_text=True))

    @patch('backend.qwen.build_opener')
    def test_missing_key_never_calls_provider(self, opener):
        client = create_app({**self.config, 'DASHSCOPE_API_KEY': ''}).test_client()
        self.assertEqual(self.post(client).status_code, 503)
        opener.assert_not_called()

    @patch('backend.qwen.build_opener')
    def test_provider_errors_do_not_leak_or_fallback(self, opener):
        errors = [(HTTPError('url', 401, 'test-secret', {}, None), 503),
                  (HTTPError('url', 429, 'test-secret', {}, None), 503),
                  (HTTPError('url', 500, 'test-secret', {}, None), 502),
                  (TimeoutError('test-secret'), 504), (URLError('test-secret'), 503)]
        for error, status in errors:
            opener.return_value.open.side_effect = error
            response = self.post()
            self.assertEqual(response.status_code, status)
            self.assertNotIn('trip', response.json)
            self.assertNotIn('test-secret', response.get_data(as_text=True))

    @patch('backend.qwen.build_opener')
    def test_bad_json_and_truncation(self, opener):
        self.response(opener, finish='length')
        self.assertEqual(self.post().status_code, 502)
        for raw in (b'not json', b'null', b'{"choices": []}', b'x'*262145):
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = raw
            self.assertEqual(self.post().status_code, 502)

    def test_output_validation(self):
        changes = [lambda o: o['days'].pop(),
                   lambda o: o['days'][0].update(date='2027-01-01'),
                   lambda o: o['days'][0]['activities'][0].update(time='29:00 - 30:00'),
                   lambda o: o['days'][0]['activities'][1].update(time='11:00 - 14:00'),
                   lambda o: o['days'][0]['activities'][0].update(cost=-1),
                   lambda o: o['days'][0]['activities'][0].update(cost=True),
                   lambda o: o['days'][0]['activities'][0].update(tags=[{}]),
                   lambda o: o['days'][0]['activities'][0].update(title=None),
                   lambda o: o['costs'][0].update(value=float('nan')),
                   lambda o: o['costs'][0].update(label='Food'),
                   lambda o: o['costs'][2].update(value=0)]
        for change in changes:
            output = copy.deepcopy(self.output)
            change(output)
            with self.assertRaises(PlannerError):
                validate_output(output, self.preferences)

    @patch('backend.qwen.build_opener')
    def test_over_budget_and_record(self, opener):
        self.response(opener)
        self.preferences['budget'] = 100
        with tempfile.TemporaryDirectory() as folder:
            client = create_app({**self.config, 'RECORD_LLM_EXPERIMENTS': True, 'EXPERIMENT_DIR': folder}).test_client()
            response = self.post(client)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json['trip']['itinerary']['checks']['withinBudget'])
            records = list(Path(folder).glob('*.json'))
            self.assertEqual(len(records), 1)
            self.assertNotIn('test-secret', records[0].read_text())
            self.assertIn('promptVersion', json.loads(records[0].read_text()))

    @patch('backend.qwen.build_opener')
    def test_invalid_input_no_billable_call(self, opener):
        self.preferences['travellers'] = 51
        self.assertEqual(self.post().status_code, 400)
        opener.assert_not_called()


    @patch('backend.qwen.build_opener')
    def test_repair_then_success(self, opener):
        self.response(opener)
        good = opener.return_value.open.return_value.__enter__.return_value.read.return_value
        bad = copy.deepcopy(self.output)
        bad['days'][0]['activities'][1]['time'] = '11:00 - 13:00'
        bad_body = {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(bad)}}]}
        opener.return_value.open.return_value.__enter__.return_value.read.side_effect = [json.dumps(bad_body).encode(), good]
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(opener.return_value.open.call_count, 2)
        payload = json.loads(opener.return_value.open.call_args.args[0].data)
        self.assertIn('time_overlap_or_range', payload['messages'][-1]['content'])

    @patch('backend.qwen.build_opener')
    def test_repair_stops_after_two_calls(self, opener):
        opener.return_value.open.return_value.__enter__.return_value.read.return_value = b'null'
        self.assertEqual(self.post().status_code, 502)
        self.assertEqual(opener.return_value.open.call_count, 2)

    def test_expanded_input_and_output_dates(self):
        from backend.validation import validate_preferences, ValidationError
        from datetime import date, timedelta
        for length in (1, 3, 12, 14):
            prefs = {**self.preferences, 'destination': 'Manchester', 'travellers': 6,
                     'end': (date.fromisoformat(self.preferences['start'])+timedelta(days=length-1)).isoformat()}
            self.assertEqual(validate_preferences(prefs)['travellers'], 6)
            out = copy.deepcopy(self.output)
            out['days'] = [dict(date=(date.fromisoformat(prefs['start'])+timedelta(days=i)).isoformat(),
                                activities=copy.deepcopy(self.output['days'][0]['activities'])) for i in range(length)]
            out['costs'][2]['value'] = 10000
            self.assertEqual(len(validate_output(out, prefs)[0]), length)
        for changes in ({'travellers': 0}, {'travellers': 1.5}, {'travellers': 51},
                        {'destination': 'Paris'}, {'destination': []}, {'end': '2026-11-16'}):
            with self.assertRaises(ValidationError):
                validate_preferences({**self.preferences, **changes})

    @patch('backend.qwen.generate_qwen_chunk')
    def test_long_trip_merge_and_lodging_nights(self, provider):
        from backend.qwen import generate_qwen, required_dates
        night_counts = []
        def part(prefs, config, lodging_nights=None):
            night_counts.append(lodging_nights)
            days = [{'date': d, 'activities': [dict(time='10:00 - 11:00', period='Morning',
                     title='Visit', description='Explore', tags=[], cost=0, note='Verify')]} for d in required_dates(prefs)]
            return {'id': prefs['start'], 'itinerary': {'days': days, 'warnings': [],
                    'costs': [{'label': c['label'], 'value': 100 if c['label']=='Accommodation' else 0} for c in self.output['costs']]}}
        provider.side_effect = part
        prefs = {**self.preferences, 'end': '2026-11-13', 'budget': 100}
        with patch('backend.outline.generate_outline',return_value={d:['Museum '+d,'Gallery '+d] for d in required_dates(prefs)}):
            trip = generate_qwen(prefs, self.config)
        self.assertEqual(len(trip['itinerary']['days']), 12)
        self.assertEqual(sum(night_counts), 11)
        self.assertEqual(trip['itinerary']['total'], 400)
        self.assertFalse(trip['itinerary']['checks']['withinBudget'])
        self.assertEqual(trip['end'], '2026-11-13')

    def test_group_allowance_normalization_is_disclosed(self):
        from backend.qwen import normalize_output
        prefs = {**self.preferences, 'travellers': 8}
        output, warnings = normalize_output(copy.deepcopy(self.output), prefs)
        days, costs = validate_output(output, prefs)
        self.assertTrue(any('increased' in warning for warning in warnings))
        self.assertGreaterEqual(sum(c['value'] for c in costs if c['label'] in ('Food', 'Activities')),
                                sum(a['cost'] for d in days for a in d['activities'])*8)

    def test_health_and_config(self):
        self.assertEqual(self.client.get('/api/health').json['mode'], 'qwen')
        with self.assertRaises(ValueError):
            create_app({'TRIP_PROVIDER': 'unknown'})

    @patch('backend.qwen.build_opener')
    def test_avoided_venue_is_rejected_after_bounded_retry(self, opener):
        self.response(opener)
        client=create_app({**self.config,'AVOID_PLACES':['The British Museum']}).test_client()
        response=self.post(client)
        self.assertEqual(response.status_code,502)
        self.assertEqual(opener.return_value.open.call_count,2)
        self.assertNotIn('trip',response.json)

    @patch('backend.qwen.build_opener')
    def test_expansion_cannot_substitute_unallocated_venues(self, opener):
        self.response(opener)
        allocation={d['date']:['Allocated Museum','Allocated Park'] for d in self.output['days']}
        client=create_app({**self.config,'ALLOCATED_PLACES':allocation}).test_client()
        response=self.post(client)
        self.assertEqual(response.status_code,502)
        self.assertEqual(opener.return_value.open.call_count,2)


if __name__ == '__main__':
    unittest.main()
