"""Small import-level tests for Person C's deterministic modules."""
from backend.app.insights import _metrics
from backend.app.simulate import simulate

def test_equity_metrics_handles_empty_state():
    m=_metrics([],[])
    assert m['min_guarantee_coverage']==1.0
    assert m['worst_days_of_supply']==0.0

def test_simulation_is_marked_hypothetical_and_does_not_mutate():
    state={'camps':{'c':{'camp_id':'c','headcount':5,'stock':{},'priority':{'tier':'low','score':1},'status':'confirmed'}},'depots':{},'requests':[]}
    result=simulate(state,'sv-0001','c',3)
    assert result['simulated'] is True
    assert state['camps']['c']['headcount']==5
