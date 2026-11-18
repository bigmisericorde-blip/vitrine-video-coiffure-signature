'use strict';
const data=window.CONSIGNES_T1, $=(id)=>document.getElementById(id);
const e=(t,text)=>{const x=document.createElement(t);x.textContent=text;return x;};
try {
 const d=data.display, key='vv-fiche-'+data.id;
 if(data.scenes.length!==4||data.sortie.frames!==900||data.sortie.audio!==false||!data.plan.prepared)throw Error('Cas invalide');
 $('caseLabel').textContent='CAS DE TEST · '+data.id;
 const initial={salon:d.salon,ville:d.ville,service:d.service,prix:new Intl.NumberFormat('fr-FR').format(d.prix)+' '+d.devise,resultat:'La coupe et la barbe finies',action:'Prendre rendez-vous',contact:''};
 let last={}; try{last=JSON.parse(sessionStorage.getItem(key)||'{}')||{};}catch{}
 for(const [id,value] of Object.entries(initial))$(id).value=typeof last[id]==='string'?last[id]:value;
 data.scenes.forEach(s=>{const li=e('li','');li.append(e('span',String(s.n).padStart(2,'0')),e('b',s.titre),e('small',s.secondes+' s'));$('captureList').append(li);});
 $('filmLink').href='film.html?test='+encodeURIComponent(data.id);
 $('checkedCase').addEventListener('change',()=>{$('startTest').disabled=!$('checkedCase').checked;});
 $('testForm').addEventListener('submit',ev=>{
  ev.preventDefault(); if(!$('checkedCase').checked)return;
  const values=Object.fromEntries(Object.keys(initial).map(id=>[id,$(id).value.trim()]));
  for(const id of ['salon','ville','service'])if(!values[id]){$(id).focus();$('ready').textContent='Complète cette réponse pour continuer.';return;}
  try{sessionStorage.setItem(key,JSON.stringify(values));}catch{$('ready').textContent='Ton navigateur ne peut pas garder cette fiche dans cet onglet. Tu peux quand même voir les 12 écrans.';return;}
  location.href='simulation.html?test='+encodeURIComponent(data.id)+'&fiche=1';
 });
} catch(err){$('ready').textContent='La fiche ne s’ouvre pas. Recharge la page.';}
