"""Versioned synthetic shopping missions, separate from advertising outcomes."""
import numpy as np
import pandas as pd

GROUPS=['Household regulars','Bargain hunters','Occasion shoppers','Specialist enthusiasts','Convenience shoppers']
MISSIONS=['Restock the household','Find a deal','Buy for a gift or occasion','Buy specialist equipment','Save time on everyday shopping']
PRIOR=np.array([.30,.24,.18,.12,.16])
DESCRIPTIONS=[
    'Repeat customers buying the everyday things their household uses.',
    'Price-conscious shoppers looking across categories for worthwhile offers.',
    'Infrequent customers buying for a birthday, celebration or seasonal event.',
    'Category-focused customers buying hobby, technology or outdoor equipment.',
    'Repeat customers who value easy reordering and delivery over finding the lowest price.',
]
QUOTES=[
    'Keep the things we use at home stocked up.',
    'Give me a good reason to buy at this price.',
    'Help me find the right gift, delivered in time.',
    'I want the right product for something I care about.',
    'Make this quick. I already know what I need.',
]
EXAMPLES=['Cleaning supplies · kitchen basics · pantry items','Fashion offers · home deals · discounted electronics','Gifts · seasonal decorations · celebration supplies','Hobby equipment · electronics · outdoor gear','Personal care · everyday essentials · repeat purchases']

# Explicit CRM rules, evaluated in this order. These identify constructed
# shopping missions, never a response-time or conversion bucket.
GROUP_RULES=[
    'Household interest + scheduled delivery + at least 4 orders/year',
    'Promotion preference of at least 75%',
    'Gift or seasonal interest + occasion-date delivery',
    'Hobby, technology or outdoor interest + careful delivery',
    'Everyday essentials + fast delivery + at least 2 orders/year',
]
# A declared scenario layer: how a retail mission changes deliberation and
# familiarity needs. Raw source histories remain available unchanged.
PACE_EXPONENT=np.array([1.,1.55,.70,.52,2.2])
FAMILIARITY_PROB=np.array([.25,.08,.50,.82,.03])
FAMILIARITY_EXTRA=np.array([1,1,1,2,1])

def identify_missions(frame):
    category=frame.preferred_category
    conditions=[
        frame.promotion_affinity.ge(.75),
        category.isin(['Hobby equipment','Technology','Sports & outdoors']) & frame.delivery_preference.eq('Careful product delivery'),
        category.isin(['Gifts & occasions','Seasonal & celebrations','Home & gifting']) & frame.delivery_preference.eq('Arrives before the occasion'),
        category.isin(['Personal care','Pantry essentials','Everyday reorders']) & frame.delivery_preference.eq('Fast delivery') & frame.orders_last_year.ge(2),
        category.isin(['Home & kitchen','Pantry & cleaning','Household essentials']) & frame.delivery_preference.eq('Reliable scheduled delivery') & frame.orders_last_year.ge(4),
    ]
    return np.select(conditions,[1,3,2,4,0],default=-1).astype(np.int8)

def decision_metadata(group,ids,strength=1.):
    group=np.asarray(group,dtype=int)
    pace=1+strength*(PACE_EXPONENT[group]-1)
    extra=np.where(stable_uniform(ids,773)<FAMILIARITY_PROB[group]*strength,FAMILIARITY_EXTRA[group],0)
    return pace,extra.astype(np.int8)

def stable_uniform(ids,salt=0):
    z=np.asarray(ids,dtype=np.uint64)+np.uint64(0x9E3779B97F4A7C15)+np.uint64(salt)
    z=(z^(z>>np.uint64(30)))*np.uint64(0xBF58476D1CE4E5B9)
    z=(z^(z>>np.uint64(27)))*np.uint64(0x94D049BB133111EB)
    z=z^(z>>np.uint64(31))
    return (z>>np.uint64(11)).astype(np.float64)/9007199254740992.

def latent_cells(frame,modes):
    def active(f):return frame[f].to_numpy()!=modes[f]
    r=np.select([~active('f8'),~active('f9'),~active('f4'),~active('f11')],[0,1,2,3],default=4)
    subtype=np.select([~active('f3')&~active('f6'),~active('f3')],[0,1],default=2)
    return (r*3+subtype).astype(np.int8)

