import io
import json
import unittest
from unittest.mock import patch

from src.gemini_chat import reply
from src.site_analyst import validate_action, system_context
from src.customer_lab import load_calibration


class SiteAnalystTests(unittest.TestCase):
    def test_navigation_and_group_are_validated(self):
        changes,section,_ = validate_action('show_site_view', {'section':'audience','group':'Specialist enthusiasts','response_day':7})
        self.assertEqual(changes, {'repetition_profile':3,'response_checkpoint':7,'audience_tab':'Response timing'})
        self.assertEqual(section,'audience')
        for args in [{'section':'javascript:alert(1)'}, {'section':'answer','tab':'Conversion rates'},
                     {'section':'audience','response_day':4}, {'section':'audience','group':'Invented group'}]:
            with self.assertRaises(ValueError):
                validate_action('show_site_view',args)

    def test_campaign_drafts_are_bounded_and_do_not_run(self):
        changes,section,_ = validate_action('set_campaign_controls', {'campaign':'focused','groups':['Specialist enthusiasts'],'contact_cap':6,'repeat_percent':80,'starting_customers':100000})
        self.assertEqual(changes['focus_groups'],[3])
        self.assertEqual(changes['focus_repeat'],80)
        self.assertEqual(section,'simulation')
        self.assertNotIn('comparison_run',changes)
        for args in [{'contact_cap':4},{'campaign':'focused','repeat_percent':81},
                     {'campaign':'wide','groups':[]},{'campaign':'focused','contact_cap':True},
                     {'campaign':'wide','contact_cap':50},{'playing':True}]:
            with self.assertRaises(ValueError):
                validate_action('set_campaign_controls',args)

    def test_tool_roundtrip_preserves_signature_and_passes_results_back(self):
        content={'role':'model','parts':[{'thoughtSignature':'signature', 'functionCall':{'name':'show_site_view','args':{'section':'audience'}}}]}
        responses=[{'candidates':[{'content':content}]}, {'candidates':[{'content':{'parts':[{'text':'Opened audience.'}]}}]}]
        with patch('src.gemini_chat.urlopen',side_effect=[io.BytesIO(json.dumps(r).encode()) for r in responses]) as send:
            result=reply('test-key',[{'role':'user','content':'Show the audience'}],tools=[{}],tool_handler=lambda name,args:{'ok':True},system_instruction='Grounded knowledge')
        payload=json.loads(send.call_args.args[0].data)
        self.assertEqual(payload['contents'][-2],content)
        self.assertTrue(payload['contents'][-1]['parts'][0]['functionResponse']['response']['ok'])
        self.assertEqual(result,'Opened audience.')

    def test_evidence_uses_actual_data_not_entire_session_state(self):
        cal=load_calibration('app/data/customer_lab')
        context=system_context(cal,{'GEMINI_API_KEY':'secret-do-not-send','initial_population':100000})
        self.assertNotIn('secret-do-not-send',context)
        self.assertIn('benchmark_increment_percentage_points',context)
        self.assertIn('"saved_simulation": null',context)
        self.assertIn('Organic',context)


if __name__=='__main__':
    unittest.main()
