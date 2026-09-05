from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math,html,json,textwrap,heapq,re
O=Path(__file__).parent
FONT='/usr/share/fonts/liberation/LiberationSans-Regular.ttf';BOLD=FONT.replace('Regular','Bold')
LANES={'C':'Customer','S':'YuvrajMedical System','T':'Staff','P':'Payment Gateway','O':'OTP / SMS Service','A':'Owner / Admin','U':'Customer / Staff / Owner'}
charts=[]
def chart(slug,title,lanes,raw,flows,note=''):
 nodes={}
 for l in raw.strip().splitlines():
  ident,lane,kind,row,label=l.split('|',4);slot=0
  if ':' in lane:lane,slot=lane.split(':');slot=float(slot)
  assert ident not in nodes
  nodes[ident]={'lane':lane,'kind':kind,'row':float(row),'label':label.replace('~','\n'),'slot':slot}
 edges=[]
 for l in flows.strip().splitlines():
  path,*guard=l.split('|');parts=path.split('>')
  for a,b in zip(parts,parts[1:]):
   assert a in nodes and b in nodes,(slug,a,b)
   edges.append({'a':a,'b':b,'guard':guard[0] if guard else ''})
 charts.append({'slug':slug,'title':title,'lanes':lanes.split(),'nodes':nodes,'edges':edges,'note':note})
