/* Les réponses ne voyagent pas dans l’URL, et ne sont jamais envoyées par le rendu local. */
(() => {
  'use strict';
  const fixture = window.CONSIGNES_T2;
  const prefix = 'vv-beaute-t1-fiche:';
  const ui=window.VVBeaute, samples=window.VVExemples;
  const lifetime = 24 * 60 * 60 * 1000;
  const finish = ui.framing;
  const action = Object.freeze({'Prendre rendez-vous':'Prendre rendez-vous','T’écrire':'Envoyer un message','T’appeler':'Appeler pour réserver','Rien pour le moment':''});
  const string = (v,n) => typeof v === 'string' ? Array.from(v.normalize('NFC').replace(/[\p{Cc}\u202A-\u202E\u2066-\u2069]/gu,' ').replace(/\s+/gu,' ').trim()).slice(0,n).join('') : '';
  const key = id => /^[a-f0-9]{32}$/.test(id||'');
  const has = (o,k) => Object.prototype.hasOwnProperty.call(o,k);

  function normalize(raw) {
    if (!raw || typeof raw !== 'object') throw Error('Fiche manquante.');
    const metier=ui.get(raw.metier).id, demo=raw.source==='demo';
    if(demo&&!samples.get(metier,'t1'))throw Error('Aucun exemple filmé pour cette prestation. Utilise tes propres prises.');
    const picked=demo?'Rien pour le moment':raw.action;
    const salon=string(raw.salon,45), ville=string(raw.ville,45), service=string(raw.service,50);
    if (!salon || !ville || !service) throw Error('Complète le nom, le lieu et la prestation.');
    const choix=raw.resultatChoix, autre=choix==='autre'?string(raw.resultatAutre,80):'';
    if (choix==='autre'?!autre:!has(finish,choix)) throw Error('Indique ce qu’il faut montrer à la fin.');
    if (!has(action,picked)) throw Error('Choisis une action de fin.');
    return Object.freeze({metier,salon,ville,service,prix:demo?'':string(raw.prix,32),resultatChoix:choix,resultatAutre:autre,
      resultat:autre||finish[choix],action:picked,cta:action[picked],contact:action[picked]?string(raw.contact,120):'',
      source:demo?'demo':'client'});
  }

  const d=fixture.display;
  const initial=normalize({metier:'coiffure',salon:d.salon,ville:d.ville,service:d.service,prix:new Intl.NumberFormat('fr-FR').format(d.prix)+' '+d.devise,
    resultatChoix:'profil',action:'Prendre rendez-vous',contact:'',source:'demo'});
  function restore(id) {
    if (!key(id)) return null;
    try {
      const item=JSON.parse(sessionStorage.getItem(prefix+id)||'null');
      if (item?.schema!=='vv.coiffure.fiche/1' || !(item.until>Date.now())) return null;
      return normalize(item.answers);
    } catch { return null; }
  }
  function save(raw,previous) {
    const answers=normalize(raw);
    const id=restore(previous)?previous:Array.from(crypto.getRandomValues(new Uint8Array(16)),x=>x.toString(16).padStart(2,'0')).join('');
    for (let i=sessionStorage.length-1;i>=0;i--) {
      const k=sessionStorage.key(i);
      if(k?.startsWith(prefix) && !restore(k.slice(prefix.length))) sessionStorage.removeItem(k);
    }
    try {sessionStorage.setItem(prefix+id,JSON.stringify({schema:'vv.coiffure.fiche/1',until:Date.now()+lifetime,answers}));}
    catch {throw Error('Active le stockage de cet onglet pour pouvoir relire ta fiche.');}
    return id;
  }
  function href(page,id,extra={}) {
    const p=new URLSearchParams(extra);
    if (key(id)) p.set('fiche',id);
    return page+(p.size?'?'+p:'');
  }
  function destination(job) {
    const c=job.contact;
    if (!job.cta || !c) return '';
    if (/^\+?\d[\d ().-]{5,26}$/.test(c)) {
      const phone=c.replace(/[^+\d]/g,'');
      return job.action==='T’écrire'?'sms:'+phone:'tel:'+phone;
    }
    try {
      const u=new URL(/^www\./i.test(c)?'https://'+c:c);
      if (['https:','http:'].includes(u.protocol)&&!u.username&&!u.password&&u.hostname) return u.href;
    } catch {}
    return '';
  }
  function sceneText(job,n) {
    if (n===0) return [job.salon,job.service,job.prix,job.ville].filter(Boolean).join(' · ');
    if (n===3) return 'À la fin : '+job.resultat;
    return 'Ton travail : '+job.service;
  }
  window.VVFicheT2=Object.freeze({initial,normalize,restore,save,href,destination,sceneText,finish});
})();
