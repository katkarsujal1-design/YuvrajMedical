from pathlib import Path
import json,heapq,math,html
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).parent
spec=json.loads((O/'validation.json').read_text())['level_1']
W,H=3800,2660
font='/usr/share/fonts/liberation/LiberationSans-Regular.ttf';bold=font.replace('Regular','Bold')
nodes={}
def node(k,label,x,y,w,h,kind):nodes[k]=dict(label=label,x=x,y=y,w=w,h=h,kind=kind)
process_pos={'1.0':(500,260),'1.1':(1350,260),'7.0':(2200,260),'9.0':(3050,260),'2.0':(500,920),'3.0':(1350,920),'5.0':(2200,920),'4.0':(3050,920),'10.0':(500,1580),'8.0':(1350,1580),'6.0':(3050,1580),'11.0':(2200,1580),'12.0':(1350,2220)}
import textwrap
for p,name in spec['processes'].items():
 x,y=process_pos[p];node(p,p+'\n'+ '\n'.join(textwrap.wrap(name,26)),x,y,340,100,'process')
local={'1.0':['auth_otps','otp_verifications','login_activity'],'1.1':['family_members','user_devices','notification_preferences'],'7.0':['delivery_addresses','delivery_areas'],'9.0':['notifications'],'2.0':['disease_categories'],'3.0':['cart','cart_saved_later','wishlist'],'5.0':['orders','order_items'],'4.0':['prescription_requests','staff'],'10.0':['reviews_feedback'],'8.0':['medicine_subscriptions'],'6.0':['payments'],'11.0':['stock_movements'],'12.0':['referral_rewards']}
for p,stores in local.items():
 x,y=process_pos[p]
 for i,s in enumerate(stores):node(s,s,x+20,y+180+i*100,300,60,'store')
node('users','users',1790,740,260,60,'store');node('medicines','medicines',1790,1400,260,60,'store')
node('Customer','Customer',60,1160,260,120,'entity');node('Staff','Staff',3460,80,260,100,'entity');node('Payment Gateway','Payment Gateway',3460,2050,300,100,'entity')
# Consolidate opposite directed flows onto a labeled two-way connector.
pairs={}
for f in spec['directed_flows']:
 a,b=f['from'],f['to'];key=tuple(sorted([a,b]));pairs.setdefault(key,[]).append(f)
short={'1.0':'Registration, login & OTP / authentication results','1.1':'Family, device & preference changes / profile details','2.0':'Search filters / medicine results','3.0':'Cart & wishlist changes / cart, saved & wishlist items','4.0':'Prescriptions / review status','5.0':'Order requests / order status','6.0':'Payment details / payment result','7.0':'Address requests / delivery details','8.0':'Subscription changes / status','9.0':'Notification requests / alerts','10.0':'Reviews / confirmation','12.0':'Referral requests / rewards'}
stafflabels={'1.0':'Staff login / login result','4.0':'Prescription decisions / requests','5.0':'Order updates / order details','11.0':'Stock changes / stock results'}
proc_labels={frozenset(['5.0','6.0']):'Payment details / status',frozenset(['5.0','7.0']):'Delivery request / availability',frozenset(['5.0','11.0']):'Sold quantity / stock result'}
edges=[]
for key,fs in pairs.items():
 a,b=fs[0]['from'],fs[0]['to'];both=len(fs)==2
 if 'Customer' in key:label=short[next(k for k in key if k!='Customer')]
 elif 'Staff' in key:label=stafflabels[next(k for k in key if k!='Staff')]
 elif 'Payment Gateway' in key:label='Payment request / transaction result'
 elif any(nodes[k]['kind']=='store' for k in key):
  label=fs[0]['label'].replace('Information','Data')
  if both:label+=' (read / write)'
 else:label=proc_labels.get(frozenset(key),fs[0]['label'])
 edges.append(dict(a=a,b=b,both=both,label=label,full=fs))
