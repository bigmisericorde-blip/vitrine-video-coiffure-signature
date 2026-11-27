'use strict';
(() => {
 const data=window.CONSIGNES_T2, fiche=window.VVFicheT2, $=id=>document.getElementById(id);
 const el=(tag,text)=>{const x=document.createElement(tag);x.textContent=text;return x;};
 const q=new URLSearchParams(location.search), previous=q.get('fiche');
 const form=$('testForm');
 const restored=fiche.restore(previous), initial=restored||fiche.initial;
 if(previous&&!restored)$('ready').textContent='Cette fiche n’est plus dans cet onglet. Tu peux la remplir à nouveau.';
 $('caseLabel').textContent='GABARIT T1 · COIFFURE & BEAUTÉ';
 for(const id of ['salon','service','ville','contact','prix'])$(id).value=restored?initial[id]:'';
 form.elements.source.value=initial.source;
 if(restored)document.querySelectorAll('[data-gallery]').forEach(a=>a.href=fiche.href('ecrans.html',previous));
 data.scenes.forEach((original,i)=>{const s=fiche.sceneGuide(null,i,original),li=el('li','');li.append(el('span',String(s.n).padStart(2,'0')),el('b',s.titre),el('small',s.secondes+' s')); $('captureList').append(li);});
 $('filmLink').href='film.html?test='+encodeURIComponent(data.id);
 const readiness=()=>form.querySelectorAll('button[type=submit]').forEach(b=>b.disabled=!$('checkedCase').checked);
 $('checkedCase').addEventListener('change',readiness);readiness();
 form.addEventListener('submit',ev=>{
  ev.preventDefault();if(!$('checkedCase').checked)return;
  try {
   const fields=Object.fromEntries(new FormData(form));
   const id=fiche.save(fields,previous);
   const destination=ev.submitter?.id==='previewScreens'?'ecrans.html':'simulation.html';
   location.href=fiche.href(destination,id,destination==='simulation.html'?{test:data.id}:{});
  } catch(err){$('ready').textContent=err.message;}
 });
})();
