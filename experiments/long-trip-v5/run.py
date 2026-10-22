import json,time
from pathlib import Path
from unittest.mock import patch
from backend.app import create_app
from backend.qwen import generate_qwen_chunk
from backend.quality import duplicate_places,travel_checks
app=create_app({'RECORD_LLM_EXPERIMENTS':True,'WEATHER_ENABLED':False})
cases=[dict(destination='London',start='2026-11-10',end='2026-11-23',travellers=2,budget=4000,currency='GBP',interests=['History','Art & Culture','Nature','Photography'],notes='Varied trip. Do not revisit venues, including different parts of the same venue.'),
dict(destination='Manchester',start='2026-11-10',end='2026-11-16',travellers=3,budget=2200,currency='GBP',interests=['History','Food','Nature'],notes='Relaxed pace, no repeated attractions.')]
for p in cases:
 segments=[]
 def measured(*args,**kwargs):
  t=time.monotonic()
  result=generate_qwen_chunk(*args,**kwargs)
  segments.append({'start':args[0]['start'],'seconds':round(time.monotonic()-t,1),'excludedVenues':len(args[1].get('AVOID_PLACES',[]))})
  print(json.dumps(segments[-1]),flush=True)
  return result
 t=time.monotonic()
 with patch('backend.qwen.generate_qwen_chunk',side_effect=measured):
  r=app.test_client().post('/api/trips/generate',json=p)
 plan=r.json.get('trip',{}).get('itinerary',{})
 row={'input':p,'status':r.status_code,'seconds':round(time.monotonic()-t,1),'segments':segments,'response':r.json,'duplicates':duplicate_places(plan['days']) if plan else None,'travelGapsChecked':travel_checks(plan['days']) if plan else None}
 Path('experiments/long-trip-v5/'+p['destination'].lower()+'.json').write_text(json.dumps(row,indent=2))
 print(json.dumps({k:v for k,v in row.items() if k!='response'}),flush=True)
