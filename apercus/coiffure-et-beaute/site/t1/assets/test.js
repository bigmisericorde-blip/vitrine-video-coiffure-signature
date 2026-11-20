'use strict';
(() => {
  const fiche=window.VVFicheT2, ui=window.VVBeaute, samples=window.VVExemples, $=id=>document.getElementById(id);
  const form=$('testForm'), q=new URLSearchParams(location.search), ticket=q.get('fiche');
  const old=fiche.restore(ticket), select=$('metier'), source=$('source'), ids=['salon','ville','service','prix','action','contact','resultatAutre'];
  let draft=null;
  ui.populate(select,old?.metier||ui.readMetier());
  for(const [key,text] of [...Object.entries(ui.framing),['autre','Autre chose']]){
    const label=document.createElement('label'),radio=document.createElement('input'),span=document.createElement('span');
    radio.type='radio';radio.name='resultatChoix';radio.value=key;span.textContent=text;label.append(radio,span);$('finOptions').append(label);
  }
  const read=()=>Object.fromEntries(new FormData(form));
  function fill(a){
    for(const id of ids)$(id).value=a[id]??(id==='action'?'Rien pour le moment':'');
    form.elements.resultatChoix.value=a.resultatChoix||'profil';source.value=a.source||'client';
  }
  function linkFor(path,extra={}){return fiche.href(path,old&&old.metier===select.value?ticket:null,{metier:select.value,...extra});}
  function refresh(){
    const p=ui.get(select.value), ex=samples.get(p.id,'t1'), demo=source.value==='demo';
    $('aideTravail').textContent='Par exemple : '+p.services.join(' · ')+'.';$('service').placeholder='Ex. '+p.services[0];
    $('resultatAutre').placeholder='Ex. '+p.preuve;
    $('home').href=ui.link('../',p.id);$('gallery').href=$('voir').href=linkFor('ecrans.html');
    $('filmLink').hidden=!ex;$('filmLink').href=linkFor('ecrans.html')+'#resultat';
    source.options[1].disabled=!ex;
    $('absenceExemple').hidden=!!ex;$('sampleNote').hidden=!demo;
    $('sampleNote').textContent=demo&&ex?`Tu utilises des images d’exemple : ${ex.title}. Ce n’est pas une offre réelle.`:'';
    $('action').disabled=$('prix').disabled=demo;
    $('consentClient').hidden=demo;$('consent').required=!demo;
    const autre=form.elements.resultatChoix.value==='autre';
    $('autreResultat').hidden=!autre;$('resultatAutre').disabled=!autre;$('resultatAutre').required=autre;
    const action=$('action').value, show=!demo&&action!=='Rien pour le moment';
    $('contactBloc').hidden=!show;$('contact').disabled=!show;
    $('contactLabel').textContent=action==='T’écrire'?'À quel numéro ou lien peut-on t’écrire ?':action==='T’appeler'?'À quel numéro peut-on t’appeler ?':'Quel lien ou numéro permet de prendre rendez-vous ?';
    $('startTest').disabled=!$('checkedCase').checked;
  }
  const uncheck=()=>{$('checkedCase').checked=false;$('consent').checked=false;};
  source.addEventListener('change',()=>{
    if(source.value==='demo'){
      draft={...read(),...Object.fromEntries(ids.map(id=>[id,$(id).value])),source:'client'};
      const ex=samples.get(select.value,'t1');
      if(ex)fill({source:'demo',salon:'Vitrine Vidéo',ville:'Lieu fictif',service:ex.title,resultatChoix:'autre',resultatAutre:ex.resultat});
    } else {fill(draft?.metier===select.value?draft:{});draft=null;}
    uncheck();refresh();
  });
  select.addEventListener('change',()=>{if(source.value==='demo')fill({});draft=null;uncheck();refresh();});
  form.addEventListener('input',e=>{if(!['checkedCase','source','metier','consent'].includes(e.target.id))$('checkedCase').checked=false;refresh();});
  for(const s of ui.scenes(window.CONSIGNES_T2.scenes,'autre','t1')){
    const li=document.createElement('li');
    for(const [tag,text] of [['span',String(s.n).padStart(2,'0')],['b',s.role],['small',s.secondes+' s']]){const v=document.createElement(tag);v.textContent=text;li.append(v);}
    $('captureList').append(li);
  }
  fill(old||{});
  if(!old&&q.get('essai')==='1'&&samples.get(select.value,'t1')){source.value='demo';source.dispatchEvent(new Event('change'));}
  if(ticket&&!old)$('ready').textContent='Cette fiche n’est plus dans cet onglet. Tu peux la remplir à nouveau.';
  refresh();document.documentElement.dataset.ready='yes';
  form.addEventListener('submit',e=>{
    e.preventDefault();if(!$('checkedCase').checked||source.value==='client'&&!$('consent').checked)return;
    try{
      const id=fiche.save(read(),ticket);
      location.href=fiche.href('simulation.html',id,{test:window.CONSIGNES_T2.id,metier:select.value});
    }catch(err){$('ready').textContent=err.message;$('ready').focus();}
  });
})();
