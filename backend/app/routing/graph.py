"""NetworkX road routing. Closed roads are removed only when the report is trusted."""
import json
from pathlib import Path
import networkx as nx
from backend.app.engine import confidence_for
ROOT=Path(__file__).resolve().parents[3]

def load_roads(path=None):
    source=Path(path) if path else ROOT/'scenario'/'roads.geojson'
    if not source.exists(): return {"type":"FeatureCollection","features":[]}
    return json.loads(source.read_text(encoding='utf-8'))

def build_graph(roads_geojson=None, events=None):
    data=roads_geojson or load_roads()
    state_events=events or []
    graph=nx.Graph()
    reports={}
    for event in state_events:
        if event.get('type')=='road_status':
            reports[event['subject']]=event
    for feature in data.get('features',[]):
        props=feature.get('properties',{})
        coords=feature.get('geometry',{}).get('coordinates',[])
        if len(coords)<2: continue
        road_id=props.get('road_id') or props.get('id')
        report=reports.get(road_id)
        status=(report or {}).get('payload',{}).get('status','open')
        confidence=confidence_for(report,state_events) if report else 0
        closed=status in ('blocked','flooded')
        trusted_closed=closed and confidence>=0.70
        warning=closed and not trusted_closed
        if trusted_closed: continue
        for a,b in zip(coords,coords[1:]):
            u=tuple(round(v,6) for v in a); v=tuple(round(v,6) for v in b)
            distance=((a[0]-b[0])**2+(a[1]-b[1])**2)**0.5*111
            graph.add_edge(u,v,weight=max(distance,0.001),road_id=road_id,
                           warning=warning,warning_text=f"Road {road_id} closure unconfirmed" if warning else None)
    return graph

def _nearest_node(graph, coordinate):
    if not graph.nodes: return None
    return min(graph.nodes,key=lambda n:(n[0]-coordinate[0])**2+(n[1]-coordinate[1])**2)

def route_between(start, end, roads_geojson=None, events=None):
    locations={}
    data=roads_geojson or load_roads()
    for f in data.get('features',[]):
        props=f.get('properties',{})
        for key in ('from_id','to_id'):
            if props.get(key) and props.get(key+'_location'): locations[props[key]]=props[key+'_location']
    locations.update((x['id'],x['location']) for x in data.get('sites',[]) if x.get('location'))
    if start not in locations or end not in locations:
        raise KeyError('unknown_site')
    graph=build_graph(data,events)
    source,target=_nearest_node(graph,locations[start]),_nearest_node(graph,locations[end])
    if source is None or target is None: raise nx.NetworkXNoPath('Road graph is empty')
    weighted=graph.copy()
    for u,v,attrs in weighted.edges(data=True):
        if attrs.get('warning'): attrs['weight']*=4
    path=nx.shortest_path(weighted,source,target,weight='weight')
    warnings=[]
    for u,v in zip(path,path[1:]):
        attrs=weighted[u][v]
        if attrs.get('warning') and attrs.get('warning_text') not in warnings: warnings.append(attrs['warning_text'])
    km=sum(weighted[u][v]['weight'] for u,v in zip(path,path[1:]))
    return {'ok':True,'eta':round(km/20*60),'distance_km':round(km,2),
            'path':{'type':'LineString','coordinates':[[x,y] for x,y in path]},'warnings':warnings}

def reachable(start, end, roads_geojson=None, events=None):
    try: route_between(start,end,roads_geojson,events); return True
    except (KeyError,nx.NetworkXNoPath,nx.NodeNotFound): return False
