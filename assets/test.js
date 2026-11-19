'use strict';
(() => {
 const data=window.CONSIGNES_T2, fiche=window.VVFicheT2, $=id=>document.getElementById(id);
 const el=(tag,text)=>{const x=document.createElement(tag);x.textContent=text;return x;};
 const q=new URLSearchParams(location.search), previous=q.get('fiche');
 const form=$('testForm'), choices=[...form.querySelectorAll('[name="resultatChoix"]')];
 const restored=fiche.restore(previous), initial=restored||fiche.initial;
 if(previous&&!restored)$('ready').textContent='Cette fiche n’est plus dans cet onglet. Tu peux la remplir à nouveau.';
 $('caseLabel').textContent='GABARIT T2 · COIFFURE';
 for(const id of ['salon','ville','service','prix','action','contact','resultatAutre'])$(id).value=initial[id];
 choices.find(x=>x.value===initial.resultatChoix).checked=true;
 form.elements.source.value=initial.source;
 // Une fiche commerciale ne part pas avec un nom ou un tarif d’exemple non relu.
 const exampleFields=['salon','ville','service','prix'];
 const untouched=new Set(restored?[]:exampleFields);
 for(const k of exampleFields)$(k).addEventListener('input',()=>untouched.delete(k));
 for(const source of form.querySelectorAll('[name=source]')) source.addEventListener('change',()=>{
  if(form.elements.source.value==='client')for(const k of untouched)$(k).value='';
 });
 if(restored)document.querySelectorAll('[data-gallery]').forEach(a=>a.href=fiche.href('ecrans.html',previous));
 const finishHint=()=>{
  const autre=form.elements.resultatChoix.value==='autre';
  $('autreResultat').hidden=!autre;$('resultatAutre').disabled=!autre;$('resultatAutre').required=autre;
 };
 const contactHint=()=>{
  const a=$('action').value;
  $('contactBloc').hidden=a==='Rien pour le moment';$('contact').disabled=$('contactBloc').hidden;
  $('contactLabel').textContent=a==='T’écrire'?'À quel numéro ou lien peut-on t’écrire ?':a==='T’appeler'?'À quel numéro peut-on t’appeler ?':'Quel lien ou numéro permet de prendre rendez-vous ?';
  $('contact').placeholder=a==='T’appeler'?'Ex. Ton numéro de téléphone':'Ex. Ton lien ou ton numéro';
 };
 choices.forEach(x=>x.addEventListener('change',finishHint));$('action').addEventListener('change',contactHint);finishHint();contactHint();
 data.scenes.forEach(s=>{const li=el('li','');li.append(el('span',String(s.n).padStart(2,'0')),el('b',s.titre),el('small',s.secondes+' s'));$('captureList').append(li);});
 $('filmLink').href='film.html?test='+encodeURIComponent(data.id);
 const readiness=()=>form.querySelectorAll('button[type=submit]').forEach(b=>b.disabled=!$('checkedCase').checked);
 $('checkedCase').addEventListener('change',readiness);readiness();
 form.addEventListener('submit',ev=>{
  ev.preventDefault();if(!$('checkedCase').checked)return;
  try {
   const fields=Object.fromEntries(new FormData(form));
   const id=fiche.save(fields,previous);
   const destination=ev.submitter?.id==='previewScreens'?'ecrans.html':'simulation.html';
   location.href=fiche.href(destination,id,destination==='simulation.html'?{test:data.id}:{});
  } catch(err){$('ready').textContent=err.message;}
 });
})();
