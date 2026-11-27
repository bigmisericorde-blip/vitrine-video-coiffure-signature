import './metiers.js?v=t2-fiche-visible-3';
import {normalizeVisual,visualAnswers,MUSIC_IDS} from '../texte/modele-visuel.mjs?v=t2-fiche-visible-3';

export const JOB='vv.coiffure.render-job/1', RESULT='vv.coiffure.render-result/1', ERROR='vv.coiffure.render-error/1';
export const knownSlots=Object.freeze(['S1','S2','S3','S4']);
export const framing=globalThis.VVBeaute.framing;
const labels=Object.freeze({
  INVALID_JOB:['Le montage ne correspond pas à la fiche et aux prises validées.',false],
  UNSUPPORTED_MEDIA:['Au moins une prise est illisible, hors format ou trop courte.',true],
  PLATFORM:['Ouvre le gabarit dans Chrome ou Edge récent, en HTTPS ou sur localhost.',false],
  RESOURCE_INVALID:['Une ressource du gabarit manque ou ne correspond pas à la version attendue.',true],
  AUDIO_INVALID:['Le fond musical n’a pas pu être ajouté. Aucun MP4 n’a été livré.',true],
  ROTATION_BUSY:['Un autre montage est à terminer ou à annuler dans ce navigateur.',true],
  STORAGE:['Le stockage ou le verrou de ce navigateur est indisponible. Active le stockage local pour monter.',true],
  TIMEOUT:['L’export est trop long sur cet appareil. Réessaie avec des prises HD plus légères.',true],
  RENDER_FAILED:['Le montage n’a pas abouti. Les prises restent disponibles pour réessayer.',true],
  CANCELLED:['Montage annulé.',true],
});
export const validId=x=>typeof x==='string'&&/^[a-f0-9]{32}$/.test(x);
const sha=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const own=(o,k)=>Object.hasOwn(o,k);
function keys(o,k){return o!==null&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).length===k.length&&k.every(x=>own(o,x));}
export class RenderFault extends Error{
  constructor(code,message){
    const name=own(labels,code)?code:'RENDER_FAILED';
    super(message||labels[name][0]); this.name='RenderFault'; this.code=name; this.retryable=labels[name][1];
  }
}
export function demand(condition,code='INVALID_JOB',message){if(!condition)throw new RenderFault(code,message);}
export function failRecord(error,core,jobId){
  const e=error instanceof RenderFault?error:new RenderFault(error?.name==='AbortError'?'CANCELLED':'RENDER_FAILED');
  return {schema:ERROR,template_id:'COIFFURE-T2',template_version:core?.template.version??null,job_id:validId(jobId)?jobId:null,code:e.code,message:e.message,retryable:e.retryable};
}
export function validError(err){
  return keys(err,['schema','template_id','template_version','job_id','code','message','retryable'])&&err.schema===ERROR&&err.template_id==='COIFFURE-T2'&&(err.template_version===null||typeof err.template_version==='string')&&(err.job_id===null||validId(err.job_id))&&own(labels,err.code)&&typeof err.message==='string'&&err.message.length>0&&err.message.length<=220&&err.retryable===labels[err.code][1];
}
export function newId(){return Array.from(crypto.getRandomValues(new Uint8Array(16)),x=>x.toString(16).padStart(2,'0')).join('');}
export function createJob(core,{id,source,detail,view,answers,variant,voice=false}){
  const t=core.template; const track=core.music.tracks.find(x=>x.id===variant);
  demand(track&&answers);
  const job={schema:JOB,template_id:t.template_id,template_version:t.version,execution_profile:t.execution_profile,audio_profile:t.audio_profile,job_id:id,
    mode:source==='demo'?'technical_fixture':'merchant',slots:detail?['S1','S2','S4']:[...knownSlots],detail:detail?'S3_from_S2':'distinct',framing:view,
    answers:visualAnswers(answers),music:{variant,track_id:track.track_id,catalogue_version:core.music.version}};
  if(voice===true)job.voice=true;
  validateJob(job,core);return job;
}
export function validateJob(job,core){
  const t=core.template;
  const jobKeys=['schema','template_id','template_version','execution_profile','audio_profile','job_id','mode','slots','detail','framing','answers','music'];
  demand(keys(job,own(job,'voice')?[...jobKeys,'voice']:jobKeys));
  demand(!own(job,'voice')||job.voice===true);
  demand(job.schema===JOB&&job.template_id===t.template_id&&job.template_version===t.version&&job.execution_profile===t.execution_profile&&job.audio_profile===t.audio_profile&&validId(job.job_id));
  const reuse=job.detail==='S3_from_S2';
  demand((reuse||job.detail==='distinct')&&(job.mode==='merchant'||job.mode==='technical_fixture'&&!reuse)&&own(framing,job.framing));
  const slots=reuse?['S1','S2','S4']:knownSlots;
  demand(Array.isArray(job.slots)&&job.slots.length===slots.length&&job.slots.every((s,i)=>s===slots[i]));
  demand(keys(job.music,['variant','track_id','catalogue_version'])&&MUSIC_IDS.includes(job.music.variant)&&job.music.catalogue_version===core.music.version);
  const track=core.music.tracks.find(x=>x.id===job.music.variant&&x.track_id===job.music.track_id);demand(track);
  demand(keys(job.answers,['service','geste','preuve','accroche','salon','ville','prix','prixMode','canal',...(own(job.answers,'numero')?['numero']:[])])&&Object.values(job.answers).every(x=>typeof x==='string'));
  let fields;try{fields=normalizeVisual(job.answers,core.questions,core.font);}catch{throw new RenderFault('INVALID_JOB');}
  demand(Object.entries(visualAnswers(fields)).every(([k,v])=>job.answers[k]===v));
  return {fields,track,reuse,slots};
}
export function createResult(job,core,byteLength,hash){
  const t=core.template;
  const result={schema:RESULT,template_id:t.template_id,template_version:t.version,job_id:job.job_id,mode:job.mode,source_count:job.slots.length,detail:job.detail,music:{...job.music},media:{...t.media,bytes:byteLength,sha256:hash},added_voice_off:job.voice===true};
  validateResult(result,job,core,byteLength);return result;
}
export function validateResult(r,job,core,bytes){
  const m=core.template.media;
  const ok=keys(r,['schema','template_id','template_version','job_id','mode','source_count','detail','music','media','added_voice_off'])&&r.schema===RESULT&&r.template_id===job.template_id&&r.template_version===job.template_version&&r.job_id===job.job_id&&r.mode===job.mode&&r.source_count===job.slots.length&&r.detail===job.detail&&r.added_voice_off===(job.voice===true)&&
    keys(r.music,['variant','track_id','catalogue_version'])&&Object.entries(job.music).every(([k,v])=>r.music[k]===v)&&
    keys(r.media,[...Object.keys(m),'bytes','sha256'])&&Object.entries(m).every(([k,v])=>r.media[k]===v)&&Number.isSafeInteger(bytes)&&r.media.bytes===bytes&&bytes>15000&&bytes<=64*1024*1024&&sha(r.media.sha256);
  demand(ok,'RENDER_FAILED');return r;
}
