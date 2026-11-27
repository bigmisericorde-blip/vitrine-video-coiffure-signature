/* Contrat commun au formulaire, aux écrans et au moteur T1 beauté. */
const expect=(condition,message)=>{if(!condition)throw Error(message);};
export function validateT1(c){
  expect(c?.schema==='vv.beaute.t1.runtime/1'&&c.template_id==='T1_BEAUTE','Contrat T1 inconnu.');
  const fields=c.merchant_input?.fields, scenes=c.capture?.scenes, screens=c.capture?.screens, r=c.renderer;
  expect(Array.isArray(fields)&&fields.map(f=>f.id).join(',')==='salon,service,ville,contact,prix','Cinq champs T1 requis.');
  expect(fields.every((f,i)=>typeof f.question==='string'&&f.question.length>5&&f.required===(i<2)&&Number.isInteger(f.max_length)&&f.max_length>0&&f.max_length<=100&&['text','tel'].includes(f.type)),'Règles des champs T1 invalides.');
  expect(Array.isArray(scenes)&&scenes.length===4&&scenes.every((s,i)=>s.id===`S${i+1}`&&s.n===i+1&&s.total===4&&Number.isInteger(s.secondes)&&s.secondes>0&&s.media===`${s.id}.mp4`&&typeof s.titre==='string'&&typeof s.consigne==='string'&&typeof s.contexte==='string'&&typeof s.question_relecture==='string'&&typeof s.example==='string'&&Array.isArray(s.a_filmer)&&Array.isArray(s.a_eviter)),'Quatre prises T1 invalides.');
  expect(Array.isArray(screens)&&screens.length===12&&screens.every((s,i)=>s.ordinal===i+1&&s.scene_id===scenes[Math.floor(i/3)].id&&s.state===['A_GUIDE','B_RECORDING','C_REVIEW'][i%3]&&typeof s.label==='string'&&s.label.length>0&&s.capture_slot===`captures.${s.scene_id}`&&s.duration_ms===1000*scenes[Math.floor(i/3)].secondes&&s.screen_id===`T1_CAPTURE_${s.scene_id}_${s.state}`&&s.next_screen===(i===11?'T1_MONTAGE_STATUS':`T1_CAPTURE_S${Math.floor((i+1)/3)+1}_${['A_GUIDE','B_RECORDING','C_REVIEW'][(i+1)%3]}`)&&s.retake_screen===(i%3===2?`T1_CAPTURE_${s.scene_id}_A_GUIDE`:null)),'Douze écrans T1 invalides.');
  expect(r?.plan_path==='ingenierie/plan.json'&&r.plan_schema==='vv.coiffure.plan/1.0'&&r.width===720&&r.height===1280&&r.fps===30&&r.frames===900&&r.duration_s===30&&r.requires_scenes.join(',')==='S1,S2,S3,S4'&&r.technical_scene_labels_in_video===false,'Montage T1 incompatible.');
  const keys=['salon','service','ville','contact','prix','geste','detail','resultat','cta'];
  expect(keys.every(k=>r.binding_fields?.[k]===k)&&Object.keys(r.binding_fields).length===keys.length,'Liaisons de montage inconnues.');
  return c;
}
export function bindT1Job(job,c){
  expect(job&&typeof job==='object'&&!Array.isArray(job),'Fiche absente.');
  const mapped={};
  for(const [target,source] of Object.entries(c.renderer.binding_fields)){
    const value=job[source];expect(typeof value==='string'&&value.length<=160,`Champ ${source} invalide.`);mapped[target]=value;
  }
  for(const f of c.merchant_input.fields){
    const x=mapped[f.id];expect(!f.required||x.trim().length>0,`${f.question} : réponse obligatoire.`);
    // La normalisation du prix peut ajouter le préfixe, après contrôle du champ de saisie.
    expect(x.length<=f.max_length+(f.id==='prix'?12:0),`Champ ${f.id} trop long.`);
  }
  return mapped;
}
