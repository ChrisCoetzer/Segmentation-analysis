"""Publish the fixed repetition reference and its denominator audit."""
from pathlib import Path
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.customer_lab import load_calibration
from src.exposure_reference import build_exposure_reference,reference_method

def main():
    runtime=ROOT/'app/data/customer_lab';out=ROOT/'outputs/retail_audiences'
    detailed,stages=build_exposure_reference(load_calibration(runtime))
    for gid,a in detailed.groupby('segment_id'):
        assert len(a)==12
        assert np.allclose(a.contacts,100000-np.r_[0,a.cumulative_responses.to_numpy()[:-1]])
        assert np.isclose(a.additional_responses.sum(),a.cumulative_responses.iloc[-1])
        assert a.contacts.min()>99000
        b=stages[stages.segment_id.eq(gid)]
        assert np.isclose(b.contacts.sum(),a.contacts.sum())
        assert np.isclose(b.additional_responses.sum(),a.additional_responses.sum())
    detailed.to_parquet(runtime/'exposure_detail.parquet',index=False)
    stages.to_parquet(runtime/'exposure_stages.parquet',index=False)
    detailed.to_csv(out/'exposure_reference_detail.csv',index=False)
    stages.to_csv(out/'exposure_reference_stages.csv',index=False)
    (runtime/'exposure_reference_method.json').write_text(json.dumps(reference_method(),indent=2),encoding='utf-8')
    (out/'exposure_reference_validation.json').write_text(json.dumps(dict(groups=5,exposures_per_group=12,customers_per_group=100000,nonresponders_included=True,stages_reconcile_to_details=True,post_response_contacts_excluded=True),indent=2))
    print(stages[['profile','stage','additional_responses','contacts','responses_per_1000_contacts']].round(3).to_string(index=False))

if __name__=='__main__':main()
