(()=>{'use strict';
const $=id=>document.getElementById(id),steps=['Consigne','Enregistrement','Relecture'],entries=[];
let loadSerial=0,current=0,configFailed=false;
function charger(url){
 const serial=++loadSerial,frame=$('screenLive');$('screenStatus').hidden=false;$('screenStatus').textContent='Chargement de cet écran…';$('screenRetry').hidden=true;frame.hidden=false;frame.src=url;
 const limit=Date.now()+25000;
 function verifier(){
  if(serial!==loadSerial)return;
  try{
   const d=frame.contentDocument,search=frame.contentWindow.location.search,expected=new URL(url,location.href).search;
   if(search===expected && d?.documentElement?.dataset.ready==='yes'){$('screenStatus').hidden=true;return;}
   if(search===expected && d?.documentElement?.dataset.ready==='error')throw Error('Chargement impossible');
  }catch(e){if(Date.now()+200<limit && e.name==='SecurityError'){}else if(e.message==='Chargement impossible'){fin();return;}}
  if(Date.now()>=limit){fin();return;}setTimeout(verifier,250);
 }
 function fin(){if(serial!==loadSerial)return;$('screenStatus').textContent='Cet écran ne s’est pas chargé. Réessaie ou ouvre-le en grand avec le lien ci-dessus.';$('screenRetry').hidden=false;}
 setTimeout(verifier,100);
}
$('screenRetry').onclick=()=>{if(configFailed){location.reload();return;}const e=entries[current-1];if(e)charger(e.url);};
fetch('config.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(({contrat})=>{
 for(const [i,s] of ['S1','S2','S3','S4'].entries()){
  const c=contrat.prises[s],group=document.createElement('section');group.className='screen-group';const title=document.createElement('h2');title.textContent=`Prise ${i+1} · ${c.titre.toLowerCase()}`;group.append(title);const row=document.createElement('div');row.className='screen-row';
  for(const [j,step] of steps.entries()){
   const n=i*3+j+1,a=document.createElement('a'),rank=String(n).padStart(2,'0'),small=document.createElement('small');small.textContent=rank;a.append(small,document.createTextNode(step));a.href=`#${n}`;a.addEventListener('click',e=>{if(e.button||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();choose(n);if(matchMedia('(max-width:760px)').matches)$('apercu').scrollIntoView({block:'start'});});row.append(a);$('screenSelect').add(new Option(`${rank} · Prise ${i+1} : ${step}`,String(n)));entries.push({a,n,url:`capture.html?ecran=${n}&v=t3-lisible-1`,label:`Écran ${n}/12 · Prise ${i+1} · ${step}`,copy:[c.guide,`Durée minimale : ${c.secondes} secondes.`,c.question][j]});
  }group.append(row);$('screenList').append(group);
 }
 function show(n){const e=entries[n-1]||entries[0];if(current===e.n)return;current=e.n;for(const x of entries){if(x.n===current)x.a.setAttribute('aria-current','true');else x.a.removeAttribute('aria-current');}$('screenLabel').textContent=e.label;$('screenText').textContent=e.copy;$('screenAlone').href=e.url;$('screenSelect').value=String(current);$('screenPrev').disabled=current===1;$('screenNext').disabled=current===12;charger(e.url);}
 function choose(n){if(!entries[n-1])return;history.pushState(null,'',`#${n}`);show(n);}const initial=()=>show(Number(location.hash.slice(1))||1);window.addEventListener('hashchange',initial);window.addEventListener('popstate',initial);$('screenPrev').onclick=()=>choose(current-1);$('screenNext').onclick=()=>choose(current+1);$('screenSelect').onchange=()=>choose(Number($('screenSelect').value));initial();document.documentElement.dataset.ready='yes';
}).catch(()=>{configFailed=true;$('screenStatus').textContent='Impossible de charger la liste des écrans. Vérifie ta connexion puis réessaie.';$('screenRetry').hidden=false;$('screenError').hidden=false;document.documentElement.dataset.ready='error';});})();
