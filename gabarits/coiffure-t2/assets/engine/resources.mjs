import {EDITION,soundPack} from '../texte/modele-visuel.mjs?v=t2-fiche-visible-3';

const root=new URL('../../',import.meta.url);
const safePath=/^(?:[a-zA-Z0-9_-]+\/)*[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)+$/;
export function resourceURL(path){
  if(typeof path!=='string'||!safePath.test(path))throw Error('Chemin de ressource invalide.');
  return new URL(path,root);
}
async function get(path){
  const response=await fetch(resourceURL(path),{credentials:'same-origin',redirect:'error',cache:'no-cache'});
  if(!response.ok)throw Error('Une ressource locale du gabarit est indisponible.');
  return response;
}
export async function readJson(path){return (await get(path)).json();}
export function digest(buffer){
  return crypto.subtle.digest('SHA-256',buffer).then(v=>Array.from(new Uint8Array(v),b=>b.toString(16).padStart(2,'0')).join(''));
}
export async function readBytes(path,expected,exact){
  const r=await get(path);
  const bytes=await r.arrayBuffer();
  if(!/^[a-f0-9]{64}$/.test(expected)||exact!==undefined&&bytes.byteLength!==exact||await digest(bytes)!==expected)
    throw Error('L’empreinte d’une ressource locale ne correspond pas au gabarit.');
  return bytes;
}
function assert(x){if(!x)throw Error('Les ressources du gabarit ne sont pas de la même révision.');}
let shared;
export function loadCore(){return shared || (shared=load().catch(e=>{shared=undefined;throw e;}));}
async function load(){
  const t=await readJson('config/template.json');
  assert(t.schema==='vv.coiffure.template/1'&&t.template_id==='COIFFURE-T2'&&/^\d+\.\d+\.\d+(?:-rc\.\d+)?$/.test(t.version)&&t.execution_profile==='browser-webcodecs');
  assert(t.editorial_revision===EDITION&&t.audio.added_voice_off===false&&t.audio.optional_voice_off===true&&t.audio.source_audio_in_output===false&&t.audio.tracks_per_output===1&&t.audio.no_immediate_repeat===true&&t.audio.fixture_affects_rotation===false);
  const v=t.media;
  assert(v.mime==='video/mp4'&&v.video_codec==='h264'&&v.width===720&&v.height===1280&&v.fps===30&&v.frames===900&&v.duration_ms===30000&&v.audio_codec==='aac-lc'&&v.audio_channels===2&&v.audio_sample_rate===48000);
  const p=t.paths;
  const [questions,habillage,font,music,guide]=await Promise.all([p.questions,p.habillage,p.font_meta,p.catalogue,p.guide].map(readJson));
  assert(questions.schema==='vv.coiffure.questions/1'&&questions.revision===EDITION&&habillage.schema==='vv.coiffure.habillage/1'&&habillage.revision===EDITION&&habillage.base===t.base.revision);
  assert(font.family==='Dancing Script'&&font.file==='DancingScript-Variable.ttf'&&font.bytes===133636
    &&font.sha256==='21808625578fe8d8cd10cb684be546dca077b27cd03a53a2f1ec11dc743c924c'
    &&font.sans.file==='../PlusJakartaSans-Variable.ttf');
  soundPack(music);
  assert(music.version===t.audio.catalogue_version&&music.audio_profile===t.audio_profile&&music.r04_base_sha256===t.base.approved_master_sha256);
  assert(Array.isArray(questions.fields)&&questions.fields.map(f=>f.id).join(',')==='salon,service,outil,ville,contact,prix'&&questions.fields.every((f,i)=>f.required===(i<2)&&typeof f.question==='string'&&Array.isArray(f.render_targets)&&f.render_targets.join(',')===['signature.name','reveal.service','','signature.city','number','price'][i]));
  assert(Array.isArray(questions.engine_fields)&&questions.engine_fields.map(f=>f.id).join(',')==='geste,preuve,accroche,canal'&&questions.flow_contract?.guide===p.guide&&questions.flow_contract?.plan===p.plan&&questions.flow_contract?.engine===p.worker);
  assert(guide.schema==='vv.coiffure.capture/1'&&guide.id===t.template_id&&guide.scenes.length===4&&guide.screens.length===12&&guide.source_audio===t.capture.source_audio);
  for(const [i,screen] of guide.screens.entries()){
    const slot=`S${Math.floor(i/3)+1}`,state=['A','B','C'][i%3],suffix=['A_GUIDE','B_RECORDING','C_REVIEW'][i%3];
    assert(screen.order===i+1&&screen.slot===slot&&screen.state===state&&screen.id===`${t.template_id}.${slot}_${suffix}`&&typeof screen.label==='string'&&screen.next_screen===(i===11?`${t.template_id}.VOICE_CHOICE`:`${t.template_id}.S${Math.floor((i+1)/3)+1}_${['A_GUIDE','B_RECORDING','C_REVIEW'][(i+1)%3]}`)&&screen.retake_screen===(i%3===2?`${t.template_id}.${slot}_A_GUIDE`:null));
  }
  for(const [i,scene] of guide.scenes.entries()){
    assert(scene.id===`S${i+1}`&&scene.secondes===t.capture.min_seconds[scene.id]&&scene.fixture_path===`fixtures/media/${scene.id}.mp4`&&scene.question_relecture===questions.capteurs[i].review&&scene.consigne===questions.capteurs[i].guide&&scene.question_links?.join(',')===(i===1?'service,outil':'service')&&(i!==1||scene.contexte_outil?.includes('{outil}'))&&typeof scene.contexte==='string'&&scene.contexte.includes('{service}')&&Array.isArray(scene.a_filmer)&&Array.isArray(scene.a_eviter));
  }
  return Object.freeze({template:t,questions,habillage,font,music,guide});
}
export async function loadPlan(core){
  const bytes=await readBytes(core.template.paths.plan,core.template.base.plan_sha256);
  return JSON.parse(new TextDecoder().decode(bytes));
}
export function loadFonts(core){
  const {font}=core;
  return Promise.all([readBytes('assets/texte/'+font.file,font.sha256,font.bytes),readBytes('assets/PlusJakartaSans-Variable.ttf',font.sans.sha256,font.sans.bytes)]);
}
export function loadBed(track){return readBytes('audio/music/'+track.path,track.sha256,track.bytes);}
