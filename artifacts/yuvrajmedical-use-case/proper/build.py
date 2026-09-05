from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,html,textwrap,heapq,re,xml.etree.ElementTree as ET
O=Path(__file__).parent;model=json.loads((O.parent/'model.json').read_text())
modules=[
('Account Access & Profile','Register|Verify OTP|Send OTP|Login|Authenticate User|Logout|Manage Profile|Manage Family Members|Manage Delivery Addresses'),
('Medicine Catalogue, Cart & Wishlist','Browse Medicines|Search Medicines|Filter Medicines|View Medicine Details|Add Medicine to Cart|Update Cart Quantity|Remove Medicine from Cart|Manage Cart|Save Medicine for Later|Move Saved Medicine to Cart|Add Medicine to Wishlist|Remove Medicine from Wishlist'),
('Orders & Checkout','Place Order|Checkout|Review Cart|Select Delivery Address|Check Stock Availability|View Order Details|Track Order|Cancel Order|View Order History|Apply Referral Reward'),
('Payments','Make Payment|Process Payment|Verify Payment|Return Payment Status|View Payments'),
('Prescription Handling','Upload Prescription|Submit Prescription Request|View Prescription Status|View Prescription Requests|View Prescription Request|Review Prescription|Approve Prescription|Reject Prescription'),
('Staff Order Processing & Inventory','View Staff Dashboard|View Orders|Process Order|Check Stock Availability|Update Stock|Update Order Status|View Medicines|Manage Medicine Stock|Record Stock Movement|Add Stock|Reduce Stock|View Stock History|View Low Stock Medicines|View Customer Order Information'),
('Subscriptions, Notifications & Rewards','Subscribe to Medicine|Manage Medicine Subscription|Use Referral|View Referral Rewards|Submit Review & Feedback|View Notifications|Manage Notification Preferences|Send Order Notification|Send Payment Notification|Send Prescription Status Notification|Send Subscription Reminder'),
('Medicine & Service Administration','Manage Medicines|Add Medicine|Update Medicine|Delete Medicine|Manage Disease Categories|Manage Delivery Areas|ViewStockPlaceholder'),
('Staff Administration & Reporting','Manage Staff|Add Staff|Update Staff|Remove Staff|View Staff Details|View Owner Dashboard|View Sales Summary|View Order Statistics|View Inventory Summary|View Customers|View Stock Movements|View Reviews & Feedback')]
modules[7]=(modules[7][0],modules[7][1].replace('|ViewStockPlaceholder',''))
modules=[(title,items.split('|')) for title,items in modules]
covered={x for _,items in modules for x in items}
assert covered==set(model['use_cases']),(set(model['use_cases'])-covered,covered-set(model['use_cases']))
W,H=2800,1950;G=20;font='/usr/share/fonts/liberation/LiberationSans-Regular.ttf';bold=font.replace('Regular','Bold');pages=[];svgs=[];rendered_assocs=set();rendered_deps={'include':set(),'extend':set()}
router=(O.parent.parent/'yuvrajmedical-dfd'/'compact.py').read_text();router=router[router.index('G=20;'):router.index('# Local store links first')]
router=router.replace("   out.append((pt,ep,portsused.get((k,ep),0)*35))", """   if n['kind']=='usecase':
    cx,cy=x+w/2,y+h/2;dx,dy=ep[0]-cx,ep[1]-cy;scale=1/math.sqrt((dx/(w/2))**2+(dy/(h/2))**2);ep=(cx+scale*dx,cy+scale*dy)
   else:ep=(x+w/2,y+h/2)
   out.append((pt,ep,portsused.get((k,ep),0)*35))""")
