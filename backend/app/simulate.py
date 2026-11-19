"""What-if calculations run on a copy of current state; no events are written."""
from copy import deepcopy
from backend.app.engine import recommend

def simulate(state, state_version, camp_id=None, headcount_delta=0, stock_deltas=None):
    hypothetical=deepcopy(state)
    if camp_id and camp_id not in hypothetical['camps']:
        raise KeyError('unknown_camp')
    if camp_id:
        camp=hypothetical['camps'][camp_id]
        camp['headcount']=max(0,int(camp.get('headcount',0)+headcount_delta))
        for item,delta in (stock_deltas or {}).items():
            old=camp.get('stock',{}).get(item,{}).get('quantity',0)
            camp.setdefault('stock',{}).setdefault(item,{'unit':'person_days'})['quantity']=max(0,old+delta)
    plan=recommend(hypothetical,state_version+'-whatif')
    return {'simulated':True,'inputs':{'camp_id':camp_id,'headcount_delta':headcount_delta,'stock_deltas':stock_deltas or {}},
            'plan':plan,'message':'Hypothetical only. No event was persisted and no dispatch was created.'}
