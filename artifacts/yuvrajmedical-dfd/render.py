from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math,html,json
O=Path(__file__).parent
FONT='/usr/share/fonts/liberation/LiberationSans-Regular.ttf'; BOLD=FONT.replace('Regular','Bold')
class Canvas:
 def __init__(self,w,h):
  self.w,self.h=w,h;self.im=Image.new('RGB',(w,h),'white');self.d=ImageDraw.Draw(self.im);self.s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="white"/>'];self.paths=[]
 def rect(self,x,y,w,h,fill,stroke='#263545',r=0):
  self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>');self.d.rounded_rectangle((x,y,x+w,y+h),r,fill,stroke,2)
 def line(self,pts,color='#263545',width=2):
  self.s.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>');self.d.line(pts,fill=color,width=width)
 def text(self,x,y,t,size=25,bold=False,color='#182738',bg=False):
  lines=t.split('\n');f=ImageFont.truetype(BOLD if bold else FONT,size)
  if bg:
   widths=[self.d.textbbox((0,0),l,font=f)[2] for l in lines];w=max(widths)+22;h=len(lines)*(size+8)+8;self.rect(x-w/2,y-h/2,w,h,'white','white',3)
  for i,l in enumerate(lines):
   yy=y+(i-(len(lines)-1)/2)*(size+8)
   self.s.append(f'<text x="{x}" y="{yy}" text-anchor="middle" dominant-baseline="central" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(l)}</text>');self.d.text((x,yy),l,font=f,fill=color,anchor='mm')
 def arrowhead(self,a,b):
  dx,dy=a[0]-b[0],a[1]-b[1];n=math.hypot(dx,dy);ux,uy=dx/n,dy/n
  p=[a,(a[0]-ux*15-uy*6,a[1]-uy*15+ux*6),(a[0]-ux*15+uy*6,a[1]-uy*15-ux*6)]
  self.s.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in p)+'" fill="#263545"/>');self.d.polygon(p,fill='#263545')
 def vertical_text(self,x,y,t,size=25):
  f=ImageFont.truetype(FONT,size);box=self.d.textbbox((0,0),t,font=f);w=box[2]+24;h=size+20
  tile=Image.new('RGB',(w,h),'white');ImageDraw.Draw(tile).text((w/2,h/2),t,font=f,fill='#182738',anchor='mm');tile=tile.rotate(90,expand=True)
  self.im.paste(tile,(round(x-tile.width/2),round(y-tile.height/2)))
  self.s.append(f'<g transform="translate({x},{y}) rotate(-90)"><rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" fill="white"/><text text-anchor="middle" dominant-baseline="central" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" fill="#182738">{html.escape(t)}</text></g>')
 def arrow(self,pts,label,pos,both=False,size=24):
  # Break the later vertical/horizontal connector at prior crossings.
  self.line(pts,'white',8);self.line(pts);self.arrowhead(pts[-1],pts[-2])
  if both:self.arrowhead(pts[0],pts[1])
  if label:self.text(*pos,label,size,bg=True)
 def node(self,name,x,y,w,h,kind):
  if kind=='store':
   self.rect(x,y,w,h,'#fff7e4','white');self.line([(x+w,y),(x,y),(x,y+h),(x+w,y+h)]);self.text(x+w/2,y+h/2,name,27)
  else:
   self.rect(x,y,w,h,'#eaf1fb' if kind=='entity' else '#e9f5ef',r=0 if kind=='entity' else 24);self.text(x+w/2,y+h/2,name,30,True)
 def save(self,name):
  (O/(name+'.svg')).write_text('\n'.join(self.s+['</svg>']));self.im.save(O/(name+'.png'),dpi=(240,240));self.im.resize((1600,round(self.h*1600/self.w))).save(O/(name+'-preview.png'))
