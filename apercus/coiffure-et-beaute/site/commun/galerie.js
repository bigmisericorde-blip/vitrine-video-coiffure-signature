/* Affichage commun des 12 écrans. La galerie ne valide jamais une prise. */
(() => {
  'use strict';
  const $=id=>document.getElementById(id),el=(tag,text)=>{const x=document.createElement(tag);if(text)x.textContent=text;return x;};
  function init({version,metier,scenes,job,makeLink,returnLink,essaiLink}){
    const sample=VVExemples.get(metier,version), profile=VVBeaute.get(metier);
    $('version').textContent=version.toUpperCase();$('profileLabel').textContent=profile.label;
    $('secteur').href=VVBeaute.link('../',metier);$('return').href=returnLink;
    $('essai').href=essaiLink;$('another').href=returnLink;
    $('galleryCase').textContent=sample?`${sample.title} · Images d’exemple, pas une offre réelle.`:'Pas encore d’exemple filmé pour cette prestation. Tu peux relire les consignes et continuer avec tes propres prises.';
    $('resultat').hidden=!sample;$('essai').hidden=!sample;$('jumpFilm').hidden=!sample;
    if(sample){
      const base=new URL('../',location.href),file=VVExemples.filmFile(metier,version),film=VVExemples.asset(metier,version,file,base).href;
      $('film').setAttribute('poster',VVExemples.asset(metier,version,'affiche.jpg',base).href);$('film').src=film;
      $('downloadDemo').href=film;$('filmTitre').textContent=sample.title;$('filmCredit').textContent=`Images : ${sample.credit} / Pexels. Exemple filmé, sans offre réelle.`;
    }
    const phase=['Consigne','Chrono','Relecture'],items=[], select=$('screenSelect'), nav=$('screenList');
    if(job)$('caseStatus').textContent='Les textes de ta fiche restent dans cet onglet. Les images de la galerie sont celles de l’exemple, pas les tiennes.';
    if(!sample&&job)$('caseStatus').textContent='Les textes de ta fiche restent dans cet onglet. Aucun fichier personnel n’est lu dans la galerie.';
    for(const [i,s] of scenes.entries()){
      const group=el('section');group.className='screen-group';group.append(el('h2',`Prise ${i+1} · ${s.role}`));
      const row=el('div');row.className='screen-row';
      phase.forEach((label,j)=>{
        const n=i*3+j+1,rank=String(n).padStart(2,'0'),a=el('a');a.href=`#${n}`;a.dataset.ecran=n;
        a.append(el('small',rank),document.createTextNode(label));
        const title=`Écran ${rank}/12 · ${s.role} · ${label}`;
        a.setAttribute('aria-label',title);a.addEventListener('click',e=>{
          if(e.ctrlKey||e.metaKey||e.altKey||e.shiftKey||e.button!==0)return;e.preventDefault();go(n);
          if(matchMedia('(max-width:760px)').matches)$('apercu').scrollIntoView({block:'start'});
        });
        items.push({n,rank,title,a,src:makeLink(n),copy:[s.a_filmer[0],`Le chrono suit les ${s.secondes} secondes de la prise.`,s.question_relecture][j],seance:sample?.details[i]});
        select.append(new Option(`${rank} · ${s.role} : ${label}`,String(n)));row.append(a);
      });
      group.append(row);nav.append(group);
    }
    let n=0;
    function show(i){
      const one=items[i-1]||items[0];if(one.n===n)return;n=one.n;
      for(const x of items){if(x===one)x.a.setAttribute('aria-current','step');else x.a.removeAttribute('aria-current');}
      $('screenLabel').textContent=one.title;$('screenText').textContent=one.copy;$('screenDetail').textContent=one.seance||'';
      $('screenAlone').href=one.src;$('screenLive').src=one.src;
      select.value=String(n);$('screenPrev').disabled=n===1;$('screenNext').disabled=n===12;
    }
    function go(i){if(!items[i-1])return;if(location.hash!==`#${i}`)history.pushState(null,'',`#${i}`);show(i);}
    function fromUrl(){const part=location.hash.slice(1);if(!part||/^\d+$/.test(part)||!n)show(Number(part));}
    window.addEventListener('hashchange',fromUrl);window.addEventListener('popstate',fromUrl);
    select.addEventListener('change',()=>go(Number(select.value)));$('screenPrev').onclick=()=>go(n-1);$('screenNext').onclick=()=>go(n+1);
    fromUrl();document.documentElement.dataset.ready='yes';
    if(location.hash==='#resultat'&&sample)requestAnimationFrame(()=>$('resultat').scrollIntoView({block:'start'}));
  }
  globalThis.VVGalerie=Object.freeze({init});
})();
