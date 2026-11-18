import unittest
import numpy as np
from src.balanced_tree import BalancedResponseTree


class BalancedTreeChecks(unittest.TestCase):
    def test_balance_nesting_and_response_selection(self):
        rng=np.random.default_rng(42)
        x=rng.uniform(size=(12000,3)).astype(np.float32)
        y=(x[:,1]>.5).astype(float)+rng.normal(0,.05,len(x))
        tree=BalancedResponseTree().fit(x,y,['a','b','c'])
        self.assertEqual(tree.nodes_[0]['feature'],'b')
        for node in tree.nodes_.values():
            if node['left']>=0:
                self.assertGreaterEqual(node['left_fraction'],.45)
                self.assertLessEqual(node['left_fraction'],.55)
        for depth in [0,1,2,3]:
            leaves=tree.apply(x,depth)
            self.assertEqual(len(np.unique(leaves)),2**depth)
            if depth:
                np.testing.assert_array_equal((leaves-1)//2,tree.apply(x,depth-1))

    def test_tied_features_cannot_fake_a_balanced_split(self):
        with self.assertRaisesRegex(ValueError,'No balanced feature threshold'):
            BalancedResponseTree().fit(np.ones((100,2)),np.ones(100),['a','b'])
