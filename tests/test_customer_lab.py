"""Behavioral checks for population conservation, capacity and seeded histories."""
from pathlib import Path
from dataclasses import replace
import unittest
import numpy as np
import pandas as pd
from src.customer_lab import Scenario,simulate,load_calibration,make_population
from src.retail_metadata import MISSIONS,identify_missions,decision_metadata

ROOT=Path(__file__).resolve().parents[1]

class CustomerLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cal=load_calibration(ROOT/'app/data/customer_lab')

    def test_linked_history_and_capacity(self):
        s=Scenario(population=5000,contact_budget=12000,contact_cap=3)
        r=simulate(s,self.cal,record_events=True)
        c=r['customers'];e=r['contacts'];t=r['transitions']
        self.assertTrue(c.customer_id.is_unique)
        self.assertTrue(e.customer_id.isin(c.customer_id).all())
        self.assertTrue(t.customer_id.isin(c.customer_id).all())
        self.assertEqual(len(e),int(c.contacts.sum()))
        self.assertLessEqual(len(e),s.contact_budget)
        self.assertLessEqual(c.contacts.max(),3)
        self.assertFalse(e.duplicated(['customer_id','day']).any())
        self.assertTrue((np.diff(r['contact_history'],axis=0)>=0).all())
        self.assertTrue((r['daily'].contacts+r['daily'].unused_contacts).sum()==s.contact_budget)
        self.assertTrue((e.merge(c[['customer_id','arrival_day']],on='customer_id').day>=e.merge(c[['customer_id','arrival_day']],on='customer_id').arrival_day).all())
        for day in range(s.days+1):self.assertEqual(len(r['history'][day]),len(c))

    def test_zero_contacts_cannot_generate_ad_responses(self):
        r=simulate(Scenario(population=5000,contact_budget=0),self.cal)
        self.assertEqual(r['daily'].ad_responses.max(),0)
        self.assertEqual(r['daily'].unique_reached.max(),0)

    def test_retail_groups_are_defined_by_customer_metadata(self):
        bank=self.cal['templates']
        expected=bank.shopping_mission.map(dict(zip(MISSIONS,range(5))))
        self.assertTrue(expected.eq(bank.segment_id).all())
        self.assertTrue(bank.groupby('segment_id').response_cell.nunique().ge(3).all())
        self.assertTrue(bank.loc[bank.segment_id.eq(0),'orders_last_year'].ge(4).all())
        self.assertTrue(bank.loc[bank.segment_id.eq(1),'promotion_affinity'].ge(.75).all())
        self.assertTrue(bank.typical_basket.gt(0).all())
        np.testing.assert_array_equal(identify_missions(bank),bank.segment_id)

    def test_retail_decision_layer_preserves_probability_and_visible_contrasts(self):
        shapes=self.cal['shapes'];frequency=self.cal['frequency']
        self.assertEqual(shapes.day.max(),30)
        for _,a in shapes.groupby('segment_id'):
            self.assertTrue(a.response_share.between(0,1).all())
            self.assertTrue(a.sort_values('day').response_share.diff().dropna().ge(0).all())
            self.assertAlmostEqual(a.sort_values('day').response_share.iloc[-1],1.)
            self.assertEqual(len(a),30)
        for _,a in frequency.groupby('segment_id'):
            self.assertTrue(a.coverage.between(0,1).all())
            self.assertTrue(a.sort_values('contact_cap').coverage.diff().dropna().ge(0).all())
        day1=shapes.query('day==1').set_index('segment_id').response_share
        cap3=frequency.query('contact_cap==3').set_index('segment_id').coverage
        self.assertGreater(day1.loc[4]-day1.loc[3],.4)
        self.assertGreater(cap3.loc[4]-cap3.loc[3],.3)
        pace,extra=decision_metadata(np.arange(5),np.arange(5))
        self.assertTrue((pace>0).all());self.assertTrue((extra>=0).all())

    def test_generated_customers_keep_retail_attributes(self):
        r=simulate(Scenario(population=5000),self.cal)
        self.assertTrue({'shopping_mission','orders_last_year','preferred_category','typical_basket','delivery_preference','promotion_affinity'}.issubset(r['customers'].columns))
        self.assertTrue(r['customers'].shopping_mission.map(dict(zip(MISSIONS,range(5)))).eq(r['customers'].segment_id).all())

    def test_explicit_profile_eligibility(self):
        s=Scenario(population=5000,contact_budget=12000,breadth=100.,eligible_profiles=(3,4))
        r=simulate(s,self.cal,record_events=True)
        self.assertTrue(r['contacts'].segment_id.isin([3,4]).all())
        self.assertGreater(len(r['contacts']),0)

    def test_fixed_seed_and_no_population_replenishment(self):
        s=Scenario(population=5000,weekly_arrivals=0,weekly_turnover=0,weekly_return=0)
        a=simulate(s,self.cal);b=simulate(s,self.cal)
        pd.testing.assert_frame_equal(a['daily'],b['daily'])
        self.assertEqual(len(a['customers']),5000)
        self.assertEqual(a['daily'].departures.sum(),0)
        self.assertEqual(a['daily'].returning.sum(),0)
        last=a['daily'].iloc[-1]
        self.assertEqual(last.active+last.responded,5000)

    def test_turnover_changes_active_population_and_flow_reconciles(self):
        s=Scenario(population=5000,contact_budget=0,weekly_arrivals=0,weekly_return=0)
        low=simulate(replace(s,weekly_turnover=0),self.cal)
        high=simulate(replace(s,weekly_turnover=40),self.cal)
        self.assertLess(high['daily'].iloc[-1].active,low['daily'].iloc[-1].active)
        self.assertTrue(high['flows'].groupby('day').customers.sum().eq(5000).all())

    def test_specialists_only_means_the_entire_starting_population(self):
        s=Scenario(population=100000,weekly_arrivals=15,population_profiles=(3,))
        c=make_population(s,self.cal)
        self.assertEqual(int(c.arrival_day.eq(0).sum()),100000)
        self.assertTrue(c.segment_id.eq(3).all())
        self.assertEqual(len(c),100000+round(100000*.15*30/7))

    def test_selected_mixture_preserves_conditional_shares_and_shared_people(self):
        s=Scenario(population=10000,weekly_arrivals=15,population_profiles=(3,4),eligible_profiles=(3,))
        a=make_population(s,self.cal);b=make_population(replace(s,eligible_profiles=(4,)),self.cal)
        pd.testing.assert_frame_equal(a,b)
        weights=self.cal['groups'].set_index('segment_id').loc[[3,4],'share']
        weights/=weights.sum()
        for mask in [a.arrival_day.eq(0),a.arrival_day.gt(0)]:
            cohort=a[mask];counts=cohort.segment_id.value_counts().reindex([3,4],fill_value=0)
            self.assertTrue((abs(counts-len(cohort)*weights)<1).all())
        self.assertTrue(a.segment_id.isin([3,4]).all())

    def controlled_timing_calibration(self,organic=False):
        c=dict(self.cal);c.pop('response_cells',None)
        c['groups']=self.cal['groups'].copy()
        c['groups']['baseline_rate']=1. if organic else 0.
        c['groups']['incremental_rate']=0. if organic else 1.
        c['templates']=self.cal['templates'].query('segment_id==0').iloc[[0]].copy()
        c['shapes']=self.cal['shapes'].copy()
        c['shapes']['response_share']=c['shapes'].day.ge(3).astype(float)
        c['frequency']=self.cal['frequency'].copy();c['frequency']['coverage']=1.
        return c

    def test_late_first_ad_does_not_inherit_time_before_contact(self):
        s=Scenario(population=1,days=5,contact_budget=1,contact_cap=1,breadth=100.,weekly_arrivals=0,weekly_turnover=0,weekly_return=0,population_profiles=(0,))
        r=simulate(s,self.controlled_timing_calibration(),record_events=True)
        self.assertEqual(r['contacts'].day.tolist(),[5])
        self.assertEqual(r['customers'].first_contact_day.iloc[0],5)
        self.assertEqual(r['daily'].ad_responses.max(),0)

    def test_response_clock_continues_without_ads_and_does_not_reset_on_repeats(self):
        base=Scenario(population=1,days=5,contact_budget=5,contact_cap=1,breadth=100.,weekly_arrivals=0,weekly_turnover=0,weekly_return=0,population_profiles=(0,))
        for scenario in [base,replace(base,contact_budget=10,contact_cap=5)]:
            r=simulate(scenario,self.controlled_timing_calibration(),record_events=True)
            self.assertEqual(r['customers'].first_contact_day.iloc[0],1)
            self.assertEqual(r['customers'].ad_response_day.iloc[0],3)
            self.assertEqual(r['daily'].ad_responses.tolist(),[0,0,1,1,1])

    def test_organic_response_clock_is_independent_of_advertising(self):
        base=Scenario(population=1,days=5,contact_budget=0,contact_cap=5,breadth=100.,weekly_arrivals=0,weekly_turnover=0,weekly_return=0,population_profiles=(0,),organic_rate_scale=1.)
        for scenario in [base,replace(base,contact_budget=10)]:
            r=simulate(scenario,self.controlled_timing_calibration(organic=True))
            self.assertEqual(r['customers'].organic_response_day.iloc[0],3)
            self.assertEqual(r['daily'].organic_responses.tolist(),[0,0,1,1,1])
            self.assertEqual(r['daily'].ad_responses.max(),0)

    def test_lower_organic_scale_reduces_baseline_purchases(self):
        base=Scenario(population=10000,contact_budget=0,weekly_arrivals=0,weekly_turnover=0,weekly_return=0,population_profiles=(3,))
        full=simulate(replace(base,organic_rate_scale=1.),self.cal)
        lower=simulate(base,self.cal)
        zero=simulate(replace(base,organic_rate_scale=0.),self.cal)
        self.assertGreater(full['daily'].organic_responses.iloc[-1],lower['daily'].organic_responses.iloc[-1])
        self.assertGreater(lower['daily'].organic_responses.iloc[-1],0)
        self.assertEqual(zero['daily'].organic_responses.iloc[-1],0)
        self.assertTrue(lower['customers'].customer_id[lower['customers'].organic_response].isin(full['customers'].customer_id[full['customers'].organic_response]).all())

if __name__=='__main__':unittest.main()