def allocation_matrix(cell_counts,strength=1.2,common=.20):
    r=np.repeat(np.array([0.,.25,.55,.82,1.]),3)
    t=np.tile(np.arange(3),5)
    # These are scenario assumptions about fictional shopping missions, not
    # recovered meanings for Criteo's anonymous features.
    logits=np.stack([
        1.2-2.5*(r-.48)**2+.65*(t==1),
        .3+1.1*r+1.8*(t==2)-.7*(t==0),
        1.6-2.5*r+.55*(t==0),
        -.2+2.7*r+1.8*(t==0)-.5*(t==2),
        -.1+3.2*r+1.35*(t==2)-.7*(t==0),
    ],axis=1)*strength
    a=np.exp(logits-logits.max(axis=1,keepdims=True))
    weights=np.array(cell_counts,dtype=float,copy=True);weights/=weights.sum()
    # Balance to a declared fictional market composition, rather than label
    # the five old response bins. Every mission contains multiple source cells.
    for _ in range(150):
        a/=a.sum(axis=1,keepdims=True)
        a*=PRIOR/np.maximum(1e-15,(a*weights[:,None]).sum(axis=0))
    a/=a.sum(axis=1,keepdims=True)
    return (1-common)*a+common*PRIOR

def assign_missions(cells,ids,matrix):
    u=stable_uniform(ids,171127)
    return np.minimum(4,(u[:,None]>np.cumsum(matrix[np.asarray(cells,dtype=int)],axis=1)).sum(axis=1)).astype(np.int8)

def metadata(frame,matrix,modes):
    """Generate actual row-level CRM attributes; mission alone defines group."""
    from scipy.stats import poisson
    out=frame.copy();ids=out.source_row_index.to_numpy()
    cell=latent_cells(out,modes);group=assign_missions(cell,ids,matrix)
    out['response_cell']=cell;out['segment_id']=group
    out['shopping_mission']=np.array(MISSIONS)[group]
    out['shopping_need']=np.array(QUOTES)[group]
    out['message_theme']=np.array(['Replenishment reminder','Relevant offer','Gift inspiration','Product expertise','Easy reorder'])[group]
    means=np.array([5.,2.5,.8,2.,6.])[group]
    minimum=np.array([4,0,0,1,2])[group]
    out['orders_last_year']=(minimum+poisson.ppf(np.clip(stable_uniform(ids,11),1e-8,1-1e-8),means)).astype(np.int16)
    u=np.maximum(1e-12,stable_uniform(ids,12));v=stable_uniform(ids,13)
    normal=np.sqrt(-2*np.log(u))*np.cos(2*np.pi*v)
    out['typical_basket']=np.round(np.clip(np.array([42,55,72,185,39])[group]*np.exp(.4*normal),8,900),2)
    low=np.array([.2,.75,.2,.05,.05])[group];high=np.array([.65,.98,.60,.50,.35])[group]
    out['promotion_affinity']=np.round(low+(high-low)*stable_uniform(ids,14),3)
    categories=[['Home & kitchen','Pantry & cleaning','Household essentials'],['Fashion & beauty','Home offers','Electronics deals'],['Gifts & occasions','Seasonal & celebrations','Home & gifting'],['Hobby equipment','Technology','Sports & outdoors'],['Personal care','Pantry essentials','Everyday reorders']]
    category=np.array(categories,dtype=object)[group,np.minimum(2,(stable_uniform(ids,15)*3).astype(int))]
    out['preferred_category']=category
    out['delivery_preference']=np.array(['Reliable scheduled delivery','Lowest delivery cost','Arrives before the occasion','Careful product delivery','Fast delivery'])[group]
    out['preferred_channel']=np.array([['Email','Email','Search'],['Social','Email','SMS'],['Search','Social','Email'],['Search','Email','Search'],['Email','SMS','Email']])[group,np.minimum(2,(stable_uniform(ids,16)*3).astype(int))]
    out['customer_relationship']=np.where(out.orders_last_year.eq(0),'First purchase','Existing customer')
    out['tenure_months']=np.where(out.orders_last_year.eq(0),0,12+(stable_uniform(ids,17)*37).astype(int)).astype(np.int16)
    out['engagement_style']=np.array(['Regular replenishment','Offer-led shopping','Occasion-led shopping','Specialist interest','Convenience-led shopping'])[group]
    out['metadata_origin']='Synthetic retail CRM attributes; mission-based segmentation'
    out['decision_pace_exponent'],out['familiarity_extra_contacts']=decision_metadata(group,ids)
    assert np.array_equal(identify_missions(out),group)
    return out
