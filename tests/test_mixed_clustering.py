import unittest
import numpy as np
from sklearn.metrics import adjusted_rand_score
from src.mixed_clustering import MixedBalancedClustering,CONTINUOUS,CATEGORICAL
from src.data import UPLIFT_FEATURES


class MixedClusteringChecks(unittest.TestCase):
    def data(self):
        rng=np.random.default_rng(5)
        x=rng.normal(size=(1200,12))
        for f in CATEGORICAL:
            x[:,UPLIFT_FEATURES.index(f)]=rng.integers(0,4,len(x))
        return x

    def test_category_recoding_preserves_geometry(self):
        x=self.data();changed=x.copy()
        replacement=np.array([1000.,-8.,.0001,27.])
        for f in CATEGORICAL:
            j=UPLIFT_FEATURES.index(f)
            changed[:,j]=replacement[x[:,j].astype(int)]
        a=MixedBalancedClustering(max_depth=2).fit(x,UPLIFT_FEATURES)
        b=MixedBalancedClustering(max_depth=2).fit(changed,UPLIFT_FEATURES)
        za=a.transform(x[:50]);zb=b.transform(changed[:50])
        np.testing.assert_allclose((za@za.T).toarray(),(zb@zb.T).toarray(),atol=1e-5)
        self.assertGreater(adjusted_rand_score(a.apply(x),b.apply(changed)),.99)

    def test_unknown_categories_and_column_precision(self):
        x=self.data()
        j=UPLIFT_FEATURES.index('f8')
        x[:,j]=np.where(x[:,j]<2,3.955396,3.95539600001)
        model=MixedBalancedClustering(max_depth=1).fit(x,UPLIFT_FEATURES)
        k=CATEGORICAL.index('f8')
        self.assertEqual(len(model.categories_[k]),2)
        new=x[:3].copy();new[:,j]=1e9
        self.assertEqual(model.apply(new).shape,(3,))

    def test_balance_nesting_and_feature_only_inputs(self):
        x=self.data();m=MixedBalancedClustering(max_depth=3).fit(x,UPLIFT_FEATURES)
        for d in range(1,4):
            labels=m.apply(x,d)
            self.assertEqual(len(np.unique(labels)),2**d)
            np.testing.assert_array_equal((labels-1)//2,m.apply(x,d-1))
        for r in m.nodes_.values():
            if r['left']>=0:
                self.assertTrue(.45<=r['left_fraction']<=.55)
        np.testing.assert_array_equal(m.apply(x[:50]),m.apply(x)[:50])
        with self.assertRaises(TypeError):
            m.fit(x,np.zeros(len(x)),UPLIFT_FEATURES)
