"""Deterministic, explainable trust, state-reduction, task and allocation rules."""
from __future__ import annotations
from datetime import datetime, timezone
from math import cos, radians, sin, asin, sqrt
from uuid import uuid5, NAMESPACE_URL
from . import settings

def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

def confidence_for(event: dict, events: list[dict], now: datetime | None = None) -> float:
    """Confidence = source trust x freshness x corroboration; result clamped to [0, 1]."""
    now = now or datetime.now(timezone.utc)
    source_factor = settings.SOURCE_TRUST.get(event.get("source"), 0.5)
    half_life = settings.FRESHNESS_HALF_LIFE_MINUTES.get(event.get("type"))
    freshness = 1.0
    stamp = parse_time(event.get("server_time") or event.get("device_time"))
    if half_life and stamp:
        age_seconds = max(0.0, (now - stamp).total_seconds())
        half_life_seconds = half_life * settings.SCENARIO_MINUTE_SECONDS
        freshness = 0.5 ** (age_seconds / max(1, half_life_seconds))
    corroboration = 1.0
    peers = [e for e in events if e.get("id") != event.get("id")
             and e.get("subject") == event.get("subject") and e.get("type") == event.get("type")
             and e.get("author_id") != event.get("author_id")]
    if peers:
        same = any(e.get("payload") == event.get("payload") for e in peers)
        corroboration = settings.CORROBORATION_AGREEMENT_MULTIPLIER if same else settings.CORROBORATION_CONFLICT_MULTIPLIER
    return round(min(1.0, max(0.0, source_factor * freshness * corroboration)), 4)

