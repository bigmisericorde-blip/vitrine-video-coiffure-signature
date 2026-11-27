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
    if(!raw||typeof raw!=='object')throw Error('Fiche manquante.');
    const salon=string(raw.salon,45),ville=string(raw.ville,45),service=string(raw.service,50),geste=string(raw.geste,60),detail=string(raw.detail,60);
    if(!salon||!service)throw Error('Complète le nom et le travail à montrer.');
    const ancienne=raw.resultatChoix==='autre'?string(raw.resultatAutre,80):finish[raw.resultatChoix]||'';
    const resultat=string(raw.resultat,80)||ancienne;
    if(!resultat)throw Error('Indique ce qu’il faut montrer à la fin.');
    if(!has(action,raw.action))throw Error('Choisis une action de fin.');
    return Object.freeze({salon,ville,service,geste,detail,prix:string(raw.prix,32),resultat,action:raw.action,cta:action[raw.action],contact:action[raw.action]?string(raw.contact,120):'',source:raw.source==='client'?'client':'demo'});
  }
  const d=fixture.display;
  const initial=normalize({salon:d.salon,ville:d.ville,service:d.service,geste:'Le geste de coupe',detail:'Les contours de la barbe',resultat:'La coupe et la barbe terminées',prix:new Intl.NumberFormat('fr-FR').format(d.prix)+' '+d.devise,action:'Prendre rendez-vous',contact:'',source:'demo'});
  function restore(id){
    if(!key(id))return null;
    try{const item=JSON.parse(sessionStorage.getItem(prefix+id)||'null');if(item?.schema!=='vv.coiffure.fiche/1'||!(item.until>Date.now()))return null;return normalize(item.answers);}catch{return null;}
  }
  function save(raw,previous){
    const answers=normalize(raw);
    if(!answers.geste||!answers.detail)throw Error('Précise le geste et le détail à filmer.');
    const id=restore(previous)?previous:Array.from(crypto.getRandomValues(new Uint8Array(16)),x=>x.toString(16).padStart(2,'0')).join('');
    for(let i=sessionStorage.length-1;i>=0;i--){const k=sessionStorage.key(i);if(k?.startsWith(prefix)&&!restore(k.slice(prefix.length)))sessionStorage.removeItem(k);}
    try{sessionStorage.setItem(prefix+id,JSON.stringify({schema:'vv.coiffure.fiche/1',until:Date.now()+lifetime,answers}));}catch{throw Error('Active le stockage de cet onglet pour pouvoir relire ta fiche.');}
    return id;
  }
  function href(page,id,extra={}){const p=new URLSearchParams(extra);if(key(id))p.set('fiche',id);return page+(p.size?'?'+p:'');}
  function destination(job){
    const c=job.contact;if(!job.cta||!c)return '';
    if(/^\+?\d[\d ().-]{5,26}$/.test(c)){const phone=c.replace(/[^+\d]/g,'');return job.action==='T’écrire'?'sms:'+phone:'tel:'+phone;}
    try{const u=new URL(/^www\./i.test(c)?'https://'+c:c);if(['https:','http:'].includes(u.protocol)&&!u.username&&!u.password&&u.hostname)return u.href;}catch{}
    return '';
  }
  function sceneText(job,n){
    if(n===0)return ['Ton travail : '+job.service,job.salon,job.ville].filter(Boolean).join(' · ');
    if(n===1)return job.geste?'Ton geste : '+job.geste:'Ton travail : '+job.service;
    if(n===2)return job.detail?'Ton détail : '+job.detail:'Ton travail : '+job.service;
    return 'À la fin : '+job.resultat;
  }
  function sceneGuide(job,n,scene){
    if(!job)return scene;
    const rows=[
      {consigne:'Filme-toi au travail. Montre ce que tu fais et, si la personne est d’accord, un peu du lieu.',a_filmer:['Le travail que tu as choisi.','Tes mains et la personne si elle accepte.'],a_eviter:['Bouger trop vite.','Filmer une personne sans son accord.'],question_relecture:'Est-ce qu’on voit bien ton travail ?'},
      {consigne:job.geste?'Filme tes mains pendant ce geste : '+job.geste+'.':'Filme tes mains pendant que tu travailles.',a_filmer:['Tes mains en action.','Ce que tu fais.'],a_eviter:['Cacher le geste avec ta main.','Filmer de trop loin.'],question_relecture:job.geste?'Est-ce qu’on voit bien ton geste : '+job.geste+' ?':'Est-ce qu’on voit bien le geste ?'},
      {consigne:job.detail?'Approche le téléphone et montre ce détail : '+job.detail+'.':'Approche le téléphone et montre un détail de ton travail.',a_filmer:['Le détail de près.','Une image nette et stable.'],a_eviter:['Trop bouger le téléphone.','Cacher le détail avec ta main.'],question_relecture:job.detail?'Est-ce qu’on voit bien ce détail : '+job.detail+' ?':'Est-ce qu’on voit bien le détail ?'},
      {consigne:'Filme ton travail terminé. Montre bien : '+job.resultat+'.',a_filmer:['Le travail terminé.','Le résultat dans la lumière.'],a_eviter:['Cacher le résultat.','Changer de personne si tu montres un avant et un après.'],question_relecture:'Est-ce qu’on voit bien le résultat que tu as choisi ?'}
    ];return {...scene,...rows[n]};
  }
  window.VVFicheT2=Object.freeze({initial,normalize,restore,save,href,destination,sceneText,sceneGuide,finish});
})();
