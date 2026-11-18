import unittest

import numpy as np

from src.segmentation import allocation, evaluate_policy, summarize_groups, responsive_audience_comparison
import pandas as pd


class PolicyChecks(unittest.TestCase):
    def setUp(self):
        # Equal randomized arms within two equal-sized groups. Effects .1 and .3.
        self.records = [dict(node=0,n=200,treated=100,control=100,treated_positives=20,control_positives=10),
                        dict(node=1,n=200,treated=100,control=100,treated_positives=40,control_positives=10)]

    def test_target_high_effect_half(self):
        weights=allocation(self.records,[1,0],.5)
        result=evaluate_policy(self.records,weights,.5)
        self.assertAlmostEqual(result['value'],.15)
        self.assertAlmostEqual(result['broad_value'],.1)
        self.assertAlmostEqual(result['gain'],.05)
        self.assertAlmostEqual(result['realized_expected_reach'],.5)

    def test_fractional_group(self):
        weights=allocation(self.records,[1,0],.75)
        self.assertEqual(weights,{1:1.,0:.5})
        self.assertAlmostEqual(evaluate_policy(self.records,weights,.75)['value'],.175)

    def test_full_reach_paired_difference_cancels(self):
        result=evaluate_policy(self.records,allocation(self.records,[1,0],1),1)
        self.assertEqual(result['gain'],0)
        self.assertEqual(result['gain_se'],0)

    def test_broad_randomization_has_zero_gain(self):
        result=evaluate_policy(self.records,{0:.5,1:.5},.5)
        self.assertEqual(result['gain'],0)
        self.assertEqual(result['gain_se'],0)

    def test_responsive_group_selected_without_evaluation_outcomes(self):
        frame=pd.DataFrame([dict(r,outcome='conversion',segments=2,group=i+1,share=.5,
                                 estimation_effect=1-i,evaluation='All evaluation rows')
                            for i,r in enumerate(self.records)])
        result=responsive_audience_comparison(frame,'conversion').iloc[0]
        # Deliberately rank the lower realized-effect group first using estimation data.
        self.assertEqual(result.selected_group,1)
        self.assertAlmostEqual(result['value'],.05)
        self.assertAlmostEqual(result.reach,50)

    def test_interval_variance_matches_direct_arm_calculation(self):
        t=np.array([1]*100+[0]*100+[1]*100+[0]*100)
        y=np.concatenate([np.r_[np.ones(k),np.zeros(100-k)] for k in [20,10,40,10]])
        leaf=np.repeat([0,1],200)
        records=summarize_groups(leaf,t,y)
        result=evaluate_policy(records,{0:0.,1:1.},.5)
        weighted=(leaf==1)*y
        expected=np.sqrt(weighted[t==1].var(ddof=1)/200+weighted[t==0].var(ddof=1)/200)
        self.assertAlmostEqual(result['se'],expected)


if __name__=='__main__':
    unittest.main()
