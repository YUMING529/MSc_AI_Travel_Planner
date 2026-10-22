import copy
import unittest
from unittest.mock import patch
from backend.qwen import validate_output, generate_qwen, PlannerError, required_dates, normalize_output
from backend.quality import duplicate_places, canonical_place, travel_checks
from backend.planner import generate_sample

class QualityTests(unittest.TestCase):
    def setUp(self):
        self.prefs=dict(destination='London', start='2026-11-01', end='2026-11-02', travellers=2,budget=500,interests=[],currency='GBP')
        self.plan=generate_sample(self.prefs)['itinerary']
        patcher=patch('backend.outline.generate_outline',side_effect=lambda prefs,config,dates:{d:['Museum '+d,'Gallery '+d] for d in dates})
        self.outline=patcher.start()
        self.addCleanup(patcher.stop)

    def test_normalized_duplicate_and_meal_exclusion(self):
        self.assertEqual(canonical_place('The British Museum (guided tour)'),canonical_place('British Museum'))
        self.assertEqual(canonical_place("St. Paul's Cathedral Crypt"), canonical_place("St Pauls Cathedral (Exterior)"))
        days=[{'activities':[{'title':'British Museum','places':['British Museum']},{'title':'Visit the British Museum','places':['The British Museum']}, {'title':'Lunch','costCategory':'Food'}, {'title':'Lunch','costCategory':'Food'}]}]
        self.assertEqual(duplicate_places(days),['british museum'])

    def test_travel_gap_and_final_travel(self):
        self.plan['days'][0]['activities'][0]['travelMinutes']=31
        with self.assertRaises(PlannerError) as error: validate_output(self.plan,self.prefs)
        self.assertEqual(error.exception.reason,'insufficient_travel_gap')
        self.plan['days'][0]['activities'][0]['travelMinutes']=30
        days,_=validate_output(self.plan,self.prefs)
        self.assertEqual(days[0]['activities'][0]['travel'],'30 min to next activity')
        self.assertFalse(travel_checks(days))
        for day in self.plan['days']:
            for a in day['activities']: a['travelMinutes']=10
        days,_=validate_output(self.plan,self.prefs)
        self.assertTrue(travel_checks(days))

    def test_bad_travel_and_place_types(self):
        for change in ({'travelMinutes':True},{'travelMinutes':-1},{'travelMinutes':1000},{'places':[{}]},{'costCategory':'Hotel'}):
            plan=copy.deepcopy(self.plan);plan['days'][0]['activities'][0].update(change)
            with self.assertRaises(PlannerError): validate_output(plan,self.prefs)

    @patch('backend.qwen.generate_qwen_chunk')
    def test_segments_use_one_disjoint_global_allocation(self, chunk):
        allocations=[]
        def answer(prefs,config,lodging_nights=None):
            allocations.append(config['ALLOCATED_PLACES'])
            days=[{'date':d,'activities':[dict(title=name,places=[name],time=f'{10+i*2}:00 - {11+i*2}:00',period='Morning',description='Visit',note='Verify',cost=0,tags=[],travelMinutes=0) for i,name in enumerate(config['ALLOCATED_PLACES'][d])]} for d in required_dates(prefs)]
            return {'id':prefs['start'],'itinerary':{'days':days,'warnings':[],'costs':[{'label':c['label'],'value':0} for c in self.plan['costs']]}}
        chunk.side_effect=answer
        trip=generate_qwen({**self.prefs,'end':'2026-11-07'}, {'QWEN_MODEL':'test'})
        self.assertEqual(len(trip['itinerary']['days']),7)
        self.assertEqual(duplicate_places(trip['itinerary']['days']),[])
        self.assertEqual(chunk.call_count,3)
        self.assertEqual(self.outline.call_count,1)
        self.assertTrue(all(a==allocations[0] for a in allocations))

    @patch('backend.qwen.generate_qwen_chunk')
    def test_merge_rejects_duplicates_even_if_segment_validator_is_bypassed(self, chunk):
        def answer(prefs,config,lodging_nights=None):
            return {'id':prefs['start'],'itinerary':{'days':[{'date':d,'activities':[dict(title='British Museum',time='10:00 - 11:00',period='Morning',description='Visit',note='Verify',cost=0,tags=[])]} for d in required_dates(prefs)],'warnings':[],'costs':[{'label':c['label'],'value':0} for c in self.plan['costs']]}}
        chunk.side_effect=answer
        with self.assertRaises(PlannerError):
            generate_qwen({**self.prefs,'end':'2026-11-04'}, {'QWEN_MODEL':'test'})

    def test_category_minima_cannot_subsidize_each_other(self):
        self.plan['days'][0]['activities'][0].update(cost=12.34, costCategory='Activities')
        self.plan['costs'] = [{'label':c['label'],'value':10000 if c['label']=='Food' else 0} for c in self.plan['costs']]
        fixed,warnings = normalize_output(self.plan,self.prefs)
        activity_min = sum(a['cost']*2 for d in fixed['days'] for a in d['activities'] if 'Food' not in a['tags'])
        self.assertGreaterEqual(next(c['value'] for c in fixed['costs'] if c['label']=='Activities'),activity_min)
        self.assertTrue(warnings)

    def test_sample_results_do_not_share_mutable_activities(self):
        first=generate_sample(self.prefs)
        first['itinerary']['days'][0]['activities'][0]['title']='Changed by caller'
        self.assertNotEqual(generate_sample(self.prefs)['itinerary']['days'][0]['activities'][0]['title'],'Changed by caller')

    @patch('backend.qwen.build_opener')
    def test_expired_deadline_does_not_call_provider(self,opener):
        from backend.qwen import generate_qwen_chunk
        with self.assertRaises(PlannerError) as error:
            generate_qwen_chunk(self.prefs,dict(DASHSCOPE_API_KEY='test-key',QWEN_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1',QWEN_MODEL='test',GENERATION_DEADLINE=0))
        self.assertEqual(error.exception.code,'provider_timeout')
        opener.assert_not_called()

    def test_safe_label_variants_normalized(self):
        item=self.plan['days'][0]['activities'][0]
        item.update(setting=' Indoors ',weatherReason='Sheltered',costCategory=' activities ')
        fixed,_=normalize_output(self.plan,self.prefs)
        self.assertEqual(fixed['days'][0]['activities'][0]['setting'],'indoor')
        self.assertEqual(fixed['days'][0]['activities'][0]['costCategory'],'Activities')
        validate_output(fixed,self.prefs)

    def test_aliases_and_empty_place_lists_do_not_hide_repeats(self):
        self.assertEqual(canonical_place('V&A Museum'),canonical_place('Victoria and Albert Museum'))
        self.assertEqual(canonical_place('Kew Gardens'),canonical_place('Royal Botanic Gardens Kew'))
        days=[{'activities':[{'title':'British Museum','places':[]},{'title':'British Museum','places':[]}]}]
        self.assertEqual(duplicate_places(days),['british museum'])
        # Two names for one venue within a single visit are not two visits.
        self.assertEqual(duplicate_places([{'activities':[{'title':'V&A','places':['V&A Museum','Victoria and Albert Museum']}]}]),[])

    @patch('backend.qwen.generate_qwen_chunk')
    def test_outline_failure_prevents_expansion_calls(self,chunk):
        self.outline.side_effect=PlannerError('provider_rate_limit','Quota exceeded',503)
        with self.assertRaises(PlannerError):
            generate_qwen({**self.prefs,'end':'2026-11-14'}, {'QWEN_MODEL':'test'})
        chunk.assert_not_called()

    def test_named_food_venues_are_not_exempt_from_deduplication(self):
        days=[{'activities':[{'title':'Food walk','places':['Borough Market'],'costCategory':'Food'},
                            {'title':'Borough Market','places':[],'costCategory':'Food'}]}]
        self.assertEqual(duplicate_places(days),['borough market'])
        days[0]['activities'][1]['title']='Lunch at Borough Market'
        self.assertEqual(duplicate_places(days),['borough market'])

    def test_missing_non_food_place_uses_existing_title_without_retry(self):
        self.plan['days'][0]['activities'][0].update(places=[],costCategory='Activities')
        fixed,warnings=normalize_output(self.plan,self.prefs)
        self.assertEqual(fixed['days'][0]['activities'][0]['places'],[fixed['days'][0]['activities'][0]['title']])
        self.assertTrue(any('derived from activity titles' in w for w in warnings))
