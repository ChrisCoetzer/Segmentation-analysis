"""Feature-only, balanced bisecting two-means clustering."""
import numpy as np
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits


class BalancedClustering:
    def __init__(self,max_depth=6,sample_size=20000,random_state=20261020):
        self.max_depth=max_depth
        self.sample_size=sample_size
        self.random_state=random_state

    def fit(self,x,feature_names):
        x=np.asarray(x,dtype=np.float32)
        if x.ndim!=2 or not np.isfinite(x).all() or x.shape[1]!=len(feature_names):
            raise ValueError('Clustering requires finite feature columns only')
        self.feature_names_=list(feature_names)
        self.mean_=x.mean(axis=0,dtype=np.float64).astype(np.float32)
        self.scale_=x.std(axis=0,dtype=np.float64).astype(np.float32)
        self.scale_[self.scale_==0]=1
        x=(x-self.mean_)/self.scale_
        self.nodes_={}
        rng=np.random.default_rng(self.random_state)

        def grow(rows,node,depth):
            info=dict(node=node,depth=depth,n_train=len(rows),left=-1,right=-1)
            self.nodes_[node]=info
            if depth==self.max_depth:
                return
            sample=x[rng.choice(rows,min(len(rows),self.sample_size),replace=False)]
            centers=KMeans(n_clusters=2,n_init=3,max_iter=50,random_state=self.random_state+node).fit(sample).cluster_centers_
            # Equal-capacity two-means assignment: order distance differences,
            # split at the median, then recompute centers. No outcome inputs.
            for _ in range(12):
                direction=centers[1]-centers[0]
                score=sample@direction
                threshold=float(np.median(score))
                mask=score<=threshold
                if not mask.any() or mask.all():
                    raise ValueError('Identical feature profiles prevent a balanced clustering split')
                updated=np.stack([sample[mask].mean(axis=0),sample[~mask].mean(axis=0)])
                if np.allclose(updated,centers,atol=1e-5):
                    centers=updated
                    break
                centers=updated
            direction=centers[1]-centers[0]
            score=x[rows]@direction
            threshold=float(np.median(score))
            mask=score<=threshold
            fraction=float(mask.mean())
            if not .45<=fraction<=.55:
                raise ValueError(f'Tied profiles prevent balance at node {node}: {fraction}')
            left,right=2*node+1,2*node+2
            info.update(left=left,right=right,direction=direction,threshold=threshold,
                        left_fraction=fraction,centers=centers)
            grow(rows[mask],left,depth+1)
            grow(rows[~mask],right,depth+1)
        with threadpool_limits(limits=1):
            grow(np.arange(len(x)),0,0)
        return self

    def apply(self,x,depth=None):
        depth=self.max_depth if depth is None else depth
        if not 0<=depth<=self.max_depth:
            raise ValueError('Requested depth exceeds fitted hierarchy')
        x=(np.asarray(x,dtype=np.float32)-self.mean_)/self.scale_
        labels=np.zeros(len(x),dtype=np.int32)
        with threadpool_limits(limits=1):
            for level in range(depth):
                for node in range(2**level-1,2**(level+1)-1):
                    rows=np.flatnonzero(labels==node)
                    info=self.nodes_[node]
                    mask=x[rows]@info['direction']<=info['threshold']
                    labels[rows]=np.where(mask,info['left'],info['right'])
        return labels
