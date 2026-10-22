"""Deterministic sample provider. Does not call an LLM or verify travel facts."""
import json
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

SAMPLE = json.loads(Path(__file__).with_name('sample_itinerary.json').read_text())


def generate_sample(preferences):
    n = preferences['travellers']
    costs = [dict(label=label, value=value) for label, value in (
        ('Intercity transport', 120*n), ('Accommodation', 140*((n+1)//2)),
        ('Food', 90*n), ('Activities', 40*n), ('Local transport', 30*n))]
    total = sum(item['value'] for item in costs)
    start = date.fromisoformat(preferences['start'])
    return {**preferences, 'id': str(uuid4()), 'itinerary': {
        'mode': 'sample',
        'days': [{'date': (start+timedelta(days=i)).isoformat(), 'activities': deepcopy(activities)}
                 for i, activities in enumerate(SAMPLE)],
        'costs': costs, 'total': total,
        'checks': {'withinBudget': total <= preferences['budget'], 'durationDays': 2,
                   'factsVerified': False},
        'warnings': ['Fixed London sample; no live AI generation.',
                     'Interests highlight matches; notes do not alter the route.',
                     'Prices, opening hours and travel times are unverified estimates.',
                     'Intercity allowance assumes travel from Edinburgh. Arrival before the first activity and any extra hotel night must be checked.'],
    }}
