/* Vérification des questions, des scènes et des douze destinations T4. */
(()=>{'use strict';const ids=['S1','S2','S3','S4'],states=['A_GUIDE','B_ENREGISTREMENT_OU_LECTURE_IMPORT','C_RELECTURE'];
 const fields=['nom','service','geste','detail','lieu','telephone','prix','action'],contexts=['service','geste','detail','service'];
 const dest=[['signature'],['guide_S1','guide_S4','film'],['guide_S2'],['guide_S3','film'],['signature'],['signature_apres_accord'],['signature_apres_confirmation'],['film_apres_confirmation']];
 const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b), text=x=>typeof x==='string'&&x.trim().length>0;
 function questions(q,c){if(q?.template_id!=='BEAUTE-T4'||q.version!=='1.0.0'||!text(q.objectif)||!Array.isArray(q.questions)||q.questions.length!==8)throw Error('Questions T4 invalides.');q.questions.forEach((x,i)=>{let id=fields[i],r=i<2;if(x.id!==id||!text(x.libelle)||x.obligatoire!==r||c.fiche[id]?.requis!==r||!same(x.destinations,dest[i]))throw Error('Une question ne correspond pas au contrat T4.');});return q;}
 function guide(g){if(g?.template_id!=='BEAUTE-T4'||g.version!=='1.0.0'||!Array.isArray(g.scenes)||g.scenes.length!==4||!Array.isArray(g.screens)||g.screens.length!==12)throw Error('Guide T4 invalide.');
 g.scenes.forEach((s,i)=>{let nxt=ids[i+1]||'EXPORT';if(s.id!==ids[i]||s.scene_suivante!==nxt||s.contexte_champ!==contexts[i]||!same(s.etats,states)||!text(s.titre_affiche)||!text(s.consigne)||!Array.isArray(s.a_filmer)||!s.a_filmer.length||!s.a_filmer.every(text)||!Array.isArray(s.a_eviter)||!s.a_eviter.length||!s.a_eviter.every(text))throw Error('Une prise du guide T4 est invalide.');states.forEach((st,j)=>{let e=g.screens[i*3+j],want=j<2?ids[i]+'_'+states[j+1]:nxt==='EXPORT'?'EXPORT':nxt+'_A_GUIDE';if(!e||e.id!==ids[i]+'_'+st||e.scene!==ids[i]||e.etat!==st||e.next_screen!==want)throw Error('La navigation du guide T4 est incohérente.');});});return g;}
 window.T4Contrats={questions,guide};
})();