def derive_state(events: list[dict], now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    camps, depots, roads, latest, volunteers = {}, {}, {}, {}, {}
    tasks, requests, decisions, deliveries = {}, [], [], []
    for e in events:
        typ, subject, p = e["type"], e["subject"], e.get("payload", {})
        if typ == "site_registered":
            item = {"camp_id": subject, "name": p.get("name", subject), "location": p.get("location"),
                    "capacity": p.get("capacity", 0), "access_difficulty": p.get("access_difficulty", 0.5),
                    "headcount": 0, "vulnerable_counts": {"elderly": 0, "children": 0, "medical": 0},
                    "stock": {}, "requests": [], "flags": []}
            if p.get("kind") == "depot":
                item["depot_id"] = subject
                depots[subject] = item
            else:
                camps[subject] = item
            latest[(typ, subject)] = e
        elif typ == "camp_status" and subject in camps:
            c = camps[subject]
            c["headcount"] = p.get("headcount", c["headcount"])
            c["capacity"] = p.get("capacity", c["capacity"])
            c["vulnerable_counts"] = p.get("vulnerable_counts", c["vulnerable_counts"])
            if p.get("name"): c["name"] = p["name"]
            latest[("camp_status", subject)] = e
        elif typ == "stock_report":
            target = camps.get(subject) or depots.get(subject)
            if target:
                item = p.get("item", "water")
                target["stock"][item] = {"quantity": p.get("quantity", 0), "unit": p.get("unit", "person_days"),
                                         "as_of": e.get("server_time") or e.get("device_time")}
                latest[("stock_report", subject + ":" + item)] = e
        elif typ == "shortage_request" and subject in camps:
            request = dict(p, reported_at=e.get("server_time") or e.get("device_time"))
            camps[subject]["requests"].append(request)
            requests.append((subject, request, e))
            latest[("shortage_request", subject)] = e
        elif typ == "verification_report" and subject in camps:
            outcome = p.get("outcome")
            if outcome == "differs":
                obs = p.get("observed", {})
                if "headcount" in obs: camps[subject]["headcount"] = obs["headcount"]
                if "vulnerable_counts" in obs: camps[subject]["vulnerable_counts"] = obs["vulnerable_counts"]
                for key, qty in obs.get("stock", {}).items():
                    old = camps[subject]["stock"].get(key, {})
                    camps[subject]["stock"][key] = dict(old, quantity=qty, as_of=e.get("server_time"))
            latest[("verification_report", subject)] = e
        elif typ == "road_status":
            roads[subject] = dict(p, road_id=subject, reported_at=e.get("server_time") or e.get("device_time"))
            latest[("road_status", subject)] = e
        elif typ == "volunteer_location":
            volunteers[e["author_id"]] = {"user_id": e["author_id"], "location": e.get("location"),
                                          "reported_at": e.get("server_time") or e.get("device_time")}
        elif typ == "task_accepted":
            tasks.setdefault(subject, {"task_id": subject})["status"] = "accepted"
        elif typ == "decision":
            decisions.append(e)
        elif typ == "delivery_update":
            deliveries.append(e)
    for camp_id, camp in camps.items():
        report_events = [e for e in events if e["subject"] == camp_id and e["type"] in
                         ("camp_status", "stock_report", "shortage_request", "verification_report")]
        last = max((parse_time(e.get("server_time") or e.get("device_time")) for e in report_events if parse_time(e.get("server_time") or e.get("device_time"))), default=None)
        age_seconds = (now - last).total_seconds() if last else float("inf")
        silent_after = settings.EXPECTED_REPORT_INTERVAL_MINUTES * settings.SILENCE_MULTIPLIER * settings.SCENARIO_MINUTE_SECONDS
        silent = age_seconds > silent_after
        camp["last_report_at"] = last.isoformat().replace("+00:00", "Z") if last else None
        camp["silent"] = silent
        confidence_event = max(report_events, key=lambda e: e.get("seq", 0), default=None)
        conf = confidence_for(confidence_event, events, now) if confidence_event else 0.0
        camp["confidence"] = conf
        camp["status"] = ("uncertain" if silent or conf < settings.CONFIDENCE_UNCONFIRMED else
                          "confirmed" if conf >= settings.CONFIDENCE_CONFIRMED else "unconfirmed")
        camp["flags"] = (["silent", "provisional"] if silent else [])
        camp["open_task_id"] = "verify-" + camp_id if silent else None
        water = camp["stock"].get("water", {}).get("quantity")
        headcount = max(1, int(camp.get("headcount") or 1))
        camp["stock"].setdefault("water", {"quantity": 0, "unit": "person_days", "days_left": 0, "as_of": None})
        camp["stock"]["water"]["days_left"] = round((water or 0) / headcount, 2)
        vulnerable = camp.get("vulnerable_counts", {})
        vshare = sum(int(v or 0) for v in vulnerable.values()) / headcount
        days = camp["stock"]["water"]["days_left"]
        medical = any(r.get("medical_flag") for r in camp["requests"])
        override = (medical and camp["status"] == "confirmed") or days < 1
        shortfall = min(1.0, max(0.0, (settings.ALLOCATION_TARGET_DAYS - days) / settings.ALLOCATION_TARGET_DAYS))
        score = 100 * (settings.SCORE_WEIGHTS["supply_shortfall"] * shortfall +
                       settings.SCORE_WEIGHTS["vulnerable_share"] * min(1, vshare) +
                       settings.SCORE_WEIGHTS["time_since_delivery"] * 0.0 +
                       settings.SCORE_WEIGHTS["access_difficulty"] * float(camp.get("access_difficulty", 0)))
        tier = "override" if override else ("high" if score >= settings.TIER_HIGH else "medium" if score >= settings.TIER_MEDIUM else "low")
        reasons = []
        if silent: reasons.append("No recent report; camp is uncertain and receives a provisional minimum")
        if medical and camp["status"] == "confirmed": reasons.append("Confirmed medical emergency")
        reasons.append(f"{days:.2f} days of water left")
        if camp.get("access_difficulty", 0) >= 0.6: reasons.append("Difficult to access")
        camp["priority"] = {"tier": tier, "score": round(score, 1), "reasons": reasons}
    return {"camps": camps, "depots": depots, "roads": roads, "volunteers": volunteers,
            "tasks": tasks, "decisions": decisions, "deliveries": deliveries, "requests": requests}

def haversine_km(a: dict, b: dict) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (a["lat"], a["lng"], b["lat"], b["lng"]))
    dlat, dlon = lat2-lat1, lon2-lon1
    h = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(h))