# Grid routing keeps arrows out of nodes and previously placed labels.
G=20;NX=W//G;NY=H//G
blocked=set(); used={}; reserved=set();labelboxes=[]
for n in nodes.values():
 for x in range((n['x']-20)//G,(n['x']+n['w']+20)//G+1):
  for y in range((n['y']-20)//G,(n['y']+n['h']+20)//G+1):blocked.add((x,y))
for x in range(NX):
 for y in range(0,9):blocked.add((x,y))
portsused={}
def ports(k):
 n=nodes[k];x,y,w,h=[n[z] for z in ['x','y','w','h']];out=[]
 for side in ['L','R','T','B']:
  for frac in [.5,.25,.75]:
   if side in ['L','R']:
    yy=round((y+h*frac)/G)*G;xx=x if side=='L' else x+w;ex=math.floor((x-40)/G)*G if side=='L' else math.ceil((x+w+40)/G)*G;ep=(xx,yy);pt=(ex//G,yy//G)
   else:
    xx=round((x+w*frac)/G)*G;yy=y if side=='T' else y+h;ey=math.floor((y-40)/G)*G if side=='T' else math.ceil((y+h+40)/G)*G;ep=(xx,yy);pt=(xx//G,ey//G)
   out.append((pt,ep,portsused.get((k,ep),0)*35))
 return out

def route(a,b):
 starts=ports(a);ends=ports(b);goals={p:(ep,cost) for p,ep,cost in ends};front=[];best={};prev={};origin={}
 def heur(p):return min(abs(p[0]-q[0])+abs(p[1]-q[1])+v[1] for q,v in goals.items())
 for p,ep,cost in starts:
  st=(p[0],p[1],4);best[st]=cost;heapq.heappush(front,(cost+heur(p),cost,st));origin[st]=ep
 final=None
 while front:
  _,cost,st=heapq.heappop(front)
  if cost!=best.get(st):continue
  x,y,di=st
  if (x,y) in goals:final=st;break
  for nd,(dx,dy) in enumerate([(1,0),(0,1),(-1,0),(0,-1)]):
   p=(x+dx,y+dy)
   if not(2<=p[0]<NX-2 and 9<=p[1]<NY-5):continue
   if p in blocked or p in reserved:continue
   nc=cost+1+(2.4 if di!=4 and di!=nd else 0)+used.get(p,0)*5
   ns=(*p,nd)
   if nc<best.get(ns,1e20):best[ns]=nc;prev[ns]=st;origin[ns]=origin[st];heapq.heappush(front,(nc+heur(p),nc,ns))
 if final is None:raise RuntimeError('No path '+a+' '+b)
 path=[];st=final
 while st in prev:path.append((st[0]*G,st[1]*G));st=prev[st]
 path.append((st[0]*G,st[1]*G));path.reverse();start=origin[final];end=goals[(final[0],final[1])][0]
 portsused[(a,start)]=portsused.get((a,start),0)+1;portsused[(b,end)]=portsused.get((b,end),0)+1
 for x,y in path:used[(x//G,y//G)]=used.get((x//G,y//G),0)+1
 pts=[start]+path+[end];simple=[pts[0]]
 for i in range(1,len(pts)-1):
  if (pts[i-1][0]==pts[i][0]==pts[i+1][0]) or (pts[i-1][1]==pts[i][1]==pts[i+1][1]):continue
  simple.append(pts[i])
 simple.append(pts[-1]);return simple

def overlap(a,b,pad=8):return not(a[2]+pad<b[0] or b[2]+pad<a[0] or a[3]+pad<b[1] or b[3]+pad<a[1])
nodeboxes=[(n['x'],n['y'],n['x']+n['w'],n['y']+n['h']) for n in nodes.values()]
fontobj=ImageFont.truetype(font,18)
def place_label(pts,label):
 lines=textwrap.wrap(label,27);ww=max(fontobj.getlength(s) for s in lines)+18;hh=len(lines)*22+10
 candidates=[]
 for a,b in zip(pts,pts[1:]):
  length=abs(a[0]-b[0])+abs(a[1]-b[1])
  for t in [.5,.25,.75]:
   x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
   offsets=[(0,0)] if a[1]==b[1] else [(ww/2+12,0),(-ww/2-12,0)]
   for ox,oy in offsets:
    cx,cy=x+ox,y+oy;box=(cx-ww/2,cy-hh/2,cx+ww/2,cy+hh/2)
    if box[0]<20 or box[2]>W-20 or box[1]<190 or box[3]>H-100:continue
    collisions=sum(overlap(box,z) for z in nodeboxes+labelboxes)
    candidates.append((collisions*100000-length,cx,cy,box,x,y))
 if not candidates:raise RuntimeError('no label')
 _,cx,cy,box,x,y=min(candidates)
 if any(overlap(box,z) for z in nodeboxes+labelboxes):print('LABEL COLLISION',label,flush=True)
 labelboxes.append(box)
 for xx in range(math.floor(box[0]/G),math.ceil(box[2]/G)+1):
  for yy in range(math.floor(box[1]/G),math.ceil(box[3]/G)+1):reserved.add((xx,yy))
 return (cx,cy,lines,box,x,y)
# Local store links first, then shared-store links, then external flows.
def priority(e):
 a,b=nodes[e['a']],nodes[e['b']];dist=abs(a['x']-b['x'])+abs(a['y']-b['y'])
 return (0 if any(n['kind']=='store' for n in [a,b]) else 1,dist)
edges.sort(key=priority)
for i,e in enumerate(edges):
 e['pts']=route(e['a'],e['b']);e['labelpos']=place_label(e['pts'],e['label']);print('Routed',i+1,'/',len(edges),flush=True) if i%15==0 else None
im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>']
def line(pts,color='#344252',width=2):
 svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>');d.line(pts,fill=color,width=width)
def rect(box,fill,stroke=None,r=0):
 x,y,xx,yy=box;svg.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" rx="{r}" fill="{fill}" stroke="{stroke or fill}" stroke-width="2"/>');d.rounded_rectangle(box,r,fill,stroke,2)
def text(x,y,lines,size=20,b=False):
 if isinstance(lines,str):lines=lines.split('\n')
 f=ImageFont.truetype(bold if b else font,size)
 for i,t in enumerate(lines):
  yy=y+(i-(len(lines)-1)/2)*(size+4);svg.append(f'<text x="{x}" y="{yy}" text-anchor="middle" dominant-baseline="central" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" font-weight="{700 if b else 400}" fill="#152b3d">{html.escape(t)}</text>');d.text((x,yy),t,font=f,fill='#152b3d',anchor='mm')
def head(a,b):
 dx,dy=a[0]-b[0],a[1]-b[1];le=math.hypot(dx,dy);ux,uy=dx/le,dy/le
 pts=[a,(a[0]-12*ux-5*uy,a[1]-12*uy+5*ux),(a[0]-12*ux+5*uy,a[1]-12*uy-5*ux)]
 svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in pts)+'" fill="#344252"/>');d.polygon(pts,fill='#344252')
text(W/2,65,'YuvrajMedical — Level 1 Data Flow Diagram',38,True)
text(W/2,118,'Detailed YuvrajMedical System',22)
for i,e in enumerate(edges):
 svg.append(f'<g class="flow" data-a="{e["a"]}" data-b="{e["b"]}"><title>'+html.escape(' | '.join(f['from']+' → '+f['to']+': '+f['label'] for f in e['full']))+'</title>')
 line(e['pts'],'white',7);line(e['pts']);head(e['pts'][-1],e['pts'][-2])
 if e['both']:head(e['pts'][0],e['pts'][1])
 svg.append('</g>')
for e in edges:
 svg.append(f'<g class="flow" data-a="{e["a"]}" data-b="{e["b"]}">');x,y,lines,box,ax,ay=e['labelpos'];rect(box,'white',r=4);text(x,y,lines,18);svg.append('</g>')
for k,n in nodes.items():
 x,y,w,h=[n[v] for v in ['x','y','w','h']];svg.append(f'<g class="node" data-id="{k}"><title>{html.escape(n["label"].replace(chr(10)," "))}</title>')
 if n['kind']=='store':
  rect((x,y,x+w,y+h),'#fff6df');line([(x+w,y),(x,y),(x,y+h),(x+w,y+h)]);text(x+w/2,y+h/2,n['label'],20)
 else:rect((x,y,x+w,y+h),'#e8f3ed' if n['kind']=='process' else '#e7effb','#344252',18 if n['kind']=='process' else 0);text(x+w/2,y+h/2,n['label'],23,True)
 svg.append('</g>')
text(W/2,H-75,'Blue rectangle: external entity     •     Green rounded rectangle: process     •     Open-ended amber box: data store',20)
text(W/2,H-40,'Arrowheads show direction. Two-way arrows carry requests/results or reads/writes. Crossing lines do not join.',18)
svg.append('</svg>');sv='\n'.join(svg)
(O/'dfd-level-1-compact.svg').write_text(sv);im.save(O/'dfd-level-1-compact.png',dpi=(240,240));im.resize((1600,1120)).save(O/'compact-preview.png')
page='''<!doctype html><html><head><meta charset="utf-8"><title>YuvrajMedical — Level 1 DFD</title><style>body{margin:0;font:16px Arial;color:#172c3f;background:#f5f7fa}header{position:sticky;top:0;background:white;border-bottom:1px solid #ccd5dd;padding:14px 24px;z-index:3;display:flex;gap:20px;align-items:center}button{padding:8px 14px;border:1px solid #b8c6d3;border-radius:6px;background:white;cursor:pointer}#diagram{padding:20px}svg{width:100%;height:auto;background:white}.node{cursor:pointer}.flow,.node{transition:opacity .15s}.dim{opacity:.08}.active{filter:drop-shadow(0 0 4px #4891c1)}#status{flex:1}</style></head><body><header><strong>YuvrajMedical · Level 1 DFD</strong><span id="status">Click a process or data store to focus on its flows. Hover an arrow for full details.</span><button onclick="reset()">Show all</button><button onclick="zoom(1.25)">Zoom +</button><button onclick="zoom(.8)">Zoom −</button></header><div id="diagram">'''+sv+'''</div><script>const root=document.querySelector('svg');function reset(){root.querySelectorAll('.dim,.active').forEach(n=>n.classList.remove('dim','active'));document.querySelector('#status').textContent='Click a process or data store to focus on its flows. Hover an arrow for full details.'}function zoom(s){root.style.width=(root.getBoundingClientRect().width*s)+'px'}root.querySelectorAll('.node').forEach(n=>n.onclick=()=>{reset();let id=n.dataset.id,keep=new Set([id]);root.querySelectorAll('.flow').forEach(e=>{let hit=e.dataset.a===id||e.dataset.b===id;e.classList.toggle('dim',!hit);if(hit){keep.add(e.dataset.a);keep.add(e.dataset.b)}});root.querySelectorAll('.node').forEach(e=>e.classList.toggle('dim',!keep.has(e.dataset.id)));n.classList.add('active');document.querySelector('#status').textContent=n.querySelector('title').textContent+' — connected flows';});</script></body></html>'''
(O/'dfd-level-1-interactive.html').write_text(page)
assert len(nodes)==40 and len([n for n in nodes.values() if n['kind']=='store'])==24
assert sum(len(e['full']) for e in edges)==112
(O/'compact-validation.json').write_text(json.dumps({'processes':13,'stores':24,'external_entities':3,'directional_flows_preserved':112,'connectors':len(edges),'image_size':[W,H]},indent=2))
print('DONE',len(edges),'connectors; all 112 directed flows preserved.')
