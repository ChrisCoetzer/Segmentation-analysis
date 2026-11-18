"""A nested tree with approximately equal-sized children and response-based splits."""
import numpy as np


class BalancedResponseTree:
    def __init__(self,max_depth=3,min_child_fraction=.45):
        self.max_depth=max_depth
        self.min_child_fraction=min_child_fraction

    def fit(self,x,target,feature_names):
        if len(x)!=len(target) or not 0<self.min_child_fraction<=.5:
            raise ValueError('Invalid target length or balance constraint')
        self.feature_names_=list(feature_names)
        self.nodes_={}
        quantiles=np.linspace(self.min_child_fraction,1-self.min_child_fraction,5)

        def grow(rows,node,depth):
            entry=dict(node=node,depth=depth,n_train=len(rows),left=-1,right=-1,
                       feature=None,feature_index=None,threshold=None)
            self.nodes_[node]=entry
            if depth==self.max_depth:
                return
            z=target[rows]
            total=float(z.sum())
            best=None
            for feature in range(x.shape[1]):
                values=x[rows,feature]
                cuts=np.unique(np.quantile(values,quantiles,method='nearest')).astype(float)
                # Cumulative histogram gives counts and response sums for every cut.
                bins=np.searchsorted(cuts,values,side='left')
                counts=np.cumsum(np.bincount(bins,minlength=len(cuts)+1))[:-1]
                sums=np.cumsum(np.bincount(bins,weights=z,minlength=len(cuts)+1))[:-1]
                for cut,nleft,total_left in zip(cuts,counts,sums):
                    fraction=nleft/len(rows)
                    if not self.min_child_fraction<=fraction<=1-self.min_child_fraction:
                        continue
                    nright=len(rows)-nleft
                    difference=total_left/nleft-(total-total_left)/nright
                    score=nleft*nright/len(rows)*difference**2
                    candidate=(float(score),-abs(fraction-.5),-feature,float(cut))
                    if best is None or candidate>best[0]:
                        best=(candidate,feature,float(cut),int(nleft))
            if best is None:
                raise ValueError(f'No balanced feature threshold exists at node {node}; '
                                 'tied feature values prevent the requested split')
            _,feature,threshold,nleft=best
            mask=x[rows,feature]<=threshold
            left,right=2*node+1,2*node+2
            entry.update(left=left,right=right,feature=self.feature_names_[feature],
                         feature_index=feature,threshold=threshold,left_fraction=nleft/len(rows))
            grow(rows[mask],left,depth+1)
            grow(rows[~mask],right,depth+1)

        grow(np.arange(len(x)),0,0)
        return self

    def apply(self,x,depth=None):
        depth=self.max_depth if depth is None else depth
        if not 0<=depth<=self.max_depth:
            raise ValueError('Requested depth exceeds the fitted tree')
        leaves=np.zeros(len(x),dtype=np.int32)
        for level in range(depth):
            for node in range(2**level-1,2**(level+1)-1):
                rows=np.flatnonzero(leaves==node)
                info=self.nodes_[node]
                left=x[rows,info['feature_index']]<=info['threshold']
                leaves[rows]=np.where(left,info['left'],info['right'])
        return leaves

    def view_nodes(self,depth):
        nodes=[]
        for node in sorted(self.nodes_):
            row=self.nodes_[node].copy()
            if row['depth']>depth:
                continue
            if row['depth']==depth:
                row.update(left=-1,right=-1,feature=None,feature_index=None,threshold=None)
            nodes.append(row)
        return nodes

    def rules(self,depth):
        nodes={r['node']:r for r in self.view_nodes(depth)}
        lines=[]
        def walk(node,prefix=''):
            row=nodes[node]
            if row['left']<0:
                lines.append(f'{prefix}Group node {node}')
            else:
                lines.append(f'{prefix}{row["feature"]} <= {row["threshold"]:.8f}')
                walk(row['left'],prefix+'  Yes: ')
                walk(row['right'],prefix+'  No:  ')
        walk(0)
        return '\n'.join(lines)
