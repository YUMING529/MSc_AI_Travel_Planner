"""Frozen acceptance suite. --live explicitly enables billable Qwen calls; weather is synthetic."""
import argparse,copy,csv,hashlib,json,logging,statistics,sys,time
from datetime import date,datetime,timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app import create_app
from backend.weather import get_weather,_cache
from backend.qwen import PROMPT_VERSION,required_dates,validate_output
from backend.quality import duplicate_places,canonical_place,places_for,interval
NOW=datetime(2026,10,22,12,tzinfo=ZoneInfo('Europe/London'))
SPECS=[
 ('C01','London',1,1,500,'clear','2026-10-24',['History','Photography']),
 ('C02','Edinburgh',2,2,600,'rain','2026-10-24',['History','Art & Culture']),
 ('C03','Manchester',7,3,2200,'mixed','2026-10-24',['Food','Nature','History']),
 ('C04','London',14,2,4000,'alternating','2026-10-24',['History','Art & Culture','Nature','Photography']),
 ('C05','Cardiff',1,50,1,'wind','2026-10-24',['Nature','History']),
 ('C06','Belfast',3,8,100000,'outage','2026-10-24',['Food','History']),
 ('C07','Bath',2,4,800,'out_of_range','2026-11-20',['History','Photography']),
 ('C08','York',4,1,500,'partial','2026-11-05',['History','Art & Culture'])]
def cases():
 return [dict(id=i,weather=w,days=n,input=dict(destination=c,start=s,end=(date.fromisoformat(s)+timedelta(days=n-1)).isoformat(),travellers=t,budget=b,currency='GBP',interests=interests,notes='Avoid repeated venues. Leave realistic travel gaps. Adapt activities to the supplied weather; do not invent missing forecasts.')) for i,c,n,t,b,w,s,interests in SPECS]
def weather_body(scenario):
 dates=[(NOW.date()+timedelta(days=i)).isoformat() for i in range(16)]
 daily={k:[] for k in ('weather_code','temperature_2m_max','temperature_2m_min','precipitation_probability_max','wind_speed_10m_max')}
 daily['time']=dates
 for i in range(16):
  mode=('rain' if i%2==0 else 'clear') if scenario=='alternating' else scenario
  code,rain,wind={'rain':(63,85,18),'wind':(0,5,48),'mixed':(3,45,20)}.get(mode,(1,10,12))
  for k,v in zip(('weather_code','temperature_2m_max','temperature_2m_min','precipitation_probability_max','wind_speed_10m_max'),(code,17,9,rain,wind)):daily[k].append(v)
 return {'daily':daily}
def fingerprint():
 files=sorted(list((ROOT/'backend').glob('*.py'))+[Path(__file__)])
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
def evaluate(response,prefs,expected_weather):
 plan=response.get('trip',{}).get('itinerary')
 if not plan:return {}
 result={}
 try:
  days,costs=validate_output(copy.deepcopy(plan),prefs);result['schema_dates_times']=True
 except Exception as error:return {'schema_dates_times':False,'validation_exception':type(error).__name__}
 repeats=duplicate_places(days);result['repeated_names']=repeats
 result['no_detected_repeats']=not repeats
 result['travel_gaps']=all(a.get('travelMinutes',0)<=interval(b['time'])[0]-interval(a['time'])[1] for d in days for a,b in zip(d['activities'],d['activities'][1:]))
 result['category_minima']=all(next(c['value'] for c in costs if c['label']==category)+.001>=sum(a['cost']*prefs['travellers'] for d in days for a in d['activities'] if a.get('costCategory')==category) for category in ('Food','Activities'))
 result['sum_consistent']=abs(sum(c['value'] for c in costs)-plan['total'])<.001
 result['budget_flag_consistent']=plan['checks']['withinBudget']==(plan['total']<=prefs['budget'])
 result['over_budget']=plan['total']>prefs['budget']
 result['over_budget_disclosed']=not result['over_budget'] or any('exceeds your budget' in w for w in plan['warnings'])
 result['weather_snapshot_matches']=plan.get('weather')==expected_weather
 result['weather_reason_authoritative']=all(a.get('weatherReason')==next(w['reason'] for w in expected_weather['days'] if w['date']==d['date']) for d in days for a in d['activities'])
 result['outdoor_backups']=all(a.get('indoorAlternative','').strip() for d in days for a in d['activities'] if a.get('setting') in ('mixed','outdoor'))
 allocation=plan.get('venueAllocation')
 result['allocation_matches']=not allocation or all({canonical_place(p) for a in d['activities'] for p in places_for(a)}=={canonical_place(p) for p in allocation[d['date']]} for d in days)
 indoor_dates={w['date'] for w in expected_weather['days'] if w['recommendation']=='indoor'}
 attractions=[a for d in days if d['date'] in indoor_dates for a in d['activities'] if a.get('costCategory')!='Food']
 result['bad_weather_named_activities']=len(attractions)
 result['bad_weather_outdoor_or_mixed']=[a['title'] for a in attractions if a.get('setting')!='indoor']
 result['estimated_total']=plan['total'];result['warnings']=plan['warnings']
 checks=['schema_dates_times','no_detected_repeats','travel_gaps','category_minima','sum_consistent','budget_flag_consistent','over_budget_disclosed','weather_snapshot_matches','weather_reason_authoritative','outdoor_backups','allocation_matches']
 result['contract_pass']=all(result[k] for k in checks)
 return result