def build_tasks(state: dict, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    out = []
    for camp_id, c in state["camps"].items():
        if not c.get("silent"): continue
        best, distance = None, float("inf")
        for user, v in state["volunteers"].items():
            stamp = parse_time(v.get("reported_at"))
            loc = v.get("location")
            if not loc or not stamp or (now-stamp).total_seconds() > settings.VOLUNTEER_LOCATION_MAX_AGE_MINUTES * settings.SCENARIO_MINUTE_SECONDS:
                continue
            d = haversine_km(c["location"], loc) if c.get("location") else float("inf")
            if d < distance: best, distance = user, d
        out.append({
            "task_id": "verify-" + camp_id, "kind": "verify_camp", "camp_id": camp_id,
            "camp_name": c["name"], "camp_location": c.get("location"),
            "status": "assigned" if best else "unassigned", "assigned_to": best,
            "reason": "No report within expected reporting interval",
            "created_at": c.get("last_report_at"), "distance_km": round(distance, 2) if best else None,
        })
    return out

def recommend(state: dict, state_version: str) -> dict:
    """Two-phase water allocation: one-day minimum first, then priority to 3-day target."""
    remaining = {}
    for depot_id, depot in state["depots"].items():
        remaining[depot_id] = {k: float(v.get("quantity", 0)) for k, v in depot["stock"].items()}
    allocations, shortages = [], []
    camps = sorted(state["camps"].items(), key=lambda pair: (
        {"override": 0, "high": 1, "medium": 2, "low": 3}[pair[1]["priority"]["tier"]],
        -pair[1]["priority"]["score"]))
    def take(camp_id, camp, item, need, provisional, phase):
        left = max(0.0, float(need))
        for depot_id in sorted(remaining):
            available = remaining[depot_id].get(item, 0.0)
            qty = min(left, available)
            if qty <= 0: continue
            remaining[depot_id][item] -= qty
            allocation_id = str(uuid5(NAMESPACE_URL, f"trana:{state_version}:{camp_id}:{item}:{phase}:{len(allocations)}"))
            allocations.append({"allocation_id": allocation_id, "camp_id": camp_id, "item": item,
                                "quantity": round(qty, 2), "unit": "person_days" if item in ("water", "food") else "kits",
                                "provisional": provisional, "tier": camp["priority"]["tier"],
                                "reasons": ["Minimum guarantee (1 day), provisional because camp is silent" if provisional and phase == 1
                                            else "Minimum guarantee (1 day)" if phase == 1
                                            else "Priority-weighted allocation toward 3-day target"],
                                "from_depot_id": depot_id})
            left -= qty
            if left <= 0: break
        if left > 0: shortages.append({"camp_id": camp_id, "item": item, "gap": round(left, 2),
                                       "unit": "person_days" if item in ("water", "food") else "kits"})
    # Phase 1: minimum guarantee to every camp in tier order.
    for camp_id, camp in camps:
        people = max(0, float(camp.get("headcount", 0)))
        for item in ("water", "food"):
            current = float(camp.get("stock", {}).get(item, {}).get("quantity", 0))
            take(camp_id, camp, item, max(0, people - current), camp["status"] == "uncertain", 1)
    # Phase 2: additional allocation, in priority order, up to 3 days total.
    for camp_id, camp in camps:
        people = max(0, float(camp.get("headcount", 0)))
        for item in ("water", "food"):
            current = float(camp.get("stock", {}).get(item, {}).get("quantity", 0))
            prior = sum(a["quantity"] for a in allocations if a["camp_id"] == camp_id and a["item"] == item)
            take(camp_id, camp, item, max(0, people * settings.ALLOCATION_TARGET_DAYS - current - prior),
                 camp["status"] == "uncertain", 2)
        for _, request, _ in [r for r in state["requests"] if r[0] == camp_id]:
            if request.get("item") == "medicine":
                take(camp_id, camp, "medicine", request.get("quantity_needed", 0), False, 3)
    plan_id = "plan-" + state_version.removeprefix("sv-")
    return {"plan_id": plan_id, "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "state_version": state_version, "allocations": allocations, "shortages": shortages, "notes": []}
