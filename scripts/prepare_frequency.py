"""Precompute the second chart from all released attribution impressions."""
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data import load_dataset
from src.frequency import aggregate_frequency


def main():
    start=time.perf_counter()
    print('Reading all attribution impressions...',flush=True)
    data=load_dataset('attribution',columns=['uid','campaign','conversion'])
    counts=aggregate_frequency(data)
    assert int(counts.impressions.sum())==len(data)
    assert (counts.converted_pairs<=counts.pairs).all()
    output=ROOT/'app/data'
    output.mkdir(parents=True,exist_ok=True)
    counts.to_parquet(output/'frequency.parquet',index=False)
    meta=dict(source='Criteo Attribution Modeling for Bidding',
              source_sha256=json.loads((ROOT/'data/raw/attribution/manifest.json').read_text())['sha256'],
              impressions=len(data),user_campaign_pairs=int(counts.pairs.sum()),
              converted_pairs=int(counts.converted_pairs.sum()),campaigns=int(counts.campaign.nunique()),
              raw_positive_impression_labels=int(data.conversion.sum()),
              elapsed_seconds=round(time.perf_counter()-start,2),
              grain='One user within one campaign over the entire released impression period.',
              numerator='Pairs with any impression labeled conversion=1, counted once per pair.',
              denominator='All observed user-campaign pairs in a frequency bin.',
              frequency='Number of recorded impressions for that user and campaign across the released log.',
              note='Descriptive association only. Log sampling means recorded frequency need not equal true frequency. '
                   '30-day forward conversion labels can repeat across impressions. '
                   'This is not a count of distinct conversion events. '
                   'Across pooled campaigns a user can occur more than once. '
                   'Observed frequency can reflect activity after conversion; no causal direction is inferred.')
    (output/'frequency_run.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(json.dumps(meta,indent=2),flush=True)


if __name__=='__main__':
    main()
