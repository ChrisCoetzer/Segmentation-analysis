import unittest

import pandas as pd

from src.frequency import aggregate_frequency, interval_table


class FrequencyChecks(unittest.TestCase):
    def test_repeated_labels_are_not_separate_converted_pairs(self):
        df=pd.DataFrame({'campaign':[1]*4+[2], 'uid':[7,7,7,8,7], 'conversion':[1,1,0,0,1]})
        summary=aggregate_frequency(df)
        self.assertEqual(summary.impressions.sum(),5)
        self.assertEqual(summary.pairs.sum(),3)
        self.assertEqual(summary.converted_pairs.sum(),2)
        campaign1=summary[summary.campaign=='1']
        self.assertEqual(campaign1[campaign1.frequency=='2–3'].converted_pairs.iloc[0],1)

    def test_bucket_boundaries(self):
        rows=[]
        for uid,count in enumerate([1,2,3,4,6,7,10,11]):
            rows.extend([dict(campaign=1,uid=uid,conversion=0)]*count)
        result=aggregate_frequency(pd.DataFrame(rows)).set_index('frequency')
        self.assertEqual(result.pairs.to_dict(),{'1':1,'2–3':2,'4–6':2,'7–10':2,'11+':1})

    def test_wilson_intervals_at_zero_and_one(self):
        result=interval_table(pd.DataFrame({'pairs':[20,20], 'converted_pairs':[0,20]}))
        self.assertTrue((result.lower>=0).all())
        self.assertTrue((result.upper<=1).all())
        self.assertTrue((result.lower<=result.rate).all())
        self.assertTrue((result.upper>=result.rate).all())


if __name__=='__main__':
    unittest.main()