chart('00-main','Main Customer Purchase Journey','C S T P O',r'''
start|C|start|0|
open|C|action|1|Open YuvrajMedical
home|S|action|1|Display home page
account|C|action|2|Register or log in
validate|S|action|2|Validate account / credentials
valid|S|decision|3|Authenticated?
autherr|C|action|3|Read error; correct credentials
browse|C|action|4|Browse / search; select medicine
show|S|action|4|Display medicine details
rx|S|decision|5|Prescription required?
upload|C|action|6|Upload prescription
pending|S|action|6|Validate file; create pending request
review|T|action|6|Review prescription
approved|T|decision|7|Prescription approved?
reject|S|action|7|Record Rejected status
rejectsms|O|action|7|Send rejection notification
rejectview|C|action|8|View rejection status
approve|S|action|8|Record Approved status
approvesms|O|action|8|Send approval notification
cart|C|action|9|Add medicine to cart; manage cart
check|S|action|9|Check session, cart, stock and prescription
checkout|S|decision|10|Checkout valid?
carterr|C|action|10|Read checkout error; correct cart
address|C|action|11|Select saved / add new delivery address
area|S|action|11|Validate delivery area
available|S|decision|12|Delivery available?
addrerr|C|action|12|Choose another address
place|C|action|13|Review summary / optional reward; place order
create|S|action|13|Create order, items and order ID
method|C|action|14|Select payment method
request|S|action|14|Send payment request
payment|P|action|14|Process transaction
paid|P|decision|15|Payment successful?
failure|S|action|15|Record failure; display Payment Failed
retry|C|decision|16|Retry payment?
hold|S:-0.34|action|17|Cancel / hold order under system rules
attemptend|C|end|18|Order attempt ended
fork|S|fork|16|Parallel completion
confirm|S:-0.30|action|18|Confirm order status
record|S:0|action|18|Record successful payment
clear|S:0.30|action|18|Clear purchased cart items
stock|T|action|17|Update stock; record movement
stockok|T|decision|18|Stock update successful?
flag|S|action|19|Flag inventory issue for staff
paysms|O|action|17|Send enabled payment confirmation
join|S|join|20|
confirmation|S|action|21|Generate order confirmation
ordersms|O|action|21|Send enabled order confirmation
receive|C|action|21|Receive order confirmation
stafflogin|T|action|22|Log in; select pending order
staffauth|S|action|22|Validate staff session
process|T|action|23|Process next stage:~Confirmed / Packed / Out for Delivery / Delivered
status|S|action|23|Update order status
statussms|O|action|23|Send enabled order-status notification
track|C|action|24|Open My Orders; track order
showstatus|S|action|24|Display current order status
delivered|S|decision|25|Order delivered?
feedback|C|action|26|Enter rating, review and feedback
save|S|action|26|Validate and save review
logout|C|action|27|Select Logout
destroy|S|action|27|Destroy session; redirect to home / login
end|S|end|28|Completed
''',r'''
start>open>home>account>validate>valid
valid>autherr|No
autherr>account
valid>browse|Yes
browse>show>rx
rx>cart|No
rx>upload|Yes
upload>pending>review>approved
approved>reject|No
reject>rejectsms>rejectview>browse
approved>approve|Yes
approve>approvesms>cart
cart>check>checkout
checkout>carterr|No
carterr>cart
checkout>address|Yes
address>area>available
available>addrerr|No
addrerr>address
available>place|Yes
place>create>method>request>payment>paid
paid>failure|No
failure>retry
retry>method|Yes
retry>hold|No
hold>attemptend
paid>fork|Yes
fork>confirm
fork>record
fork>clear
fork>stock
fork>paysms
stock>stockok
stockok>flag|No
stockok>join|Yes
flag>join
confirm>join
record>join
clear>join
paysms>join
join>confirmation>ordersms>receive>stafflogin>staffauth>process>status>statussms>track>showstatus>delivered
delivered>process|No
delivered>feedback|Yes
feedback>save>logout>destroy>end
''','Expanded registration, shopping, checkout, cancellation, notification, subscription and admin flows follow in the supporting diagrams.')
chart('01-registration','Registration & OTP Verification','C S O',r'''
s|C|start|0|
select|C|action|1|Select Register
form|C|action|2|Enter name, email, phone, address and password
validate|S|action|2|Validate registration details
valid|S|decision|3|Details valid?
error|S|action|4|Show validation error
request|S|action|5|Request OTP
send|O|action|5|Send OTP
enter|C|action|6|Enter OTP
verify|S|action|6|Verify OTP
ok|S|decision|7|OTP valid?
otperror|S|action|8|Show OTP error
choice|C|decision|8|Retry or resend?
create|S|action|9|Create customer account
success|S|action|10|Display Registration Successful
login|C|action|10|Proceed to Login
e|C|end|11|
''',r'''
s>select>form>validate>valid
valid>error|No
error>form
valid>request|Yes
request>send>enter>verify>ok
ok>otperror|No
otperror>choice
choice>enter|Retry
choice>request|Resend
ok>create|Yes
create>success>login>e
''')
chart('02-login-logout','Login, Session & Logout','U S',r'''
s|U|start|0|
form|U|action|1|Enter email / phone and password
validate|S|action|1|Validate credentials
correct|S|decision|2|Credentials correct?
error|S|action|3|Display Invalid Login Message
record|S|action|4|Record login activity
session|S|action|5|Create authenticated session
dashboard|S|action|6|Display appropriate dashboard / home page
use|U|action|7|Use permitted system functions
logout|U|action|8|Select Logout
destroy|S|action|8|Destroy session
activity|S|action|9|Record logout activity if applicable
redirect|S|action|10|Redirect to Login / Home Page
e|S|end|11|
''',r'''
s>form>validate>correct
correct>error|No
error>form
correct>record|Yes
record>session>dashboard>use>logout>destroy>activity>redirect>e
''')
chart('03-medicine-browsing','Medicine Browsing & Prescription Requirement','C S',r'''
s|C|start|0|
browse|C|action|1|Select Browse Medicines
list|S|action|1|Display medicine list
search|C|action|2|Search; filter category / price; select details
results|S|action|2|Retrieve and display matching medicines
found|S|decision|3|Medicine found?
none|S|action|4|Display No medicines found
details|C|action|5|View medicine details
rx|S|decision|5|Prescription required?
message|S|action|6|Display Prescription Required
upload|C|decision|6|Upload prescription now?
rxflow|C|action|7|Continue to prescription upload workflow
shop|C|action|8|Choose shopping action
endrx|C|end|9|Prescription workflow
endshop|S|end|9|Shopping workflow
''',r'''
s>browse>list>search>results>found
found>none|No
none>search
found>details|Yes
details>rx
rx>shop|No
rx>message|Yes
message>upload
upload>rxflow|Yes
upload>shop|Later
rxflow>endrx
shop>endshop
''','Checkout still requires prescription approval for medicines that require a prescription.')
chart('04-shopping-actions','Shopping Actions','C S',r'''
s|C|start|0|
choose|C|decision|1|Choose action
add|C|action|2|Select Add to Cart
stock|S|action|2|Check stock availability
instock|S|decision|3|In stock?
out|S|action|4|Display Out of Stock
addcart|S|action|5|Add medicine to cart; display Cart Updated
wish|C|action|6|Select Add to Wishlist
wishlist|S|action|6|Add medicine; display Wishlist Updated
save|C|action|7|Select Save for Later
incart|S|decision|7|Item already in cart?
notcart|S|action|8|Explain item must be in cart
saved|S|action|9|Move cart item to Saved for Later; confirm
subscribe|C|action|10|Select Subscribe
schedule|C|action|11|Choose frequency, quantity and start date
validate|S|action|11|Validate subscription
valid|S|decision|12|Subscription valid?
suberror|S|action|13|Display validation error
create|S|action|14|Create subscription; display Subscription Created
medicine|C|action|15|Return to medicine page
end|C|end|16|
''',r'''
s>choose
choose>add|Add to Cart
choose>wish|Wishlist
choose>save|Save for Later
choose>subscribe|Subscribe
add>stock>instock
instock>out|No
out>medicine
instock>addcart|Yes
addcart>medicine
wish>wishlist>medicine
save>incart
incart>notcart|No
notcart>medicine
incart>saved|Yes
saved>medicine
subscribe>schedule>validate>valid
valid>suberror|No
suberror>schedule
valid>create|Yes
create>medicine>end
''')
chart('05-prescriptions','Prescription Request & Staff Decision','C S T O',r'''
s|C|start|0|
select|C|action|1|Select Upload Prescription
file|C|action|2|Upload prescription file
validate|S|action|2|Validate file
valid|S|decision|3|Valid prescription file?
error|S|action|4|Display invalid file error
pending|S|action|5|Create prescription request; set Pending
notify|S|action|6|Notify staff
view|T|action|6|View prescription request
review|T|action|7|Review prescription
approved|T|decision|8|Prescription approved?
reject|T:-0.28|action|9|Reject prescription
approve|T:0.28|action|9|Approve prescription
rejected|S:-0.28|action|10|Update status to Rejected
accepted|S:0.28|action|10|Update status to Approved
rejectsms|O:-0.28|action|11|Send rejection notification
acceptsms|O:0.28|action|11|Send approval notification
rejection|C|action|12|View rejection; return to browsing
continue|C|action|13|Continue shopping / order
endno|S|end|12|Return to browse
endyes|S|end|13|Continue order
''',r'''
s>select>file>validate>valid
valid>error|No
error>file
valid>pending|Yes
pending>notify>view>review>approved
approved>reject|No
approved>approve|Yes
reject>rejected>rejectsms>rejection>endno
approve>accepted>acceptsms>continue>endyes
''')
chart('06-cart-checkout','Cart, Checkout & Delivery Address','C S',r'''
s|C|start|0|
cart|C|action|1|Open Cart
items|S|action|1|Display cart items
edit|C|action|2|Increase / decrease quantity; remove; save for later; move saved item to cart
total|S|action|2|Recalculate total
proceed|C|decision|3|Proceed to checkout?
return|C|action|4|Continue cart / browsing
checks|S|action|5|Check authentication, nonempty cart, stock and required prescription approval
valid|S|decision|6|Checkout conditions valid?
error|S|action|7|Show error: empty cart, stock, pending / rejected prescription, or unavailable item
address|C|action|8|Select delivery address
existing|C|decision|9|Existing address?
saved|C:-0.28|action|10|Select saved address
new|C:0.28|action|10|Add new delivery address
area|S|action|11|Check delivery area
available|S|decision|12|Delivery available?
noarea|S|action|13|Display Delivery not available in this area
summary|C|action|14|Continue to order summary
e|C|end|15|
''',r'''
s>cart>items>edit>total>proceed
proceed>return|No
return>cart
proceed>checks|Yes
checks>valid
valid>error|No
error>cart
valid>address|Yes
address>existing
existing>saved|Yes
existing>new|No
saved>area
new>area
area>available
available>noarea|No
noarea>address
available>summary|Yes
summary>e
''')
chart('07-rewards-order','Referral Reward & Order Creation','C S',r'''
s|C|start|0|
apply|C|decision|1|Apply referral reward?
validate|S|action|2|Validate reward balance
available|S|decision|3|Reward available?
none|S|action|4|Display Reward unavailable; continue without reward
discount|S|action|5|Apply discount; update order total
summary|C|action|6|Review medicines, quantity, address, total and reward discount
place|C|action|7|Select Place Order
order|S|action|7|Create order
items|S|action|8|Create order items
id|S|action|9|Generate order ID
payment|C|action|10|Proceed to payment
e|C|end|11|
''',r'''
s>apply
apply>summary|No
apply>validate|Yes
validate>available
available>none|No
none>summary
available>discount|Yes
discount>summary>place>order>items>id>payment>e
''')
chart('08-payment','Payment Attempt & Retry','C S P',r'''
s|C|start|0|
method|C|action|1|Select payment method
request|S|action|1|Send payment request / transaction amount
process|P|action|2|Process transaction
success|P|decision|3|Payment successful?
failure|P:-0.28|action|4|Return failure
accepted|P:0.28|action|4|Return success
failedrecord|S|action|5|Record failed payment
message|C|action|5|View Payment Failed
retry|C|decision|6|Retry payment?
hold|S|action|7|Cancel / hold order under system rules
endattempt|C|end|8|Order attempt ended
completion|S|action|9|Begin successful-payment completion: payment record, confirmation and inventory work
e|S|end|10|Continue completion
''',r'''
s>method>request>process>success
success>failure|No
failure>failedrecord>message>retry
retry>method|Yes
retry>hold|No
hold>endattempt
success>accepted|Yes
accepted>completion>e
''')
chart('09-parallel-completion','Parallel Post-Payment Completion','C S T O',r'''
s|S|start|0|
success|S|action|1|Accept successful payment result
fork|S|fork|2|
confirm|S:-0.30|action|4|Set order Confirmed
payment|S:0|action|4|Record successful payment
cart|S:0.30|action|4|Clear purchased items from cart
stock|T|action|3|Update medicine stock; record stock movement
ok|T|decision|4|Stock update successful?
flag|T|action|5|Escalate inventory issue to system
issue|S|action|6|Flag inventory issue for staff
notify|O|action|3|Send enabled payment confirmation
join|S|join|7|
generate|S|action|8|Generate order confirmation
send|O|action|8|Send enabled order confirmation
receive|C|action|9|Receive confirmations
e|C|end|10|
''',r'''
s>success>fork
fork>confirm
fork>payment
fork>cart
fork>stock
fork>notify
stock>ok
ok>join|Yes
ok>flag|No
flag>issue>join
confirm>join
payment>join
cart>join
notify>join
join>generate>send>receive>e
''','All five fork branches must finish before the join continues. Notification preferences are resolved by the notification workflow.')
chart('10-staff-processing','Staff Order Processing & Status Updates','C S T O',r'''
s|T|start|0|
login|T|action|1|Log in as staff
validate|S|action|1|Validate staff login
valid|S|decision|2|Staff credentials valid?
error|S|action|3|Display login error
dashboard|T|action|4|Open Staff Dashboard; view pending orders
select|T|action|5|Select order; view details
ready|T|decision|6|Order ready for processing?
hold|S|action|7|Keep Pending / On Hold
wait|T|action|8|Wait for readiness; recheck pending order
process|T|action|9|Process next stage: Confirmed → Packed → Out for Delivery → Delivered
update|S|action|9|Update order for the new status
sms|O|action|10|Send enabled order-status notification
receive|C|action|10|Receive updated status
done|S|decision|11|Delivered?
e|T|end|12|Processing complete
''',r'''
s>login>validate>valid
valid>error|No
error>login
valid>dashboard|Yes
dashboard>select>ready
ready>hold|No
hold>wait>select
ready>process|Yes
process>update>sms>receive>done
done>process|No
done>e|Yes
''')
chart('11-tracking','Customer Order Tracking','C S',r'''
s|C|start|0|
orders|C|action|1|Open My Orders
history|S|action|1|Display order history
select|C|action|2|Select order
details|S|action|2|Display order details
track|C|action|3|Select Track Order
status|S|action|3|Display current status: Pending / Confirmed / Packed / Out for Delivery / Delivered / Cancelled
e|C|end|4|
''',r'''
s>orders>history>select>details>track>status>e
''')
chart('12-cancellation','Order Cancellation & Refund Handling','C S O',r'''
s|C|start|0|
details|C|action|1|Open order details
eligible|S|decision|2|Order can be cancelled?
blocked|S|action|3|Display Order cannot be cancelled
cancel|C|action|4|Select Cancel Order
ask|S|action|4|Ask for confirmation
confirm|C|decision|5|Confirm cancellation?
status|S|action|6|Update order to Cancelled
stock|S|action|7|Restore medicine stock
movement|S|action|8|Record stock movement
paid|S|decision|9|Payment already completed?
refund|S|action|10|Initiate / mark refund under system rules
send|O|action|11|Send enabled cancellation notification
message|S|action|12|Display Order Cancelled
e|C|end|13|Cancellation complete
viewend|C|end|3|Continue viewing order
''',r'''
s>details>eligible
eligible>blocked|No
blocked>viewend
eligible>cancel|Yes
cancel>ask>confirm
confirm>details|No
confirm>status|Yes
status>stock>movement>paid
paid>refund|Yes
paid>send|No
refund>send>message>e
''','Eligibility: not delivered, not already cancelled and within the permitted processing stage. Refund execution follows the system payment rules.')
chart('13-notifications','Notification Preferences & Delivery','C S O',r'''
s|S|start|0|
event|S|action|1|Receive event: OTP; prescription decision; payment success / failure; order status / cancellation; subscription reminder
prefs|S|action|2|Check notification preferences and event requirements
enabled|S|decision|3|Notification enabled?
required|S|decision|4|Required service message / OTP?
skip|S|action|5|Do not send optional notification
prepare|S|action|6|Prepare message for enabled / required channel
send|O|action|6|Send OTP / notification through configured channel
receive|C|action|7|Receive notification
e|S|end|8|
''',r'''
s>event>prefs>enabled
enabled>prepare|Yes
enabled>required|No
required>prepare|Yes
required>skip|No
skip>e
prepare>send>receive>e
''','Optional-message preferences do not suppress OTP needed for authentication. Other configured channels follow the same system notification decision.')
chart('14-reviews','Delivered-Order Review & Feedback','C S',r'''
s|C|start|0|
open|C|action|1|Open order for review
delivered|S|decision|2|Order delivered?
policy|S|decision|3|Delivered-order review required?
blocked|S|action|4|Do not allow review yet
select|C|action|5|Select Review & Feedback
enter|C|action|6|Enter rating, review and feedback
validate|S|action|6|Validate submission
valid|S|decision|7|Submission valid?
error|S|action|8|Display validation error
save|S|action|9|Save review
thanks|S|action|10|Display Thank you for your feedback
e|C|end|11|
''',r'''
s>open>delivered
delivered>select|Yes
delivered>policy|No
policy>blocked|Yes
policy>select|No
blocked>e
select>enter>validate>valid
valid>error|No
error>enter
valid>save|Yes
save>thanks>e
''')
chart('15-subscriptions','Medicine Subscription Reminder & Renewal','C S O',r'''
s|S|start|0|
monitor|S|action|1|Check active subscriptions
wait|S|action|2|Wait until next scheduled check
due|S|decision|3|Subscription due?
reminder|S|action|4|Generate medicine reminder
preferences|S|action|5|Apply notification preference workflow
send|O|action|5|Send enabled reminder notification
open|C|action|6|Open subscription
continue|C|decision|7|Continue subscription?
active|S|action|8|Keep active; proceed to next cycle
cancel|C|action|9|Cancel subscription
update|S|action|9|Update subscription status
e|C|end|10|
''',r'''
s>monitor>due
due>wait|No
wait>monitor
due>reminder|Yes
reminder>preferences>send>open>continue
continue>active|Yes
active>wait
continue>cancel|No
cancel>update>e
''')
chart('16-administration','Owner / Admin Management & Logout','A S',r'''
s|A|start|0|
login|A|action|1|Log in as Owner / Admin
validate|S|action|1|Validate admin credentials
valid|S|decision|2|Credentials valid?
error|S|action|3|Display login error
dashboard|S|action|4|Display Owner Dashboard
choose|A|decision|5|Choose management function
medicine|A|action|6|Add / update / delete medicine
medvalidate|S|action|6|Validate medicine data
medupdate|S|action|7|Update medicine records; show success
staff|A|action|8|Add / update / remove staff
staffvalidate|S|action|8|Validate staff data
staffupdate|S|action|9|Update staff information; show success
areas|A|action|10|Manage disease categories / delivery areas
areaupdate|S|action|10|Validate and apply selected changes
reports|A|action|11|Choose orders, payments, customers, prescriptions, stock movements, reviews, referral rewards or dashboard statistics
show|S|action|11|Display selected management view / report
logout|A|action|12|Select Logout
destroy|S|action|12|Destroy session; record activity if applicable
redirect|S|action|13|Redirect to Login / Home Page
e|A|end|14|
''',r'''
s>login>validate>valid
valid>error|No
error>login
valid>dashboard|Yes
dashboard>choose
choose>medicine|Medicines
medicine>medvalidate>medupdate>choose
choose>staff|Staff
staff>staffvalidate>staffupdate>choose
choose>areas|Categories / Areas
areas>areaupdate>choose
choose>reports|Views / Reports
reports>show>choose
choose>logout|Logout
logout>destroy>redirect>e
''')
# Alternative inventory outcomes merge before the AND-join.
for c in charts:
 if c['slug']=='01-registration':
  for n in c['nodes'].values():
   if n['row']>=1:n['row']+=1
  c['nodes']['registered']={'lane':'C','kind':'decision','row':1,'label':'Already registered?','slot':0}
  c['edges']=[e for e in c['edges'] if not(e['a']=='s' and e['b']=='select')]+[{'a':'s','b':'registered','guard':''},{'a':'registered','b':'select','guard':'No'},{'a':'registered','b':'login','guard':'Yes'}]
 if c['slug'] in ['00-main','09-parallel-completion']:
  nd=c['nodes'];main=c['slug']=='00-main';nd['inventorymerge']={'lane':'T','kind':'merge','row':19.6 if main else 6,'label':'','slot':0}
  for e in c['edges']:
   if e['b']=='join' and e['a'] in (['stockok','flag'] if main else ['ok','issue']):e['b']='inventorymerge'
  c['edges'].append({'a':'inventorymerge','b':'join','guard':''})
 if c['slug']=='15-subscriptions':
  c['nodes']['enabled']={'lane':'S','kind':'decision','row':6,'label':'Reminder enabled?','slot':0}
  for ident,row in [('send',6),('open',7),('continue',8),('active',9),('cancel',10),('update',10),('e',11)]:c['nodes'][ident]['row']=row
  c['edges']=[e for e in c['edges'] if not(e['a']=='preferences' and e['b']=='send')]+[{'a':'preferences','b':'enabled','guard':''},{'a':'enabled','b':'send','guard':'Yes'},{'a':'enabled','b':'wait','guard':'No'}]

