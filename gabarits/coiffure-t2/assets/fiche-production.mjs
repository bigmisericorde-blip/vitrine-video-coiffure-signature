import {loadCore,readJson} from './engine/resources.mjs';
import {framing} from './engine/contract.mjs';
import {href,restoreFiche,saveFiche,normalizeFiche} from './engine/fiche.mjs';

const $=id=>document.getElementById(id);
const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
const ticket=new URLSearchParams(location.search).get('fiche');
async function init(){
  const core=await loadCore(), form=$('testForm');
  const {questions}=core, controls={}, metier=$('metier'), profiles=globalThis.VVBeaute;
  profiles.populate(metier,'coiffure');
  const make=(field,parent)=>{
    const row=el('div'), label=el('label',field.question);label.htmlFor=field.id;
    const input=el(field.options?'select':'input');input.id=input.name=field.id;input.required=Boolean(field.required);
    if(field.options){for(const [key,value] of field.options)input.add(new Option(value,key));}
    else{input.type='text'; if(field.max)input.maxLength=field.max; if(field.example)input.placeholder=`Ex. ${field.example}`;}
    if(field.id==='prix')input.inputMode='numeric';
    row.append(label,input);if(field.hint){const hint=el('small',field.hint);hint.id='hint-'+field.id;input.setAttribute('aria-describedby',hint.id);row.append(hint);}
    controls[field.id]=input;parent.append(row);return row;
  };
  for(const f of questions.fields)make(f,$(f.group==='preuve'?'fieldsProof':'fieldsOffer'));
  const priceMode=make({id:'prixMode',question:'Quel type de tarif ?',options:[['fixe','Tarif exact'],['minimum','À partir de']]},$('conditions'));
  const contact=make({id:'contact',question:'Quelle destination utiliser ?',max:120,hint:'Indicatif international +… et numéro, ou lien HTTPS selon le canal.'},$('conditions'));
  const check=$('contactConfirme');$('contactConfirmationLabel').textContent=questions.conditional[2].label;
  for(const [key,title] of Object.entries(framing))$('framing').add(new Option(title,key));
  const renderConditions=()=>{
    const isDemo=$('source').value==='demo';
    controls.canal.disabled=isDemo;
    const showContact=!isDemo&&controls.canal.value!=='aucun';
    const showPrice=Boolean(controls.prix.value.trim());
    contact.hidden=$('confirmation').hidden=!showContact;check.required=controls.contact.required=showContact;
    controls.contact.disabled=check.disabled=!showContact;
    priceMode.hidden=!showPrice;controls.prixMode.disabled=!showPrice;
    $('sampleNote').hidden=!isDemo;$('consentClient').hidden=isDemo;$('checkedCase').required=!isDemo;
    controls.contact.inputMode=controls.canal.value==='lien'?'url':'tel';
  };
  for(const c of [controls.prix,controls.canal,$('source')])c.addEventListener(c===controls.prix?'input':'change',renderConditions);
  const fill=(a)=>{
    for(const [key,input] of Object.entries(controls))input.value=a[key]??(key==='prixMode'?'fixe':key==='canal'?'aucun':'');
    check.checked=a.contactConfirme===true;$('source').value=a.source||'client';$('framing').value=a.framing||'profil';
    renderConditions();
  };
  const old=restoreFiche(ticket,core);profiles.populate(metier,old?.metier||'coiffure');fill(old||{});
  const refreshProfile=()=>{
    const p=profiles.get(metier.value);
    for(const [key,value] of Object.entries({service:p.services[0],geste:p.geste,preuve:p.preuve})){
      controls[key].placeholder='Ex. '+value;
    }
    $('gallery').href=href('ecrans.html',old?ticket:null,{metier:p.id});
  };
  metier.addEventListener('change',refreshProfile);refreshProfile();
  $('sample').onclick=async()=>{
    try{
      const rows=await readJson('formulaire/exemples.json');
      const p=profiles.get(metier.value);
      fill({...rows.examples[0].answers,service:p.services[0],geste:p.geste,preuve:p.preuve,source:'demo',contact:'',contactConfirme:false,canal:'aucun'});
      $('formAlert').textContent='Fiche d’exemple chargée. Les clips fournis sont des mires de test, pas une prestation réelle.';
      $('service').focus();
    }catch{$('formAlert').textContent='La fiche d’exemple n’a pas chargé.';}
  };
  form.addEventListener('submit',e=>{
    e.preventDefault();$('formAlert').textContent='';
    try{
      const source=$('source').value;
      if(source==='client'&&!$('checkedCase').checked)throw Error('Confirme que tu as l’autorisation d’utiliser les prises.');
      const raw={...Object.fromEntries(Object.entries(controls).map(([k,v])=>[k,v.value])),metier:metier.value,source,framing:$('framing').value,contactConfirme:check.checked};
      const saved=saveFiche(normalizeFiche(raw,core),core,ticket);
      location.assign(href('simulation.html',saved));
    }catch(err){$('formAlert').textContent=err.message;$('formAlert').focus();}
  });
  $('startTest').disabled=false;$('sample').disabled=false;
  if(old)$('gallery').href=href('ecrans.html',ticket,{metier:metier.value});
  document.documentElement.dataset.ready='yes';
}
init().catch(()=>{$('formAlert').textContent='Le gabarit n’a pas chargé. Ouvre-le depuis le serveur local en suivant le guide d’intégration.';document.documentElement.dataset.ready='error';});
