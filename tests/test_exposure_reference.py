"""The reference must count all advertising effort, not only buyers' histories."""
from pathlib import Path
import unittest
import numpy as np
from src.customer_lab import load_calibration
from src.exposure_reference import build_exposure_reference

class ExposureReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal=load_calibration(Path(__file__).resolve().parents[1]/'app/data/customer_lab')
        cls.detail,cls.stages=build_exposure_reference(cls.cal)

    def test_contacts_include_nonresponders_and_stop_after_response(self):
        for gid,a in self.detail.groupby('segment_id'):
            self.assertEqual(a.contacts.iloc[0],100000)
            np.testing.assert_allclose(a.contacts,100000-np.r_[0,a.cumulative_responses.to_numpy()[:-1]])
            self.assertGreater(a.contacts.min(),99000)
            self.assertAlmostEqual(a.additional_responses.sum(),a.cumulative_responses.iloc[-1])
            self.assertLessEqual(a.cumulative_responses.iloc[-1],a.response_potential.iloc[0])
            b=self.stages[self.stages.segment_id.eq(gid)]
            self.assertAlmostEqual(b.contacts.sum(),a.contacts.sum())
            self.assertAlmostEqual(b.additional_responses.sum(),a.additional_responses.sum())

    def test_multi_exposure_stages_are_normalized_by_all_contacts(self):
        s=self.stages.set_index(['segment_id','stage_id'])
        self.assertGreater(s.loc[(3,2),'responses_per_1000_contacts'],2*s.loc[(3,0),'responses_per_1000_contacts'])
        self.assertGreater(s.loc[(4,0),'responses_per_1000_contacts'],20*s.loc[(4,3),'responses_per_1000_contacts'])
        for _,r in self.stages.iterrows():
            self.assertAlmostEqual(r.responses_per_1000_contacts,1000*r.additional_responses/r.contacts)

if __name__=='__main__':unittest.main()