router_source=(O.parent/'yuvrajmedical-dfd'/'compact.py').read_text();router_source=router_source[router_source.index('G=20;'):router_source.index('# Local store links first')]
router_source=router_source.replace('pad=8','pad=0')
router_source=router_source.replace('   out.append((pt,ep,portsused.get((k,ep),0)*35))','   if pt not in blocked:out.append((pt,ep,portsused.get((k,ep),0)*35))')
router_source=router_source.replace('for frac in [.5,.25,.75]:',"for frac in ([.5] if n['kind'] in ['decision','merge','start','end'] else [.5,.25,.75]):")
all_svg=[];pdf_pages=[];reports=[]
for ci,c in enumerate(charts):
 raw=c['nodes'];lanes=c['lanes'];maxrow=max(n['row'] for n in raw.values());H=max(1700,int(600+maxrow*135));W=max(3500,int(H*1.45)//20*20);margin=65;top=220;bottom=H-105;laneW=(W-2*margin)/len(lanes)
 nodes={};styles={}
 for ident,n in raw.items():
  laneidx=lanes.index(n['lane']);cx=margin+laneW*(laneidx+.5+n['slot']);cy=335+n['row']*135;kind=n['kind'];slot=n['slot']
  narrow=(c['slug']=='00-main' and ident in ['confirm','record','clear']) or (c['slug']=='09-parallel-completion' and ident in ['confirm','payment','cart'])
  size=23 if slot or narrow else 27
  w=min(650,int(laneW*.72)) if not slot else min(300,int(laneW*.255))
  if narrow:w=min(300,int(laneW*.255))
  wrap=max(13,int(w/(size*.56)));ls=[]
  for part in n['label'].split('\n'):ls+=textwrap.wrap(part,wrap) or ['']
  h=max(74,len(ls)*(size+5)+22)
  if kind=='decision':w=min(265,int(laneW*.35));h=120;size=22;ls=textwrap.wrap(n['label'],18)
  if kind=='merge':w=h=30;ls=[]
  if kind=='start':w=h=28;ls=[]
  if kind=='end':w=h=38;ls=[]
  if kind in ['fork','join']:w=int(laneW*.83);h=14;ls=[]
  nodes[ident]={'x':int(cx-w/2),'y':int(cy-h/2),'w':w,'h':h,'kind':kind,'lane':n['lane'],'label':n['label']}
  styles[ident]={'size':size,'lines':ls}
 # Explicit merge diamonds for alternative routes that re-enter an action.
 incoming={i:[] for i in nodes}
 for e in c['edges']:incoming[e['b']].append(e)
 edges=[dict(e) for e in c['edges']]
 for ident,ins in incoming.items():
  if len(ins)>1 and nodes[ident]['kind']=='action':
   n=nodes[ident];merge=ident+'__merge';x=n['x']-65;y=n['y']+n['h']/2-15
   nodes[merge]={'x':int(x),'y':int(y),'w':30,'h':30,'kind':'merge','lane':n['lane'],'label':''};styles[merge]={'size':20,'lines':[]}
   for e in edges:
    if e['b']==ident:e['b']=merge
   edges.append({'a':merge,'b':ident,'guard':''})
 # Validate graph semantics and branch guards before layout.
 starts=[i for i,n in nodes.items() if n['kind']=='start'];ends=[i for i,n in nodes.items() if n['kind']=='end'];assert len(starts)==1 and ends
 outgoing={i:[] for i in nodes};inc={i:[] for i in nodes}
 for e in edges:outgoing[e['a']].append(e);inc[e['b']].append(e)
 for ident,n in nodes.items():
  if n['kind']=='decision':assert len(outgoing[ident])>=2 and all(e['guard'] for e in outgoing[ident]),(c['slug'],ident)
  if n['kind']=='merge':assert len(outgoing[ident])==1
  if n['kind']=='join':assert len(inc[ident])==5 and len(outgoing[ident])==1,(c['slug'],ident,len(inc[ident]))
  if n['kind']=='fork':assert len(outgoing[ident])==5 and len(inc[ident])==1
  if n['kind']!='end':assert outgoing[ident],(c['slug'],ident,'dead-end action')
 reached=set(starts);queue=list(starts)
 while queue:
  a=queue.pop()
  for e in outgoing[a]:
   if e['b'] not in reached:reached.add(e['b']);queue.append(e['b'])
 assert reached==set(nodes),(c['slug'],set(nodes)-reached)
 # Every node has a route to a final node (loops can be exited).
 canend=set(ends);q=list(ends)
 while q:
  b=q.pop()
  for e in inc[b]:
   if e['a'] not in canend:canend.add(e['a']);q.append(e['a'])
 assert canend==set(nodes),(c['slug'],'unexitable component')
 # Set up orthogonal routing with node and guard-label avoidance.
 font=FONT
 exec(router_source)
 for gx in range(W//G):
  for gy in range(0,265//G):blocked.add((gx,gy))
  for gy in range(int((H-92)//G),H//G):blocked.add((gx,gy))
 def anchor(a,b):
  na,nb=nodes[a],nodes[b];ax=na['x']+na['w']/2;ay=na['y']+na['h']/2;bx=nb['x']+nb['w']/2;by=nb['y']+nb['h']/2
  if abs(ax-bx)<1:
   sign=1 if by>ay else -1;return [(ax,ay+sign*na['h']/2),(bx,by-sign*nb['h']/2)]
  if abs(ay-by)<1:
   sign=1 if bx>ax else -1;return [(ax+sign*na['w']/2,ay),(bx-sign*nb['w']/2,by)]
  return None
 def intersects(pts,a,b):
  # Segment/rectangle clipping handles half-pixel diagonal anchors as well as orthogonal routes.
  for ident,box in nodes.items():
   if ident in [a,b]:continue
   x,y,w,h=[box[k] for k in ['x','y','w','h']]
   bounds=[(x-3,x+w+3),(y-3,y+h+3)]
   for p,t in zip(pts,pts[1:]):
    low,high=0.0,1.0
    for axis,(mn,mx) in enumerate(bounds):
     delta=t[axis]-p[axis]
     if abs(delta)<1e-9:
      if not mn<p[axis]<mx:low,high=1,0;break
     else:
      a0,b0=(mn-p[axis])/delta,(mx-p[axis])/delta
      low=max(low,min(a0,b0));high=min(high,max(a0,b0))
    if low<high:return True
  return False
 for e in sorted(edges,key=lambda e:math.dist((nodes[e['a']]['x'],nodes[e['a']]['y']),(nodes[e['b']]['x'],nodes[e['b']]['y']))):
  pts=anchor(e['a'],e['b'])
  if pts is None:
   na,nb=nodes[e['a']],nodes[e['b']];ax=na['x']+na['w']/2;ay=na['y']+na['h']/2;bx=nb['x']+nb['w']/2;by=nb['y']+nb['h']/2
   if by>ay and nb['y']>na['y']+na['h']+15:
    my=(na['y']+na['h']+nb['y'])/2;candidate=[(ax,na['y']+na['h']),(ax,my),(bx,my),(bx,nb['y'])]
    if not intersects(candidate,e['a'],e['b']):pts=candidate
  if e['guard'] and pts and math.dist(pts[0],pts[-1])<90:
   na,nb=nodes[e['a']],nodes[e['b']];side=-1 if e['guard']=='No' else 1
   ax=na['x']+(na['w'] if side==1 else 0);ay=na['y']+na['h']/2;bx=nb['x']+(nb['w'] if side==1 else 0);by=nb['y']+nb['h']/2
   xx=(max(ax,bx)+70) if side==1 else (min(ax,bx)-70);pts=[(ax,ay),(xx,ay),(xx,by),(bx,by)]
  if pts is None or intersects(pts,e['a'],e['b']):
   try:pts=route(e['a'],e['b'])
   except RuntimeError:
    old_reserved=reserved;reserved=set()
    try:pts=route(e['a'],e['b'])
    finally:reserved=old_reserved
  assert not intersects(pts,e['a'],e['b']),(c['slug'],e['a'],e['b'],'connector crosses another node')
  e['pts']=pts
  if e['guard']:e['labelpos']=place_label(pts,e['guard'])
 im=Image.new('RGB',(W,H),'white');draw=ImageDraw.Draw(im);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>']
 def rect(box,fill='white',stroke='#374553',radius=0,width=2):
  x,y,xx,yy=box;svg.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>');draw.rounded_rectangle(box,radius,fill,stroke,width)
 def text(x,y,lines,size=26,bold=False):
  if isinstance(lines,str):lines=lines.split('\n')
  f=ImageFont.truetype(BOLD if bold else FONT,size)
  for j,line in enumerate(lines):
   yy=y+(j-(len(lines)-1)/2)*(size+5);svg.append(f'<text x="{x}" y="{yy}" text-anchor="middle" dominant-baseline="central" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="#182b3b">{html.escape(line)}</text>');draw.text((x,yy),line,font=f,fill='#182b3b',anchor='mm')
 def poly(pts,fill=None,color='#374553',width=2):
  if fill is not None:
   svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="{fill}" stroke="{color}" stroke-width="{width}"/>');draw.polygon(pts,fill=fill,outline=color,width=width)
  else:
   svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>');draw.line(pts,fill=color,width=width)
 def circle(x,y,r,fill,stroke='#17232d',width=2):
  svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>');draw.ellipse((x-r,y-r,x+r,y+r),fill=fill,outline=stroke,width=width)
 def arrow(a,b):
  dx,dy=a[0]-b[0],a[1]-b[1];le=math.hypot(dx,dy)
  if not le:return
  ux,uy=dx/le,dy/le;poly([a,(a[0]-ux*14-uy*6,a[1]-uy*14+ux*6),(a[0]-ux*14+uy*6,a[1]-uy*14-ux*6)],'#374553')
 text(W/2,66,'YuvrajMedical — UML Activity Diagram',42,True);text(W/2,122,c['title'],31,True)
 fills=['#f2f6fc','#f1f7f3','#faf5ed','#f6f1fa','#f1f7f8','#f9f5f0']
 for i,lane in enumerate(lanes):
  x=margin+i*laneW;rect((x,top,x+laneW,bottom),fills[i%len(fills)],'#a8b4bf',width=1);rect((x,top,x+laneW,top+62),fills[i%len(fills)],'#a8b4bf',width=1);text(x+laneW/2,top+31,LANES[lane],29,True)
 for e in edges:
  svg.append(f'<g class="flow" data-from="{e["a"]}" data-to="{e["b"]}"><title>{html.escape(e["guard"] or "Control flow")}</title>');poly(e['pts'],color='white',width=7);poly(e['pts']);arrow(e['pts'][-1],e['pts'][-2]);svg.append('</g>')
 for e in edges:
  if not e['guard']:continue
  x,y,_,box,_,_=e['labelpos'];rect(box,'white','white',radius=4);text(x,y,e['guard'],22,True)
 for ident,n in nodes.items():
  x,y,w,h=[n[k] for k in ['x','y','w','h']];cx,cy=x+w/2,y+h/2;kind=n['kind'];svg.append(f'<g class="node" data-id="{ident}" data-kind="{kind}" data-lane="{n["lane"]}"><title>{html.escape(n["label"] or kind)}</title>')
  if kind=='action':rect((x,y,x+w,y+h),'white','#374553',radius=18);text(cx,cy,styles[ident]['lines'],styles[ident]['size'])
  elif kind in ['decision','merge']:
   poly([(cx,y),(x+w,cy),(cx,y+h),(x,cy)],'#fffdf4');text(cx,cy,styles[ident]['lines'],styles[ident]['size'])
  elif kind=='start':circle(cx,cy,14,'#17232d')
  elif kind=='end':circle(cx,cy,18,'white',width=3);circle(cx,cy,10,'#17232d');text(cx,cy+39,n['label'],18)
  elif kind in ['fork','join']:rect((x,y,x+w,y+h),'#17232d','#17232d')
  svg.append('</g>')
 text(W/2,H-58,'Filled circle: start • Bullseye: end • Diamond: decision / merge • Black bar: fork / join • Arrows: control flow',22)
 if c['note']:text(W/2,H-25,textwrap.wrap(c['note'],max(100,int(W/14))),18)
 svg.append('</svg>');sv='\n'.join(svg);(O/(c['slug']+'.svg')).write_text(sv);im.save(O/(c['slug']+'.png'),dpi=(240,240));im.resize((1600,round(H*1600/W))).save(O/(c['slug']+'-preview.png'))
 if ci==0:im.save(O/'YuvrajMedical-Main-Activity.pdf',resolution=240.0,title='YuvrajMedical — Main Activity Diagram')
 pdf_pages.append(im);all_svg.append({'title':c['title'],'slug':c['slug'],'svg':sv,'note':c['note']})
 reports.append({'diagram':c['slug'],'start_nodes':len(starts),'end_nodes':len(ends),'actions':sum(n['kind']=='action' for n in nodes.values()),'decisions':sum(n['kind']=='decision' for n in nodes.values()),'forks':sum(n['kind']=='fork' for n in nodes.values()),'joins':sum(n['kind']=='join' for n in nodes.values()),'nodes':len(nodes),'edges':len(edges),'all_nodes_reachable':True,'all_decision_branches_labelled':True})
 print('Rendered',c['slug'],len(nodes),'nodes',flush=True)
pdf_pages[0].save(O/'YuvrajMedical-Activity-Complete.pdf',save_all=True,append_images=pdf_pages[1:],resolution=240.0,title='YuvrajMedical — Activity Diagrams, Main and Supporting Workflows',author='YuvrajMedical')
(O/'model.json').write_text(json.dumps(charts,indent=2));(O/'validation.json').write_text(json.dumps({'status':'passed','diagrams':reports},indent=2))
opts=''.join(f'<option value="{i}">{html.escape(v["title"])}</option>' for i,v in enumerate(all_svg))
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>YuvrajMedical — Activity Diagrams</title><style>body{margin:0;background:#f4f6f8;color:#182b3b;font:16px Arial}header{position:sticky;top:0;background:white;border-bottom:1px solid #c5d0d9;padding:14px 20px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;z-index:3}h1{font-size:20px;margin:0}select,button{padding:9px;border:1px solid #b7c6d1;border-radius:6px;background:white}main{padding:16px}svg{width:100%;height:auto;background:white}#note{padding:12px 20px;font-size:14px}</style></head><body><header><h1>YuvrajMedical · Activity Diagrams</h1><select id="views">'''+opts+'''</select><button onclick="zoom(1.2)">Zoom +</button><button onclick="zoom(1/1.2)">Zoom −</button><button onclick="document.querySelector('svg').style.width='100%'">Fit page</button></header><div id="note"></div><main></main><script>const views=DATA;const menu=document.querySelector('#views'),main=document.querySelector('main');function show(i){main.innerHTML=views[i].svg;document.querySelector('#note').textContent=views[i].note||'Follow the control-flow arrows. Decision branches are explicitly labelled.'}function zoom(s){let svg=document.querySelector('svg');svg.style.width=(svg.getBoundingClientRect().width*s)+'px'}menu.onchange=()=>show(Number(menu.value));show(0);</script></body></html>'''.replace('DATA',json.dumps(all_svg).replace('</','<\\/'))
(O/'YuvrajMedical-Activity-Interactive.html').write_text(page);Path('/tmp/yuvraj-activity.js').write_text(re.search(r'<script>(.*?)</script>',page,re.S).group(1))
print('COMPLETE',len(charts),'diagrams',flush=True)
