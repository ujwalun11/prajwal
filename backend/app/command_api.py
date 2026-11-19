"""Person C command endpoints. Mount command_router from backend.app.main after A's engine is merged."""
import csv, io, json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .db import SessionLocal, list_events
from .main import _state, _version
from .engine import recommend
from .settings import ALLOCATION_TARGET_DAYS, MINIMUM_GUARANTEE_DAYS
from .routing.graph import route_between
from .insights import build_insights
from .simulate import simulate

command_router=APIRouter()

class SimulateRequest(BaseModel):
    camp_id: str | None = None
    headcount_delta: int = 0
    stock_deltas: dict[str,float] = Field(default_factory=dict)

@command_router.get('/api/routes')
def get_route(from_id: str = Query(alias='from'), to_id: str = Query(alias='to')):
    with SessionLocal() as s:
        events=list_events(s,0,10000)
        try: return route_between(from_id,to_id,events=events)
        except KeyError: raise HTTPException(404,detail={'code':'unknown_site'})
        except Exception as exc: raise HTTPException(404,detail={'code':'no_route','message':str(exc)})

@command_router.get('/api/insights')
def get_insights():
    with SessionLocal() as s:
        events=list_events(s,0,10000); state=_state(s); plan=recommend(state,_version(s))
        return build_insights(state,plan,events,ALLOCATION_TARGET_DAYS,MINIMUM_GUARANTEE_DAYS)

@command_router.post('/api/simulate')
def what_if(body: SimulateRequest):
    with SessionLocal() as s:
        try: return simulate(_state(s),_version(s),body.camp_id,body.headcount_delta,body.stock_deltas)
        except KeyError: raise HTTPException(404,detail={'code':'unknown_camp'})

@command_router.get('/api/report')
def report(format: str = Query(pattern='^(pdf|csv)$')):
    with SessionLocal() as s:
        events=list_events(s,0,10000); state=_state(s); plan=recommend(state,_version(s))
        insights=build_insights(state,plan,events,ALLOCATION_TARGET_DAYS,MINIMUM_GUARANTEE_DAYS)
    if format=='csv':
        stream=io.StringIO(); writer=csv.writer(stream); writer.writerow(['camp_id','camp_name','status','confidence','tier','priority_score','water_days'])
        for c in state['camps'].values():
            writer.writerow([c['camp_id'],c['name'],c['status'],c['confidence'],c['priority']['tier'],c['priority']['score'],c['stock']['water']['days_left']])
        return Response(stream.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=trana-situation.csv'})
    buffer=io.BytesIO(); pdf=canvas.Canvas(buffer,pagesize=A4); width,height=A4
    pdf.setTitle('TRANA simulated situation report'); y=height-52
    pdf.setFont('Helvetica-Bold',16); pdf.drawString(42,y,'TRANA — Simulated Situation Report'); y-=28
    pdf.setFont('Helvetica',9); pdf.drawString(42,y,'For demonstration only · as of '+str(insights.get('as_of'))); y-=26
    for c in state['camps'].values():
        if y<70: pdf.showPage(); y=height-50
        pdf.setFont('Helvetica-Bold',10); pdf.drawString(42,y,f"{c['name']} — {c['status']} — {c['priority']['tier']} ({c['priority']['score']})"); y-=14
        pdf.setFont('Helvetica',9); pdf.drawString(52,y,f"People: {c['headcount']} | Water days: {c['stock']['water']['days_left']} | Confidence: {c['confidence']}"); y-=20
    pdf.save(); buffer.seek(0)
    return Response(buffer.read(),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename=trana-situation.pdf'})
