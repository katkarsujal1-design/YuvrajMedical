from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,html,textwrap,heapq
O=Path(__file__).parent;W,H=7600,4600
font='/usr/share/fonts/liberation/LiberationSans-Regular.ttf';bold=font.replace('Regular','Bold')
customer='Register|Login|Logout|Verify OTP|Manage Profile|Manage Family Members|Manage Delivery Addresses|Browse Medicines|Search Medicines|Filter Medicines|View Medicine Details|Add Medicine to Cart|Update Cart Quantity|Remove Medicine from Cart|Save Medicine for Later|Move Saved Medicine to Cart|Add Medicine to Wishlist|Remove Medicine from Wishlist|Subscribe to Medicine|Manage Medicine Subscription|Upload Prescription|Submit Prescription Request|View Prescription Status|Place Order|Checkout|Select Delivery Address|Make Payment|View Order History|View Order Details|Track Order|Cancel Order|View Notifications|Manage Notification Preferences|Submit Review & Feedback|Use Referral|View Referral Rewards|Manage Cart'.split('|')
staff='Login|Logout|View Staff Dashboard|View Orders|Process Order|Update Order Status|View Prescription Requests|Review Prescription|Approve Prescription|Reject Prescription|View Medicines|Manage Medicine Stock|Add Stock|Reduce Stock|Record Stock Movement|View Stock History|View Low Stock Medicines|View Customer Order Information'.split('|')
admin='Login|Logout|View Owner Dashboard|View Sales Summary|View Order Statistics|View Inventory Summary|Manage Medicines|Add Medicine|Update Medicine|Delete Medicine|Manage Disease Categories|Manage Staff|Add Staff|Update Staff|Remove Staff|View Staff Details|Manage Delivery Areas|View Orders|View Payments|View Customers|View Prescription Requests|View Stock Movements|View Reviews & Feedback|View Referral Rewards'.split('|')
roles={'Customer':customer,'Staff':staff,'Owner / Admin':admin,'Payment Gateway':['Process Payment','Verify Payment','Return Payment Status'],'OTP / SMS Service':['Send OTP','Verify OTP','Send Order Notification','Send Payment Notification','Send Prescription Status Notification','Send Subscription Reminder']}
includes=[('Register','Verify OTP'),('Login','Authenticate User'),('Verify OTP','Send OTP'),('Add Medicine to Cart','View Medicine Details'),('Checkout','Review Cart'),('Checkout','Select Delivery Address'),('Place Order','Checkout'),('Place Order','Check Stock Availability'),('Make Payment','Process Payment'),('Process Payment','Verify Payment'),('Process Order','Check Stock Availability'),('Process Order','Update Stock'),('Manage Medicine Stock','Record Stock Movement'),('Upload Prescription','Submit Prescription Request'),('Review Prescription','View Prescription Request'),('View Staff Details','Manage Staff')]
extends=[('Cancel Order','View Order Details'),('Track Order','View Order Details'),('Save Medicine for Later','Manage Cart'),('Move Saved Medicine to Cart','Save Medicine for Later'),('Apply Referral Reward','Checkout'),('Approve Prescription','Review Prescription'),('Reject Prescription','Review Prescription'),('Add Medicine','Manage Medicines'),('Update Medicine','Manage Medicines'),('Delete Medicine','Manage Medicines'),('Add Staff','Manage Staff'),('Update Staff','Manage Staff'),('Remove Staff','Manage Staff')]
# Each use case has one oval, even when multiple actors participate.
modules=[
('Authentication',0,520,'#edf3fc','Register|Verify OTP|Send OTP|Login|Authenticate User|Logout'),
('Shopping',1,520,'#eaf5ef','Add Medicine to Cart|Update Cart Quantity|Remove Medicine from Cart|Manage Cart|Save Medicine for Later|Move Saved Medicine to Cart|Add Medicine to Wishlist|Remove Medicine from Wishlist'),
('Medicine catalogue',2,520,'#eaf5ef','Browse Medicines|Search Medicines|Filter Medicines|View Medicine Details|View Medicines'),
('Orders',3,520,'#fff5e6','Place Order|Checkout|Review Cart|Select Delivery Address|View Order Details|Track Order|Cancel Order|View Order History|Apply Referral Reward'),
('Payments',4,520,'#fff5e6','Make Payment|Process Payment|Verify Payment|Return Payment Status'),
('Prescriptions',5,520,'#f4eef9','Upload Prescription|Submit Prescription Request|View Prescription Status|View Prescription Requests|View Prescription Request|Review Prescription|Approve Prescription|Reject Prescription'),
('Staff operations & stock',6,520,'#edf3fc','View Staff Dashboard|View Orders|Process Order|Check Stock Availability|Update Stock|Update Order Status|Manage Medicine Stock|Record Stock Movement|Add Stock|Reduce Stock|View Stock History|View Low Stock Medicines|View Customer Order Information'),
('Personal account',0,2850,'#edf3fc','Manage Profile|Manage Family Members|Manage Delivery Addresses|Manage Notification Preferences|View Notifications'),
('Subscriptions & rewards',1,2850,'#eaf5ef','Subscribe to Medicine|Manage Medicine Subscription|Use Referral|View Referral Rewards|Submit Review & Feedback'),
('Notifications',2,2850,'#f4eef9','Send Order Notification|Send Payment Notification|Send Prescription Status Notification|Send Subscription Reminder'),
('Medicine administration',3,2850,'#f6f0e6','Manage Medicines|Add Medicine|Update Medicine|Delete Medicine|Manage Disease Categories|Manage Delivery Areas'),
('Staff administration',4,2850,'#f6f0e6','Manage Staff|Add Staff|Update Staff|Remove Staff|View Staff Details'),
('Owner reports',5,2850,'#f6f0e6','View Owner Dashboard|View Sales Summary|View Order Statistics|View Inventory Summary|View Payments'),
('Owner records',6,2850,'#f6f0e6','View Customers|View Stock Movements|View Reviews & Feedback')]
nodes={};headers=[]
for title,col,y,fill,items in modules:
 x=700+col*860;headers.append((x+270,y-105,title))
 for i,name in enumerate(items.split('|')):
  assert name not in nodes,name
  nodes[name]={'x':x,'y':y+i*145,'w':540,'h':104,'kind':'usecase','label':name,'fill':fill}
