import {MUSIC_IDS} from '../texte/modele-visuel.mjs?v=t2-fiche-visible-3';
import {RenderFault,validId} from './contract.mjs?v=t2-fiche-visible-3';

// Une réservation à la fois par origine et catalogue, comme dans l’orchestrateur de référence.
// Une erreur garde la piste du job ; seul un résultat validé change le dernier succès.
const KEEP=128, LEASE_MS=15*60*1000;
export const fresh=()=>({schema:1,last:null,pending:null,recent:[]});
const choice=x=>MUSIC_IDS.includes(x);
function stored(raw){
  if(raw===null)return fresh();
  try{
    const s=JSON.parse(raw);
    if(s.schema!==1||!Array.isArray(s.recent)||s.recent.length>KEEP||!s.recent.every(p=>Array.isArray(p)&&p.length===2&&validId(p[0])&&choice(p[1])))throw Error();
    const ids=new Set(s.recent.map(p=>p[0]));
    if(ids.size!==s.recent.length||s.last!==(s.recent[0]?.[1]??null))throw Error();
    const p=s.pending;
    if(p!==null&&(!validId(p.id)||ids.has(p.id)||!choice(p.variant)||p.variant===s.last||!Number.isSafeInteger(p.at)||p.at<0))throw Error();
    return s;
  }catch{throw new RenderFault('STORAGE','La rotation locale est illisible. Vérifie le stockage du site avant de recommencer.');}
}
export function reserve(s,id,now){
  if(!validId(id))throw new RenderFault('INVALID_JOB');
  const done=s.recent.find(p=>p[0]===id);if(done)return done[1];
  if(s.pending&&(now-s.pending.at>LEASE_MS||s.pending.at-now>LEASE_MS))s.pending=null;
  if(s.pending&&s.pending.id!==id)throw new RenderFault('ROTATION_BUSY');
  const pool=MUSIC_IDS.filter(letter=>letter!==s.last);
  const variant=s.pending?.variant??pool[Number.parseInt(id.slice(0,8),16)%pool.length];
  s.pending={id,variant,at:now};return variant;
}
export function finish(s,id,variant){
  const existing=s.recent.find(p=>p[0]===id);
  if(existing?.[1]===variant)return;
  if(!s.pending||s.pending.id!==id||s.pending.variant!==variant||s.last===variant)throw new RenderFault('ROTATION_BUSY');
  s.last=variant;s.pending=null;s.recent=[[id,variant],...s.recent].slice(0,KEEP);
}
export function abandon(s,id){
  if(s.pending?.id===id){s.pending=null;return true;}
  return false;
}
function keyOf(core){
  return ['vv-coiffure-rotation-1',core.template.template_id,core.template.audio_profile,core.music.version].join(':');
}
function read(key){
  let raw;try{raw=localStorage.getItem(key);}catch{throw new RenderFault('STORAGE');}
  return stored(raw);
}
function store(key,s){try{localStorage.setItem(key,JSON.stringify(s));}catch{throw new RenderFault('STORAGE');}}
function locks(){if(!globalThis.navigator?.locks)throw new RenderFault('STORAGE');return navigator.locks;}
export function rotate(core,id,signal,render){
  const key=keyOf(core);
  return locks().request(key,{mode:'exclusive',signal},async()=>{
    signal.throwIfAborted();const s=read(key), before=JSON.stringify(s), variant=reserve(s,id,Date.now());
    if(JSON.stringify(s)!==before)store(key,s);
    const result=await render(variant);
    signal.throwIfAborted();
    if(!result||result.result?.music?.variant!==variant||result.result.job_id!==id)throw new RenderFault('RENDER_FAILED');
    finish(s,id,variant);store(key,s);
    return result;
  });
}
export function releaseReservation(core,id){
  const key=keyOf(core);
  return locks().request(key,()=>{const s=read(key);if(abandon(s,id))store(key,s);});
}
