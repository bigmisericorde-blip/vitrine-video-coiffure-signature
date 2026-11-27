// Couche éditoriale de revue : sans effet sur le plan de prises ou le master R04.
const LENGTH=s=>Array.from(s).length;
export const EDITION='r04-texte-02';
export const FPS=30;
export const MUSIC_IDS=Object.freeze(['A','B','C','D']);
export const SHORT_ACTIONS=Object.freeze({whatsapp:'Écris-nous sur WhatsApp.',telephone:'Appelle pour réserver.',lien:'Réserve ton créneau.'});
export const ASSIST_ACTIONS=Object.freeze({whatsapp:'Ouvrir WhatsApp',telephone:'Appeler',lien:'Ouvrir la réservation'});
const INPUT_IDS=['service','geste','preuve','accroche','salon','ville','prix'];
const safe=(value)=>value.normalize('NFC').replace(/\s+/gu,' ').trim();
const text=(value,key)=>{
  if(value==null)return '';
  if(typeof value!=='string'||/[\p{Cc}\u202A-\u202E\u2066-\u2069<>]/u.test(value))throw new Error(`${key} : saisis du texte sans balises ni caractères de contrôle.`);
  return safe(value);
};
export function price(s,mode){
  if(!s)return '';
  const piece=s.replace(/\s*FCFA$/iu,'');
  const x=piece.replace(/\p{Zs}/gu,'');
  if(!/^[1-9]\d{0,6}$/u.test(x)||(!/^\d+$/u.test(piece)&&!/^\d{1,3}(?:\p{Zs}\d{3}){1,2}$/u.test(piece)))throw Error('Tarif : indique un montant de 1 à 9 999 999 FCFA, avec des groupes de trois chiffres si tu mets des espaces.');
  return (mode==='minimum'?'À partir de ':'')+x.replace(/\B(?=(\d{3})+(?!\d))/g,'\u00A0')+' FCFA';
}
export function contactDestination(canal,str){
  if(canal==='aucun')return '';
  if(canal==='whatsapp'||canal==='telephone'){
    const phone=str.replace(/[ ().-]/g,'');
    if(!/^\+[1-9]\d{7,14}$/.test(phone))throw Error('Contact : ajoute l’indicatif international, puis le numéro complet.');
    return canal==='whatsapp'?`https://wa.me/${phone.slice(1)}`:`tel:${phone}`;
  }
  if(canal==='lien'){
    let u; try{u=new URL(str);}catch{}
    if(!u||u.protocol!=='https:'||u.username||u.password||!u.hostname.includes('.')||u.hostname.length>85||str.includes('\\'))throw Error('Réservation : saisis un lien https:// valide, sans identifiant ni mot de passe.');
    return u.href;
  }
  throw Error('Canal de réservation inconnu.');
}
export function normalizeVisual(raw,config,fontMeta){
  if(!raw||typeof raw!=='object'||Array.isArray(raw))throw Error('Fiche manquante.');
  const r={},glyphs=new Set(fontMeta.glyphs),signGlyphs=new Set(fontMeta.sans.glyphs);
  for(const id of INPUT_IDS){
    const rule=config.fields.find(x=>x.id===id); const s=text(raw[id],rule.question).replace(/\u2011/gu,'-');
    if((!s&&rule.required)||(s&&(LENGTH(s)<rule.min||LENGTH(s)>rule.max)))throw Error(`${rule.question} ${rule.min} à ${rule.max} caractères.`);
    if(id==='accroche'&&s){const n=s.split(' ').length; if(n<2||n>6)throw Error('Accroche : choisis 2 à 6 mots.');}
    if(id!=='prix'&&Array.from(s).some(ch=>!(id==='salon'||id==='ville'?signGlyphs:glyphs).has(ch.codePointAt(0))))throw Error(`${rule.question} La police de revue ne peut pas écrire ce caractère.`);
    r[id]=s;
  }
  const choix=config.fields.find(f=>f.id==='canal').options.map(x=>x[0]);
  const c=raw.canal??'aucun';if(!choix.includes(c))throw Error('Sélectionne un moyen de réservation.');
  if(r.prix&&raw.prixMode!==undefined&&!['fixe','minimum'].includes(raw.prixMode))throw Error('Choisis un tarif exact ou un minimum.');
  r.prixMode=r.prix&&raw.prixMode==='minimum'?'minimum':'fixe';
  r.tarif=price(r.prix,r.prixMode);r.canal=c;
  r.numero=text(raw.numero,'Numéro');
  if(r.numero && !/^\+[1-9]\d{7,14}$/.test(r.numero))throw Error('Numéro : format international invalide.');
  return Object.freeze(r);
}
export function normalize(raw,config,fontMeta){
  const r={...normalizeVisual(raw,config,fontMeta),contact:'',destination:'',contactConfirme:false};
  const c=r.canal;
  if(c!=='aucun'){
    if(raw.contactConfirme!==true)throw Error('Confirme que la destination est vérifiée et que tu peux la communiquer.');
    r.contact=text(raw.contact,'Contact');if(!r.contact||LENGTH(r.contact)>120)throw Error('Indique la destination (120 caractères maximum).');
    r.destination=contactDestination(c,r.contact);r.contactConfirme=true;
    if(c==='whatsapp'||c==='telephone')r.numero=r.contact.replace(/[ ().-]/g,'');
  }
  return Object.freeze(r);
}
function splitHook(s){
  const words=s.split(' ');
  if(words.length<=4)return words;
  if(words.length===5)return [words.slice(0,2).join(' '),...words.slice(2)];
  return [words.slice(0,2).join(' '),words.slice(2,4).join(' '),...words.slice(4)];
}
export function makeVisualPlan(fields,id,config){
  const v=config.variants[id],g=config.common;if(!v)throw Error('Son inconnu.');
  const b=v.beats, out=[];
  const put=(key,text,on,off,slot,role='sign')=>{if(text)out.push({key,text,on,off,slot,role});};
  const h=fields.accroche?splitHook(fields.accroche):v.hook;
  const hookSlots=h.length===2?[0,1]:h.length===3?[0,1,3]:[0,1,2,3];
  const hookBeat=h.length===2?[b.intro[0],b.intro[2]]:h.length===3?[b.intro[0],b.intro[1],b.intro[3]]:b.intro;
  h.forEach((s,i)=>put('intro-'+i,s,hookBeat[i],g.introEnd,`i${hookSlots[i]}`,'intro'));
  put('before',v.before,b.before,g.beforeEnd,'single');
  put('work',v.work,b.work,g.workEnd,'upper');
  put('gesture',fields.geste,b.gesture,g.workEnd,'lower');
  put('detail',v.detail,b.detail,g.detailEnd,'upper');
  put('proof',fields.preuve,b.proof,g.detailEnd,'lower');
  put('reveal',v.reveal,b.reveal,g.revealEnd,'upper');
  put('service',fields.service,b.service,g.revealEnd,'lower');
  const closing=SHORT_ACTIONS[fields.canal]||v.closing;
  const sig=[fields.salon,fields.ville].filter(Boolean).join(' · ');
  put('closing',closing,b.closing,g.end,fields.numero?'closeWithNumber':(sig||fields.tarif)?'close':'single');
  put('signature',sig,b.signature,g.end,fields.numero?'credit0':fields.tarif?'credit1':'credit2','info');
  put('price',fields.tarif,b.signature,g.end,fields.numero?'credit1':'credit2','info');
  put('number',fields.numero,b.signature,g.end,'credit2','info');
  for(const x of out){if(!Number.isInteger(x.on)||x.on<0||x.off>x.on+900||x.off>900||x.off<x.on+12)throw Error('Repère texte invalide.');}
  return {variant:id,revision:config.revision,captions:out,closing,animation:{...g.captionAnimation}};
}
export function visualAnswers(normalized){
  const out=Object.fromEntries([...INPUT_IDS,'prixMode','canal'].map(id=>[id,normalized[id]]));
  if(normalized.numero)out.numero=normalized.numero;
  return out;
}

export function soundPack(rows){
  const safeLicense='https://creativecommons.org/licenses/by/4.0/';
  if(rows.schema!=='vv.music.catalogue/1'||rows.network_required!==false||rows.selection?.no_immediate_repeat!==true||rows.tracks?.map(t=>t.id).join('')!=='ABCD'||new Set(rows.tracks.map(t=>t.track_id)).size!==4)throw Error('Catalogue des quatre pistes invalide.');
  for(const t of rows.tracks){
    if(!/^fma-\d+$/.test(t.track_id)||!t.source.startsWith('https://freemusicarchive.org/music/')||t.licence!==safeLicense||!/^\w[\s\S]+$/u.test(t.title)||!t.artist||t.duration_ms!==30000||t.rate_hz!==48000||t.path!==`fonds/${t.id}.m4a`||!/^[a-f\d]{64}$/.test(t.sha256))throw Error('Source musicale non conforme.');
  }
  return rows;
}