for index,(title,cases) in enumerate(modules):
 nodes={};columns=3 if len(cases)<=12 else 4;rows=math.ceil(len(cases)/columns);cw=1900/columns;rw=1250/max(rows,3);ow=450 if columns==3 else 340;oh=110
 # Separate rows of paired dependencies to keep labels in the gaps.
 for i,name in enumerate(cases):
  col=i%columns;row=i//columns;cx=540+cw*(col+.5);cy=420+rw*row
  nodes[name]={'x':int(cx-ow/2),'y':int(cy-oh/2),'w':ow,'h':oh,'kind':'usecase','label':name}
 roles={actor:[uc for uc in ucs if uc in cases] for actor,ucs in model['actors'].items()};roles={a:ucs for a,ucs in roles.items() if ucs}
 rights=[a for a in ['OTP / SMS Service','Staff','Payment Gateway','Owner / Admin'] if a in roles]
 rightYs={a:340+i*(1150/max(len(rights)-1,1)) for i,a in enumerate(rights)}
 if len(rights)==1:rightYs[rights[0]]=950
 for a in roles:
  x,y=(160,920) if a=='Customer' else (2630,rightYs[a]);nodes[a]={'x':int(x-60),'y':int(y-65),'w':120,'h':130,'kind':'actor','label':a}
 exec(router)
 # Confine diagram routes above the notes; do not route over headings.
 for xx in range(W//G):
  for yy in range(0,270//G):blocked.add((xx,yy))
  for yy in range(1740//G,H//G):blocked.add((xx,yy))
 edges=[]
 for kind in ['include','extend']:
  for a,b in model[kind]:
   if a in cases and b in cases:
    e={'a':a,'b':b,'kind':kind,'label':'<<'+kind+'>>'}
    if a=='Process Order' and b=='Check Stock Availability':
     na,nb=nodes[a],nodes[b];ax=na['x']+na['w']/2;bx=nb['x']+nb['w']/2;e['pts']=[(ax,na['y']),(ax,315),(bx,315),(bx,nb['y'])]
    else:e['pts']=route(a,b)
    e['labelpos']=place_label(e['pts'],e['label']);edges.append(e);rendered_deps[kind].add((a,b))
 for actor,ucs in roles.items():
  for uc in ucs:edges.append({'a':actor,'b':uc,'kind':'association','pts':route(actor,uc)});rendered_assocs.add((actor,uc))
 im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>']
 def text(x,y,t,size=24,b=False):
  f=ImageFont.truetype(bold if b else font,size);ls=t.split('\n')
  for k,l in enumerate(ls):
   yy=y+(k-(len(ls)-1)/2)*(size+6);svg.append(f'<text x="{x}" y="{yy}" text-anchor="middle" dominant-baseline="central" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" font-weight="{700 if b else 400}" fill="#172b3b">{html.escape(l)}</text>');d.text((x,yy),l,font=f,fill='#172b3b',anchor='mm')
 def rect(box,fill='white',stroke='#344252'):
  x,y,xx,yy=box;svg.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>');d.rectangle(box,fill,stroke,2)
 def line(pts,dash=False,color='#344252',width=2):
  svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"'+(' stroke-dasharray="10 7"' if dash else '')+'/>')
  for a,b in zip(pts,pts[1:]):
   if not dash:d.line([a,b],fill=color,width=width);continue
   le=math.dist(a,b)
   if not le:continue
   for k in range(0,math.ceil(le),17):
    z=min(k+10,le);d.line([(a[0]+(b[0]-a[0])*k/le,a[1]+(b[1]-a[1])*k/le),(a[0]+(b[0]-a[0])*z/le,a[1]+(b[1]-a[1])*z/le)],fill=color,width=width)
 def arrow(a,b):
  dx,dy=a[0]-b[0],a[1]-b[1];le=math.hypot(dx,dy);ux,uy=dx/le,dy/le;line([(a[0]-ux*16-uy*7,a[1]-uy*16+ux*7),a,(a[0]-ux*16+uy*7,a[1]-uy*16-ux*7)],width=3)
 text(W/2,65,title,37,True);text(W/2,112,f'YuvrajMedical · UML Use Cases · Section {index+1} of {len(modules)}',23)
 rect((400,185,2440,1750));text(1420,230,'YuvrajMedical Online Medical Store System',30,True)
 for e in sorted(edges,key=lambda e:e['kind']!='association'):
  svg.append(f'<g class="edge" data-a="{html.escape(e["a"],quote=True)}" data-b="{html.escape(e["b"],quote=True)}" data-kind="{e["kind"]}"><title>{html.escape(e["a"]+" — "+e["kind"]+" — "+e["b"])}</title>');line(e['pts'],color='white',width=7);line(e['pts'],dash=e['kind']!='association')
  if e['kind']!='association':arrow(e['pts'][-1],e['pts'][-2])
  svg.append('</g>')
 for e in edges:
  if e['kind']=='association':continue
  x,y,ls,box,_,_=e['labelpos'];svg.append(f'<g class="edge" data-a="{html.escape(e["a"],quote=True)}" data-b="{html.escape(e["b"],quote=True)}" data-kind="{e["kind"]}">');rect(box,'white','white');text(x,y,e['label'],21);svg.append('</g>')
 for n,nd in nodes.items():
  x,y,w,h=[nd[k] for k in ['x','y','w','h']];cx,cy=x+w/2,y+h/2;svg.append(f'<g class="node" data-id="{html.escape(n,quote=True)}" data-kind="{nd["kind"]}"><title>{html.escape(n)}</title>')
  if nd['kind']=='usecase':
   svg.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="#eff5f8" stroke="#344252" stroke-width="2"/>');d.ellipse((x,y,x+w,y+h),fill='#eff5f8',outline='#344252',width=2);text(cx,cy,'\n'.join(textwrap.wrap(n,29 if columns==3 else 23)),25)
   assert x>400 and x+w<2440 and y>185 and y+h<1750
  else:
   svg.append(f'<circle cx="{cx}" cy="{cy-60}" r="24" fill="white" stroke="#344252" stroke-width="3"/>');d.ellipse((cx-24,cy-84,cx+24,cy-36),fill='white',outline='#344252',width=3);line([(cx,cy-36),(cx,cy+40)],width=3);line([(cx-48,cy),(cx+48,cy)],width=3);line([(cx-44,cy+100),(cx,cy+40),(cx+44,cy+100)],width=3);rect((cx-145,cy+116,cx+145,cy+188),'white','white');text(cx,cy+146,'\n'.join(textwrap.wrap(n,16)),26,True)
   assert x+w<400 or x>2440
  svg.append('</g>')
 text(W/2,1800,'Solid line: actor association     •     Dashed open arrow: <<include>> / <<extend>>',22)
 notes=[]
 if 'Customer' in roles:notes.append('Authenticated Customer required for protected shopping, account and order functions.')
 if 'Staff' in roles:notes.append('Authenticated Staff required for staff operations.')
 if 'Owner / Admin' in roles:notes.append('Authenticated Owner/Admin required for administrative operations.')
 text(W/2,1850,'\n'.join(notes),20)
 svg.append('</svg>');sv='\n'.join(svg);slug=f'{index+1:02d}-'+re.sub('[^a-z0-9]+','-',title.lower()).strip('-');(O/(slug+'.svg')).write_text(sv);im.save(O/(slug+'.png'),dpi=(200,200));im.resize((1400,975)).save(O/(slug+'-preview.png'));pages.append(im);svgs.append({'title':title,'svg':sv,'cases':cases,'roles':roles});print('Rendered',title,flush=True)
pages[0].save(O/'YuvrajMedical-Use-Cases-Complete.pdf',save_all=True,append_images=pages[1:],resolution=180.0,title='YuvrajMedical — Complete UML Use Cases',author='YuvrajMedical',subject='Readable section views of the complete UML use case model')
expected_assocs={(a,uc) for a,ucs in model['actors'].items() for uc in ucs}
assert rendered_assocs==expected_assocs,(expected_assocs-rendered_assocs)
for k in ['include','extend']:assert rendered_deps[k]=={tuple(e) for e in model[k]},(k,{tuple(e) for e in model[k]}-rendered_deps[k])
# Keep the authoritative, non-duplicated master in this deliverable.
master=(O.parent/'yuvrajmedical-use-case.svg').read_text();(O/'YuvrajMedical-Use-Cases-Master.svg').write_text(master)
views=[{'title':'Complete master diagram','svg':master}]+svgs
css='''body{margin:0;font:16px Arial,sans-serif;color:#172b3b;background:#f3f5f7}header{padding:16px 24px;background:white;border-bottom:1px solid #c7d1da;position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:14px;flex-wrap:wrap}h1{font-size:20px;margin:0 16px 0 0}select,button{padding:10px;border:1px solid #b9c7d2;border-radius:6px;background:white;color:#172b3b}#hint{padding:12px 24px;background:#edf3f7;font-size:14px}main{padding:20px}svg{width:100%;height:auto;background:white}.node{cursor:pointer}.dim{opacity:.055}.focus{filter:drop-shadow(0 0 5px #4f8ba8)}.edge,.node{transition:opacity .15s}aside{display:none;position:fixed;right:20px;top:150px;bottom:20px;width:310px;padding:18px;overflow:auto;background:white;border:1px solid #c7d1da;box-shadow:0 3px 18px #0001;z-index:4}aside h2{font-size:18px}aside li{font-size:14px;margin-bottom:12px}'''
options=''.join(f'<option value="{i}">{html.escape(v["title"])}</option>' for i,v in enumerate(views))
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>YuvrajMedical — Complete UML Use Cases</title><style>'''+css+'''</style></head><body><header><h1>YuvrajMedical · Use Cases</h1><label>Section <select id="sections">'''+options+'''</select></label><button id="all">Clear highlight</button><button id="in">Zoom +</button><button id="out">Zoom −</button><button id="fit">Fit page</button></header><div id="hint">All 86 use cases are included across these sections. Choose “Complete master diagram” for the single system-wide view. Click an actor or use case to inspect its connections.</div><main id="canvas"></main><aside id="details"></aside><script>const views=VIEWS,model=MODEL;
const select=document.querySelector('#sections'),canvas=document.querySelector('#canvas'),details=document.querySelector('#details');
function clear(){canvas.querySelectorAll('.dim,.focus').forEach(n=>n.classList.remove('dim','focus'));details.style.display='none'}
function show(i){canvas.innerHTML=views[i].svg;select.value=i;clear();canvas.querySelectorAll('.node').forEach(n=>n.addEventListener('click',()=>focus(n.dataset.id)))}
function focus(id){clear();let keep=new Set([id]),present=new Set([...canvas.querySelectorAll('.node')].map(n=>n.dataset.id)),actor=!!model.actors[id];
canvas.querySelectorAll('.edge').forEach(e=>{let hit=e.dataset.a===id||e.dataset.b===id;if(hit){keep.add(e.dataset.a);keep.add(e.dataset.b)}e.classList.toggle('dim',!hit)});canvas.querySelectorAll('.node').forEach(n=>{n.classList.toggle('dim',!keep.has(n.dataset.id));n.classList.toggle('focus',n.dataset.id===id)});
details.replaceChildren();let h=document.createElement('h2');h.textContent=id;details.append(h);let ul=document.createElement('ul'),items=actor?model.actors[id].filter(x=>present.has(x)):Object.entries(model.actors).filter(([a,ucs])=>ucs.includes(id)&&present.has(a)).map(([a])=>'Actor: '+a);if(!actor){for(let kind of ['include','extend'])model[kind].filter(([a,b])=>(a===id||b===id)&&present.has(a)&&present.has(b)).forEach(([a,b])=>items.push(a+' <<'+kind+'>> '+b))}items.forEach(t=>{let li=document.createElement('li');li.textContent=t;ul.append(li)});details.append(ul);details.style.display='block'}
select.onchange=()=>show(Number(select.value));document.querySelector('#all').onclick=clear;document.querySelector('#in').onclick=()=>{let s=canvas.querySelector('svg');s.style.width=(s.getBoundingClientRect().width*1.2)+'px'};document.querySelector('#out').onclick=()=>{let s=canvas.querySelector('svg');s.style.width=(s.getBoundingClientRect().width/1.2)+'px'};document.querySelector('#fit').onclick=()=>canvas.querySelector('svg').style.width='100%';show(1);
</script></body></html>'''.replace('VIEWS',json.dumps(views).replace('</','<\\/')).replace('MODEL',json.dumps(model))
(O/'YuvrajMedical-Use-Cases-Interactive.html').write_text(page)
report={'status':'passed','unique_master_actors':5,'unique_master_use_cases':len(covered),'actor_associations':len(rendered_assocs),'include_dependencies':len(rendered_deps['include']),'extend_dependencies':len(rendered_deps['extend']),'readable_sections':len(modules),'missing_use_cases':[],'missing_associations':[],'missing_dependencies':[],'note':'Section views share contextual nodes where needed. The full master diagram contains each actor and use case exactly once.'}
(O/'coverage-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
Path('/tmp/yuvraj-proper-uml.js').write_text(re.search(r'<script>(.*?)</script>',page,re.S).group(1))
