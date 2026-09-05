from pathlib import Path
import json,shutil,xml.etree.ElementTree as ET,re
p=Path(__file__).parent
spec=json.loads((p/'validation.json').read_text())['level_1'];flows=spec['directed_flows'];pairs={(f['from'],f['to']) for f in flows};ps=set(spec['processes']);stores=set(spec['data_stores']);entities=set(spec['external_entities'])
requirements={
'1.0':{'rw':['users','auth_otps','otp_verifications','user_devices'],'w':['login_activity']},
'1.1':{'rw':['users','family_members','user_devices','notification_preferences']},
'2.0':{'r':['medicines','disease_categories']},
'3.0':{'rw':['cart','cart_saved_later','wishlist'],'r':['medicines','users']},
'4.0':{'rw':['prescription_requests'],'r':['users','staff']},
'5.0':{'rw':['orders','order_items'],'r':['cart','medicines','users','delivery_addresses']},
'6.0':{'rw':['payments','orders']},
'7.0':{'rw':['delivery_addresses'],'r':['delivery_areas','users']},
'8.0':{'rw':['medicine_subscriptions'],'r':['medicines','users']},
'9.0':{'rw':['notifications'],'r':['notification_preferences','users']},
'10.0':{'rw':['reviews_feedback'],'r':['medicines','users']},
'11.0':{'rw':['medicines','stock_movements'],'r':['staff']},
'12.0':{'rw':['referral_rewards'],'r':['users']}}
for proc,modes in requirements.items():
 for mode,ss in modes.items():
  for s in ss:
   if 'r' in mode:assert (s,proc) in pairs,(s,proc)
   if 'w' in mode:assert (proc,s) in pairs,(proc,s)
for proc in ['1.0','1.1','2.0','3.0','4.0','5.0','6.0','7.0','8.0','10.0','12.0']:
 assert ('Customer',proc) in pairs and (proc,'Customer') in pairs
for proc in ['1.0','4.0','5.0','11.0']:assert ('Staff',proc) in pairs and (proc,'Staff') in pairs
for proc in ['6.0','7.0','11.0']:assert ('5.0',proc) in pairs and (proc,'5.0') in pairs
for proc in ['4.0','5.0','6.0','8.0']:assert (proc,'9.0') in pairs
assert ('9.0','Customer') in pairs
assert len(flows)==len(pairs)==112
for f in flows:
 a,b=f['from'],f['to'];assert a in ps or b in ps;assert f['label'].strip()
 if 'Payment Gateway' in [a,b]:assert '6.0' in [a,b]
root=ET.parse(p/'dfd-level-1-compact.svg').getroot();ns={'s':'http://www.w3.org/2000/svg'}
nodes=[g for g in root.findall('s:g',ns) if g.get('class')=='node'];assert len(nodes)==40
assert {g.get('data-id') for g in nodes}==ps|stores|entities
edgegroups=[g for g in root.findall('s:g',ns) if g.get('class')=='flow' and g.find('s:title',ns) is not None]
actual=set()
for g in edgegroups:
 a,b=g.get('data-a'),g.get('data-b');assert g.find('s:title',ns).text
 heads=g.findall('s:polygon',ns);actual.add((a,b))
 if len(heads)==2:actual.add((b,a))
assert actual==pairs
for ext in ['svg','png']:shutil.copyfile(p/f'dfd-level-1-compact.{ext}',p/f'dfd-level-1.{ext}')
shutil.copyfile(p/'compact-preview.png',p/'dfd-level-1-preview.png')
page=(p/'dfd-level-1-interactive.html').read_text()
page=page.replace('</style>','aside{display:none;position:fixed;right:18px;top:90px;bottom:20px;width:340px;overflow:auto;background:white;border:1px solid #bdccd8;border-radius:10px;padding:18px;box-shadow:0 4px 24px #0002;z-index:4}aside h2{font-size:18px}aside li{margin:0 0 18px;line-height:1.45;font-size:14px}aside small{display:block;color:#456}</style>')
page=page.replace('<div id="diagram">','<aside id="details"></aside><div id="diagram">')
data=json.dumps(flows);names=json.dumps(spec['processes'])
script='''<script>
const allFlows=DATA, processNames=NAMES, panel=document.querySelector('#details');
function nameOf(id){return processNames[id]?id+' '+processNames[id]:id}
root.querySelectorAll('.node').forEach(n=>n.addEventListener('click',()=>{
 panel.replaceChildren();let h=document.createElement('h2');h.textContent=nameOf(n.dataset.id);panel.append(h);
 let ul=document.createElement('ul');allFlows.filter(f=>f.from===n.dataset.id||f.to===n.dataset.id).forEach(f=>{let li=document.createElement('li'),b=document.createElement('b'),s=document.createElement('small');b.textContent=nameOf(f.from)+' → '+nameOf(f.to);s.textContent=f.label;li.append(b,s);ul.append(li)});panel.append(ul);panel.style.display='block';
}));document.querySelector('button').addEventListener('click',()=>{panel.style.display='none'});
</script>'''.replace('DATA',data).replace('NAMES',names)
page=page.replace('</body>',script+'</body>');(p/'dfd-level-1-interactive.html').write_text(page)
Path('/tmp/yuvraj-dfd-final.js').write_text('\n'.join(re.findall(r'<script>(.*?)</script>',page,re.S)))
report={'status':'passed','required_store_directions':'all present','required_external_and_internal_flows':'all present','rendered_svg_directional_flows':len(actual),'processes':len(ps),'data_stores':len(stores),'external_entities':len(entities),'gateway':'only connects to 6.0','prohibited_connections':0,'duplicate_nodes':0}
(p/'final-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
