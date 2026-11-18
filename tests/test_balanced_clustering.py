import unittest
import numpy as np
from src.balanced_clustering import BalancedClustering
from src.segmentation import summarize_groups,evaluate_standardized_policy


class ClusteringChecks(unittest.TestCase):
    def test_feature_similarity_balance_and_nesting(self):
        rng=np.random.default_rng(12)
        x=np.r_[rng.normal([-4,0],.2,(600,2)),rng.normal([4,0],.2,(600,2))].astype(np.float32)
        model=BalancedClustering(max_depth=3,sample_size=1200).fit(x,['a','b'])
        first=model.apply(x,1)
        self.assertEqual(len(np.unique(first[:600])),1)
        self.assertNotEqual(first[0],first[-1])
        for depth in range(4):
            labels=model.apply(x,depth)
            self.assertEqual(len(np.unique(labels)),2**depth)
            if depth:
                np.testing.assert_array_equal((labels-1)//2,model.apply(x,depth-1))
        for info in model.nodes_.values():
            if info['left']>=0:
                self.assertGreaterEqual(info['left_fraction'],.45)
                self.assertLessEqual(info['left_fraction'],.55)

    def test_feature_units_do_not_drive_clustering(self):
        rng=np.random.default_rng(21)
        x=rng.normal(size=(1000,3)).astype(np.float32)
        a=BalancedClustering(max_depth=2).fit(x,['a','b','c'])
        scaled=x*np.array([100,2,.1],dtype=np.float32)+np.array([20,1,-3],dtype=np.float32)
        b=BalancedClustering(max_depth=2).fit(scaled,['a','b','c'])
        np.testing.assert_array_equal(a.apply(x),b.apply(scaled))

    def test_no_outcome_argument_and_frozen_prediction(self):
        rng=np.random.default_rng(21)
        x=rng.normal(size=(1000,3)).astype(np.float32)
        model=BalancedClustering(max_depth=2).fit(x,['a','b','c'])
        np.testing.assert_array_equal(model.apply(x[:100]),model.apply(x)[:100])
        with self.assertRaises(TypeError):
            model.fit(x,np.zeros(len(x)),['a','b','c'])

    def test_identical_profiles_do_not_fake_clusters(self):
        with self.assertRaises(ValueError):
            BalancedClustering(max_depth=1).fit(np.ones((100,2)),['a','b'])

    def test_standardization_uses_same_group_mix_in_both_arms(self):
        r=[dict(node=0,n=200,treated=180,control=20,treated_positives=36,control_positives=2),
           dict(node=1,n=200,treated=20,control=180,treated_positives=8,control_positives=18)]
        result=evaluate_standardized_policy(r,{0:0.,1:1.},.5)
        self.assertAlmostEqual(result['value'],.15)
        self.assertAlmostEqual(result['broad_value'],.1)
        self.assertAlmostEqual(result['gain'],.05)
        self.assertAlmostEqual(result['realized_expected_reach'],.5)
        self.assertEqual(evaluate_standardized_policy(r,{0:.5,1:.5},.5)['gain_se'],0)
        self.assertEqual(evaluate_standardized_policy(r,{0:1.,1:1.},1.)['gain'],0)
