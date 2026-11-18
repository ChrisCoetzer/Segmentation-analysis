"""Balanced bisecting k-means with nominal categories and scaled continuous features."""
import numpy as np
from scipy import sparse
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits

CONTINUOUS=['f0','f2','f7','f10']
CATEGORICAL=['f1','f3','f4','f5','f6','f8','f9','f11']


class MixedBalancedClustering:
    def __init__(self,max_depth=6,sample_size=20000,random_state=20261020):
        self.max_depth=max_depth
        self.sample_size=sample_size
        self.random_state=random_state

    def _encode(self,x):
        x=np.asarray(x,dtype=np.float64)
        if x.ndim!=2 or x.shape[1]!=len(self.feature_names_) or not np.isfinite(x).all():
            raise ValueError('Expected finite raw features with fitted column order')
        continuous=((x[:,self.continuous_indices_]-self.mean_)/self.scale_/np.sqrt(2)).astype(np.float32)
        codes=np.empty((len(x),len(self.categorical_indices_)),dtype=np.int32)
        for j,(index,vocabulary) in enumerate(zip(self.categorical_indices_,self.categories_)):
            found=np.searchsorted(vocabulary,x[:,index])
            valid=found<len(vocabulary)
            valid[valid]&=vocabulary[found[valid]]==x[valid,index]
            codes[:,j]=np.where(valid,found,len(vocabulary))
        return continuous,codes

    def _sparse(self,continuous,codes):
        n=len(continuous)
        columns=(codes+self.offsets_).ravel()
        rows=np.repeat(np.arange(n),codes.shape[1])
        cats=sparse.csr_matrix((np.full(len(rows),1/np.sqrt(2),dtype=np.float32),(rows,columns)),shape=(n,self.category_width_))
        return sparse.hstack([sparse.csr_matrix(continuous),cats],format='csr',dtype=np.float32)

    def transform(self,x):
        return self._sparse(*self._encode(x))

    def _score(self,continuous,codes,rows,direction):
        width=continuous.shape[1]
        score=continuous[rows]@direction[:width]
        for j,offset in enumerate(self.offsets_):
            score+=direction[width+offset+codes[rows,j]]/np.sqrt(2)
        return score

    def fit(self,x,feature_names):
        self.feature_names_=list(feature_names)
        self.continuous_indices_=[self.feature_names_.index(f) for f in CONTINUOUS if f in self.feature_names_]
        self.categorical_indices_=[self.feature_names_.index(f) for f in CATEGORICAL if f in self.feature_names_]
        if len(self.continuous_indices_)+len(self.categorical_indices_)!=len(feature_names):
            raise ValueError('Unknown feature type')
        x=np.asarray(x,dtype=np.float64)
        if not np.isfinite(x).all():
            raise ValueError('Expected finite features')
        self.mean_=x[:,self.continuous_indices_].mean(axis=0)
        self.scale_=x[:,self.continuous_indices_].std(axis=0)
        self.scale_[self.scale_==0]=1
        self.categories_=[np.unique(x[:,index]) for index in self.categorical_indices_]
        sizes=[len(v)+1 for v in self.categories_] # reserve unknown category
        self.offsets_=np.r_[0,np.cumsum(sizes)[:-1]].astype(np.int32)
        self.category_width_=sum(sizes)
        continuous,codes=self._encode(x)
        self.nodes_={}
        rng=np.random.default_rng(self.random_state)
        def grow(rows,node,depth):
            info=dict(node=node,depth=depth,n_train=len(rows),left=-1,right=-1)
            self.nodes_[node]=info
            if depth==self.max_depth:
                return
            chosen=rng.choice(rows,min(len(rows),self.sample_size),replace=False)
            sample=self._sparse(continuous[chosen],codes[chosen])
            centers=KMeans(n_clusters=2,n_init=3,max_iter=50,random_state=self.random_state+node).fit(sample).cluster_centers_
            for _ in range(12):
                direction=centers[1]-centers[0]
                score=np.asarray(sample@direction).ravel()
                mask=score<=np.median(score)
                if not mask.any() or mask.all():
                    raise ValueError(f'Tied profiles prevent mixed clustering at node {node}')
                updated=np.stack([np.asarray(sample[mask].mean(axis=0)).ravel(),np.asarray(sample[~mask].mean(axis=0)).ravel()])
                if np.allclose(updated,centers,atol=1e-5):
                    centers=updated
                    break
                centers=updated
            direction=centers[1]-centers[0]
            scores=self._score(continuous,codes,rows,direction)
            threshold=float(np.median(scores));mask=scores<=threshold
            fraction=float(mask.mean())
            if not .45<=fraction<=.55:
                raise ValueError(f'Tied profiles prevent mixed balance at node {node}: {fraction}')
            left,right=2*node+1,2*node+2
            info.update(left=left,right=right,direction=direction,threshold=threshold,left_fraction=fraction)
            grow(rows[mask],left,depth+1)
            grow(rows[~mask],right,depth+1)
        with threadpool_limits(limits=1):
            grow(np.arange(len(x)),0,0)
        return self

    def apply(self,x,depth=None):
        depth=self.max_depth if depth is None else depth
        if not 0<=depth<=self.max_depth:
            raise ValueError('Requested depth exceeds fitted hierarchy')
        continuous,codes=self._encode(x)
        labels=np.zeros(len(continuous),dtype=np.int32)
        with threadpool_limits(limits=1):
            for level in range(depth):
                for node in range(2**level-1,2**(level+1)-1):
                    rows=np.flatnonzero(labels==node)
                    info=self.nodes_[node]
                    mask=self._score(continuous,codes,rows,info['direction'])<=info['threshold']
                    labels[rows]=np.where(mask,info['left'],info['right'])
        return labels
