from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math,html,json,textwrap,heapq,re,xml.etree.ElementTree as ET
O=Path(__file__).parent;W,H=4400,2900
font='/usr/share/fonts/liberation/LiberationSans-Regular.ttf';bold=font.replace('Regular','Bold')
layout=[
(950,[(420,'Register'),(650,'Login'),(880,'Manage Profile & Family'),(1110,'Browse & Search Medicines'),(1340,'Manage Cart & Wishlist'),(1570,'Manage Medicine Subscription'),(1800,'Submit Review & Feedback'),(2030,'Use Referral & View Rewards')]),
(1820,[(420,'Manage Delivery Addresses'),(650,'Place Order'),(880,'Checkout'),(1110,'View Order Details'),(1340,'Track Order'),(1570,'Cancel Order'),(1800,'Upload Prescription'),(2030,'View Prescription Status'),(2260,'View Notifications')]),
(2690,[(420,'Verify OTP'),(650,'Send OTP'),(1110,'Make Payment'),(1340,'Process Payment'),(1570,'Verify Payment'),(1800,'Check Stock Availability')]),
(3560,[(420,'Review Prescription'),(650,'Approve Prescription'),(880,'Reject Prescription'),(1110,'Process Order'),(1340,'Manage Medicine Stock'),(1800,'Manage Medicines'),(2030,'Manage Staff'),(2260,'Manage Delivery Areas'),(2490,'View Sales Summary')])]
nodes={}
for cx,rows in layout:
 for cy,n in rows:nodes[n]={'x':cx-265,'y':cy-60,'w':530,'h':120,'kind':'usecase','label':n}
roles={
'Customer':['Register','Login','Manage Profile & Family','Browse & Search Medicines','Manage Cart & Wishlist','Manage Medicine Subscription','Submit Review & Feedback','Use Referral & View Rewards','Manage Delivery Addresses','Place Order','Checkout','View Order Details','Track Order','Cancel Order','Upload Prescription','View Prescription Status','View Notifications','Make Payment'],
'Staff':['Login','Review Prescription','Approve Prescription','Reject Prescription','Process Order','Manage Medicine Stock'],
'Owner / Admin':['Login','Manage Medicines','Manage Staff','Manage Delivery Areas','View Sales Summary'],
'Payment Gateway':['Process Payment','Verify Payment'],
'OTP / SMS Service':['Verify OTP','Send OTP']}
AP={'Customer':(180,1380),'Staff':(4240,790),'Owner / Admin':(4240,2300),'Payment Gateway':(4240,1510),'OTP / SMS Service':(4240,350)}
for a,(x,y) in AP.items():nodes[a]={'x':x-60,'y':y-65,'w':120,'h':130,'kind':'actor','label':a}
includes=[('Register','Verify OTP'),('Verify OTP','Send OTP'),('Place Order','Checkout'),('Place Order','Check Stock Availability'),('Make Payment','Process Payment'),('Process Payment','Verify Payment'),('Process Order','Check Stock Availability')]
extends=[('Track Order','View Order Details'),('Cancel Order','View Order Details'),('Approve Prescription','Review Prescription'),('Reject Prescription','Review Prescription')]
router=(O.parent/'yuvrajmedical-dfd'/'compact.py').read_text();router=router[router.index('G=20;'):router.index('# Local store links first')]
router=router.replace("   out.append((pt,ep,portsused.get((k,ep),0)*35))","""   if n['kind']=='usecase':
    cx,cy=x+w/2,y+h/2;dx,dy=ep[0]-cx,ep[1]-cy;scale=1/math.sqrt((dx/(w/2))**2+(dy/(h/2))**2);ep=(cx+scale*dx,cy+scale*dy)
   else:ep=(x+w/2,y+h/2)
   out.append((pt,ep,portsused.get((k,ep),0)*35))""")
