'use strict';
const fixture=window.CONSIGNES_T1, $=(id)=>document.getElementById(id);
const nav=$('screenList'), frame=$('screenPreview'), names=['Consigne','Enregistrement','Après lecture'];
const entries=[];
fixture.scenes.forEach((scene,i)=>{
 const group=document.createElement('section');group.className='screen-group';
 const title=document.createElement('h2');title.textContent=`Prise ${i+1} · ${scene.titre.toLowerCase()}`;group.append(title);
 const row=document.createElement('div');row.className='screen-row';
 names.forEach((label,j)=>{
  const n=i*3+j+1, a=document.createElement('a'), url=`simulation.html?test=${encodeURIComponent(fixture.id)}&ecran=${n}`;
  a.href=url;a.dataset.ecran=String(n);
  const order=document.createElement('small');order.textContent=String(n).padStart(2,'0');a.append(order,document.createTextNode(label));
  a.addEventListener('click',ev=>{
   if(ev.button!==0||ev.ctrlKey||ev.metaKey||ev.shiftKey||ev.altKey)return;
   ev.preventDefault(); if(location.hash!==`#${n}`)location.hash=String(n);
   if(matchMedia('(max-width: 760px)').matches)$('screenLabel').scrollIntoView({block:'start'});
  });
  row.append(a);entries.push({n,a,url,label:`Écran ${n}/12 · Prise ${i+1} · ${label}`});
 });group.append(row);nav.append(group);
});
let current=0;
function show(){
 const n=Number(location.hash.slice(1));const o=Number.isInteger(n)&&n>=1&&n<=12?entries[n-1]:entries[0];
 if(current===o.n)return;current=o.n;
 entries.forEach(({a,n})=>{if(n===current)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');});
 $('screenLabel').textContent=o.label;$('screenAlone').href=o.url;frame.title=o.label;frame.src=o.url;
}
window.addEventListener('hashchange',show);show();
