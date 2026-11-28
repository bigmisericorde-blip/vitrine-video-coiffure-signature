(()=>{'use strict';
const $=id=>document.getElementById(id),steps=['Consigne','Enregistrement','Relecture'],entries=[];
async function init(){
 let prises;try{const r=await fetch('config.json',{cache:'no-store'});if(!r.ok)throw Error();prises=(await r.json()).contrat.prises;if(!['S1','S2','S3','S4'].every(s=>prises[s]?.titre&&prises[s]?.guide&&prises[s]?.question))throw Error();}catch{throw Error("Configuration T3 indisponible.");}
 for(const [i,s] of ['S1','S2','S3','S4'].entries()){
  const c=prises[s],group=document.createElement('section');group.className='screen-group';const title=document.createElement('h2');title.textContent=`Prise ${i+1} · ${c.titre.toLowerCase()}`;group.append(title);const row=document.createElement('div');row.className='screen-row';
  for(const [j,step] of steps.entries()){
   const n=i*3+j+1,a=document.createElement('a'),rank=String(n).padStart(2,'0'),small=document.createElement('small');small.textContent=rank;a.append(small,document.createTextNode(step));a.href=`#${n}`;a.addEventListener('click',e=>{if(e.button||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();choose(n);if(matchMedia('(max-width:760px)').matches)$('apercu').scrollIntoView({block:'start'});});row.append(a);$('screenSelect').add(new Option(`${rank} · Prise ${i+1} : ${step}`,String(n)));entries.push({a,n,rank,url:`capture.html?ecran=${n}&v=t3-revision-30s-3`,label:`Écran ${n}/12 · Prise ${i+1} · ${step}`,copy:[c.guide,`De 2 à ${c.secondes} secondes, selon la durée disponible.`,c.question][j]});
  }group.append(row);$('screenList').append(group);
 }
 let current=0;const image=$('screenPreview');image.onerror=()=>{$('screenError').hidden=false;};image.onload=()=>{$('screenError').hidden=true;};
 function show(n){const e=entries[n-1]||entries[0];if(current===e.n)return;current=e.n;for(const x of entries){if(x.n===current)x.a.setAttribute('aria-current','true');else x.a.removeAttribute('aria-current');}$('screenLabel').textContent=e.label;$('screenText').textContent=e.copy;$('screenAlone').href=e.url;$('screenSelect').value=String(current);$('screenPrev').disabled=current===1;$('screenNext').disabled=current===12;image.alt=e.label;image.src=`livrables/12-ecrans/${e.rank}.webp?v=2`;}
 function choose(n){if(!entries[n-1])return;if(location.hash!==`#${n}`)history.pushState(null,'',`#${n}`);show(n);}const initial=()=>show(Number(location.hash.slice(1))||1);window.addEventListener('hashchange',initial);window.addEventListener('popstate',initial);$('screenPrev').onclick=()=>choose(current-1);$('screenNext').onclick=()=>choose(current+1);$('screenSelect').onchange=()=>choose(Number($('screenSelect').value));initial();document.documentElement.dataset.ready='yes';
}
init().catch(()=>{$('screenError').hidden=false;document.documentElement.dataset.ready='error';});})();
