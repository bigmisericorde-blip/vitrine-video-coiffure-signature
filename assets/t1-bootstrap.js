/* Le JSON est chargé avant chaque écran : en son absence, aucun parcours trompeur. */
(() => {
  'use strict';
  const page=document.currentScript.dataset.page;
  const load=src=>new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=()=>reject(Error('Ressource indisponible : '+src));document.head.appendChild(s);});
  async function init(){
    const response=await fetch('config/t1-beaute.json',{cache:'no-cache',redirect:'error'});
    if(!response.ok)throw Error('Le contrat T1 est indisponible.');
    const c=await response.json();
    const {validateT1}=await import('./t1-contract.mjs?v=1');validateT1(c);
    window.VV_T1_CONTRACT=c;
    window.CONSIGNES_T2={...window.CONSIGNES_T2,scenes:c.capture.scenes.map((s,i)=>({...window.CONSIGNES_T2.scenes[i],...s,exemple:s.example}))};
    if(page==='fiche'){
      const target=document.getElementById('commercialFields');
      for(const [i,field] of c.merchant_input.fields.entries()){
        const row=document.createElement('div'),label=document.createElement('label'),input=document.createElement('input');
        label.htmlFor=field.id;label.textContent=`${i+1}. ${field.question}`;row.append(label);
        if(field.hint){const hint=document.createElement('small');hint.id='hint-'+field.id;hint.textContent=field.hint;input.setAttribute('aria-describedby',hint.id);row.append(hint);}
        input.id=input.name=field.id;input.type=field.type;input.maxLength=field.max_length;input.placeholder=field.example;input.required=field.required;if(field.type==='tel')input.inputMode='tel';row.append(input);target.append(row);
      }
    }
    await load('assets/fiche-t2.js?v=contrat-t1-1');
    if(page==='fiche')await load('assets/test.js?v=contrat-t1-1');
    else if(page==='galerie')await load('assets/ecrans.js?v=contrat-t1-1');
    else if(page==='capture'){
      await load('assets/afrobeat-catalogue.js?v=selection-fma-1');await load('assets/tirage-son.js?v=t2-1');
      await load('ingenierie/prises-web.js?v=t2-1');await load('assets/simulation-t2.js?v=contrat-t1-1');
    }else throw Error('Écran inconnu.');
    document.documentElement.dataset.t1Ready='yes';
  }
  init().catch(e=>{document.documentElement.dataset.t1Ready='error';const target=document.getElementById('ready')||document.getElementById('screenError')||document.getElementById('consigne');if(target){target.hidden=false;target.textContent='Le parcours T1 n’a pas chargé. Recharge la page. '+e.message;}console.error(e);});
})();
