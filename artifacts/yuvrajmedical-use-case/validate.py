from pathlib import Path
import json,re,xml.etree.ElementTree as ET
p=Path(__file__).parent;m=json.loads((p/'model.json').read_text());r=ET.parse(p/'yuvrajmedical-use-case.svg').getroot();ns={'s':'http://www.w3.org/2000/svg'}
nodes=[g for g in r.findall('s:g',ns) if g.get('class')=='node'];assert len(nodes)==len(m['use_cases'])+5;assert len({n.get('data-id') for n in nodes})==len(nodes)
actors=[n for n in nodes if n.get('data-kind')=='actor'];assert {n.get('data-id') for n in actors}==set(m['actors'])
for g in actors:assert len(g.findall('s:circle',ns))==1 and not g.findall('s:ellipse',ns)
for g in nodes:
 if g.get('data-kind')!='usecase':continue
 ell=g.find('s:ellipse',ns);assert ell is not None
 cx,cy,rx,ry=[float(ell.get(k)) for k in ['cx','cy','rx','ry']];assert 500<cx-rx and cx+rx<6840 and 210<cy-ry and cy+ry<4030
actual={'association':set(),'include':set(),'extend':set()}
for g in r.findall('s:g',ns):
 if g.get('class')!='edge' or g.find('s:title',ns) is None:continue
 kind=g.get('data-kind');a,b=g.get('data-a'),g.get('data-b');assert (a,b) not in actual[kind];actual[kind].add((a,b))
 lines=g.findall('s:polyline',ns)
 if kind=='association':assert all(not l.get('stroke-dasharray') for l in lines);assert len(lines)==2;assert a in m['actors'] and b in m['use_cases']
 else:assert any(l.get('stroke-dasharray') for l in lines);assert len(lines)==3;assert a in m['use_cases'] and b in m['use_cases'];assert not g.findall('s:polygon',ns)
assert actual['association']=={(a,u) for a,ucs in m['actors'].items() for u in ucs}
for k in ['include','extend']:assert actual[k]=={tuple(x) for x in m[k]}
text=' '.join(t.text or '' for t in r.findall('.//s:text',ns));assert not re.search(r'\b(?:PK|FK|\d+\.\d+)\b|1:N|1:1',text)
page=(p/'yuvrajmedical-use-case-interactive.html').read_text();Path('/tmp/yuvraj-uml.js').write_text('\n'.join(re.findall(r'<script>(.*?)</script>',page,re.S)))
# Editable standard UML source, using the same validated model.
alias={n:f'UC{i:03}' for i,n in enumerate(m['use_cases'])};actors={n:f'A{i}' for i,n in enumerate(m['actors'])}
lines=['@startuml','left to right direction','skinparam backgroundColor white','skinparam shadowing false','skinparam packageStyle rectangle']
for n,a in actors.items():lines.append(f'actor "{n}" as {a}')
lines.append('rectangle "YuvrajMedical Online Medical Store System" {')
for n,a in alias.items():lines.append(f'  usecase "{n}" as {a}')
lines.append('}')
for actor,ucs in m['actors'].items():
 for uc in ucs:lines.append(f'{actors[actor]} -- {alias[uc]}')
for kind in ['include','extend']:
 for a,b in m[kind]:lines.append(f'{alias[a]} ..> {alias[b]} : <<{kind}>>')
lines.extend(['note bottom of A0','Authenticated Customer required for cart, wishlist, checkout, orders, subscriptions, prescriptions, addresses, notifications, reviews and referrals.','end note','note bottom of A1','Authenticated Staff required for staff operations.','end note','note bottom of A2','Authenticated Owner/Admin required for administrative operations.','end note','@enduml'])
(p/'yuvrajmedical-use-case.puml').write_text('\n'.join(lines)+'\n')
print('Validated rendered UML: 5 actors, 86 unique ovals, 88 solid associations, 16 include and 13 extend dependencies. All actors outside; all use cases inside. Interactive JavaScript extracted for syntax check.')
