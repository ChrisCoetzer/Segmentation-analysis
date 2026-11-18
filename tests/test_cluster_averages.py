import unittest
import numpy as np
import pandas as pd
from src.segmentation import summarize_groups,cluster_average_comparison
from src.investment import cluster_investment_scenario

class AverageChecks(unittest.TestCase):
    def data(self):
        t=np.tile(np.r_[np.ones(100),np.zeros(100)],2).astype(int)
        y=np.concatenate([np.r_[np.ones(k),np.zeros(100-k)] for k in [20,10,40,10]])
        leaves=np.repeat([1,2],200)
        rows=[]
        for count,labels in [(1,np.zeros(400)),(2,leaves)]:
            for r in summarize_groups(labels,t,y):
                rows.append(dict(outcome='conversion',segments=count,group=int(r['node']),share=r['n']/400,
                                 estimation_effect=1 if r['node']==1 else 0,evaluation='All evaluation rows',**r))
        return pd.DataFrame(rows)

    def test_estimation_selects_and_all_members_average(self):
        data=self.data();result=cluster_average_comparison(data,'conversion')
        # Estimation picks node 1 even though node 2's evaluation effect is higher.
        self.assertEqual(result.iloc[1].node,1)
        self.assertAlmostEqual(result.iloc[1]['value'],.1)
        self.assertAlmostEqual(result.iloc[1]['gain'],-.1)
        self.assertEqual(result.iloc[1]['n'],200)
        self.assertEqual(result.iloc[1]['reach'],50.)
        self.assertAlmostEqual(result.iloc[0]['gain'],0.)

    def test_financial_scenario_uses_average_ratio(self):
        data=self.data();data.loc[(data.segments==2)&(data.node==2),'estimation_effect']=2
        averages=cluster_average_comparison(data,'conversion')
        result=cluster_investment_scenario(averages,10000,10,100)
        self.assertAlmostEqual(result.iloc[1].benchmark_relative_gain,.5)
        self.assertAlmostEqual(result.iloc[1].additional_conversions,5.)
        self.assertAlmostEqual(result.iloc[1].break_even_cost,500.)
