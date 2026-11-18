'use strict';
const fixture=window.CONSIGNES_T1, $=(id)=>document.getElementById(id);
const nav=$('screenList'), picture=$('screenPreview'), select=$('screenSelect'), names=['Consigne','Enregistrement','Après lecture'];
const entries=[];
fixture.scenes.forEach((scene,i)=>{
 const group=document.createElement('section');group.className='screen-group';
 const title=document.createElement('h2');title.textContent=`Prise ${i+1} · ${scene.titre.toLowerCase()}`;group.append(title);
 const row=document.createElement('div');row.className='screen-row';
 names.forEach((step,j)=>{
  const n=i*3+j+1, a=document.createElement('a'), rank=String(n).padStart(2,'0');
  const url=`simulation.html?test=${encodeURIComponent(fixture.id)}&ecran=${n}&v=2`;
  const label=`Écran ${n}/12 · Prise ${i+1} · ${step}`;
  const copy=[scene.consigne,`Temps de la prise : ${scene.secondes} secondes. Le chrono avance quand la vidéo se joue.`,scene.question_relecture][j];
  a.href=`#${n}`;a.dataset.ecran=String(n);
  const order=document.createElement('small');order.textContent=rank;a.append(order,document.createTextNode(step));
  a.addEventListener('click',ev=>{
   if(ev.button!==0||ev.ctrlKey||ev.metaKey||ev.shiftKey||ev.altKey)return;
   ev.preventDefault();choose(n);
   if(matchMedia('(max-width: 760px)').matches)$('apercu').scrollIntoView({block:'start'});
  });
  row.append(a);select.append(new Option(`${rank} · Prise ${i+1} : ${step}`,String(n)));entries.push({n,a,url,label,copy,rank});
 });group.append(row);nav.append(group);
});
let current=0;
function show(n){
 const o=Number.isInteger(n)&&entries[n-1]?entries[n-1]:entries[0];
 if(current===o.n)return;current=o.n;
 entries.forEach(({a,n})=>{if(n===current)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');});
 $('screenLabel').textContent=o.label;$('screenText').textContent=o.copy;$('screenAlone').href=o.url;
 select.value=String(o.n);$('screenPrev').disabled=o.n===1;$('screenNext').disabled=o.n===entries.length;
 $('screenError').hidden=true;picture.hidden=false;picture.alt=o.label;
 picture.src=`livrables/12-ecrans/${o.rank}.webp?v=2`;
}
function choose(n){
 if(!entries[n-1])return;
 if(location.hash!==`#${n}`)history.pushState(null,'',`#${n}`);
 show(n);
}
function fromUrl(){show(Number(location.hash.slice(1)));}
window.addEventListener('hashchange',fromUrl);window.addEventListener('popstate',fromUrl);
$('screenPrev').onclick=()=>choose(current-1);$('screenNext').onclick=()=>choose(current+1);
select.onchange=()=>choose(Number(select.value));
picture.onerror=()=>{picture.hidden=true;$('screenError').hidden=false;};
fromUrl();