# Context, exactly one process and no stores.
c=Canvas(2800,1700);c.text(1400,85,'YuvrajMedical — DFD Level 0',44,True);c.text(1400,142,'Context Diagram',27)
c.node('Customer',80,430,340,680,'entity');c.node('0.0 YuvrajMedical\nOnline Medical Store System',1060,480,650,600,'process');c.node('Staff',2220,160,430,360,'entity');c.node('Payment Gateway',2220,1120,430,330,'entity')
ctx=[('Customer','System','Registration Details · Login Credentials\nSearch Request · Cart Request · Prescription\nOrder Request · Payment Details\nDelivery Address · Review & Feedback'),('System','Customer','Authentication Result · Medicine Information\nCart Details · Prescription Status\nOrder Confirmation · Payment Status\nDelivery/Order Status · Notifications'),('Staff','System','Login Information · Prescription Decision\nOrder Updates · Stock Updates'),('System','Staff','Order Information\nPrescription Requests · Stock Information'),('System','Payment Gateway','Payment Request'),('Payment Gateway','System','Payment Result')]
c.arrow([(420,610),(1060,610)],ctx[0][2],(740,490),size=23);c.arrow([(1060,970),(420,970)],ctx[1][2],(740,1095),size=23)
c.arrow([(2220,260),(1870,260),(1870,590),(1710,590)],ctx[2][2],(1950,170),size=23);c.arrow([(1710,730),(2040,730),(2040,440),(2220,440)],ctx[3][2],(1970,825),size=23)
c.arrow([(1710,920),(1880,920),(1880,1200),(2220,1200)],ctx[4][2],(1990,1160));c.arrow([(2220,1370),(1790,1370),(1790,1020),(1710,1020)],ctx[5][2],(1990,1415))
c.save('dfd-level-0')
# Detailed process/data specification. Each store and each process has one node.
P=[('1.0','User Authentication'),('1.1','User Profile Management'),('2.0','Medicine Browsing & Search'),('3.0','Cart & Wishlist Management'),('4.0','Prescription Management'),('5.0','Order Management'),('6.0','Payment Processing'),('7.0','Delivery Management'),('8.0','Medicine Subscription Management'),('9.0','Notification Management'),('10.0','Review & Feedback Management'),('11.0','Inventory & Stock Management'),('12.0','Referral & Rewards Management')]
local=[['users','auth_otps','otp_verifications','login_activity'],['family_members','user_devices','notification_preferences'],['medicines','disease_categories'],['cart','cart_saved_later','wishlist'],['prescription_requests','staff'],['orders','order_items'],['payments'],['delivery_addresses','delivery_areas'],['medicine_subscriptions'],['notifications'],['reviews_feedback'],['stock_movements'],['referral_rewards']]
# Mode is relative to process: read, write, or read/write.
S={
'1.0':[('users','rw','Account Records'),('auth_otps','rw','Authentication OTP Records'),('otp_verifications','rw','OTP Verification Records'),('login_activity','w','Login Activity Record'),('user_devices','rw','Device Records'),('staff','r','Staff Login Records')],
'1.1':[('users','rw','Profile Details'),('family_members','rw','Family Member Details'),('user_devices','rw','Device Details'),('notification_preferences','rw','Notification Preferences')],
'2.0':[('medicines','r','Medicine Information'),('disease_categories','r','Disease Categories')],
'3.0':[('cart','rw','Cart Items'),('cart_saved_later','rw','Saved Items'),('wishlist','rw','Wishlist Items'),('medicines','r','Medicine Details'),('users','r','Customer Details')],
'4.0':[('prescription_requests','rw','Prescription Requests & Decisions'),('users','r','Customer Details'),('staff','r','Staff Details')],
'5.0':[('orders','rw','Order Records'),('order_items','rw','Order Item Records'),('cart','r','Selected Cart Items'),('medicines','r','Medicine Details'),('users','r','Customer Details'),('delivery_addresses','r','Delivery Address Details')],
'6.0':[('payments','rw','Payment & Transaction Records'),('orders','rw','Order Payment Details & Status')],
'7.0':[('delivery_addresses','rw','Delivery Address Records'),('delivery_areas','r','Serviceable Delivery Areas'),('users','r','Customer Details')],
'8.0':[('medicine_subscriptions','rw','Subscription Records'),('medicines','r','Medicine Details'),('users','r','Customer Details')],
'9.0':[('notifications','rw','Notification Records'),('notification_preferences','r','Notification Preferences'),('users','r','Customer Contact Details')],
'10.0':[('reviews_feedback','rw','Review & Feedback Records'),('medicines','r','Medicine Details'),('users','r','Customer Details')],
'11.0':[('medicines','rw','Medicine Inventory & Stock'),('stock_movements','rw','Stock Movement Records'),('staff','r','Staff Details')],
'12.0':[('referral_rewards','rw','Referral & Reward Records'),('users','r','Customer Details')]}
C={
'1.0':('Registration Details · Login Credentials\nOTP Request · OTP Verification Data','Registration Result · Login Result\nOTP Result · Authentication Status'),
'1.1':('Profile Details · Family Member Details\nDevice Details · Notification Preferences','Profile Details · Family Member Details\nDevice Details · Preference Update Result'),
'2.0':('Search Query · Category Selection · Medicine Filter','Medicine List · Medicine Details\nSearch Results · Category Results'),
'3.0':('Add to Cart · Update Quantity · Remove from Cart\nSave for Later · Move to Cart\nAdd to Wishlist · Remove from Wishlist','Cart Contents · Updated Cart\nSaved Items · Wishlist Contents'),
'4.0':('Prescription Upload · Prescription Request','Prescription Status · Approval Result · Rejection Result'),
'5.0':('Place Order Request · Selected Cart Items\nOrder Cancellation Request · Order Tracking Request','Order Confirmation · Order Details\nOrder Status · Cancellation Result'),
'6.0':('Payment Method · Payment Details','Payment Confirmation · Payment Failure Message'),
'7.0':('Add Address · Update Address\nDelete Address · Select Delivery Address','Saved Addresses · Delivery Availability\nDelivery Information'),
'8.0':('Subscribe Medicine · Change Subscription\nCancel Subscription','Subscription Status · Subscription Details\nReminder Information'),
'9.0':('Notification View Request','Order Notification · Payment Notification\nPrescription Notification · Subscription Reminder'),
'10.0':('Rating · Review · Feedback','Review Confirmation · Feedback Confirmation'),
'12.0':('Referral Information · Reward Request','Referral Status · Reward Balance · Reward Result')}
flows=[]
def add(a,b,label):assert label.strip();flows.append({'from':a,'to':b,'label':label})
# Dimensions reserve a separate routing field for shared stores.
W,H=11600,7600;c=Canvas(W,H);c.text(W/2,85,'YuvrajMedical — DFD Level 1',48,True);c.text(W/2,150,'Detailed YuvrajMedical System',30)
c.text(510,235,'EXTERNAL ENTITY',23,True);c.text(3010,235,'PROCESSES',23,True);c.text(9380,235,'DATA STORES',23,True)
ys={pid:360+i*540 for i,(pid,_) in enumerate(P)}
px,pw=2600,820; sx,sw=8950,1000
stores={}
for i,group in enumerate(local):
 for j,n in enumerate(group):stores[n]=(sx,ys[P[i][0]]+35+j*95,sw,64)
