from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import html,json,math
OUT=Path(__file__).parent
W,H=2620,1580
S=2
im=Image.new('RGB',(W*S,H*S),'white'); d=ImageDraw.Draw(im)
font_path='/usr/share/fonts/liberation/LiberationSans-Regular.ttf'
bold_path='/usr/share/fonts/liberation/LiberationSans-Bold.ttf'
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>']
def line(points,width=2.2):
    svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="#253342" stroke-width="{width}" stroke-linejoin="round"/>')
    d.line([(int(x*S),int(y*S)) for x,y in points],fill='#253342',width=round(width*S))
def rect(x,y,w,h,fill,stroke=None):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="2"' if stroke else '')+'/>')
    d.rounded_rectangle((x*S,y*S,(x+w)*S,(y+h)*S),radius=5*S,fill=fill,outline=stroke,width=2*S)
def text(x,y,t,size=23,bold=False,color='#182738',bg=False):
    f=ImageFont.truetype(bold_path if bold else font_path,size*S)
    if bg:
        box=d.textbbox((0,0),t,font=f); tw=(box[2]-box[0])/S
        rect(x-tw/2-5,y-size/2-4,tw+10,size+8,'white')
    svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="central" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(t)}</text>')
    d.text((x*S,y*S),t,font=f,fill=color,anchor='mm')
nodes={}
def node(n,x,y,w=280,h=60):nodes[n]=(x,y,w,h)
left=['auth_otps','family_members','login_activity','notification_preferences','notifications','otp_verifications','referral_rewards','user_devices']
for i,n in enumerate(left):node(n,60,270+95*i,330)
node('users',550,260,280,760)
for i,n in enumerate(['cart','cart_saved_later','medicine_subscriptions','reviews_feedback','wishlist']):node(n,980,330+115*i,300)
node('medicines',1450,260,280,620)
node('disease_categories',1450,110)
node('stock_movements',1850,330)
node('order_items',1850,650)
node('orders',1850,1000)
node('payments',2300,1000)
node('delivery_addresses',550,1180)
node('delivery_areas',550,1420)
node('prescription_requests',1050,1330,310)
node('staff',1850,1330)
edges=[]
def edge(p,c,pts,one=False):
    edges.append((p,c,'1:1' if one else '1:N'))
    line(pts)
    # Parent/child numeric labels offset from each connector endpoint.
    for idx,label in [(0,'1'),(-1,'1' if one else 'N')]:
        a=pts[idx]; b=pts[1 if idx==0 else -2]
        vx,vy=b[0]-a[0],b[1]-a[1]; length=math.hypot(vx,vy); ux,uy=vx/length,vy/length
        px,py=a[0]+ux*34,a[1]+uy*34
        if abs(ux)>.5:py-=17
        else:px+=19
        text(px,py,label,22,True,bg=True)
    if not one:
        a=pts[-1]; b=pts[-2]; vx,vy=b[0]-a[0],b[1]-a[1]; length=math.hypot(vx,vy); ux,uy=vx/length,vy/length
        pivot=(a[0]+ux*19,a[1]+uy*19)
        line([(a[0]-uy*9,a[1]+ux*9),pivot,(a[0]+uy*9,a[1]-ux*9)])
for i,n in enumerate(left):
    y=300+95*i; edge('users',n,[(550,y),(390,y)],n=='notification_preferences')
for i,n in enumerate(['cart','cart_saved_later','medicine_subscriptions','reviews_feedback','wishlist']):
    y=360+115*i
    edge('users',n,[(830,y),(980,y)])
    edge('medicines',n,[(1450,y),(1280,y)])
edge('disease_categories','medicines',[(1590,170),(1590,260)])
edge('medicines','stock_movements',[(1730,360),(1850,360)])
edge('medicines','order_items',[(1730,680),(1850,680)])
edge('orders','order_items',[(1990,1000),(1990,710)])
edge('orders','payments',[(2130,1030),(2300,1030)])
edge('users','orders',[(830,970),(1650,970),(1650,1030),(1850,1030)])
edge('users','delivery_addresses',[(650,1020),(650,1180)])
edge('delivery_areas','delivery_addresses',[(650,1420),(650,1240)])
edge('delivery_addresses','orders',[(830,1210),(1910,1210),(1910,1060)])
edge('users','prescription_requests',[(760,1020),(760,1100),(900,1100),(900,1360),(1050,1360)])
edge('staff','prescription_requests',[(1850,1360),(1360,1360)])
edge('staff','stock_movements',[(2130,1360),(2200,1360),(2200,450),(1990,450),(1990,390)])
expected_tables='auth_otps cart cart_saved_later delivery_addresses delivery_areas disease_categories family_members login_activity medicine_subscriptions medicines notification_preferences notifications order_items orders otp_verifications payments prescription_requests referral_rewards reviews_feedback staff stock_movements user_devices users wishlist'.split()
expected=[('users',c,'1:1' if c=='notification_preferences' else '1:N') for c in left+['delivery_addresses','prescription_requests','orders','cart','cart_saved_later','medicine_subscriptions','reviews_feedback','wishlist']]
expected += [('medicines',c,'1:N') for c in ['cart','cart_saved_later','medicine_subscriptions','reviews_feedback','wishlist','order_items','stock_movements']]
expected += [(p,c,'1:N') for p,c in [('disease_categories','medicines'),('orders','order_items'),('orders','payments'),('delivery_addresses','orders'),('delivery_areas','delivery_addresses'),('staff','stock_movements'),('staff','prescription_requests')]]
assert len(nodes)==24 and set(nodes)==set(expected_tables)
assert len(edges)==30 and len(set(edges))==30 and set(edges)==set(expected)
# White breaks distinguish crossings from relationships.
for x,y in [(900,1210),(2200,1030)]:
    rect(x-7,y-9,14,18,'white')
    line([(x,y-11),(x,y+11)])
for n,(x,y,w,h) in nodes.items():
    rect(x,y,w,h,'#f1f5f9' if n in ['users','medicines','orders'] else '#ffffff','#253342')
    text(x+w/2,y+h/2,n,24,True)
svg.append('</svg>')
(OUT/'yuvrajmedical-er.svg').write_text('\n'.join(svg))
im.save(OUT/'yuvrajmedical-er.png',dpi=(240,240))
im.resize((W,H)).save(OUT/'preview.png')
(OUT/'relationships.json').write_text(json.dumps({'tables':list(nodes),'relationships':[{'parent':p,'child':c,'cardinality':r} for p,c,r in edges],'validation':{'tables':24,'unique_relationships':30,'status':'passed'}},indent=2))
print('Validated 24 unique tables, 30 exact unique relationships. Exported SVG and 5240 × 3160 PNG.')