exec(router)
for xx in range(W//G):
 for yy in range(0,280//G):blocked.add((xx,yy))
 for yy in range(2620//G,H//G):blocked.add((xx,yy))
edges=[]
for kind,pairs in [('include',includes),('extend',extends)]:
 for a,b in pairs:
  e={'a':a,'b':b,'kind':kind,'pts':route(a,b),'label':'<<'+kind+'>>'};e['labelpos']=place_label(e['pts'],e['label']);edges.append(e)
for a,ucs in roles.items():
 for uc in ucs:edges.append({'a':a,'b':uc,'kind':'association','pts':route(a,uc)})
im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>']
def rect(box,fill='white',stroke='#334353'):
 x,y,xx,yy=box;svg.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>');d.rectangle(box,fill,stroke,2)
def text(x,y,t,size=26,b=False):
 f=ImageFont.truetype(bold if b else font,size);ls=t.split('\n')
 for i,s in enumerate(ls):
  yy=y+(i-(len(ls)-1)/2)*(size+6);svg.append(f'<text x="{x}" y="{yy}" text-anchor="middle" dominant-baseline="central" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" font-weight="{700 if b else 400}" fill="#172b3b">{html.escape(s)}</text>');d.text((x,yy),s,font=f,fill='#172b3b',anchor='mm')
def line(pts,color='#334353',width=2,dash=False):
 svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"'+(' stroke-dasharray="10 7"' if dash else '')+'/>')
 for a,b in zip(pts,pts[1:]):
  if not dash:d.line([a,b],fill=color,width=width);continue
  le=math.dist(a,b)
  if not le:continue
  for k in range(0,math.ceil(le),17):
   z=min(k+10,le);d.line([(a[0]+(b[0]-a[0])*k/le,a[1]+(b[1]-a[1])*k/le),(a[0]+(b[0]-a[0])*z/le,a[1]+(b[1]-a[1])*z/le)],fill=color,width=width)
def arrow(a,b):
 dx,dy=a[0]-b[0],a[1]-b[1];le=math.hypot(dx,dy);ux,uy=dx/le,dy/le;line([(a[0]-ux*18-uy*8,a[1]-uy*18+ux*8),a,(a[0]-ux*18+uy*8,a[1]-uy*18-ux*8)],width=3)
text(W/2,70,'UML Use Case Diagram — Intermediate Detail',38,True)
rect((450,180,3980,2590));text(2215,240,'YuvrajMedical Online Medical Store System',38,True)
for e in sorted(edges,key=lambda x:x['kind']!='association'):
 svg.append(f'<g class="edge" data-a="{html.escape(e["a"],quote=True)}" data-b="{html.escape(e["b"],quote=True)}" data-kind="{e["kind"]}">');line(e['pts'],'white',7);line(e['pts'],dash=e['kind']!='association')
 if e['kind']!='association':arrow(e['pts'][-1],e['pts'][-2])
 svg.append('</g>')
for e in edges:
 if e['kind']=='association':continue
 x,y,_,box,_,_=e['labelpos'];rect(box,'white','white');text(x,y,e['label'],21)
for n,v in nodes.items():
 x,y,w,h=[v[k] for k in ['x','y','w','h']];cx,cy=x+w/2,y+h/2;svg.append(f'<g class="node" data-id="{html.escape(n,quote=True)}" data-kind="{v["kind"]}">')
 if v['kind']=='usecase':
  fill='#eff5fa' if cx<2200 else '#f0f6ef' if cy<1700 else '#faf4ea';svg.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="#334353" stroke-width="2"/>');d.ellipse((x,y,x+w,y+h),fill=fill,outline='#334353',width=2);text(cx,cy,'\n'.join(textwrap.wrap(n,29)),29)
  assert x>450 and x+w<3980 and y>180 and y+h<2590
 else:
  svg.append(f'<circle cx="{cx}" cy="{cy-65}" r="26" fill="white" stroke="#334353" stroke-width="3"/>');d.ellipse((cx-26,cy-91,cx+26,cy-39),fill='white',outline='#334353',width=3);line([(cx,cy-39),(cx,cy+43)],width=3);line([(cx-50,cy),(cx+50,cy)],width=3);line([(cx-45,cy+108),(cx,cy+43),(cx+45,cy+108)],width=3);rect((cx-150,cy+120,cx+150,cy+190),'white','white');text(cx,cy+153,'\n'.join(textwrap.wrap(n,16)),28,True)
  assert x+w<450 or x>3980
 svg.append('</g>')
text(W/2,2670,'Main functions are retained; routine add, edit, remove and view actions are grouped.',25)
text(W/2,2720,'Protected customer functions require authentication. Staff and Owner/Admin operations require their respective authenticated roles.',23)
text(W/2,2780,'Solid line: actor association     •     Dashed open arrow: <<include>> / <<extend>>',24)
svg.append('</svg>');sv='\n'.join(svg);(O/'yuvrajmedical-use-case-intermediate.svg').write_text(sv);im.save(O/'yuvrajmedical-use-case-intermediate.png',dpi=(240,240));im.save(O/'yuvrajmedical-use-case-intermediate.pdf',resolution=200.0,title='YuvrajMedical — Intermediate UML Use Case Diagram');im.resize((1760,1160)).save(O/'intermediate-preview.png')
assert len(nodes)==37 and len(roles)==5
assert all(e['a'] in roles and e['b'] not in roles for e in edges if e['kind']=='association')
report={'actors':5,'use_cases':32,'associations':sum(map(len,roles.values())),'include':includes,'extend':extends,'scope':'Intermediate view: routine CRUD operations and secondary supporting functions are grouped or omitted.'}
(O/'intermediate-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['include','extend']}))
