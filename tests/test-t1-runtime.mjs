import {validateT1,bindT1Job} from '../assets/t1-contract.mjs';
import fs from 'node:fs';import assert from 'node:assert/strict';
const c=JSON.parse(fs.readFileSync(new URL('../config/t1-beaute.json',import.meta.url)));validateT1(c);
const good={salon:'Atelier',service:'Manucure',ville:'',contact:'',prix:'',geste:'Le geste en action',detail:'Les détails de la prestation',resultat:'Le résultat : Manucure',cta:'Découvrir la prestation'};
assert.equal(bindT1Job(good,c).service,'Manucure');
assert.throws(()=>bindT1Job({...good,salon:''},c));assert.throws(()=>bindT1Job({...good,service:''},c));
for(const mutate of [x=>x.capture.screens.pop(),x=>x.capture.scenes[1].id='S4',x=>x.renderer.binding_fields.salon='service',x=>x.renderer.technical_scene_labels_in_video=true,x=>x.merchant_input.fields[2].required=true]){const bad=structuredClone(c);mutate(bad);assert.throws(()=>validateT1(bad));}
console.log('Contrat : 5 champs, 4 prises, 12 écrans, liaisons et cas invalides OK');
