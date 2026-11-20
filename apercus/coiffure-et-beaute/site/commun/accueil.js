(() => {
  'use strict';
  const {profiles, get, link} = VVBeaute;
  const $=id=>document.getElementById(id);
  const el=(t,txt,cls)=>{const e=document.createElement(t);if(txt)e.textContent=txt;if(cls)e.className=cls;return e;};
  const selected=new URLSearchParams(location.search).get('metier');
  const form=$('demarrer');
  for (const p of profiles) {
    const label=el('label','','metier'),input=el('input');input.type='radio';input.name='metier';input.value=p.id;input.required=true;input.checked=p.id===selected;
    const copy=el('span','','metier-copy');copy.append(el('b',p.label),el('small',p.sub));
    const icon=el('span','','pick-dot');icon.setAttribute('aria-hidden','true');
    label.append(input,copy,icon);$('metiers').append(label);
  }
  function ready(){const val=form.elements.metier.value;for(const id of ['ouvrirT1','ouvrirT2'])$(id).disabled=!val;$('selection').textContent=val?'Choix : '+get(val).label:'Choisis ta prestation ci-dessus.';}
  form.addEventListener('change',ready);window.addEventListener('pageshow',ready);ready();
  for(const [k,v] of [['coiffure','t1'],['manucure','t2']]){
    const sample=VVExemples.get(k,v),p=get(k),card=el('article','','exemple');
    const image=el('img');image.src=`exemples/${sample.dir}/affiche.jpg`;image.width=540;image.height=390;image.loading='lazy';image.alt='';
    const content=el('div','','exemple-copy');content.append(el('p',`${v.toUpperCase()} · ${p.label}`,'eyebrow'),el('h3',sample.title));
    const links=el('div','','mini-links'),a=el('a','Les 12 écrans →'),b=el('a','Le film →');
    a.href=link(`${v}/ecrans.html`,k);b.href=a.href+'#resultat';
    links.append(a,b);content.append(links);card.append(image,content);$('exempleCards').append(card);
  }
})();
