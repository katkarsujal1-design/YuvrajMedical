from pathlib import Path
import math,json,textwrap
O=Path(__file__).parent
source=(O/'render.py').read_text();exec(source[:source.index('# Context')])
O=Path(__file__).parent
W,H=3900,2300;c=Canvas(W,H)
c.text(W/2,75,'YuvrajMedical — Simplified Level 1 DFD',42,True)
c.text(W/2,132,'Main user and staff interactions',26)
N={};names=json.loads((O/'validation.json').read_text())['level_1']['processes']
ring=['1.0','4.0','5.0','6.0','7.0','8.0','9.0','12.0','10.0','3.0','2.0']
center=(1600,1170)
for i,p in enumerate(ring):
 a=-math.pi/2+i*2*math.pi/len(ring);x=center[0]+1090*math.cos(a);y=center[1]+820*math.sin(a)
 N[p]=(x-210,y-66,420,132,'process')
N['Customer']=(1400,1095,400,150,'entity')
N['Staff']=(3400,290,360,130,'entity')
N['11.0']=(3330,780,500,150,'process')
N['Payment Gateway']=(3330,1470,500,140,'entity')
labels={'1.0':'Credentials /\nauthentication result','2.0':'Search request /\nmedicine results','3.0':'Cart changes /\ncart & wishlist contents','4.0':'Prescription /\napproval status','5.0':'Order request /\norder status','6.0':'Payment details /\npayment result','7.0':'Address changes /\ndelivery information','8.0':'Subscription request /\nsubscription status','9.0':'Notification request /\nnotifications','10.0':'Review & feedback /\nconfirmation','12.0':'Referral request /\nreward result'}
def mid(k):
 x,y,w,h,_=N[k];return x+w/2,y+h/2
def boundary(k,toward):
 x,y,w,h,_=N[k];cx,cy=mid(k);dx,dy=toward[0]-cx,toward[1]-cy;s=min(w/2/abs(dx) if dx else 1e9,h/2/abs(dy) if dy else 1e9);return cx+s*dx,cy+s*dy
flows=[]
for p in ring:
 a=boundary('Customer',mid(p));b=boundary(p,center);t=.63;pos=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
 c.arrow([a,b],labels[p],pos,both=True,size=25);flows.append(('Customer',p,labels[p]))
# Staff routes stay outside the customer spokes.
x,y,w,h,_=N['1.0'];c.arrow([(3400,335),(3170,335),(3170,220),(1600,220),(1600,y)],'Staff login / authentication result',(2400,220),both=True,size=24);flows.append(('Staff','1.0','Staff login / authentication result'))
a=boundary('Staff',mid('4.0'));b=boundary('4.0',mid('Staff'));c.arrow([a,b],'Prescription decisions /\npending requests',((a[0]+b[0])/2,(a[1]+b[1])/2),both=True,size=24);flows.append(('Staff','4.0','Prescription decisions / pending requests'))
c.arrow([(3580,420),(3580,780)],'Stock updates /\nstock information',(3580,600),both=True,size=24);flows.append(('Staff','11.0','Stock updates / stock information'))
a=boundary('6.0',mid('Payment Gateway'));b=boundary('Payment Gateway',mid('6.0'));c.arrow([a,b],'Payment request /\ntransaction result',((a[0]+b[0])/2,(a[1]+b[1])/2),both=True,size=24);flows.append(('6.0','Payment Gateway','Payment request / transaction result'))
for k,(x,y,w,h,kind) in N.items():
 label=k if kind=='entity' else k+'\n'+'\n'.join(textwrap.wrap(names[k],27))
 c.node(label,x,y,w,h,kind)
c.text(W/2,2180,'Two-way arrows show requests and returned information. Every interaction passes through a process.',25)
c.text(W/2,2230,'Simplified view: database stores and internal process-to-process flows are omitted. The full DFD remains available separately.',24)
assert len(N)==15 and len([x for x in N.values() if x[-1]=='process'])==12
assert all(a in names or b in names for a,b,_ in flows)
c.save('dfd-level-1-simple')
(O/'simple-validation.json').write_text(json.dumps({'scope':'Simplified external-interaction view; data stores and internal exchanges omitted','processes':12,'external_entities':3,'labeled_two_way_flows':len(flows),'flows':flows},indent=2))
print('Created simplified 12-process, 3-entity overview with 15 labeled two-way connectors.')
