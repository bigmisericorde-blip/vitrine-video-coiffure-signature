import {normalize,visualAnswers,ASSIST_ACTIONS} from '../texte/modele-visuel.mjs';
import {framing,newId,validId} from './contract.mjs?v=voix-1';

const schema='vv.coiffure.fiche/2', prefix='vv-coiffure-fiche-2:', age=24*60*60*1000;
export function normalizeFiche(raw,core){
  if(!raw||!['client','demo'].includes(raw.source)||!Object.hasOwn(framing,raw.framing))throw Error('Choisis l’origine des prises et le cadrage du résultat.');
  // Une simulation n'utilise jamais de coordonnées, même si une autre fiche les avait.
  const fields=normalize(raw.source==='demo'?{...raw,canal:'aucun',contact:'',contactConfirme:false}:raw,core.questions,core.font);
  const rule=core.questions.fields.find(f=>f.id==='outil');
  const input=raw.outil??'';
  if(typeof input!=='string'||/[\p{Cc}\u202A-\u202E\u2066-\u2069<>]/u.test(input))throw Error('Indique simplement ce que tu utilises, sans caractères de contrôle.');
  const outil=input.normalize('NFC').replace(/\s+/gu,' ').trim();
  if(Array.from(outil).length>rule.max)throw Error(`La réponse sur ce que tu utilises doit contenir ${rule.max} caractères maximum.`);
  const metier=raw.metier||'coiffure';
  if(!globalThis.VVBeaute.profiles.some(p=>p.id===metier))throw Error('Choisis une prestation connue.');
  return Object.freeze({...fields,outil,metier,source:raw.source,framing:raw.framing});
}
export function restoreFiche(id,core){
  if(!validId(id))return null;
  try{
    const item=JSON.parse(sessionStorage.getItem(prefix+id)||'null');
    if(item?.schema!==schema||item.revision!==core.template.editorial_revision||item.until<=Date.now())return null;
    return normalizeFiche(item.answers,core);
  }catch{return null;}
}
export function saveFiche(fields,core,previous){
  const answers={...visualAnswers(fields),outil:fields.outil,metier:fields.metier,source:fields.source,framing:fields.framing,contact:fields.contact,contactConfirme:fields.contactConfirme};
  const id=restoreFiche(previous,core)?previous:newId();
  try{
    for(let i=sessionStorage.length-1;i>=0;i--){const k=sessionStorage.key(i);if(k?.startsWith(prefix)&&!restoreFiche(k.slice(prefix.length),core))sessionStorage.removeItem(k);}
    sessionStorage.setItem(prefix+id,JSON.stringify({schema,revision:core.template.editorial_revision,until:Date.now()+age,answers}));
  }catch{throw Error('Autorise le stockage de cet onglet pour continuer sans envoyer tes réponses.');}
  return id;
}
export function href(page,id,extra={}){
  const query=new URLSearchParams(extra);if(validId(id))query.set('fiche',id);
  return page+(query.size?'?'+query:'');
}
export function sceneText(fiche,n,core){
  if(!fiche)return '';
  const scene=core.guide.scenes[n];
  const context=scene.contexte.replace(/\{(service|framing)\}/g,(_,k)=>k==='service'?fiche.service:framing[fiche.framing]);
  return fiche.outil&&scene.contexte_outil ? context+' · '+scene.contexte_outil.replace('{outil}',fiche.outil) : context;
}
export function contactAction(fiche){
  if(fiche?.source!=='client'||!fiche.destination||!fiche.contactConfirme)return null;
  if(fiche.canal==='lien'&&new URL(fiche.destination).hostname.endsWith('.invalid'))return null;
  return {href:fiche.destination,label:ASSIST_ACTIONS[fiche.canal]};
}
