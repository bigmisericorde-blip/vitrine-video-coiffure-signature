import {loadCore,readJson} from './engine/resources.mjs?v=t2-six-q2';
import {framing} from './engine/contract.mjs?v=t2-six-q2';
import {href,restoreFiche,saveFiche,normalizeFiche} from './engine/fiche.mjs?v=t2-six-q2';

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
    else{input.type=field.type||'text'; if(field.max)input.maxLength=field.max; if(field.example)input.placeholder=`Ex. ${field.example}`;}
    if(field.id==='prix')input.inputMode='numeric';
    row.append(label,input);if(field.hint){const hint=el('small',field.hint);hint.id='hint-'+field.id;input.setAttribute('aria-describedby',hint.id);row.append(hint);}
    controls[field.id]=input;parent.append(row);return row;
  };
  const byId=id=>questions.fields.find(f=>f.id===id);
  const target=$('commercialFields');target.replaceChildren();
  let channel;
  for(const field of questions.fields){
    make(field,target);
    if(field.id==='contact')channel=make({id:'canal',question:'Utiliser ce numéro pour',options:[['telephone','Téléphone'],['whatsapp','WhatsApp']]},target);
  }
  const check=$('contactConfirme');
  for(const [key,title] of Object.entries(framing))$('framing').add(new Option(title,key));
  const renderConditions=()=>{
    const isDemo=$('source').value==='demo',hasContact=Boolean(controls.contact.value.trim())&&!isDemo;
    channel.hidden=!hasContact;controls.canal.disabled=!hasContact;
    $('confirmation').hidden=!hasContact;check.required=hasContact;check.disabled=!hasContact;
    controls.contact.disabled=isDemo;
    $('sampleNote').hidden=!isDemo;$('consentClient').hidden=isDemo;$('checkedCase').required=!isDemo;
    controls.contact.inputMode='tel';
  };
  for(const c of [controls.contact,$('source')])c.addEventListener(c===controls.contact?'input':'change',renderConditions);
  const fill=(a)=>{
    for(const [key,input] of Object.entries(controls))input.value=a[key]??(key==='canal'?'telephone':'');
    if(!['telephone','whatsapp'].includes(controls.canal.value))controls.canal.value='telephone';
    check.checked=a.contactConfirme===true;$('source').value=a.source||'client';$('framing').value=a.framing||'profil';
    renderConditions();
  };
  const old=restoreFiche(ticket,core);profiles.populate(metier,old?.metier||'manucure');fill(old||{});
  const refreshProfile=()=>{
    const p=profiles.get(metier.value);
    controls.service.placeholder='Ex. '+p.services[0];
    $('gallery').href=href('ecrans.html',old?ticket:null,{metier:p.id});
  };
  metier.addEventListener('change',refreshProfile);refreshProfile();
  $('sample').onclick=async()=>{
    try{
      const rows=await readJson('formulaire/exemples.json');
      const p=profiles.get(metier.value);
      fill({...rows.examples[0].answers,service:p.services[0],source:'demo',contact:'',contactConfirme:false});
      $('formAlert').textContent='Fiche fictive chargée. Les clips fournis sont des mires de test, pas une prestation réelle.';
      $('service').focus();
    }catch{$('formAlert').textContent='La fiche d’exemple n’a pas chargé.';}
  };
  form.addEventListener('submit',e=>{
    e.preventDefault();$('formAlert').textContent='';
    try{
      const source=$('source').value;
      if(source==='client'&&!$('checkedCase').checked)throw Error('Confirme que tu as l’autorisation d’utiliser les prises.');
      const raw={...Object.fromEntries(Object.entries(controls).map(([k,v])=>[k,v.value])),geste:'',preuve:'',accroche:'',prixMode:controls.prix.value.trim()?'minimum':'fixe',canal:source==='client'&&controls.contact.value.trim()?controls.canal.value:'aucun',metier:metier.value,source,framing:$('framing').value,contactConfirme:check.checked};
      const saved=saveFiche(normalizeFiche(raw,core),core,ticket);
      location.assign(href('simulation.html',saved));
    }catch(err){$('formAlert').textContent=err.message;$('formAlert').focus();}
  });
  $('startTest').disabled=false;$('sample').disabled=false;
  if(old)$('gallery').href=href('ecrans.html',ticket,{metier:metier.value});
  document.documentElement.dataset.ready='yes';
}
init().catch(()=>{
  const msg='Les questions n’ont pas pu charger. Vérifie ta connexion, puis recharge la page.';
  $('commercialFields').textContent=msg;$('formAlert').textContent=msg;
  document.documentElement.dataset.ready='error';
});
