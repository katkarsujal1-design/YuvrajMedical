from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math,html,json,textwrap
O=Path(__file__).parent;W,H=3200,2100
im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im);s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>'];font='/usr/share/fonts/liberation/LiberationSans-Regular.ttf'
def text(x,y,t,size=26,b=False,bg=False):
 f=ImageFont.truetype(font.replace('Regular','Bold') if b else font,size);ls=t.split('\n')
 if bg:
  w=max(f.getlength(l) for l in ls)+18;h=len(ls)*(size+6)+10;rect(x-w/2,y-h/2,w,h,'white','white')
 for i,l in enumerate(ls):
  yy=y+(i-(len(ls)-1)/2)*(size+6);s.append(f'<text x="{x}" y="{yy}" text-anchor="middle" dominant-baseline="central" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" font-weight="{700 if b else 400}" fill="#172b3b">{html.escape(l)}</text>');d.text((x,yy),l,font=f,fill='#172b3b',anchor='mm')
def rect(x,y,w,h,fill='white',stroke='#344252'):
 s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>');d.rectangle((x,y,x+w,y+h),fill,stroke,2)
def line(p,dash=False):
 s.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in p)+'" fill="none" stroke="#344252" stroke-width="2"'+(' stroke-dasharray="10 7"' if dash else '')+'/>')
 for a,b in zip(p,p[1:]):
  if not dash:d.line([a,b],fill='#344252',width=2);continue
  le=math.dist(a,b)
  for k in range(0,math.ceil(le),17):
   v=min(k+10,le);d.line([(a[0]+(b[0]-a[0])*k/le,a[1]+(b[1]-a[1])*k/le),(a[0]+(b[0]-a[0])*v/le,a[1]+(b[1]-a[1])*v/le)],fill='#344252',width=2)
def oval(n,x,y,w=410,h=100):
 s.append(f'<ellipse cx="{x}" cy="{y}" rx="{w/2}" ry="{h/2}" fill="#edf4f8" stroke="#344252" stroke-width="2"/>');d.ellipse((x-w/2,y-h/2,x+w/2,y+h/2),fill='#edf4f8',outline='#344252',width=2);text(x,y,'\n'.join(textwrap.wrap(n,25)),26)
def actor(n,x,y):
 s.append(f'<circle cx="{x}" cy="{y-60}" r="25" fill="white" stroke="#344252" stroke-width="3"/>');d.ellipse((x-25,y-85,x+25,y-35),fill='white',outline='#344252',width=3);line([(x,y-35),(x,y+45)]);line([(x-50,y),(x+50,y)]);line([(x-45,y+105),(x,y+45),(x+45,y+105)]);text(x,y+145,n,27,True,bg=True)
rect(410,150,2370,1780)
text(1595,210,'YuvrajMedical Online Medical Store System',35,True)
N={'Login':(1450,380),'Verify OTP':(1900,380),'Send OTP':(2550,380),'Browse Medicines':(820,600),'Manage Cart':(820,820),'Place Order':(820,1040),'Make Payment':(820,1260),'Submit Prescription Request':(820,1480),'View Notifications':(820,1700),'Process Payment':(2500,1260),'Review Prescription':(2260,690),'Process Order':(2260,880),'Manage Medicine Stock':(2260,1070),'Manage Medicines':(2260,1510),'Manage Staff':(2260,1680),'View Sales Summary':(2260,1850)}
A={'Customer':(180,1000),'Staff':(3010,730),'Owner / Admin':(3010,1710),'Payment Gateway':(3010,1260),'OTP / SMS Service':(3010,365)}
def end(n,target):
 x,y=N[n];dx,dy=target[0]-x,target[1]-y;f=1/math.sqrt((dx/205)**2+(dy/50)**2);return x+dx*f,y+dy*f
assocs=[]
def assoc(a,n,p=None):
 pt=A[a];ep=end(n,pt)
 if p:p=[pt]+p+[end(n,p[-1])]
 else:p=[pt,ep]
 line(p);assocs.append((a,n))
for n in ['Browse Medicines','Manage Cart','Place Order','Make Payment','Submit Prescription Request']:assoc('Customer',n)
assoc('Customer','View Notifications',[(440,1710)])
assoc('Customer','Login',[(330,1000),(330,380)])
assoc('Customer','Verify OTP',[(300,1000),(300,290),(2050,290)])
for n in ['Review Prescription','Process Order','Manage Medicine Stock']:assoc('Staff',n)
assoc('Staff','Login',[(2840,730),(2840,520),(1450,520)])
for n in ['Manage Medicines','Manage Staff','View Sales Summary']:assoc('Owner / Admin',n)
assoc('Owner / Admin','Login',[(2890,1710),(2890,560),(1510,560),(1510,470)])
assoc('Payment Gateway','Process Payment')
assoc('OTP / SMS Service','Send OTP')
assoc('OTP / SMS Service','Verify OTP',[(2850,365),(2850,300),(2180,300)])
def include(a,b):
 p=[end(a,N[b]),end(b,N[a])];line(p,True);z,t=p[-1],p[-2];dx,dy=z[0]-t[0],z[1]-t[1];le=math.hypot(dx,dy);ux,uy=dx/le,dy/le;line([(z[0]-ux*16-uy*7,z[1]-uy*16+ux*7),z,(z[0]-ux*16+uy*7,z[1]-uy*16-ux*7)]);text((p[0][0]+p[1][0])/2,(p[0][1]+p[1][1])/2-22,'<<include>>',23,bg=True)
include('Make Payment','Process Payment');include('Verify OTP','Send OTP')
for n,(x,y) in N.items():oval(n,x,y)
for n,(x,y) in A.items():actor(n,x,y)
text(W/2,1990,'Simplified view — main functions only; detailed actions remain in the full diagram.',25)
text(W/2,2045,'Solid lines: actor associations     •     Dashed arrows: required included behavior',23)
s.append('</svg>');(O/'yuvrajmedical-use-case-simple.svg').write_text('\n'.join(s));im.save(O/'yuvrajmedical-use-case-simple.png',dpi=(240,240));im.resize((1600,1050)).save(O/'simple-preview.png')
assert len(A)==5 and len(N)==16 and len(assocs)==19
(O/'simple-model.json').write_text(json.dumps({'scope':'Main functions only','actors':list(A),'use_cases':list(N),'associations':assocs,'include':[['Make Payment','Process Payment'],['Verify OTP','Send OTP']]},indent=2))
print('Created simplified UML: 5 actors, 16 use cases, 19 associations, 2 include dependencies.')
