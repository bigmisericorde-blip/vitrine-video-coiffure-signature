'use strict';
const data=window.CONSIGNES_T1, $=(id)=>document.getElementById(id);
const e=(t,text)=>{const x=document.createElement(t);x.textContent=text;return x;};
try {
 const d=data.display, key='vv-fiche-'+data.id;
 if(data.scenes.length!==4||data.sortie.frames!==900||data.sortie.audio!==false||!data.plan.prepared)throw Error('Cas invalide');
 $('caseLabel').textContent='CAS DE TEST · '+data.id;
 const initial={salon:d.salon,ville:d.ville,service:d.service,prix:new Intl.NumberFormat('fr-FR').format(d.prix)+' '+d.devise,action:'Prendre rendez-vous',contact:''};
 const form=$('testForm'), choices=[...form.querySelectorAll('[name="resultatChoix"]')];
 const finishText={profil:'Le résultat entier, vu de côté.',contours:'Les contours, filmés de près.',couleur:'La couleur et les reflets, dans la lumière.',detail:'Un détail : une tresse, une boucle ou une mèche.'};
 let last={};try{last=JSON.parse(sessionStorage.getItem(key)||'{}')||{};}catch{}
 for(const [id,value] of Object.entries(initial))$(id).value=typeof last[id]==='string'?last[id]:value;
 if(!$('action').value)$('action').value=initial.action;
 const oldChoice=choices.find(x=>x.value===last.resultatChoix);
 if(oldChoice)oldChoice.checked=true;
 else if(typeof last.resultat==='string'&&last.resultat.trim()&&last.resultat!=='La coupe et la barbe finies'&&!Object.values(finishText).includes(last.resultat)){
  choices.find(x=>x.value==='autre').checked=true;$('resultatAutre').value=last.resultat.slice(0,80);
 }
 if(typeof last.resultatAutre==='string')$('resultatAutre').value=last.resultatAutre.slice(0,80);
 const finishHint=()=>{
  const autre=form.elements.resultatChoix.value==='autre';$('autreResultat').hidden=!autre;$('resultatAutre').disabled=!autre;
 };
 const contactHint=()=>{
  const a=$('action').value;
  $('contactBloc').hidden=a==='Rien pour le moment';$('contact').disabled=$('contactBloc').hidden;
  $('contactLabel').textContent=a==='T’écrire'?'À quel numéro ou lien peut-on t’écrire ?':a==='T’appeler'?'À quel numéro peut-on t’appeler ?':'Quel lien ou numéro permet de prendre rendez-vous ?';
  $('contact').placeholder=a==='T’appeler'?'Ex. Ton numéro de téléphone':'Ex. Ton lien ou ton numéro';
 };
 choices.forEach(x=>x.addEventListener('change',finishHint));$('action').addEventListener('change',contactHint);finishHint();contactHint();
 data.scenes.forEach(s=>{const li=e('li','');li.append(e('span',String(s.n).padStart(2,'0')),e('b',s.titre),e('small',s.secondes+' s'));$('captureList').append(li);});
 $('filmLink').href='film.html?test='+encodeURIComponent(data.id);
 $('checkedCase').addEventListener('change',()=>{$('startTest').disabled=!$('checkedCase').checked;});
 form.addEventListener('submit',ev=>{
  ev.preventDefault();if(!$('checkedCase').checked)return;
  const values=Object.fromEntries(Object.keys(initial).map(id=>[id,$(id).value.trim()]));
  for(const id of ['salon','ville','service'])if(!values[id]){$(id).focus();$('ready').textContent='Complète cette réponse pour continuer.';return;}
  let choix=form.elements.resultatChoix.value;
  const autre=$('resultatAutre').value.trim();if(!choix||(choix==='autre'&&!autre))choix='profil';
  values.resultatChoix=choix;values.resultatAutre=autre;values.resultat=choix==='autre'?autre:finishText[choix];
  if($('contact').disabled)values.contact='';
  try{sessionStorage.setItem(key,JSON.stringify(values));}catch{$('ready').textContent='Ton navigateur ne peut pas garder cette fiche dans cet onglet. Tu peux quand même voir les 12 écrans.';return;}
  location.href='simulation.html?test='+encodeURIComponent(data.id)+'&fiche=1';
 });
} catch(err){$('ready').textContent='La fiche ne s’ouvre pas. Recharge la page.';}
