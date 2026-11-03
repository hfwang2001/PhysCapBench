'use strict';
const $=s=>document.querySelector(s);
const dimensions=[['Event coverage','#2563eb'],['Objects and roles','#f97316'],['Actions and motion','#16a34a'],['Contact and interaction','#7c3aed'],['States and outcomes','#e11d48'],['Physical mechanisms and causality','#0f766e'],['Temporal order','#64748b']];
function toast(s){$('#toast').textContent=s;$('#toast').style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').style.display='none',3000)}
let data=[], datasets={}, activeDomain='ego';
const domainNames={ego:'Egocentric',third:'Third-person',umi:'Handheld grippers'};
const domainFiles={ego:'egocentric',third:'third-person'};
const medal=n=>n<=3?['🥇','🥈','🥉'][n-1]:'';
const rank=(value,key)=>1+data.filter(row=>(key==='overall'?row.overall:row.scores[key])>value).length;
function scoreCell(value,n,overall=false){return `<td class="metric-cell${overall?' overall-cell':''}" data-metric-rank="${n}"><div class="cell-score"><span class="cell-rank rank-${n}" aria-label="Rank ${n}">${medal(n)?`<span class="cell-medal" aria-hidden="true">${medal(n)}</span>`:''}#${n}</span><span class="score-value">${value.toFixed(2)}</span></div></td>`}
function render(){
$('#table-head').innerHTML='<tr><th scope="col" class="model-col">Model</th><th scope="col" class="rank-col">#</th><th scope="col" class="metric-header" style="--accent:#a16207" title="Overall mean over per-video scores">PhysCapBench<br>Score</th>'+dimensions.map(([n,c])=>`<th scope="col" class="metric-header" style="--accent:${c}">${n}</th>`).join('')+'</tr>';
$('#table-body').innerHTML='<tr id="top-group" class="range-row"><th scope="row" class="model-col">Top '+data.length+'</th><td class="rank-col"></td><td colspan="8"></td></tr>'+data.map((r,i)=>{const n=rank(r.overall,'overall');return `<tr id="strategy-${i}" data-name="${r.name}"><th scope="row" class="model-col">${r.name}</th><td class="rank-col"><span class="rank-badge" aria-label="Overall rank ${n}">${medal(n)?`<span class="row-medal" aria-hidden="true">${medal(n)}</span>`:n}</span></td>${scoreCell(r.overall,n,true)}${r.scores.map((v,j)=>scoreCell(v,rank(v,j))).join('')}</tr>`}).join('');
$('#board-count').textContent=`Reported strategies: ${data.length}`;
$('#rank-menu summary').textContent=`Top ${data.length}`;
$('#jump-top').textContent=`Top ${data.length} · All results`;
$('.reference-table caption').textContent=`${domainNames[activeDomain]} captioning results. Fixed overall ranking with per-dimension ranks; higher scores are better.`;
$('.board-footnote').textContent=`${domainNames[activeDomain]} captioning strategies evaluated against shared references. Overall scores are reported per-video averages, not the mean of the displayed dimension averages. Equal scores share the same rank.`+(activeDomain==='third'?' LingBot strategies are reconstructed from the paper description.':'');
$('#model-names').innerHTML=data.map(r=>`<option value="${r.name}"></option>`).join('');
$('#result-count').textContent=`${data.length} strategies · ${domainNames[activeDomain]} · Ranked by overall score`;
}
function clearHighlight(){document.querySelectorAll('[data-highlighted]').forEach(r=>r.removeAttribute('data-highlighted'))}
$('#locator').onsubmit=e=>{e.preventDefault();clearHighlight();const query=$('#search').value.trim().toLowerCase();if(!query){$('#locator-status').textContent='Enter a model or strategy name to locate it.';return}let i=data.findIndex(r=>r.name.toLowerCase()===query);if(i<0)i=data.findIndex(r=>r.name.toLowerCase().includes(query));if(i<0){$('#locator-status').textContent=`No matching strategy. All ${data.length} results remain displayed.`;return}const row=$(`#strategy-${i}`);row.dataset.highlighted='true';row.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'nearest',inline:'nearest'});$('#locator-status').textContent=`Located ${data[i].name} · Overall rank #${rank(data[i].overall,'overall')}.`};
$('#search').oninput=()=>{clearHighlight();$('#locator-status').textContent=''};
$('#jump-top').onclick=()=>{$('#rank-menu').open=false;$('#top-group').scrollIntoView({block:'nearest',inline:'nearest',behavior:'smooth'});clearHighlight();$('#search').value='';$('#locator-status').textContent=`Showing all ${data.length} strategies in overall rank order.`};
function switchDomain(domain){
 activeDomain=domain;
 for(const b of document.querySelectorAll('[data-board]')){const current=b.dataset.board===domain;b.classList.toggle('active',current);b.setAttribute('aria-pressed',String(current))}
 $('#results-board').hidden=domain==='umi';$('#umi-board').hidden=domain!=='umi';
 $('#search').value='';$('#locator-status').textContent='';$('#rank-menu').open=false;clearHighlight();
 if(domain==='umi'){$('#board-count').textContent='Results pending';return}
 data=datasets[domain]||[];render();$('.table-scroll').scrollTop=0;$('.table-scroll').scrollLeft=0;
}
for(const b of document.querySelectorAll('[data-board]'))b.onclick=()=>switchDomain(b.dataset.board);
$('#csv').onclick=()=>{const lines=[['Rank','Strategy','Overall',...dimensions.map(d=>d[0])],...data.map(r=>[rank(r.overall,'overall'),r.name,r.overall,...r.scores])];const content=lines.map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n');const u=URL.createObjectURL(new Blob([content],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=u;a.download=`physcapbench-${domainFiles[activeDomain]}-results.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);toast(`Exported all ${data.length} ${domainNames[activeDomain].toLowerCase()} strategies.`)};
fetch('results.json').then(async response=>{
 if(!response.ok)throw Error('Results unavailable');
 const snapshot=await response.json();
 const keys=Object.keys(snapshot.dimension_labels);
 for(const domain of ['ego','third'])datasets[domain]=snapshot.domains[domain].results.map(row=>({name:row.strategy,overall:row.overall,scores:keys.map(key=>row.dimensions[key])})).sort((a,b)=>b.overall-a.overall);
 switchDomain(activeDomain);
}).catch(()=>{$('#locator-status').textContent='Results could not be loaded. Please refresh to retry.'});