class Capture(logging.Handler):
 def __init__(self):super().__init__();self.messages=[]
 def emit(self,record):self.messages.append(record.getMessage())
def run():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--live',action='store_true');parser.add_argument('--output',required=True)
 args=parser.parse_args()
 if not args.live:parser.error('--live is required; Qwen calls may incur charges')
 out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
 app=create_app({'TRIP_PROVIDER':'qwen','WEATHER_ENABLED':True,'RECORD_LLM_EXPERIMENTS':False})
 if not app.config['DASHSCOPE_API_KEY'].strip():raise SystemExit('Backend key missing')
 before=fingerprint()
 manifest={'startedAt':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'promptVersion':PROMPT_VERSION,'model':app.config['QWEN_MODEL'],'weather':'synthetic HTTP fixtures with frozen weather clock; real Qwen','weatherClock':NOW.isoformat(),'sourceHashes':before,'cases':cases(),'repeatsPerCase':1}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
 base=cases()[0]['input']
 invalids=[('unsupported_city',{'destination':'Paris'}),('15_days',{'end':'2026-11-07'}),('zero_people',{'travellers':0}),('51_people',{'travellers':51}),('fractional_people',{'travellers':1.5}),('zero_budget',{'budget':0}),('over_max_budget',{'budget':100000.01}),('reverse_dates',{'end':'2026-10-23'})]
 controls=[]
 with patch('backend.app.generate_qwen') as provider,patch('backend.app.get_weather') as weather:
  for name,changes in invalids:
   r=app.test_client().post('/api/trips/generate',json={**base,**changes})
   controls.append({'id':name,'status':r.status_code,'pass':r.status_code==400})
  assert provider.call_count==weather.call_count==0
 (out/'invalid-inputs.json').write_text(json.dumps(controls,indent=2))
 results=[]
 for case in cases():
  capture=Capture();logger=logging.getLogger('backend.qwen');logger.addHandler(capture)
  scenario=case['weather'];_cache.clear()
  def frozen(prefs,enabled=True):return get_weather(prefs,enabled=enabled,now=NOW)
  with patch('backend.weather.urlopen') as network,patch('backend.app.get_weather',side_effect=frozen):
   if scenario=='outage':network.side_effect=TimeoutError('Synthetic weather timeout')
   else:network.return_value.__enter__.return_value.read.return_value=json.dumps(weather_body(scenario)).encode()
   expected_weather=frozen(case['input']);_cache.clear()
   started=time.monotonic()
   r=app.test_client().post('/api/trips/generate',json=case['input'])
   elapsed=round(time.monotonic()-started,3)
  logger.removeHandler(capture)
  row={**case,'status':r.status_code,'seconds':elapsed,'response':r.json,'validationEvents':capture.messages,'metrics':evaluate(r.json or {},case['input'],expected_weather)}
  results.append(row);(out/(case['id']+'.json')).write_text(json.dumps(row,ensure_ascii=False,indent=2))
  (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
  print(json.dumps({'id':case['id'],'city':case['input']['destination'],'days':case['days'],'weather':scenario,'status':r.status_code,'seconds':elapsed,'contract_pass':row['metrics'].get('contract_pass',False),'weather_review':row['metrics'].get('bad_weather_outdoor_or_mixed',[])},ensure_ascii=False),flush=True)
 success=[r for r in results if r['status']==200]
 summary={'cases':len(results),'generation_success':len(success),'generation_success_rate':len(success)/len(results),'contract_pass':sum(r['metrics'].get('contract_pass',False) for r in results),'invalid_inputs_pass':sum(r['pass'] for r in controls),'invalid_inputs_total':len(controls),'mean_seconds_all':round(statistics.mean(r['seconds'] for r in results),3),'median_seconds_all':round(statistics.median(r['seconds'] for r in results),3),'max_seconds_all':max(r['seconds'] for r in results),'unchanged_sources':before==fingerprint(),'finishedAt':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}
 (out/'summary.json').write_text(json.dumps(summary,indent=2))
 with (out/'results.csv').open('w',newline='') as f:
  writer=csv.writer(f);writer.writerow(['id','city','days','travellers','budget','weather_fixture','http','seconds','contract_pass','estimated_total','over_budget','bad_weather_outdoor_or_mixed_count'])
  for r in results:
   m=r['metrics'];writer.writerow([r['id'],r['input']['destination'],r['days'],r['input']['travellers'],r['input']['budget'],r['weather'],r['status'],r['seconds'],m.get('contract_pass',False),m.get('estimated_total'),m.get('over_budget'),len(m.get('bad_weather_outdoor_or_mixed',[]))])
 print(json.dumps(summary),flush=True)
if __name__=='__main__':run()
