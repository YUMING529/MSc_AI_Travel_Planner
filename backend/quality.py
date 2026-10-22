"""Conservative duplicate detection; venue identity and travel estimates remain unverified."""
import re
import unicodedata


def canonical_place(name):
    text = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    text = text.replace('&', ' and ')
    text = re.sub(r'\bsaint\b', 'st', text)
    text = re.sub(r'\([^)]*\)', ' ', text)
    text = re.sub(r"['’]s\b", 's', text)
    # A different area of the same venue is still a repeat visit.
    text = re.sub(r'\b(crypt|exterior|interior|access|only)\b', ' ', text)
    text = re.sub(r'\b(visit|visiting|explore|exploring|tour|guided|the|at|of)\b', ' ', text)
    key = ' '.join(re.findall(r'[a-z0-9]+', text))
    aliases = {'v and a':'victoria and albert museum', 'v and a museum':'victoria and albert museum',
               'kew gardens':'royal botanic gardens kew', 'royal botanic gardens':'royal botanic gardens kew'}
    return aliases.get(key, key)


def places_for(activity):
    # Meals can legitimately recur; do not flag a generic lunch as a repeated attraction.
    is_food = activity.get('costCategory') == 'Food' or activity.get('tags') == ['Food']
    places = activity.get('places')
    if not places:
        title = activity['title'].strip()
        # Only generic meal labels are exempt. Named markets are attractions too.
        if is_food and re.fullmatch(r'(breakfast|lunch|dinner|snacks?|afternoon tea)( at (a |the )?(local )?(restaurant|pub|cafe|hotel))?', title, re.I):
            return []
        title = re.sub(r'^(breakfast|lunch|dinner|afternoon tea) at ', '', title, flags=re.I)
        places = [title]
    return [p for p in places if len(canonical_place(p)) > 5]


def duplicate_places(days):
    seen, repeated = set(), set()
    for day in days:
        for activity in day['activities']:
            for key in {canonical_place(place) for place in places_for(activity)}:
                if key in seen:
                    repeated.add(key)
                seen.add(key)
    return sorted(repeated)


def interval(value):
    h1, m1, h2, m2 = map(int, re.findall(r'\d+', value))
    return h1*60+m1, h2*60+m2


def travel_checks(days):
    pairs = [(a,b) for day in days for a,b in zip(day['activities'], day['activities'][1:])]
    return all('travelMinutes' in a for a,b in pairs)
