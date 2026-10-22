import unittest
from backend.app import create_app


class PlannerAPI(unittest.TestCase):
    def setUp(self):
        self.client = create_app({'TRIP_PROVIDER': 'sample'}).test_client()
        self.preferences = dict(destination='London', start='2026-11-02', end='2026-11-03',
                                currency='GBP', budget=500, travellers=1,
                                interests=['History', 'Food'], notes='Relaxed pace')

    def generate(self, **changes):
        return self.client.post('/api/trips/generate', json={**self.preferences, **changes})

    def test_valid_trip(self):
        response = self.generate()
        self.assertEqual(response.status_code, 200)
        trip = response.json['trip']
        self.assertEqual(trip['itinerary']['total'], 420)
        self.assertEqual([d['date'] for d in trip['itinerary']['days']], ['2026-11-02', '2026-11-03'])
        self.assertFalse(trip['itinerary']['checks']['factsVerified'])
        self.assertEqual(trip['notes'], 'Relaxed pace')
        self.assertNotEqual(trip['id'], self.generate().json['trip']['id'])

    def test_group_costs_and_budget_warning(self):
        trip = self.generate(travellers=3, budget=100).json['trip']
        self.assertEqual(trip['itinerary']['total'], 1120)
        self.assertFalse(trip['itinerary']['checks']['withinBudget'])

    def test_invalid_preferences(self):
        for change in [dict(destination='Edinburgh'), dict(currency='USD'), dict(start='bad'),
                       dict(end='2026-11-01'), dict(end='2026-11-05'), dict(budget=0),
                       dict(budget='NaN'), dict(budget=True), dict(travellers=True),
                       dict(travellers=5), dict(interests=[{}]), dict(notes='x'*2001)]:
            with self.subTest(change=change):
                response = self.generate(**change)
                self.assertEqual(response.status_code, 400)
                self.assertIn('message', response.json['error'])

    def test_bad_request_bodies(self):
        for data in ['null', '[]', '{', '{}']:
            self.assertEqual(self.client.post('/api/trips/generate', data=data, content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post('/api/trips/generate', data='text').status_code, 415)
        self.assertEqual(self.client.post('/api/trips/generate', data='x'*17000, content_type='application/json').status_code, 413)

    def test_health(self):
        self.assertEqual(self.client.get('/api/health').json, {'status': 'ok', 'mode': 'sample'})


if __name__ == '__main__':
    unittest.main()