# Customer is a single extended external entity with one centered name.
c.node('Customer',160,350,520,6990,'entity')
# Nodes rendered after paths; process height supplies distinct ports.
# Store links: pair of labeled opposite flows use one two-headed connector,
# explicitly labeling READ (store → process) and WRITE (process → store).
store_links=[]
for pid,_ in P:
 for j,(st,mode,data) in enumerate(S[pid]):
  py=ys[pid]+38+j*62; dy=stores[st][1]+32
  label=('Read / Write: '+data) if mode=='rw' else ('Read: ' if mode=='r' else 'Write: ')+data
  if mode in ['r','rw']:add(st,pid,data)
  if mode in ['w','rw']:add(pid,st,data)
  store_links.append((pid,st,mode,label,py,dy))
# Render long paths first, distinct lanes, label beside the process.
for i,(pid,st,mode,label,py,dy) in enumerate(store_links):
 lane=5700+i*53
 pts=[(px+pw,py),(lane,py),(lane,dy),(sx,dy)]
 # Give shared-store connections distinct destination ports, keeping them inside store.
 same=[z for z in store_links if z[1]==st];k=same.index((pid,st,mode,label,py,dy));dy=stores[st][1]+8+(k+1)*48/(len(same)+1)
 pts=[(px+pw,py),(lane,py),(lane,dy),(sx,dy)]
 if mode=='r':pts=list(reversed(pts))
 c.arrow(pts,label,(4510,py-17),both=mode=='rw',size=23)
# Customer input and output are separate directed arrows.
for pid,(incoming,outgoing) in C.items():
 y=ys[pid]
 c.arrow([(680,y+130),(px,y+130)],incoming,(1550,y+60),size=25);add('Customer',pid,incoming.replace('\n',' '))
 c.arrow([(px,y+330),(680,y+330)],outgoing,(1550,y+400),size=25);add(pid,'Customer',outgoing.replace('\n',' '))
