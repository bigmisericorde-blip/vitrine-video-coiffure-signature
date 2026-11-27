/* Les réponses restent dans l’onglet et ne sont jamais envoyées par le rendu local. */
(() => {
  'use strict';
  const contract=window.VV_T1_CONTRACT, fixture=window.CONSIGNES_T2, prefix='vv-t2-fiche:', lifetime=24*60*60*1000;
  // Anciens choix : conversion uniquement pour relire une fiche déjà enregistrée.
  const finish=Object.freeze({profil:'Le résultat entier, vu de côté.',contours:'Les contours, filmés de près.',couleur:'La couleur et les reflets, dans la lumière.',detail:'Un détail : une tresse, une boucle ou une mèche.'});
  const action=Object.freeze({'Prendre rendez-vous':'Prendre rendez-vous','T’écrire':'Envoyer un message','T’appeler':'Appeler','Rien pour le moment':''});
  const string=(v,n)=>typeof v==='string'?Array.from(v.normalize('NFC').replace(/[\p{Cc}\u202A-\u202E\u2066-\u2069]/gu,' ').replace(/\s+/gu,' ').trim()).slice(0,n).join(''):'';
  const key=id=>/^[a-f0-9]{32}$/.test(id||'');
  const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
  function normalize(raw){
    if(!raw||typeof raw!== 'object')throw Error('Fiche manquante.');
    const limits=Object.fromEntries(contract.merchant_input.fields.map(f=>[f.id,f.max_length]));
    const salon=string(raw.salon,limits.salon),service=string(raw.service,limits.service),ville=string(raw.ville,limits.ville);
    if(contract.merchant_input.fields.some(f=>f.required&&!string(raw[f.id],f.max_length)))throw Error('Complète le nom et la prestation à présenter.');
    const oldAction=raw.commercial===true?null:(has(action,raw.action)?raw.action:null);
    const contact=oldAction==='Rien pour le moment'?'':string(raw.contact,limits.contact),saisiePrix=string(raw.prix,limits.prix);
    const prix=saisiePrix&&!oldAction&&!/^à partir de\b/i.test(saisiePrix)?'À partir de '+saisiePrix:saisiePrix;
    // Anciens champs conservés en lecture seulement pour ne pas casser les fiches déjà enregistrées.
    const ancienne=raw.resultatChoix==='autre'?string(raw.resultatAutre,80):finish[raw.resultatChoix]||'';
    const resultat=(oldAction&&(string(raw.resultat,80)||ancienne))||('Le résultat : '+service);
    const geste=(oldAction&&string(raw.geste,60))||'Le geste en action';
    const detail=(oldAction&&string(raw.detail,60))||'Les détails de la prestation';
    const cta=oldAction?action[oldAction]:(contact?'Nous contacter':'Découvrir la prestation');
    return Object.freeze({salon,service,ville,contact,prix,geste,detail,resultat,action:oldAction||'T’appeler',cta,commercial:!oldAction,source:raw.source==='client'?'client':'demo'});
  }
  const d=fixture.display;
  const initial=normalize({salon:d.salon,ville:d.ville,service:'Coupe et barbe',prix:'1 500 FCFA',contact:'',source:'demo'});
  function restore(id){
    if(!key(id))return null;
    try{const item=JSON.parse(sessionStorage.getItem(prefix+id)||'null');if(item?.schema!=='vv.coiffure.fiche/1'||!(item.until>Date.now()))return null;return normalize(item.answers);}catch{return null;}
  }
  function save(raw,previous){
    const answers=normalize(raw);
    const id=restore(previous)?previous:Array.from(crypto.getRandomValues(new Uint8Array(16)),x=>x.toString(16).padStart(2,'0')).join('');
    for(let i=sessionStorage.length-1;i>=0;i--){const k=sessionStorage.key(i);if(k?.startsWith(prefix)&&!restore(k.slice(prefix.length)))sessionStorage.removeItem(k);}
    try{sessionStorage.setItem(prefix+id,JSON.stringify({schema:'vv.coiffure.fiche/1',until:Date.now()+lifetime,answers}));}catch{throw Error('Active le stockage de cet onglet pour pouvoir relire ta fiche.');}
    return id;
  }
  function href(page,id,extra={}){const p=new URLSearchParams(extra);if(key(id))p.set('fiche',id);return page+(p.size?'?'+p:'');}
  function destination(job){
    const c=job.contact;if(job.commercial||!job.cta||!c)return ''; // Numéro WhatsApp ou téléphone : ne pas supposer lequel.
    if(/^\+?\d[\d ().-]{5,26}$/.test(c)){const phone=c.replace(/[^+\d]/g,'');return job.action==='T’écrire'?'sms:'+phone:'tel:'+phone;}
    try{const u=new URL(/^www\./i.test(c)?'https://'+c:c);if(['https:','http:'].includes(u.protocol)&&!u.username&&!u.password&&u.hostname)return u.href;}catch{}
    return '';
  }
  const expand=(template,job)=>template.replace(/\{(service|salon|ville)\}/g,(_,key)=>job?.[key]|| (key==='service'?'ta prestation':''));
  function sceneText(job,n){
    const scene=contract.capture.scenes[n];return expand(scene.contexte,job).split(' · ').filter(Boolean).join(' · ');
  }
  function sceneGuide(job,n,scene){
    const rule=contract.capture.scenes[n];
    if(!rule||rule.id!==scene.id)throw Error('Scène incompatible avec le contrat T1.');
    const text=job?.source!=='client'&&rule.consigne_demo?rule.consigne_demo:rule.consigne;
    return {...scene,titre:rule.titre,consigne:expand(text,job),a_filmer:rule.a_filmer,a_eviter:rule.a_eviter,question_relecture:rule.question_relecture};
  }
  window.VVFicheT2=Object.freeze({initial,normalize,restore,save,href,destination,sceneText,sceneGuide,finish});
})();
