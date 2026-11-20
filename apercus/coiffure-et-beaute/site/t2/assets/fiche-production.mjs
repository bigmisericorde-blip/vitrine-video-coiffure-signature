import '../../commun/metiers.js';
import '../../commun/exemples.js';
import {loadCore} from './engine/resources.mjs';
import {framing} from './engine/contract.mjs';
import {href,restoreFiche,saveFiche,normalizeFiche} from './engine/fiche.mjs';

const $=id=>document.getElementById(id), {VVBeaute:ui,VVExemples:samples}=globalThis;
const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
const query=new URLSearchParams(location.search), ticket=query.get('fiche');
async function init(){
  const core=await loadCore(), form=$('testForm');
  const {questions}=core, controls={}, metier=$('metier'), source=$('source'), check=$('contactConfirme');
  let draft=null;
  const make=(field,parent)=>{
    const row=el('div'), label=el('label',field.question);label.htmlFor=field.id;
    const input=el(field.options?'select':'input');input.id=input.name=field.id;input.required=Boolean(field.required);
    if(field.options){for(const [key,value] of field.options)input.add(new Option(value,key));}
    else{input.type='text';if(field.max)input.maxLength=field.max;if(field.example)input.placeholder=`Ex. ${field.example}`;}
    if(field.id==='prix')input.inputMode='numeric';
    row.append(label);
    if(field.hint){const hint=el('small',field.hint);hint.id='hint-'+field.id;input.setAttribute('aria-describedby',hint.id);row.append(hint);}
    row.append(input);controls[field.id]=input;parent.append(row);return row;
  };
  for(const f of questions.fields)make(f,$(f.group==='preuve'?'fieldsProof':'fieldsOffer'));
  const priceMode=make({id:'prixMode',question:'Quel type de tarif ?',options:[['fixe','Tarif exact'],['minimum','À partir de']]},$('conditions'));
  const contact=make({id:'contact',question:'Quel numéro ou lien peut-on utiliser ?',max:120,hint:'Un numéro avec l’indicatif (+…) ou un lien HTTPS, selon ton choix.'},$('conditions'));
  $('contactConfirmationLabel').textContent=questions.conditional[2].label;
  for(const [key,title] of Object.entries(framing))$('framing').add(new Option(title,key));
  const old=restoreFiche(ticket,core);
  ui.populate(metier,old?.metier||ui.readMetier());
  const read=()=>({...Object.fromEntries(Object.entries(controls).map(([k,v])=>[k,v.value])),metier:metier.value,source:source.value,framing:$('framing').value,contactConfirme:check.checked});
  function refresh(){
    const p=ui.get(metier.value),ex=samples.get(p.id,'t2'),demo=source.value==='demo';
    const hints={service:'Par exemple : '+p.services.join(' · ')+'.',geste:'Décris un geste qu’on verra vraiment. Ex. '+p.geste+'.',preuve:'Choisis une finition visible. Ex. '+p.preuve+'.'};
    for(const [key,example] of Object.entries({service:p.services[0],geste:p.geste,preuve:p.preuve})){
      $('hint-'+key).textContent=hints[key];controls[key].placeholder='Ex. '+example;
    }
    $('home').href=ui.link('../',p.id);
    const gal=href('ecrans.html',old?.metier===p.id?ticket:null,{metier:p.id});
    $('gallery').href=$('voir').href=gal;$('filmLink').href=gal+'#resultat';$('filmLink').hidden=!ex;
    source.options[1].disabled=!ex;$('absenceExemple').hidden=!!ex;
    controls.canal.disabled=controls.prix.disabled=demo;
    const showContact=!demo&&controls.canal.value!=='aucun', showPrice=!demo&&Boolean(controls.prix.value.trim());
    contact.hidden=$('confirmation').hidden=!showContact;check.required=controls.contact.required=showContact;
    controls.contact.disabled=check.disabled=!showContact;
    priceMode.hidden=!showPrice;controls.prixMode.disabled=!showPrice;
    $('sampleNote').hidden=!demo;$('consentClient').hidden=demo;$('checkedCase').required=!demo;
    $('sampleNote').textContent=demo&&ex?`Tu utilises des images d’exemple : ${ex.title}. Ce n’est pas une offre réelle.`:'';
    controls.contact.inputMode=controls.canal.value==='lien'?'url':'tel';
  }
  function fill(a){
    for(const [key,input] of Object.entries(controls))input.value=a[key]??(key==='prixMode'?'fixe':key==='canal'?'aucun':'');
    check.checked=a.contactConfirme===true;source.value=a.source||'client';$('framing').value=a.framing||'profil';
  }
  source.addEventListener('change',()=>{
    if(source.value==='demo'){
      draft={...read(),source:'client'};
      const ex=samples.get(metier.value,'t2');
      if(ex)fill({source:'demo',service:ex.title,geste:ex.geste,preuve:ex.preuve});
    }else{fill(draft?.metier===metier.value?draft:{});draft=null;}
    $('checkedCase').checked=false;refresh();
  });
  metier.addEventListener('change',()=>{if(source.value==='demo')fill({});draft=null;$('checkedCase').checked=false;refresh();});
  controls.prix.addEventListener('input',refresh);
  controls.canal.addEventListener('change',()=>{check.checked=false;refresh();});controls.contact.addEventListener('input',()=>{check.checked=false;});
  fill(old||{});
  if(!old&&query.get('essai')==='1'&&samples.get(metier.value,'t2')){source.value='demo';source.dispatchEvent(new Event('change'));}
  if(ticket&&!old)$('formAlert').textContent='Cette fiche n’est plus dans cet onglet. Tu peux la remplir à nouveau.';
  refresh();$('startTest').disabled=false;
  form.addEventListener('submit',e=>{
    e.preventDefault();$('formAlert').textContent='';
    try{
      if(source.value==='client'&&!$('checkedCase').checked)throw Error('Confirme que tu as l’autorisation d’utiliser les prises.');
      const saved=saveFiche(normalizeFiche(read(),core),core,ticket);
      location.assign(href('simulation.html',saved,{metier:metier.value}));
    }catch(err){$('formAlert').textContent=err.message;$('formAlert').focus();}
  });
  document.documentElement.dataset.ready='yes';
}
init().catch(()=>{$('formAlert').textContent='Les ressources n’ont pas chargé. Recharge cette page depuis l’aperçu, ou ouvre-la depuis le serveur local.';document.documentElement.dataset.ready='error';});
