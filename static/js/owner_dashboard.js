'use strict';
(() => {
  const data = JSON.parse(document.getElementById('ownerData').textContent);
  const $ = id => document.getElementById(id);
  const currency = value => new Intl.NumberFormat('en-IN', {style:'currency',currency:'INR'}).format(Number(value));
  const sidebar = $('sidebar');
  function closeSidebar() { sidebar.classList.remove('open'); $('sidebarScrim').hidden = true; $('menuToggle').setAttribute('aria-expanded','false'); }
  $('menuToggle').addEventListener('click', () => { const open = sidebar.classList.toggle('open'); $('sidebarScrim').hidden = !open; $('menuToggle').setAttribute('aria-expanded',String(open)); });
  $('sidebarScrim').addEventListener('click',closeSidebar);
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeSidebar(); });
  function navigate() {
    const links = [...document.querySelectorAll('[data-nav]')];
    const section = links.some(link => '#'+link.dataset.nav === location.hash) ? location.hash.slice(1) : 'dashboard';
    document.querySelectorAll('.owner-section').forEach(node => { node.hidden = node.id !== section; });
    links.forEach(link => { const active = link.dataset.nav === section; link.classList.toggle('active',active); if(active) { link.setAttribute('aria-current','page'); $('pageTitle').textContent = link.childNodes[1].textContent.trim(); } else link.removeAttribute('aria-current'); });
    closeSidebar(); window.scrollTo(0,0);
  }
  window.addEventListener('hashchange',navigate); navigate();
  const colors = ['#087f8c','#50b7ae','#efb65a','#7f9dce','#d8757a','#aac5cc','#8475af','#8caf77'];
  const charts = {};
  function chart(id,type,labels,values,compare) {
    if (!window.Chart) { const message = document.createElement('p'); message.className='empty-state'; message.textContent='Chart could not load. Please refresh; recorded totals remain available.'; $(id).replaceWith(message); return; }
    const datasets = [{label:type==='line'?'Verified revenue':'Recorded total',data:values.map(Number),borderColor:colors[0],backgroundColor:type==='line'?'rgba(8,127,140,.08)':colors,fill:type==='line',tension:.3,borderWidth:type==='line'?2:0,pointRadius:type==='line'?2:0}];
    if(compare) datasets.push({label:'Previous period',data:compare.map(Number),borderColor:'#adc0cd',borderDash:[4,4],pointRadius:0,borderWidth:2,tension:.3});
    charts[id] = new Chart($(id),{type,data:{labels,datasets},options:{responsive:true,maintainAspectRatio:false,animation:!matchMedia('(prefers-reduced-motion: reduce)').matches,plugins:{legend:{display:!!compare,position:'bottom',labels:{boxWidth:10,font:{size:10}}},tooltip:{callbacks:{label: context => type==='line'||id==='paymentChart' ? context.dataset.label+': '+currency(context.parsed.y ?? context.parsed) : context.label+': '+context.formattedValue}}},...(type==='doughnut'?{cutout:'74%'}:{scales:{x:{grid:{display:false},ticks:{maxTicksLimit:7,maxRotation:0,font:{size:9},color:'#82939b'}},y:{beginAtZero:true,grid:{color:'#edf2f4'},ticks:{precision:0,font:{size:9},color:'#82939b'}}}})}});
  }
  const daily=data.revenue.charts.daily;
  chart('overviewRevenue','line',daily.labels,daily.values);
  chart('analyticsRevenue','line',daily.labels,daily.values,daily.previous_values);
  $('overviewRevenueEmpty').hidden=daily.values.some(Number); $('analyticsRevenueEmpty').hidden=daily.values.some(Number);
  chart('statusChart','doughnut',data.statuses.map(x=>x.label),data.statuses.map(x=>x.value));
  chart('categoryChart','bar',data.categories.map(x=>x.label),data.categories.map(x=>x.value));
  chart('paymentChart','doughnut',data.payments.map(x=>x.label),data.payments.map(x=>x.value));
  function updateChartTheme() {
    const dark = document.documentElement.dataset.theme === 'dark';
    const text = dark ? '#b8cbd5' : '#657985';
    for (const instance of Object.values(charts)) {
      instance.options.plugins.legend.labels.color = text;
      for (const scale of Object.values(instance.options.scales || {})) {
        scale.ticks.color = text;
        scale.grid.color = dark ? '#304653' : '#edf2f4';
        scale.border = {...scale.border, color: dark ? '#304653' : '#e1e9ed'};
      }
      instance.update('none');
    }
  }
  window.addEventListener('owner-theme-change', updateChartTheme);
  updateChartTheme();
  $('revenuePeriod').addEventListener('change',()=>{ for(const id of ['revenueStart','revenueEnd']) { $(id).disabled=$('revenuePeriod').value!=='custom'; $(id).required=!$(id).disabled; } });
  $('revenueFilter').addEventListener('submit',async event=>{
    event.preventDefault(); const button=event.target.querySelector('button'); button.disabled=true; $('revenueError').hidden=true;
    try { const response=await fetch('/api/owner/revenue?'+new URLSearchParams(new FormData(event.target)),{headers:{Accept:'application/json'}}); const result=await response.json(); if(!response.ok) throw new Error(result.error||'Revenue could not be loaded.');
      const next=result.charts.daily, target=charts.analyticsRevenue;
      if(target) { target.data.labels=next.labels; target.data.datasets[0].data=next.values; target.data.datasets[1].data=next.previous_values; target.update(); }
      $('revenueTotal').textContent=currency(result.selected_period.current); $('revenueRange').textContent=result.range.start+' to '+result.range.end; $('analyticsRevenueEmpty').hidden=next.values.some(Number);
      $('revenueComparison').textContent='Previous period: '+currency(result.selected_period.previous)+(result.selected_period.growth_percentage===null?' · No percentage comparison available.':' · Change: '+result.selected_period.growth_percentage+'%');
    } catch(error) { $('revenueError').textContent=error.message; $('revenueError').hidden=false; } finally { button.disabled=false; }
  });
  document.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
  document.querySelectorAll('dialog').forEach(dialog=>dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}}));
  document.querySelectorAll('[data-order]').forEach(button=>button.addEventListener('click',()=>{const order=JSON.parse(button.dataset.order);$('orderForm').action='/update_order_status/'+order.id;$('orderForm').elements.status.value=order.status;$('orderForm').elements.delivery_otp.value='';$('orderTitle').textContent='Update order #'+order.id;$('orderDialog').showModal();}));
  document.querySelectorAll('[data-edit-medicine]').forEach(button=>button.addEventListener('click',()=>{const medicine=JSON.parse(button.dataset.editMedicine),form=$('medicineForm');form.reset();form.action='/owner/inventory/'+medicine.id+'/update';for(const input of form.elements){if(input.name&&input.name!=='owner_csrf'){const key=input.name==='expiry'?'expiry_date':input.name;input.value=medicine[key]??'';}}$('medicineTitle').textContent='Edit '+(medicine.name||'medicine');$('medicineDialog').showModal();}));
  document.querySelectorAll('[data-adjust-id]').forEach(button=>button.addEventListener('click',()=>{$('adjustForm').reset();$('adjustForm').action='/owner/inventory/'+button.dataset.adjustId+'/adjust';$('adjustTitle').textContent='Adjust '+button.dataset.name;$('adjustDialog').showModal();}));
  document.querySelectorAll('[data-confirm]').forEach(form=>form.addEventListener('submit',event=>{if(!window.confirm(form.dataset.confirm))event.preventDefault();}));
  function reportKind() {
    const kind=$('reportKind').value, snapshot=['users','inventory'].includes(kind), prescription=kind==='prescriptions';
    $('reportForm').action='/owner/reports/'+kind;
    for(const id of ['reportFrom','reportTo']) $(id).disabled=snapshot;
    $('reportPayment').disabled=snapshot||prescription; $('reportStatus').disabled=snapshot;
    $('reportStatus').replaceChildren(new Option('All statuses',''),...(prescription?['Pending Review','Approved','Rejected']:data.orderStatuses).map(status=>new Option(status,status)));
    $('reportHint').textContent=snapshot?'Current snapshot. Date filters are unavailable for this report.':prescription?'Dates filter prescription submission time. Leave blank for all records.':'Dates filter order creation time. Leave blank for all records.';
  }
  $('reportKind').addEventListener('change',reportKind); reportKind();
})();
