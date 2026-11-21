/* Les vues de la galerie sont des aperçus. Une validation n’a d’effet que dans l’essai séparé. */
(()=>{'use strict';
const $=id=>document.getElementById(id), d=JSON.parse($('vv-data').textContent), phase=['Consigne','Chrono','Relecture'];
const text=(id,s)=>{$(id).textContent=s;}, two=i=>String(i).padStart(2,'0');
const media=f=>{const raw=atob(f.b64), out=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);return URL.createObjectURL(new Blob([out],{type:'video/mp4'}));};
const parts=d.scenes;
const movie=media(d.film), film=$('film'); film.src=movie;film.poster=d.poster; $('downloadDemo').href=movie;
text('version','T3');text('profileLabel','Soin du visage');text('galleryCase','Soin du visage · Images d’exemple, pas une offre réelle.');text('filmTitre','Soin du visage — film d’exemple');
text('filmCredit','Film muet · Images : Mixkit. Le carton « Réserver ce soin » n’ouvre pas de lien.');
for(const k of ['resultat','essai','jumpFilm'])$(k).hidden=false;
$('secteur').href='#accueil';$('return').href='#fiche';$('essai').href='#essai';$('another').href='#fiche';
const planche=$('vv-planche-data').textContent;
$('vv-planche-link').hidden=planche==='null';
const nav=$('screenList'),select=$('screenSelect'),make=(tag,s)=>{const el=document.createElement(tag);if(s)el.textContent=s;return el;};
const listing=[];
for(const [i,p] of parts.entries()){
 const group=make('section');group.className='screen-group';group.append(make('h2',`Prise ${i+1} · ${p.role}`));const row=make('div');row.className='screen-row';
 for(const [j,label] of phase.entries()){
  const n=i*3+j+1, link=make('a'), rank=two(n), title=`Écran ${rank}/12 · ${p.role} · ${label}`;
  link.href='#'+n;link.dataset.ecran=n;link.append(make('small',rank),document.createTextNode(label));link.setAttribute('aria-label',title);row.append(link);
  listing.push({n,i,j,link,title,copy:[p.consignes[0],`Chrono simulé : il suit les ${p.duree.toFixed(1).replace('.',',')} secondes de l’extrait.`,p.question][j]});
  select.append(new Option(`${rank} · ${p.role} : ${label}`,String(n)));
  link.addEventListener('click',e=>{if(e.ctrlKey||e.metaKey||e.shiftKey||e.altKey||e.button!==0)return;e.preventDefault();go('#'+n);if(matchMedia('(max-width:760px)').matches)$('apercu').scrollIntoView({block:'start'});});
 } group.append(row);nav.append(group);
}
const screen=$('screenLive'),solo=$('vv-solo-frame');let shown=0,routeKey='',token=0;
function inject(frame,n,demo=false){
 const config={n,demo,token:++token,parts:demo?parts:parts.map((x,i)=>{if(i===Math.floor((n-1)/3))return x;const {b64,...labels}=x;return labels;})};
 const payload=JSON.stringify(config).replace(/</g,'\\u003c'); frame.srcdoc=d.prise.replace('__PRISE_CONFIG__',payload);
}
function show(n){
 const x=listing[n-1]||listing[0];if(shown===x.n&&screen.srcdoc)return;shown=x.n;
 for(const a of listing){if(a===x)a.link.setAttribute('aria-current','step');else a.link.removeAttribute('aria-current');}
 text('screenLabel',x.title);text('screenText',x.copy);text('screenDetail',parts[x.i].exemple);
 select.value=String(shown);$('screenPrev').disabled=shown===1;$('screenNext').disabled=shown===12;$('screenAlone').href='#seul-'+shown;inject(screen,shown);
}
function clear(frame){if(frame.srcdoc){frame.removeAttribute('srcdoc');frame.src='about:blank';}}
function renderRoute(raw,scroll){
 const old=raw.match(/^#ecran-(0[1-9]|1[0-2])$/);const hash=old?'#'+Number(old[1]):raw||'#1';if(hash===routeKey&&!scroll)return;routeKey=hash;
 const single=hash.match(/^#seul-([1-9]|1[0-2])$/), demo=hash==='#essai', lone=!!single||demo, aux=['#fiche','#accueil','#credits',...(planche==='null'?[]:['#planche'])].includes(hash)?hash.slice(1):null;
 document.body.classList.toggle('vv-solo',lone);$('vv-solo').hidden=!lone;$('vv-gallery').hidden=lone||!!aux;
 for(const id of ['fiche','accueil','credits','planche'])$('vv-'+id).hidden=id!==aux;
 if(lone){film.pause();clear(screen);const n=demo?1:Number(single[1]);$('vv-back').href='#'+n;text('vv-solo-label',demo?'Essai · caméra simulée':`Écran ${two(n)}/12 · consultation`);inject(solo,n,demo);if(scroll)window.scrollTo(0,0);return;}
 clear(solo);if(aux){if(aux==='planche'&&!$('vv-planche-img').src)$('vv-planche-img').src='data:image/jpeg;base64,'+JSON.parse(planche);film.pause();clear(screen);if(scroll)window.scrollTo(0,0);return;}
 const num=hash.match(/^#([1-9]|1[0-2])$/);show(num?Number(num[1]):shown||1);
 if(hash==='#resultat')requestAnimationFrame(()=>$('resultat').scrollIntoView({block:'start'}));
 else film.pause();
}
function go(hash,scroll=false){
 if(location.hash!==hash){try{history.pushState(null,'',hash);}catch(_){try{location.hash=hash;}catch(_){}}}renderRoute(hash,scroll);
}
function bindAnchor(a){if(!a)return;a.addEventListener('click',e=>{if(e.ctrlKey||e.metaKey||e.shiftKey||e.altKey||e.button!==0)return; const h=a.getAttribute('href');if(/^#(?:[1-9]|1[0-2]|seul-[1-9]|seul-1[0-2]|essai|fiche|accueil|credits|planche|resultat)$/.test(h||'')){e.preventDefault();go(h,h!=='#resultat');}});}
for(const a of document.querySelectorAll('a:not([data-ecran])'))bindAnchor(a);
select.addEventListener('change',()=>go('#'+select.value));$('screenPrev').onclick=()=>go('#'+(shown-1));$('screenNext').onclick=()=>go('#'+(shown+1));
for(const key of ['hashchange','popstate'])window.addEventListener(key,()=>renderRoute(location.hash,false));
window.addEventListener('message',e=>{const r=e.data;if(e.source===solo.contentWindow && routeKey==='#essai'&&r?.type==='vv-t3-film'&&r.token===token&&r.prises===4)go('#resultat',true);});
renderRoute(location.hash,false);document.documentElement.dataset.ready='yes';
})();
