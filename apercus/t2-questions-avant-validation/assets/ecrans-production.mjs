import {loadCore} from './engine/resources.mjs?v=t2-six-q2';
import {href,restoreFiche} from './engine/fiche.mjs?v=t2-six-q2';
const $=id=>document.getElementById(id), nav=$('screenList'), select=$('screenSelect');
const entries=[],ticket=new URLSearchParams(location.search).get('fiche');
let names=[];
async function init(){
  const core=await loadCore(),guide=core.guide,job=restoreFiche(ticket,core);
  names=guide.screens.slice(0,3).map(x=>x.label);
  const metier=job?.metier||new URLSearchParams(location.search).get('metier')||'manucure';
  const scenes=globalThis.VVBeaute.scenes(guide.scenes,metier,'t2');
  if(ticket){$('galleryCase').hidden=false;$('galleryCase').textContent=job?'Ta fiche est disponible dans cet onglet. La galerie présente des images de démonstration.':'La fiche n’est plus dans cet onglet. Voici les écrans de recette.';}
  if(job)document.querySelectorAll('a[href="index.html"]').forEach(a=>a.href=href('index.html',ticket));
  for(const [i,scene] of scenes.entries()){
    const group=document.createElement('section');group.className='screen-group';
    const title=document.createElement('h2');title.textContent=`Prise ${i+1} · ${scene.titre.toLowerCase()}`;group.append(title);
    const row=document.createElement('div');row.className='screen-row';
    for(const [j,step] of names.entries()){
      const n=i*3+j+1,a=document.createElement('a'),rank=String(n).padStart(2,'0');
      const url=href('simulation.html',job?ticket:null,{ecran:n,metier});
      const label=`Écran ${n}/12 · Prise ${i+1} · ${step}`;
      const copy=[scene.consigne,`Durée minimale : ${scene.secondes} secondes.`,scene.question_relecture][j];
      a.href=`#${n}`;a.dataset.ecran=String(n);
      const order=document.createElement('small');order.textContent=rank;a.append(order,document.createTextNode(step));
      a.addEventListener('click',ev=>{if(ev.button!==0||ev.ctrlKey||ev.metaKey||ev.shiftKey||ev.altKey)return;ev.preventDefault();choose(n);if(matchMedia('(max-width: 760px)').matches)$('apercu').scrollIntoView({block:'start'});});
      row.append(a);select.append(new Option(`${rank} · Prise ${i+1} : ${step}`,String(n)));entries.push({n,a,url,label,copy});
    }
    group.append(row);nav.append(group);
  }
  let current=0;
  function show(n){
    const o=Number.isInteger(n)&&entries[n-1]?entries[n-1]:entries[0]; if(current===o.n)return;current=o.n;
    entries.forEach(({a,n})=>{if(n===current)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');});
    $('screenLabel').textContent=o.label;$('screenText').textContent=o.copy;$('screenAlone').href=o.url;
    select.value=String(current);$('screenPrev').disabled=current===1;$('screenNext').disabled=current===entries.length;
    $('screenLive').hidden=false;$('screenLive').src=o.url;
  }
  function choose(n){if(!entries[n-1])return;if(location.hash!==`#${n}`)history.pushState(null,'',`#${n}`);show(n);}
  const fromUrl=()=>show(Number(location.hash.slice(1)));
  window.addEventListener('hashchange',fromUrl);window.addEventListener('popstate',fromUrl);
  $('screenPrev').onclick=()=>choose(current-1);$('screenNext').onclick=()=>choose(current+1);select.onchange=()=>choose(Number(select.value));
  fromUrl();document.documentElement.dataset.ready='yes';
}
init().catch(()=>{$('screenError').hidden=false;document.documentElement.dataset.ready='error';});
