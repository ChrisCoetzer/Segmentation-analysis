import unittest
import pandas as pd
from src.investment import population_investment_scenario

class PopulationChecks(unittest.TestCase):
    def groups(self):
        # Four equally sized leaves, effects .01/.02/.03/.04, equal arm sizes.
        rows=[]
        for count in [1,2,4]:
            for j in range(count):
                members=list(range(j*4//count,(j+1)*4//count))
                tp=sum([2,3,4,5][k] for k in members)
                cp=len(members)
                rows.append(dict(outcome='conversion',segments=count,node=count-1+j,group=j+1,
                                 n=200*len(members),treated=100*len(members),control=100*len(members),
                                 treated_positives=tp,control_positives=cp,estimation_effect=j,
                                 evaluation='All evaluation rows'))
        return pd.DataFrame(rows)

    def test_combines_top_groups_at_equal_reach(self):
        result=population_investment_scenario(self.groups(),100000,50,10,100)
        self.assertTrue((result.targeted_users==50000).all())
        self.assertEqual(result.iloc[-1].whole_clusters,2)
        self.assertEqual(result.iloc[-1].boundary_cluster_fraction,0)
        # Average lift of top two leaves .035 versus broad .025 = 40% gain.
        self.assertAlmostEqual(result.iloc[-1].benchmark_relative_gain,.4)
        self.assertAlmostEqual(result.iloc[-1].additional_conversions,20)

    def test_partial_boundary_and_zero_full_reach(self):
        result=population_investment_scenario(self.groups(),100000,37.5,10,100)
        self.assertEqual(result.iloc[-1].whole_clusters,1)
        self.assertAlmostEqual(result.iloc[-1].boundary_cluster_fraction,.5)
        for pct in [0,100]:
            result=population_investment_scenario(self.groups(),100000,pct,10,100)
            self.assertTrue((result.additional_conversions==0).all())
