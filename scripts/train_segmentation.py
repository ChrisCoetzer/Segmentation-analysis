"""Fit feature-only balanced clustering, then rank/evaluate response separately."""
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys
import time
import joblib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data import UPLIFT_FEATURES,load_dataset
from src.mixed_clustering import MixedBalancedClustering,CONTINUOUS,CATEGORICAL
from src.segmentation import allocation,summarize_groups,evaluate_standardized_policy


def main(cluster_seed=20261020,publish=True):
    started=time.perf_counter()
    output=ROOT/('outputs/mixed_clustering' if cluster_seed==20261020 else f'outputs/clustering_stability/seed_{cluster_seed}')
    exported=ROOT/'app/data' if publish else output/'app_results'
    output.mkdir(parents=True,exist_ok=True)
    exported.mkdir(parents=True,exist_ok=True)
    archive=output/'previous_app_results'
    if not archive.exists():
        archive.mkdir()
        for name in ['groups.parquet','policies.parquet','baselines.parquet','run.json','trees.json','rules.json']:
            if (exported/name).exists():
                shutil.copy2(exported/name,archive/name)
    df=load_dataset('uplift',UPLIFT_FEATURES+['treatment','conversion','visit'])
    n=len(df)
    order=np.random.default_rng(20261020).permutation(n)
    train,estimation,test=np.split(order,[int(.6*n),int(.8*n)])
    np.savez_compressed(output/'split_rows.npz',train=train,estimation=estimation,test=test)
    x=df[UPLIFT_FEATURES].to_numpy(dtype=np.float64)
    print(f'Fitting feature-only clusters on {len(train):,} users',flush=True)
    model=MixedBalancedClustering(max_depth=5,random_state=cluster_seed).fit(x[train],UPLIFT_FEATURES)
    joblib.dump(dict(model=model,features=UPLIFT_FEATURES),output/'clustering.joblib')
    print('Feature-only hierarchy fitted; assigning separate estimation/evaluation users',flush=True)
    le=model.apply(x[estimation]);lv=model.apply(x[test])
    counts=[1,2,4,8,16,32]
    profiles=[]
    # Evaluate geometric compactness on fixed training-sample features only.
    sample=x[train[:50000]]
    sample_encoded=model.transform(sample)
    sample_leaves=model.apply(sample)
    geometry=[]
    for count in counts:
        labels=(sample_leaves+1)//(32//count)-1
        within=0.
        for node in np.unique(labels):
            values=sample_encoded[labels==node]
            center=np.asarray(values.mean(axis=0)).ravel()
            within+=max(0.,float(values.multiply(values).sum())-values.shape[0]*float(center@center))
            profiles.append(dict(segments=count,node=int(node),sample_users=values.shape[0]))
        geometry.append(dict(segments=count,mean_squared_distance=within/len(sample)))
    pd.DataFrame(profiles).to_parquet(output/'feature_profiles.parquet',index=False)
    del x,sample,sample_encoded
    t=df.treatment.to_numpy(dtype=np.int8)
    policies,groups,baselines=[],[],[]
    for outcome in ['conversion','visit']:
        y=df[outcome].to_numpy(dtype=np.int8)
        fine=summarize_groups(lv,t[test],y[test])
        baseline=evaluate_standardized_policy(fine,{r['node']:1. for r in fine},1.)
        baselines.append(dict(outcome=outcome,**baseline))
        for count in counts:
            divisor=32//count
            est_labels=(le+1)//divisor-1
            test_labels=(lv+1)//divisor-1
            calibration=summarize_groups(est_labels,t[estimation],y[estimation])
            ranked=[r['node'] for r in sorted(calibration,key=lambda r:(-r['effect'],r['node']))]
            effects={r['node']:r['effect'] for r in calibration}
            records=summarize_groups(test_labels,t[test],y[test])
            for evaluation,indexes in [('All evaluation rows',np.arange(len(test))),
                                       ('Half 1',np.arange(len(test)//2)),
                                       ('Half 2',np.arange(len(test)//2,len(test)))]:
                details=records if evaluation=='All evaluation rows' else summarize_groups(test_labels[indexes],t[test][indexes],y[test][indexes])
                for r in details:
                    groups.append(dict(outcome=outcome,segments=count,segment_limit=count,
                        group=int(r['node']-(count-1)+1),estimation_effect=effects[r['node']],
                        share=r['n']/len(indexes),evaluation=evaluation,**r))
            for percent in np.arange(1,201)/2:
                reach=percent/100
                coarse=allocation(records,ranked,reach)
                weights={r['node']:coarse[(r['node']+1)//divisor-1] for r in fine}
                policies.append(dict(outcome=outcome,segments=count,segment_limit=count,reach=percent,
                    **evaluate_standardized_policy(fine,weights,reach)))
            joblib.dump(dict(model=model,depth=int(np.log2(count)),features=UPLIFT_FEATURES,
                             ranked_nodes=ranked,calibrated_effects=effects,outcome=outcome),
                        output/f'{outcome}_{count}_segments.joblib')
            print(f'{outcome}: {count} clusters ranked and evaluated',flush=True)
    meta=dict(seed=20261020,cluster_seed=cluster_seed,total_rows=n,train_rows=len(train),estimation_rows=len(estimation),test_rows=len(test),
        segments=counts,max_depth=5,features=UPLIFT_FEATURES,method='Feature-only balanced mixed-data bisecting two-means clustering',
        continuous_features=CONTINUOUS,categorical_features=CATEGORICAL,
        category_counts={f:len(v) for f,v in zip(CATEGORICAL,model.categories_)},
        preprocessing='Train-only continuous standardization; nominal one-hot categorical encoding. Each category mismatch has squared distance 1; each standardized continuous difference contributes squared distance / 2. Category code magnitude is ignored.',
        fitting='Two-means initialization and balanced median distance-difference assignments on up to 20,000 training users per node. Frozen median threshold on all training members. Outcomes and treatment excluded.',
        ranking='Separate estimation-set treatment-minus-control rate; rankings may differ by outcome, cluster membership does not.',
        evaluation='Common 32-cluster feature strata and common population-share weights in both arms for every policy. Fractional boundary-cluster selection is random in expectation.',
        uncertainty='95% pointwise normal intervals conditional on fixed clusters, rankings, allocations and stratum counts. No training or privacy-sampling uncertainty.',
        status='Exploratory benchmark; previously inspected evaluation release, not a new confirmatory experiment.',
        geometry_sample_rows=50000,geometry=geometry,
        training_balance_range=[min(v['left_fraction'] for v in model.nodes_.values() if v['left']>=0),
                                max(v['left_fraction'] for v in model.nodes_.values() if v['left']>=0)],
        actual_segments_by_outcome={k:counts for k in ['conversion','visit']},
        source_sha256=json.loads((ROOT/'data/raw/uplift/manifest.json').read_text())['sha256'],
        versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','pyarrow']},
        elapsed_seconds=round(time.perf_counter()-started,2))
    # Publish only after fitting and all evaluations succeed.
    pd.DataFrame(groups).to_parquet(exported/'groups.parquet',index=False)
    pd.DataFrame(policies).to_parquet(exported/'policies.parquet',index=False)
    pd.DataFrame(baselines).to_parquet(exported/'baselines.parquet',index=False)
    for folder in [output,exported]:
        (folder/'run.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(f'Finished in {meta["elapsed_seconds"]}s',flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--cluster-seed',type=int,default=20261020)
    parser.add_argument('--no-publish',action='store_true')
    args=parser.parse_args()
    main(args.cluster_seed,not args.no_publish)
