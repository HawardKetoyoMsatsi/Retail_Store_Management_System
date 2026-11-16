const $=id=>document.getElementById(id);
const K=n=>(Number(n)||0).toLocaleString('en-KE',{maximumFractionDigits:2});
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let TODAY='',ITEMS=[],STOCK={name:'Sunday',js:0,def:''};

async function api(path,method='GET',body){
  const r=await fetch(path,{method,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});
  const j=await r.json(); if(!r.ok) throw new Error(j.error||'Something went wrong'); return j;
}
function ok(id,t){const e=$(id);e.style.color='#188038';e.textContent='✓ '+t}
function bad(id){return e=>{const x=$(id);x.style.color='#d93025';x.textContent='⚠ '+e.message}}
function table(heads,rows){
  if(!rows.length) return '<p class="muted">Nothing recorded yet.</p>';
  return '<table><tr>'+heads.map(h=>'<th>'+h+'</th>').join('')+'</tr>'+
   rows.map(r=>'<tr>'+r.map((c,i)=>'<td>'+(typeof c==='number'?K(c):c)+'</td>').join('')+'</tr>').join('')+'</table>';
}

/* tabs */
function openTab(name){
  document.querySelectorAll('#nav button').forEach(x=>x.classList.toggle('active',x.dataset.tab===name));
  ['dash','items','buy','daily','stock'].forEach(t=>$(t).classList.toggle('hide',t!==name));
  ({dash:loadDash,items:loadItems,buy:loadBuy,daily:loadDay,stock:loadStock})[name]();
}
document.querySelectorAll('#nav button').forEach(b=>b.onclick=()=>openTab(b.dataset.tab));

/* items list (catalog) */
async function loadItems(){
  const rows=await api('/api/catalog');
  $('itemCount').textContent=rows.length?'· '+rows.length:'';
  if(!rows.length){$('itemList2').innerHTML='<p class="muted">No items yet. Add your first one above.</p>';return}
  $('itemList2').innerHTML='<table><tr><th>Item</th><th>Usual buy</th><th>Usual sell</th><th>Purchases</th><th></th></tr>'+
    rows.map(r=>`<tr><td><input id="cn${r.id}" value="${esc(r.name)}" maxlength="80"></td>`+
     `<td><input type="number" step="any" min="0" id="cb${r.id}" value="${r.buy}" style="width:90px"></td>`+
     `<td><input type="number" step="any" min="0" id="cs${r.id}" value="${r.sell}" style="width:90px"></td>`+
     `<td>${r.used}</td><td style="white-space:nowrap"><button class="link" onclick="saveItem(${r.id})">Save</button> `+
     `<button class="x" title="${r.used?'Has purchase records, cannot be deleted':'Delete'}" onclick="removeItem(${r.id})">🗑</button></td></tr>`).join('')+'</table>';
}
async function addItem(){
  try{
    const r=await api('/api/catalog','POST',{name:$('niName').value,buy:$('niBuy').value,sell:$('niSell').value});
    $('niName').value='';$('niBuy').value='';$('niSell').value='';
    await loadItems();ok('itemMsg',`'${r.added}' added`);$('niName').focus();
  }catch(e){bad('itemMsg')(e)}
}
async function saveItem(id){
  try{
    const r=await api('/api/catalog/update','POST',{id,name:$('cn'+id).value,buy:$('cb'+id).value,sell:$('cs'+id).value});
    await loadItems();ok('itemMsg',`'${r.updated}' saved`);
  }catch(e){bad('itemMsg')(e)}
}
async function removeItem(id){
  if(!confirm('Delete this item from your list?')) return;
  try{await api('/api/catalog/'+id,'DELETE');await loadItems();ok('itemMsg','Item deleted')}catch(e){bad('itemMsg')(e)}
}

