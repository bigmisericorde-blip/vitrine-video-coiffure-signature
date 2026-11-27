import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {normalize,normalizeVisual,visualAnswers,makeVisualPlan,soundPack} from '../assets/texte/modele-visuel.mjs';
import {createJob,validateJob,createResult,validateResult,failRecord,validError,RenderFault} from '../assets/engine/contract.mjs';
import {fresh,reserve,finish,abandon} from '../assets/engine/rotation.mjs';

const bytes=f=>fs.readFileSync(new URL('../'+f,import.meta.url));
const json=f=>JSON.parse(bytes(f));
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const core={template:json('config/template.json'),questions:json('formulaire/questions.json'),habillage:json('formulaire/habillage.json'),font:json('assets/texte/police.json'),music:soundPack(json('audio/music/catalogue.json'))};
const example=json('formulaire/exemples.json').examples;
const id=n=>digest(String(n)).slice(0,32);
assert.equal(digest(bytes(core.template.paths.plan)),core.template.base.plan_sha256);
assert.equal(digest(bytes('assets/texte/'+core.font.file)),core.font.sha256);
assert.equal(digest(bytes('assets/PlusJakartaSans-Variable.ttf')),core.font.sans.sha256);
for(const t of core.music.tracks){const b=bytes('audio/music/'+t.path);assert.equal(b.length,t.bytes);assert.equal(digest(b),t.sha256);}
let count=0;
for(const x of example){
 const fields=normalize(x.answers,core.questions,core.font), visual=visualAnswers(fields);
 for(const {id:variant} of core.music.tracks){
  const p=makeVisualPlan(normalizeVisual(visual,core.questions,core.font),variant,core.habillage,core.questions);
  assert.equal(p.captions.find(t=>t.key==='service').text,fields.service);
  assert.equal(p.captions.find(t=>t.key==='gesture').text,fields.geste);
  assert.equal(p.captions.find(t=>t.key==='proof').text,fields.preuve);
  assert.equal(p.captions.find(t=>t.key==='reveal').on,581);
  assert.equal(p.captions.some(t=>t.key==='price'),!!fields.tarif);
  assert.equal(p.captions.some(t=>t.key==='signature'),!!(fields.salon||fields.ville));
  assert(p.captions.every(t=>t.on>=0&&t.off<=900&&t.on<t.off&&!t.text.includes('.invalid')&&!t.text.includes('https:')));
  assert(!Object.hasOwn(p,'voice'));
  const job=createJob(core,{id:id(++count),source:'client',detail:count%2===0,view:'profil',answers:fields,variant});
  assert.equal(validateJob(job,core).fields.service,fields.service);
  const out=createResult(job,core,120000,digest('sample'));
  assert.equal(validateResult(out,job,core,120000),out);
  assert.throws(()=>validateJob({...job,answers:{...job.answers,contact:fields.contact}},core));
  assert.throws(()=>validateResult({...out,added_voice_off:true},job,core,120000));
  const voiced={...job,voice:true};validateJob(voiced,core);const voicedResult=createResult(voiced,core,120000,digest('sample'));assert.equal(voicedResult.added_voice_off,true);validateResult(voicedResult,voiced,core,120000);assert.throws(()=>validateResult({...voicedResult,added_voice_off:false},voiced,core,120000));
  assert.throws(()=>validateJob({...job,music:{...job.music,track_id:'fma-0'}},core));
 }
}
const norm=(o={})=>normalize({...example[0].answers,...o},core.questions,core.font);
for(const o of [{service:''},{geste:'<texte>'},{preuve:'🧑🏾'},{prix:'12 34'},{accroche:'Un'},{canal:'lien',contact:'https://user:pass@example.invalid',contactConfirme:true},{canal:'whatsapp',contact:'+2290123456789',contactConfirme:false}])assert.throws(()=>norm(o));
assert.equal(norm({prix:'3500 FCFA',prixMode:'minimum'}).tarif,'À partir de 3\u00a0500 FCFA');
assert.equal(norm({canal:'whatsapp',contact:'+229 01 00 00 00 00',contactConfirme:true}).destination,'https://wa.me/2290100000000');
assert.equal(norm({geste:'  Se\u0301parer   les mèches  '}).geste,'Séparer les mèches');
for(const f of ['job-3-prises','job-4-prises'])validateJob(json('fixtures/contracts/'+f+'.json'),core);
assert(validError(failRecord(new RenderFault('AUDIO_INVALID'),core,id('err'))));

const s=fresh(), totals=Object.fromEntries(core.music.tracks.map(t=>[t.id,0]));
let now=1700000000000;
for(let i=0;i<10000;i++){
 const key=id('new'+i), before=s.last, variant=reserve(s,key,now++);
 assert.notEqual(variant,before);
 assert.equal(reserve(s,key,now++),variant);
 assert.equal(s.last,before);
 if(i%113===0)assert.throws(()=>reserve(s,id('blocked'),now),{code:'ROTATION_BUSY'});
 finish(s,key,variant);totals[variant]++;
 if(i>0){const beforeRetry=s.last,keyOld=id('new'+(i-1)), old=reserve(s,keyOld,now++);finish(s,keyOld,old);assert.equal(s.last,beforeRetry);}
}
const last=s.last;reserve(s,id('cancel'),now);assert(abandon(s,id('cancel')));assert.equal(s.last,last);
reserve(s,id('expired'),now);reserve(s,id('recovered'),now+16*60*1000);assert.equal(s.pending.id,id('recovered'));
console.log(JSON.stringify({form_combinations:count,required_field_and_contact_validation:true,contracts_roundtrip:true,optional_voice_contract:true,resource_hashes:7,rotation_successes:10000,rotation_repeats:0,distribution:totals,stable_retry:true,failure_not_committed:true,abandon_and_expiration:true},null,2));
