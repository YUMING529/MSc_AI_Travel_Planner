import json,time,unittest
from unittest.mock import patch
from backend.outline import validate_outline,generate_outline
from backend.qwen import PlannerError
class OutlineTests(unittest.TestCase):
    def test_dates_aliases_and_unique_parent_venues(self):
        dates=['2026-11-01','2026-11-02']
        data={'days':[{'date':dates[0],'places':['V&A Museum','British Museum']},{'date':dates[1],'places':['Victoria and Albert Museum','National Gallery']}]}
        with self.assertRaises(PlannerError): validate_outline(data,dates)
        data['days'][1]['places'][0]='Tate Modern'
        self.assertEqual(len(validate_outline(data,dates)),2)
        data['days'][1]['date']=dates[0]
        with self.assertRaises(PlannerError): validate_outline(data,dates)

    @patch('backend.outline.build_opener')
    def test_invalid_outline_has_one_retry_and_no_unbounded_loop(self,opener):
        opener.return_value.open.return_value.__enter__.return_value.read.return_value=b'{}'
        with self.assertRaises(PlannerError):
            generate_outline({},dict(DASHSCOPE_API_KEY='test',QWEN_BASE_URL='https://example.com/v1',QWEN_MODEL='test',GENERATION_DEADLINE=time.monotonic()+10),['2026-11-01'])
        self.assertEqual(opener.return_value.open.call_count,2)

    def test_optional_stop_removal_preserves_route_and_never_fills_missing_places(self):
        from backend.outline import constrain_to_allocation
        day={'date':'2026-11-01','activities':[
          {'title':'First Museum','places':['First Museum'],'travelMinutes':10},
          {'title':'Unallocated Park','places':['Unallocated Park'],'travelMinutes':20},
          {'title':'Second Museum','places':['Second Museum'],'travelMinutes':0}]}
        data={'days':[day]}
        warnings=constrain_to_allocation(data,{'2026-11-01':['First Museum','Second Museum']})
        self.assertEqual(len(day['activities']),2)
        self.assertEqual(day['activities'][0]['travelMinutes'],30)
        self.assertTrue(warnings)
        constrain_to_allocation(data,{'2026-11-01':['First Museum','Missing Venue']})
        self.assertEqual([a['title'] for a in day['activities']],['First Museum'])