/* charts (plain SVG, no libraries) */
function barChart(labels,series){
  if(!labels.length) return '<p class="muted">No data yet.</p>';
  const W=460,H=190,L=44,B=24,T=8,R=6, pw=W-L-R, ph=H-T-B;
  const max=Math.max(1,...series.flatMap(s=>s.values));
  const gw=pw/labels.length, bw=Math.min(22,(gw-6)/series.length);
  let g='';
  for(let i=0;i<=4;i++){const y=T+ph-ph*i/4;g+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" stroke="#eee"/><text x="${L-4}" y="${y+3}" text-anchor="end">${K(Math.round(max*i/4))}</text>`}
  labels.forEach((lb,i)=>{
    series.forEach((s,j)=>{
      const h=ph*s.values[i]/max, x=L+i*gw+(gw-bw*series.length)/2+j*bw;
      g+=`<rect x="${x}" y="${T+ph-h}" width="${bw-1}" height="${h}" rx="2" fill="${s.color}"><title>${esc(lb)} · ${esc(s.name)}: ${K(s.values[i])}</title></rect>`});
    g+=`<text x="${L+i*gw+gw/2}" y="${H-8}" text-anchor="middle">${esc(lb.slice(5))}</text>`});
  const lg='<div class="legend">'+series.map(s=>`<span><i style="background:${s.color}"></i>${esc(s.name)}</span>`).join('')+'</div>';
  return lg+`<svg viewBox="0 0 ${W} ${H}" width="100%">${g}</svg>`;
}

/* balance check panel */
function recHtml(r){
  let banner;
  if(!r.stock_taken) banner=`<div class="banner warn">No stock take recorded for ${r.date} yet.</div>`;
  else if(r.balanced) banner='<div class="banner ok">✓ Balanced. Stock + sales money equals the selling value of goods bought.</div>';
  else banner=`<div class="banner bad">${r.difference<0?'⚠ Short by KES '+K(-r.difference):'⚠ Over by KES '+K(r.difference)} — check counts, prices, or missing daily records.</div>`;
  const s=(l,v,c)=>`<div class="stat">${l}<b${c?` style="color:${c}"`:''}>${K(v)}</b></div>`;
  return banner+'<div class="grid">'+
   s('Selling value of goods bought',r.total_selling)+s('Stock value (at selling price)',r.stock_value)+
   s('Money available'+(r.available_as_of?' ('+r.available_as_of+')':''),r.available)+
   s('Used to buy goods (total)',r.spent)+s('Drawn from business (total)',r.drawn)+s('Opening capital',r.capital)+
   s('Sales money',r.sales_money)+s('Stock + sales money',r.accounted)+
   s('Difference',r.difference,r.balanced?'#188038':'#d93025')+'</div>'+
   '<p class="muted">Sales money = money available + money used to buy goods + money drawn − opening capital.</p>';
}

/* dashboard */
async function loadDash(){
  const d=await api('/api/dashboard');
  const sb=$('stockBanner'), ss=d.stock_status;
  sb.className='banner '+({done:'ok',due:'warn',overdue:'bad',none:'warn',upcoming:'warn'}[ss.state]||'warn');
  sb.textContent=ss.message;
  $('recDate').textContent=d.last_stocktake?'· stock take of '+d.last_stocktake:'';
  $('dashRec').innerHTML=recHtml(d.rec);
  const mn=d.money_now, gp=d.all_selling-d.all_cost;
  const k=(l,v)=>`<div class="stat">${l}<b>${v}</b></div>`;
  $('kpis').innerHTML=k('Money now'+(mn?' ('+mn.date+')':''),'KES '+K(mn?mn.total:0))+
    k('Cash / Pochi / M-Pesa',mn?K(mn.cash)+' / '+K(mn.pochi)+' / '+K(mn.mpesa):'—')+
    k('Items stocked',d.item_count)+k('Total stock bought (cost)','KES '+K(d.all_cost))+k('Expected gross profit','KES '+K(gp));
  $('chMoney').innerHTML=barChart(d.money_trend.map(x=>x.date),[
    {name:'Total available',color:'#1a73e8',values:d.money_trend.map(x=>x.total)}]);
  $('chBuy').innerHTML=barChart(d.buy_trend.map(x=>x.date),[
    {name:'Cost',color:'#e8710a',values:d.buy_trend.map(x=>x.cost)},
    {name:'Selling value',color:'#188038',values:d.buy_trend.map(x=>x.sell_value)}]);
  $('dashStock').innerHTML=table(['Item','Counted','Price','Value'],d.stock_rows.map(x=>[esc(x.item),x.qty,x.price,x.value]));
  $('dashDaily').innerHTML=table(['Date','Total','Bought goods','Drawn'],d.recent_daily.map(x=>[x.date,x.total,x.spent,x.drawn]));
  $('dashBuy').innerHTML=table(['Date','Item','Qty','Cost'],d.recent_purchases.map(x=>[x.date,esc(x.item),x.qty,x.cost]));
  $('capital').value=d.rec.capital;
}
async function saveCapital(){
  try{await api('/api/capital','POST',{capital:$('capital').value});ok('capMsg','Saved');loadDash()}catch(e){bad('capMsg')(e)}
}

/* purchases */
function itemOptions(selected){
  return '<option value="">Select item…</option>'+ITEMS.map(i=>`<option value="${esc(i.item)}"${i.item===selected?' selected':''}>${esc(i.item)}</option>`).join('');
}
function addRow(){
  const d=document.createElement('div');d.className='prow';
  d.innerHTML='<select>'+itemOptions('')+'</select><input type="number" step="any" min="0" placeholder="Buy">'+
   '<input type="number" step="any" min="0" placeholder="Sell"><input type="number" step="any" min="0" placeholder="Qty">'+
   '<button class="x" title="Remove row" onclick="this.parentNode.remove()">×</button>';
  d.querySelector('select').onchange=e=>{ /* fill in the usual prices for the chosen item */
    const it=ITEMS.find(i=>i.item===e.target.value), n=d.querySelectorAll('input');
    if(it){n[0].value=it.buy;n[1].value=it.sell}
  };
  $('buyRows').appendChild(d);
}
async function loadBuy(){
  if(!$('buyDate').value) $('buyDate').value=TODAY;
  ITEMS=await api('/api/items');
  $('buyEmpty').classList.toggle('hide',ITEMS.length>0);
  if(!$('buyRows').children.length) addRow();
  document.querySelectorAll('#buyRows select').forEach(s=>{const v=s.value;s.innerHTML=itemOptions(v)}); /* pick up new items */
  const rows=await api('/api/purchases');
  $('buyList').innerHTML=table(['Date','Item','Buy','Sell','Qty','Total cost','Selling value',''],
    rows.map(x=>[x.date,esc(x.item),x.buy,x.sell,x.qty,x.cost,x.sell_value,
      `<button class="x" title="Delete" onclick="delPurchase(${x.id})">🗑</button>`]));
}
async function delPurchase(id){
  if(!confirm('Delete this purchase record?')) return;
  await api('/api/purchases/'+id,'DELETE'); loadBuy();
}
async function savePurchases(){
  const items=[...$('buyRows').querySelectorAll('.prow')].map(r=>{const i=r.querySelectorAll('input');
    return {item:r.querySelector('select').value,buy:i[0].value,sell:i[1].value,qty:i[2].value}});
  try{
    const r=await api('/api/purchases','POST',{date:$('buyDate').value,items});
    $('buyRows').innerHTML='';addRow();await loadBuy();
    ok('buyMsg',`${r.saved} item(s) saved. Total cost KES ${K(r.total_cost)}`);
  }catch(e){bad('buyMsg')(e)}
}

/* daily */
async function fillDay(){
  const d=await api('/api/daily?date='+$('dayDate').value);
  $('dCash').value=d.cash;$('dPochi').value=d.pochi;$('dMpesa').value=d.mpesa;$('dSpent').value=d.spent;$('dDrawn').value=d.drawn;
  $('dayMsg').style.color='#5f6368';
  $('dayMsg').textContent=d.exists?'Editing the existing record for this date.':'“Money used to buy goods” is pre-filled from your purchases on this date.';
  updTotal();
}
function updTotal(){
  const t=(+$('dCash').value||0)+(+$('dPochi').value||0)+(+$('dMpesa').value||0);
  $('dayTotal').textContent='Total money available: KES '+K(t);
}
['dCash','dPochi','dMpesa'].forEach(id=>$(id).addEventListener('input',updTotal));
$('dayDate').addEventListener('change',fillDay);
async function loadDay(){
  if(!$('dayDate').value) $('dayDate').value=TODAY;
  fillDay();
  const rows=await api('/api/dailies');
  $('dayList').innerHTML=table(['Date','Cash','Pochi','M-Pesa','Total','Bought goods','Drawn'],
    rows.map(x=>[x.date,x.cash,x.pochi,x.mpesa,x.total,x.spent,x.drawn]));
}
async function saveDaily(){
  try{
    const r=await api('/api/daily','POST',{date:$('dayDate').value,cash:$('dCash').value,pochi:$('dPochi').value,
      mpesa:$('dMpesa').value,spent:$('dSpent').value,drawn:$('dDrawn').value});
    await loadDay();ok('dayMsg',(r.updated?'Updated':'Saved')+'. Total available KES '+K(r.total));
  }catch(e){bad('dayMsg')(e)}
}

/* stock take */
/* stock is counted on one day a week (Sunday); other dates snap back to the latest one */
function snapToStockDay(v){
  const d=new Date(v+'T00:00:00');
  d.setDate(d.getDate()-((d.getDay()-STOCK.js+7)%7));
  const p=n=>String(n).padStart(2,'0');
  return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());
}
async function fillCounts(){
  const info=$('stockInfo'), want=$('stDate').value;
  const snapped=snapToStockDay(want);
  if(snapped!==want){
    $('stDate').value=snapped;
    info.className='banner warn';info.textContent=`Stock take is done on ${STOCK.name}s only. Moved to ${STOCK.name} ${snapped}.`;
  }else if(snapped===STOCK.def){info.className='banner hide';info.textContent=''}
  const r=await api('/api/stocktake?date='+$('stDate').value);
  ITEMS.forEach((i,n)=>{const el=$('cnt'+n);if(el) el.value=r.exists&&(i.item.toLowerCase() in r.counts)?r.counts[i.item.toLowerCase()]:''});
  if(r.exists&&info.className.includes('hide')){info.className='banner ok';info.textContent='A stock take for this day is already saved. Saving again replaces it.'}
}
async function loadStock(){
  $('stLabel').textContent=`Stock take date (${STOCK.name}s only)`;
  $('stDate').max=TODAY;
  if(!$('stDate').value) $('stDate').value=STOCK.def;
  ITEMS=await api('/api/items');
  if(!ITEMS.length){$('stockRows').innerHTML='<p class="muted">Add the items you sell on the Items tab first.</p>';return}
  $('stockRows').innerHTML='<table><tr><th>Item</th><th>Total bought</th><th>Selling price</th><th>Counted qty</th></tr>'+
    ITEMS.map((i,n)=>`<tr><td>${esc(i.item)}</td><td>${K(i.bought)}</td><td>${K(i.sell)}</td>`+
      `<td><input type="number" step="any" min="0" id="cnt${n}" style="width:90px"></td></tr>`).join('')+'</table>';
  $('stockInfo').className='banner hide';
  fillCounts();
}
$('stDate').addEventListener('change',()=>{$('stockInfo').className='banner hide';if(ITEMS.length) fillCounts()});
async function saveStock(){
  const counts=ITEMS.map((i,n)=>({item:i.item,qty:$('cnt'+n).value||0}));
  try{
    const r=await api('/api/stocktake','POST',{date:$('stDate').value,counts});
    ok('stockMsg','Stock take saved.');$('recCard').classList.remove('hide');$('stockRec').innerHTML=recHtml(r);
  }catch(e){bad('stockMsg')(e)}
}

/* start */
(async()=>{
  const i=await api('/api/init');TODAY=i.today;
  STOCK={name:i.stock_day_name,js:i.stock_day_js,def:i.default_stock_date};
  $('todayLbl').textContent=new Date().toLocaleDateString('en-KE',{weekday:'long',day:'numeric',month:'long',year:'numeric'});
  loadDash();
})();
