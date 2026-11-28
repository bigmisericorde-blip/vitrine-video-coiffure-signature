import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {normalizeVisual,makeVisualPlan,visualAnswers} from '../assets/texte/modele-visuel.mjs';
const root=new URL('../',import.meta.url),get=async p=>JSON.parse(await readFile(new URL(p,root)));
const [questions,font,habillage]=await Promise.all(['formulaire/questions.json','assets/texte/police.json','formulaire/habillage-onglerie.json'].map(get));
const raw={salon:'Awa Ongles',service:'Pose de vernis',outil:'Pinceau fin',ville:'Cotonou Akpakpa',prix:'2500',prixMode:'minimum',canal:'aucun',geste:'',preuve:'',accroche:''};
for(const outil of ['Pinceau fin','Peigne et brosse','']){
 const fields=normalizeVisual({...raw,outil},questions,font),job=visualAnswers(fields);
 assert.equal(job.outil,outil);
 for(const id of ['A','B','C','D']){
  const plan=makeVisualPlan(fields,id,habillage,questions),text=plan.captions.find(x=>x.key==='gesture');
  assert.equal(text?.text||'',outil);
 }
}
assert.throws(()=>normalizeVisual({...raw,outil:'X'.repeat(61)},questions,font));
console.log('T2 : outil transmis au RenderJob et affiché dans les 4 variantes ; champ vide et longueur contrôlés.');
