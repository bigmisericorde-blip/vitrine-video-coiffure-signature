'use strict';
const c=window.CONSIGNES_T1,d=c.display;let time=null;
const g=(i)=>document.getElementById(i),el=(t,s)=>{let o=document.createElement(t);o.textContent=s;return o;};
const status=g('result'),acc=g('selectSlot'),items=['10:00','11:30','16:00'];
g('back').href='film.html?test='+encodeURIComponent(c.id);
for(const [k,v] of [['Prestation',d.service],['Salon de démo',d.salon+' · '+d.ville],['Tarif fictif',new Intl.NumberFormat('fr-FR').format(d.prix)+' '+d.devise]])g('reserveData').append(el('dt',k),el('dd',v));
const choose=(btn,t)=>{time=t;g('slots').querySelectorAll('.slot').forEach(q=>{q.setAttribute('aria-checked',String(q===btn));q.tabIndex=q===btn?0:-1;});acc.disabled=false;status.textContent='';};
items.forEach((t,i)=>{const btn=el('button',t);btn.type='button';btn.className='slot';btn.setAttribute('role','radio');btn.setAttribute('aria-checked','false');btn.tabIndex=i===0?0:-1;btn.onclick=()=>choose(btn,t);btn.onkeydown=(ev)=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(ev.key)){ev.preventDefault();const next=(i+items.length+(['ArrowLeft','ArrowUp'].includes(ev.key)?-1:1))%items.length;g('slots').children[next].click();g('slots').children[next].focus();}};g('slots').append(btn);});
acc.onclick=()=>{if(time){status.textContent='✓ Test réussi : '+time+' sélectionné pour « '+d.service+' ». Aucun rendez-vous réel.';status.classList.add('ok');}};
