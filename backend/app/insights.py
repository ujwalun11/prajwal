"""Equity comparison and decision log for the coordinator dashboard."""
from collections import Counter

def _metrics(camps, allocations, target_days=3, minimum_days=1):
    by_camp_item=Counter()
    for a in allocations: by_camp_item[(a['camp_id'],a['item'])]+=float(a.get('quantity',0))
    high=[c for c in camps if c.get('priority',{}).get('tier') in ('override','high')]
    covered=0
    for c in high:
        people=max(1,float(c.get('headcount') or 1))
        current=float(c.get('stock',{}).get('water',{}).get('quantity',0))
        if current+by_camp_item[(c['camp_id'],'water')]>=people*minimum_days: covered+=1
    ratios=[]; days=[]
    for c in camps:
        people=max(1,float(c.get('headcount') or 1))
        water=float(c.get('stock',{}).get('water',{}).get('quantity',0))+by_camp_item[(c['camp_id'],'water')]
        ratios.append(water/(people*target_days))
        days.append(water/people)
    return {'min_guarantee_coverage':covered/len(high) if high else 1.0,
            'worst_days_of_supply':min(days) if days else 0.0,
            'need_ratio_min':min(ratios) if ratios else 0.0,
            'need_ratio_spread':max(ratios)-min(ratios) if ratios else 0.0}

def build_insights(state, plan, events, target_days=3, minimum_days=1):
    camps=list(state['camps'].values())
    trana=_metrics(camps,plan.get('allocations',[]),target_days,minimum_days)
    total_water=sum(float(d.get('stock',{}).get('water',{}).get('quantity',0)) for d in state['depots'].values())
    request_counts=Counter()
    for camp_id,request,event in state.get('requests',[]): request_counts[camp_id]+=1
    total=sum(request_counts.values())
    baseline_allocations=[]
    if total:
        for c in camps:
            share=request_counts[c['camp_id']]/total
            baseline_allocations.append({'camp_id':c['camp_id'],'item':'water','quantity':total_water*share})
    baseline=_metrics(camps,baseline_allocations,target_days,minimum_days)
    decision_log=[]
    for event in events:
        if event.get('type')=='decision':
            p=event.get('payload',{})
            decision_log.append({'timestamp':event.get('server_time') or event.get('device_time'),
              'plan_id':p.get('plan_id'),'action':p.get('action'),'approved_by':p.get('approved_by'),
              'reasons':p.get('reasons',[])})
    return {'as_of':max((e.get('server_time') or e.get('device_time') for e in events),default=None),
            'equity':{'trana':trana,'baseline':baseline},'decision_log':decision_log}
