import {loadExample} from './donnees.mjs';
const $ = id => document.getElementById(id);
const names = ['Consigne','Enregistrement','Relecture'];
const entries = [];
let current = 0;
const frame = $('screenLive'), select = $('screenSelect');
const allowed = n => Number.isInteger(n) && n >= 1 && n <= 12;
const path = n => `prise.html?ecran=${n}`;
function show(value) {
  const n = allowed(value) ? value : 1;
  if (!entries.length || current === n) return;
  current = n;
  for (const e of entries) {
    if (e.n === n) e.a.setAttribute('aria-current','true');
    else e.a.removeAttribute('aria-current');
  }
  const e = entries[n-1];
  $('screenLabel').textContent = e.label;
  $('screenText').textContent = e.copy;
  $('screenAlone').href = path(n);
  $('screenPrev').disabled = n === 1;
  $('screenNext').disabled = n === 12;
  select.value = String(n);
  frame.title = e.label;
  frame.hidden = false;
  frame.src = path(n);
}
function choose(n, jump=false) {
  if (!allowed(n)) return;
  if (location.hash !== `#${n}`) history.pushState(null, '', `#${n}`);
  show(n);
  if (jump && matchMedia('(max-width:760px)').matches) $('apercu').scrollIntoView({block:'start'});
}
function jumpFromURL(){const m=/^#([0-9]{1,2})$/.exec(location.hash); if (m) show(Number(m[1])); else if (!location.hash) show(1);}
async function main() {
  const {guide,gallery} = await loadExample();
  guide.scenes.forEach((scene, i)=>{
    const clip = gallery.clips[i], group = document.createElement('section'), title = document.createElement('h2'), row = document.createElement('div');
    group.className = 'screen-group'; row.className = 'screen-row';
    title.textContent = `Prise ${i+1} · ${clip.label.toLowerCase()}`; group.append(title,row);
    names.forEach((phase,j)=>{
      const n = i*3+j+1, rank = String(n).padStart(2,'0'), a = document.createElement('a'), small = document.createElement('small');
      a.href = `#${n}`; a.dataset.ecran = n; small.textContent = rank;
      a.append(small,document.createTextNode(phase)); row.append(a);
      select.append(new Option(`${rank} · Prise ${i+1} : ${phase}`, String(n)));
      entries.push({a,n,label:`Écran ${n}/12 · Prise ${i+1} · ${phase}`,copy:[scene.consigne,`${clip.illustration} ${clip.seconds} s, au rythme de la vidéo.`,scene.question_relecture][j]});
      a.addEventListener('click',ev=>{if(ev.button || ev.metaKey || ev.shiftKey || ev.ctrlKey || ev.altKey) return;ev.preventDefault();choose(n,true);});
    });
    $('screenList').append(group);
  });
  const music=gallery.result?.music;
  if(music && /^https:\/\/freemusicarchive\.org\//.test(music.source)){
    const link=document.createElement('a');link.href=music.source;link.textContent=`${music.title} — ${music.artist}`;
    $('musicCredit').append('Musique seule, sans voix off : ', link, ' · CC BY 4.0.');
  }
  select.disabled = false;
  select.onchange = () => choose(Number(select.value));
  $('screenPrev').onclick = () => choose(current-1);
  $('screenNext').onclick = () => choose(current+1);
  window.addEventListener('hashchange',jumpFromURL);
  window.addEventListener('popstate',jumpFromURL);
  window.addEventListener('message',ev=>{
    if (ev.origin!==location.origin || ev.source!==frame.contentWindow || ev.data?.type!=='coiffure-demo/choose') return;
    if (ev.data.from!==current) return;
    if ((current-1)%3===0 && ev.data.screen===current+1) choose(current+1,true);
    if (current%3===0 && ev.data.screen===current-2) choose(current-2,true);
    if (current%3===0 && ev.data.screen===current+1) {
      if (current===12) {location.hash='resultat';$('resultTitle').focus({preventScroll:true});}
      else choose(current+1,true);
    }
  });
  jumpFromURL();if(!current)show(1);
  if(/^#[0-9]{1,2}$/.test(location.hash) && matchMedia('(max-width:760px)').matches) requestAnimationFrame(()=>$('apercu').scrollIntoView({block:'start'}));
  document.documentElement.dataset.ready='yes';
}
main().catch(()=>{$('screenError').hidden=false;document.documentElement.dataset.ready='error';});
