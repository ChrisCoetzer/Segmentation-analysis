import unittest
import pandas as pd
from src.investment import investment_scenario


class InvestmentChecks(unittest.TestCase):
    def setUp(self):
        self.policies=pd.DataFrame([dict(outcome='conversion',reach=12.5,segments=s,value=v)
                                   for s,v in [(1,.001),(2,.002),(4,.003),(8,.004)]])

    def calculate(self,**overrides):
        args=dict(policies=self.policies,eligible_audience=100000,reach_percent=12.5,
                  baseline_per_10k=10,contribution_per_conversion=100,transfer_percent=50,
                  costs={2:100,4:200,8:300})
        args.update(overrides)
        return investment_scenario(**args)

    def test_known_scenario(self):
        row=self.calculate().iloc[-1]
        self.assertEqual(row.targeted_users,12500)
        self.assertEqual(row.baseline_incremental_conversions,12.5)
        self.assertAlmostEqual(row.additional_conversions,18.75)
        self.assertAlmostEqual(row.additional_contribution,1875)
        self.assertAlmostEqual(row.net_value,1575)

    def test_zero_transfer_never_creates_benefit(self):
        data=self.calculate(transfer_percent=0)
        self.assertTrue((data.additional_conversions==0).all())
        self.assertTrue((data.net_value==-data.segmentation_cost).all())
        self.assertEqual(data.loc[data.net_value.idxmax(),'segments'],1)

    def test_full_reach_never_creates_benefit(self):
        frame=self.policies.copy()
        frame['reach']=100.
        frame['value']=.01
        self.assertTrue((self.calculate(policies=frame,reach_percent=100).additional_conversions==0).all())

    def test_zero_baseline_and_zero_audience(self):
        for setting in [dict(baseline_per_10k=0),dict(eligible_audience=0)]:
            self.assertTrue((self.calculate(**setting).additional_conversions==0).all())

    def test_unphysical_rate_rejected(self):
        with self.assertRaisesRegex(ValueError,'outside'):
            self.calculate(baseline_per_10k=9000,transfer_percent=100)

    def test_visits_never_enter_conversion_economics(self):
        visits=self.policies.copy()
        visits['outcome']='visit'
        visits['value']=999
        expected=self.calculate()
        actual=self.calculate(policies=pd.concat([self.policies,visits],ignore_index=True))
        pd.testing.assert_frame_equal(actual,expected)

    def test_sixteen_group_benchmark(self):
        frame=pd.concat([self.policies,pd.DataFrame([dict(outcome='conversion',reach=12.5,segments=16,value=.005)])],ignore_index=True)
        result=self.calculate(policies=frame,costs={2:100,4:200,8:300,16:400})
        self.assertEqual(result.segments.tolist(),[1,2,4,8,16])
        self.assertAlmostEqual(result.iloc[-1].additional_conversions,25.)
