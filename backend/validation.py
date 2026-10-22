"""Request validation shared by every generation request."""
from datetime import date
from math import isfinite

DESTINATIONS = ['London', 'Edinburgh', 'Manchester', 'Birmingham', 'Liverpool', 'Glasgow', 'Bristol', 'Leeds', 'Cardiff', 'Belfast', 'Newcastle', 'Nottingham', 'Sheffield', 'Oxford', 'Cambridge', 'Bath', 'York']
MAX_DAYS = 14
MAX_TRAVELLERS = 50

INTERESTS = {'History', 'Food', 'Photography', 'Nature', 'Shopping', 'Art & Culture', 'Nightlife'}


class ValidationError(ValueError):
    pass


def validate_preferences(data, mode='qwen'):
    if not isinstance(data, dict):
        raise ValidationError('Send a JSON object containing trip preferences.')
    if data.get('destination') not in DESTINATIONS:
        raise ValidationError('Choose a supported UK city.')
    if data.get('currency') != 'GBP':
        raise ValidationError('This prototype currently supports GBP only.')
    try:
        start, end = (date.fromisoformat(data[key]) for key in ('start', 'end'))
        if start.isoformat() != data['start'] or end.isoformat() != data['end']:
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise ValidationError('Provide valid start and end dates in YYYY-MM-DD format.')
    if not 1 <= (end - start).days + 1 <= MAX_DAYS:
        raise ValidationError('Choose a trip lasting 1–14 days (including start and end dates).')
    try:
        budget = float(data['budget'])
        if isinstance(data['budget'], bool) or not isfinite(budget) or not 1 <= budget <= 100000:
            raise ValueError()
    except (KeyError, ValueError, TypeError, OverflowError):
        raise ValidationError('Budget must be a number between 1 and 100,000.')
    travellers = data.get('travellers')
    if type(travellers) is not int or not 1 <= travellers <= MAX_TRAVELLERS:
        raise ValidationError('Enter a whole number of travellers between 1 and 50.')
    interests = data.get('interests')
    if not isinstance(interests, list) or any(not isinstance(i, str) or i not in INTERESTS for i in interests):
        raise ValidationError('Choose interests from the available options.')
    notes = data.get('notes', '')
    if not isinstance(notes, str) or len(notes) > 2000:
        raise ValidationError('Additional preferences must be text of up to 2,000 characters.')
    if mode == 'sample' and (data['destination'] != 'London' or (end-start).days != 1 or travellers > 4):
        raise ValidationError('Offline sample mode only supports London, two days and 1–4 travellers. Enable Qwen for other trips.')
    return dict(destination=data['destination'], start=start.isoformat(), end=end.isoformat(),
                currency='GBP', budget=budget, travellers=travellers,
                interests=list(dict.fromkeys(interests)), notes=notes.strip())
