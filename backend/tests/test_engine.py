from datetime import datetime, timezone, timedelta
from backend.app.engine import confidence_for, derive_state, recommend

def envelope(typ, subject, payload, source="camp_lead", author="lead-1", minutes_ago=0, seq=1):
    stamp=(datetime.now(timezone.utc)-timedelta(minutes=minutes_ago)).isoformat().replace("+00:00","Z")
    return {"id":str(seq),"type":typ,"subject":subject,"payload":payload,"source":source,"author_id":author,
            "device_time":stamp,"server_time":stamp,"severity":"info","seq":seq}

def test_confidence_is_clamped_and_source_based():
    e=envelope("camp_status","camp-1",{"headcount":100})
    assert 0 <= confidence_for(e,[e]) <= 1

def test_independent_agreement_increases_confidence():
    e=envelope("camp_status","camp-1",{"headcount":100},author="lead-1",seq=1)
    peer=envelope("camp_status","camp-1",{"headcount":100},author="vol-1",source="volunteer",seq=2)
    assert confidence_for(e,[e,peer]) >= confidence_for(e,[e])

def test_silent_camp_is_uncertain_and_gets_provisional_minimum():
    events=[
      envelope("site_registered","camp-1",{"kind":"camp","name":"Camp 1","capacity":100,"location":{"lat":12.9,"lng":74.8}},"system","system",seq=1),
      envelope("camp_status","camp-1",{"headcount":80,"vulnerable_counts":{"elderly":5,"children":10,"medical":1}},"camp_lead","lead-1",minutes_ago=30,seq=2),
      envelope("site_registered","depot-1",{"kind":"depot","name":"Depot 1","location":{"lat":12.8,"lng":74.8}},"system","system",seq=3),
      envelope("stock_report","depot-1",{"item":"water","quantity":500,"unit":"person_days"},"system","system",seq=4),
    ]
    state=derive_state(events)
    camp=state["camps"]["camp-1"]
    assert camp["status"]=="uncertain"
    plan=recommend(state,"sv-0004")
    assert plan["allocations"][0]["provisional"] is True
    assert plan["allocations"][0]["quantity"]==80

def test_plan_is_bounded_by_available_depot_stock():
    events=[
      envelope("site_registered","camp-1",{"kind":"camp","name":"Camp 1","capacity":100,"location":{"lat":12.9,"lng":74.8}},"system","system",seq=1),
      envelope("camp_status","camp-1",{"headcount":50,"vulnerable_counts":{}},"camp_lead","lead-1",seq=2),
      envelope("site_registered","depot-1",{"kind":"depot","name":"Depot 1","location":{"lat":12.8,"lng":74.8}},"system","system",seq=3),
      envelope("stock_report","depot-1",{"item":"water","quantity":30,"unit":"person_days"},"system","system",seq=4),
    ]
    plan=recommend(derive_state(events),"sv-0004")
    assert sum(a["quantity"] for a in plan["allocations"] if a["item"]=="water") <= 30