actorpos={'Customer':(180,2000),'Staff':(7240,1250),'Owner / Admin':(7240,3420),'Payment Gateway':(7240,2310),'OTP / SMS Service':(7240,450)}
for name,(x,y) in actorpos.items():nodes[name]={'x':x-65,'y':y-80,'w':130,'h':150,'kind':'actor','label':name}
expected=set(sum(roles.values(),[]))|{n for pair in includes+extends for n in pair}
assert set(nodes)==expected|set(roles)
# Reuse the proven node-avoiding orthogonal router; UML rendering is separate.
router=(O.parent/'yuvrajmedical-dfd'/'compact.py').read_text();router=router[router.index('G=20;'):router.index('# Local store links first')]
router=router.replace('G=20;','G=25;')
router=router.replace("   out.append((pt,ep,portsused.get((k,ep),0)*35))", """   if n['kind']=='usecase':
    cx,cy=x+w/2,y+h/2;dx,dy=ep[0]-cx,ep[1]-cy;scale=1/math.sqrt((dx/(w/2))**2+(dy/(h/2))**2);ep=(cx+scale*dx,cy+scale*dy)
   else:ep=(x+w/2,y+h/2)
   out.append((pt,ep,portsused.get((k,ep),0)*35))""")
exec(router)
# Keep routes away from module headings and the boundary title.
for xx in range(2050//G,5300//G+1):
 for yy in range(235//G,345//G+1):reserved.add((xx,yy))
for cx,cy,title in headers:
 for xx in range(int((cx-330)//G),int((cx+330)//G)+1):
  for yy in range(int((cy-24)//G),int((cy+24)//G)+1):reserved.add((xx,yy))
edges=[{'a':a,'b':b,'kind':'include'} for a,b in includes]+[{'a':a,'b':b,'kind':'extend'} for a,b in extends]
edges.sort(key=lambda e:abs(nodes[e['a']]['x']-nodes[e['b']]['x'])+abs(nodes[e['a']]['y']-nodes[e['b']]['y']))
for e in edges:
 e['pts']=route(e['a'],e['b']);e['label']='<<'+e['kind']+'>>';e['labelpos']=place_label(e['pts'],e['label'])
for actor,cases in roles.items():
 for uc in sorted(cases,key=lambda s:abs(nodes[actor]['x']-nodes[s]['x'])+abs(nodes[actor]['y']-nodes[s]['y'])):
  edges.append({'a':actor,'b':uc,'kind':'association','pts':route(actor,uc)})
 print('Routed',actor,flush=True)
im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>']
def rect(box,fill='white',stroke='#263445',r=0):
 x,y,xx,yy=box;svg.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>');d.rounded_rectangle(box,r,fill,stroke,2)
def text(x,y,t,size=24,b=False):
 lines=t.split('\n');f=ImageFont.truetype(bold if b else font,size)
 for i,s in enumerate(lines):
  yy=y+(i-(len(lines)-1)/2)*(size+6);svg.append(f'<text x="{x}" y="{yy}" text-anchor="middle" dominant-baseline="central" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" font-weight="{700 if b else 400}" fill="#172b3b">{html.escape(s)}</text>');d.text((x,yy),s,font=f,fill='#172b3b',anchor='mm')
def line(pts,color='#39434d',width=2,dash=False):
 svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"'+(' stroke-dasharray="10 7"' if dash else '')+'/>')
 if not dash:d.line(pts,fill=color,width=width)
 else:
  for a,b in zip(pts,pts[1:]):
   dx,dy=b[0]-a[0],b[1]-a[1];le=math.hypot(dx,dy)
   if not le:continue
   for st in range(0,math.ceil(le),17):
    en=min(st+10,le);d.line([(a[0]+dx*st/le,a[1]+dy*st/le),(a[0]+dx*en/le,a[1]+dy*en/le)],fill=color,width=width)
def arrow(a,b):
 dx,dy=a[0]-b[0],a[1]-b[1];le=math.hypot(dx,dy);ux,uy=dx/le,dy/le
 line([(a[0]-ux*17-uy*8,a[1]-uy*17+ux*8),a,(a[0]-ux*17+uy*8,a[1]-uy*17-ux*8)],width=3)
rect((500,210,6840,4030),stroke='#172b3b')
text(3670,290,'YuvrajMedical Online Medical Store System',42,True)
for e in sorted(edges,key=lambda e:e['kind']!='association'):
 svg.append(f'<g class="edge" data-a="{html.escape(e["a"],quote=True)}" data-b="{html.escape(e["b"],quote=True)}" data-kind="{e["kind"]}"><title>{html.escape(e["a"]+" — "+e["kind"]+" — "+e["b"])}</title>')
 line(e['pts'],'white',7);line(e['pts'],width=2,dash=e['kind']!='association')
 if e['kind']!='association':arrow(e['pts'][-1],e['pts'][-2])
 svg.append('</g>')
for e in edges:
 if e['kind']=='association':continue
 x,y,ls,box,_,_=e['labelpos'];svg.append(f'<g class="edge" data-a="{html.escape(e["a"],quote=True)}" data-b="{html.escape(e["b"],quote=True)}" data-kind="{e["kind"]}">');rect(box,'white','white');text(x,y,e['label'],20);svg.append('</g>')
rect((2050,240,5300,340),'white','white')
text(3670,290,'YuvrajMedical Online Medical Store System',42,True)
for cx,cy,title in headers:text(cx,cy,title,29,True)
for key,n in nodes.items():
 x,y,w,h=[n[z] for z in ['x','y','w','h']];cx,cy=x+w/2,y+h/2;svg.append(f'<g class="node" data-id="{html.escape(key,quote=True)}" data-kind="{n["kind"]}"><title>{html.escape(key)}</title>')
 if n['kind']=='usecase':
  svg.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="{n["fill"]}" stroke="#263445" stroke-width="2"/>');d.ellipse((x,y,x+w,y+h),fill=n['fill'],outline='#263445',width=2);text(cx,cy,'\n'.join(textwrap.wrap(key,32)),25)
 else:
  # Standard UML stick figure; all actor geometry remains outside the boundary.
  svg.append(f'<circle cx="{cx}" cy="{cy-67}" r="24" fill="white" stroke="#263445" stroke-width="3"/>');d.ellipse((cx-24,cy-91,cx+24,cy-43),fill='white',outline='#263445',width=3)
  line([(cx,cy-43),(cx,cy+35)],width=3);line([(cx-48,cy-8),(cx+48,cy-8)],width=3);line([(cx-44,cy+91),(cx,cy+35),(cx+44,cy+91)],width=3)
  rect((cx-170,cy+110,cx+170,cy+175),'white','white')
  text(cx,cy+133,'\n'.join(textwrap.wrap(key,18)),28,True)
 svg.append('</g>')
# UML note beneath the boundary avoids repetitive login dependencies.
rect((600,4140,6740,4470),'#fffdf3','#b8b5a5',8)
text(3670,4190,'Authentication preconditions',29,True)
text(3670,4255,'Authenticated Customer required for cart, wishlist, checkout, orders, subscriptions, prescriptions, addresses, notifications, reviews and referrals.',24)
text(3670,4310,'Authenticated Staff required for staff operations.',24)
text(3670,4365,'Authenticated Owner/Admin required for administrative operations.',24)
text(3670,4430,'Solid line: actor association     •     Dashed open arrow: <<include>> or <<extend>> dependency',23)
svg.append('</svg>');sv='\n'.join(svg)
(O/'yuvrajmedical-use-case.svg').write_text(sv);im.save(O/'yuvrajmedical-use-case.png',dpi=(240,240));im.resize((1900,1150)).save(O/'preview.png')
model={'actors':roles,'include':includes,'extend':extends,'use_cases':sorted(expected)}
(O/'model.json').write_text(json.dumps(model,indent=2))
assert len(roles)==5 and len(nodes)==len(expected)+5
for a,b in includes+extends:assert a in expected and b in expected
for n in nodes.values():
 x,y,w,h=[n[z] for z in ['x','y','w','h']]
 if n['kind']=='usecase':assert x>500 and x+w<6840 and y>210 and y+h<4030
 else:assert x+w<500 or x>6840
assert roles['Payment Gateway']==['Process Payment','Verify Payment','Return Payment Status']
assert all('OTP' in n or 'Notification' in n or 'Reminder' in n for n in roles['OTP / SMS Service'])
report={'actors':5,'unique_use_cases':len(expected),'actor_associations':sum(map(len,roles.values())),'include_dependencies':len(includes),'extend_dependencies':len(extends),'duplicate_nodes':0,'status':'passed'}
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
# The full diagram remains intact; actor focus reveals who can do what.
page='''<!doctype html><html><head><meta charset="utf-8"><title>YuvrajMedical UML Use Cases</title><style>body{margin:0;background:#f3f5f8;font:16px Arial;color:#172b3b}header{position:sticky;top:0;background:white;padding:14px 20px;display:flex;align-items:center;gap:16px;border-bottom:1px solid #cbd3da;z-index:3}button,select{padding:9px;border:1px solid #becbd5;border-radius:6px;background:white}main{padding:18px}svg{width:100%;height:auto;background:white}.node{cursor:pointer}.edge,.node{transition:opacity .15s}.dim{opacity:.055}.focus{filter:drop-shadow(0 0 4px #477ca1)}aside{display:none;position:fixed;right:15px;top:85px;bottom:18px;width:300px;overflow:auto;background:white;padding:18px;border:1px solid #c7d0d9;border-radius:8px;z-index:2}li{margin:0 0 10px;font-size:14px}h2{font-size:18px}#hint{flex:1}</style></head><body><header><b>YuvrajMedical · UML Use Cases</b><select id="actor"><option value="">All actors</option>'''+''.join('<option>'+html.escape(a)+'</option>' for a in roles)+'''</select><span id="hint">Select an actor or click an oval to highlight its associations.</span><button onclick="clearFocus()">Show all</button><button onclick="zoom(1.25)">Zoom +</button><button onclick="zoom(.8)">Zoom −</button></header><main>'''+sv+'''</main><aside id="panel"></aside><script>
const model=MODEL,svg=document.querySelector('svg'),panel=document.querySelector('#panel');
function zoom(s){svg.style.width=(svg.getBoundingClientRect().width*s)+'px'}
function clearFocus(){document.querySelector('#actor').value='';svg.querySelectorAll('.dim,.focus').forEach(e=>e.classList.remove('dim','focus'));panel.style.display='none'}
function focus(id){clearFocus();let keep=new Set([id]),isActor=!!model.actors[id];
 if(isActor)model.actors[id].forEach(x=>keep.add(x));else{Object.entries(model.actors).forEach(([a,c])=>{if(c.includes(id))keep.add(a)});[...model.include,...model.extend].forEach(([a,b])=>{if(a===id||b===id){keep.add(a);keep.add(b)}})}
 svg.querySelectorAll('.node').forEach(e=>{e.classList.toggle('dim',!keep.has(e.dataset.id));if(e.dataset.id===id)e.classList.add('focus')});
 svg.querySelectorAll('.edge').forEach(e=>{let show=e.dataset.kind==='association'?(isActor?e.dataset.a===id:e.dataset.b===id):(isActor?keep.has(e.dataset.a)&&keep.has(e.dataset.b):e.dataset.a===id||e.dataset.b===id);e.classList.toggle('dim',!show)});
 panel.replaceChildren();let h=document.createElement('h2');h.textContent=id;panel.append(h);let ul=document.createElement('ul');let items=isActor?model.actors[id]:Object.entries(model.actors).filter(([a,c])=>c.includes(id)).map(([a])=>'Actor: '+a).concat(model.include.filter(([a,b])=>a===id||b===id).map(([a,b])=>a+' <<include>> '+b),model.extend.filter(([a,b])=>a===id||b===id).map(([a,b])=>a+' <<extend>> '+b));items.forEach(t=>{let li=document.createElement('li');li.textContent=t;ul.append(li)});panel.append(ul);panel.style.display='block';if(isActor)document.querySelector('#actor').value=id;
}
document.querySelector('#actor').onchange=e=>e.target.value?focus(e.target.value):clearFocus();svg.querySelectorAll('.node').forEach(e=>e.onclick=()=>focus(e.dataset.id));
</script></body></html>'''.replace('MODEL',json.dumps(model))
(O/'yuvrajmedical-use-case-interactive.html').write_text(page)
