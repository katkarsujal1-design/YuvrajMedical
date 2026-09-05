from pathlib import Path
import xml.etree.ElementTree as E,json,re
p=Path(__file__).parent;ns={'s':'http://www.w3.org/2000/svg'};model=json.loads((p/'model.json').read_text());summary=json.loads((p/'validation.json').read_text())
for c in model:
 root=E.parse(p/(c['slug']+'.svg')).getroot();w,h=int(root.get('width')),int(root.get('height'));assert w>h
 nodes=[g for g in root.findall('s:g',ns) if g.get('class')=='node'];ids=[g.get('data-id') for g in nodes];assert len(ids)==len(set(ids))
 assert len([g for g in nodes if g.get('data-kind')=='start'])==1
 for g in nodes:
  kind=g.get('data-kind');lane=g.get('data-lane');assert lane in c['lanes'];left=65+c['lanes'].index(lane)*(w-130)/len(c['lanes']);right=left+(w-130)/len(c['lanes'])
  if kind=='action':
   r=g.find('s:rect',ns);assert r is not None and float(r.get('rx'))>0
   x,y,ww,hh=[float(r.get(k)) for k in ['x','y','width','height']];assert left<=x and x+ww<=right and 282<=y and y+hh<h-105,(c['slug'],g.get('data-id'),'outside lane')
  if kind=='decision' or kind=='merge':assert g.find('s:polygon',ns) is not None
  if kind=='end':assert len(g.findall('s:circle',ns))==2
  assert not g.findall('s:ellipse',ns)
 flows=[g for g in root.findall('s:g',ns) if g.get('class')=='flow'];assert all(g.find('s:polygon',ns) is not None for g in flows)
 out={i:[] for i in ids}
 for g in flows:assert g.get('data-from') in out and g.get('data-to') in out;out[g.get('data-from')].append(g)
 for g in nodes:
  if g.get('data-kind')=='decision':assert len(out[g.get('data-id')])>=2 and all(e.find('s:title',ns).text!='Control flow' for e in out[g.get('data-id')])
 text=' '.join(t.text or '' for t in root.findall('.//s:text',ns));assert not re.search(r'\b(?:PK|FK)\b|1:N|1:1',text)
main=model[0];assert main['lanes']==['C','S','T','P','O']
assert all(n['label'].startswith('Send') for n in main['nodes'].values() if n['lane']=='O' and n['kind']=='action')
assert [n['label'] for n in main['nodes'].values() if n['lane']=='P' and n['kind']=='action']==['Process transaction']
pdf=(p/'YuvrajMedical-Activity-Complete.pdf').read_bytes();assert len(re.findall(rb'/Type /Page\b',pdf))==17
print('Validated 17 landscape activity diagrams: lane placement, labelled decisions, unique nodes, control-flow arrows, one start per diagram, proper final nodes, and five correctly ordered main swimlanes.')
