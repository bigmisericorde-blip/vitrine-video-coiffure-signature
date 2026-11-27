/* Les réponses restent dans l’onglet et ne sont jamais envoyées par le rendu local. */
(() => {
  'use strict';
  const fixture=window.CONSIGNES_T2, prefix='vv-t2-fiche:', lifetime=24*60*60*1000;
  // Anciens choix : conversion uniquement pour relire une fiche déjà enregistrée.
  const finish=Object.freeze({profil:'Le résultat entier, vu de côté.',contours:'Les contours, filmés de près.',couleur:'La couleur et les reflets, dans la lumière.',detail:'Un détail : une tresse, une boucle ou une mèche.'});
  const action=Object.freeze({'Prendre rendez-vous':'Prendre rendez-vous','T’écrire':'Envoyer un message','T’appeler':'Appeler','Rien pour le moment':''});
  const string=(v,n)=>typeof v==='string'?Array.from(v.normalize('NFC').replace(/[\p{Cc}\u202A-\u202E\u2066-\u2069]/gu,' ').replace(/\s+/gu,' ').trim()).slice(0,n).join(''):'';
  const key=id=>/^[a-f0-9]{32}$/.test(id||'');
  const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
  function normalize(raw){
    if(!raw||typeof raw!== 'object')throw Error('Fiche manquante.');
    const salon=string(raw.salon,45),service=string(raw.service,50),ville=string(raw.ville,45);
    if(!salon||!service)throw Error('Complète le nom et la prestation à présenter.');
    const oldAction=raw.commercial===true?null:(has(action,raw.action)?raw.action:null);
    const contact=oldAction==='Rien pour le moment'?'':string(raw.contact,30),saisiePrix=string(raw.prix,40);
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
  function sceneText(job,n){
    if(n===0)return ['Prestation : '+job.service,job.salon,job.ville].filter(Boolean).join(' · ');
    if(n===1)return 'Ton geste : '+job.service;
    if(n===2)return 'Un détail : '+job.service;
    return 'Le résultat : '+job.service;
  }
  function sceneGuide(job,n,scene){
    const service=job?.service||'ta prestation';
    const rows=[
      {titre:'AVANT LA PRESTATION',consigne:'Avant de commencer, filme la personne ou la zone concernée par '+service+'. Garde un angle qui permettra de comparer avec le résultat.',a_filmer:['La situation avant la prestation.','La personne ou la zone concernée, avec son accord.'],a_eviter:['Commencer à filmer après la prestation.','Changer de personne pour le résultat.'],question_relecture:'Est-ce que la situation avant est bien visible ?'},
      {titre:'LE GESTE',consigne:'Filme tes mains pendant la prestation : '+service+'.',a_filmer:['Tes mains en action.','Le geste bien visible.'],a_eviter:['Cacher le geste.','Filmer de trop loin.'],question_relecture:'Est-ce qu’on voit bien le geste ?'},
      {titre:'LE DÉTAIL',consigne:'Approche le téléphone et montre un détail de la prestation : '+service+'.',a_filmer:['Un détail de près.','Une image nette et stable.'],a_eviter:['Trop bouger le téléphone.','Cacher le détail.'],question_relecture:'Est-ce qu’on voit bien le détail ?'},
      {titre:'LE RÉSULTAT',consigne:'Filme le résultat de '+service+' sur la même personne ou zone, sous un angle proche de la première prise.',a_filmer:['Le résultat terminé.','La même personne ou zone qu’au début.'],a_eviter:['Cacher le résultat.','Changer de personne ou de zone.'],question_relecture:'Est-ce que le résultat est bien visible ?'}
    ];
    if(n===0&&job?.source!=='client')rows[0].consigne='Dans cet exemple, la coiffure est déjà commencée. Pour ta vidéo, filme la personne ou la zone avant de commencer.';
    if(n===3&&job?.source!=='client')rows[3].consigne='Dans cet exemple, on voit les finitions. Pour ta vidéo, filme le résultat de '+service+' sur la même personne et sous un angle proche du début.';
    return {...scene,...rows[n]};
  }
  window.VVFicheT2=Object.freeze({initial,normalize,restore,save,href,destination,sceneText,sceneGuide,finish});
})();