# Interprocess flows route along narrow lanes left of process boxes.
X=[('5.0','6.0','Payment Details'),('6.0','5.0','Payment Status'),('5.0','7.0','Delivery Request · Order Delivery Details'),('7.0','5.0','Validated Address · Delivery Availability'),('5.0','9.0','Order Status Event'),('6.0','9.0','Payment Event'),('4.0','9.0','Prescription Status Event'),('8.0','9.0','Subscription Reminder Event'),('5.0','11.0','Sold Medicine Quantity'),('11.0','5.0','Stock Availability · Stock Update Result')]
# Route process exchanges in lower row gutters and use rightmost lane bank.
portcount={p:0 for p,_ in P}
for i,(a,b,label) in enumerate(X):
 ay=ys[a]+440+portcount[a]*13;portcount[a]+=1
 by=ys[b]+440+portcount[b]*13;portcount[b]+=1
 lane=10100+i*65
 ax=px+40+portcount[a]*50;bx=px+40+portcount[b]*50
 pts=[(ax,ys[a]+420),(ax,ay),(lane,ay),(lane,by),(bx,by),(bx,ys[b]+420)]
 c.arrow(pts,'',(0,0));c.vertical_text(lane+17,(ay+by)/2,label,24);add(a,b,label)
# Staff is on the upper right. Its paths connect solely to processes.
staffx=10890;c.node('Staff',staffx,350,550,450,'entity')
SF=[('1.0','Login Information','Authentication Result'),('4.0','Prescription Review · Approval · Rejection','Pending Prescription Requests · Prescription Details'),('5.0','Order Status Update · Order Processing Information','New Order · Pending Order · Order Details'),('11.0','Add Stock · Remove Stock · Stock Adjustment\nMedicine Stock Update','Current Stock · Stock Update Result · Low Stock Information')]
for i,(pid,inp,out) in enumerate(SF):
 # Two direction-specific flows represented by one paired connector with explicit labels.
 y=ys[pid]+410;lane=10690+i*35
 pts=[(staffx+70+i*110,800),(staffx+70+i*110,840+i*36),(lane,840+i*36),(lane,y),(px+pw,y)]
 c.arrow(pts,'Staff → Process: '+inp.replace('\n',' ')+'\nProcess → Staff: '+out,(6700,y-23),both=True,size=23)
 add('Staff',pid,inp.replace('\n',' '));add(pid,'Staff',out)
# Gateway only connects with 6.0.
gy=ys['6.0'];c.node('Payment Gateway',10890,gy+70,550,320,'entity')
c.arrow([(px+pw,gy+395),(10580,gy+395),(10580,gy+150),(10890,gy+150)],'Payment Request · Transaction Amount',(7650,gy+365),size=24);add('6.0','Payment Gateway','Payment Request · Transaction Amount')
c.arrow([(10890,gy+320),(10530,gy+320),(10530,gy+505),(px+600,gy+505),(px+600,gy+420)],'Transaction Result · Payment Success · Payment Failure',(7600,gy+520),size=24);add('Payment Gateway','6.0','Transaction Result · Payment Success · Payment Failure')
for pid,name in P:
 # Preserve exact names; wrap only at word boundaries.
 import textwrap
 label=pid+'\n'+'\n'.join(textwrap.wrap(name,31))
 c.node(label,px,ys[pid],pw,420,'process')
for name,(x,y,w,h) in stores.items():c.node(name,x,y,w,h,'store')
# Strict structure checks.
expected=set('users auth_otps otp_verifications login_activity user_devices family_members notification_preferences notifications medicines disease_categories cart cart_saved_later wishlist medicine_subscriptions reviews_feedback prescription_requests orders order_items payments delivery_addresses delivery_areas referral_rewards staff stock_movements'.split())
processes={p for p,_ in P};entities={'Customer','Staff','Payment Gateway'}
assert set(stores)==expected and len(stores)==24 and len(processes)==13
assert len({(f['from'],f['to']) for f in flows})==len(flows)
for f in flows:
 a,b=f['from'],f['to'];assert a in processes or b in processes
 assert a in processes|entities|expected and b in processes|entities|expected
 if 'Payment Gateway' in [a,b]:assert '6.0' in [a,b]
 assert f['label'] and not any(t in f['label'] for t in ['1:N','1:1','PK','FK'])
c.text(W/2,7465,'Rectangles: external entities     •     Rounded rectangles: processes     •     Open-ended rectangles: data stores',25)
c.text(W/2,7510,'Read: store → process     •     Write: process → store     •     Arrowheads indicate flow direction; crossing lines do not join.',25)
c.save('dfd-level-1')
(O/'validation.json').write_text(json.dumps({'level_0':{'processes':1,'entities':3,'data_stores':0,'flows':ctx},'level_1':{'processes':dict(P),'external_entities':sorted(entities),'data_stores':sorted(stores),'directed_flows':flows},'validation':'Passed: unique nodes, allowed stores, labeled flows, process-mediated connections, gateway restricted to Payment Processing.'},indent=2))
print(f'Validated Level 0 and Level 1: {len(P)} processes (including optional 1.1), 24 unique stores, {len(flows)} directed Level 1 flows.')
