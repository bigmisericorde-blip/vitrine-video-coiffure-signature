/* Ces extraits illustrent une seule prestation à la fois ; pas d’offre ou de contact réel. */
(() => {
  const manicure={dir:'manucure', title:'Pose de vernis rouge', credit:'Artem Podrez', geste:'Poser le vernis au pinceau', preuve:'Le bord net du vernis', resultat:'Les ongles en rouge dans la même lumière.',
    details:['La main et les ongles en préparation.','Le pinceau pose la couleur.','Le contour d’un ongle vu de près.','Les ongles vernis, sans outil devant.']};
  const ex={coiffure:{t1:{dir:'coiffure-t1',title:'Coupe et barbe',credit:'Pavel Danilyuk',geste:'Préciser la ligne de coupe',preuve:'Des contours précis',resultat:'La coupe et la barbe terminées.',details:['La personne au début.','La coupe en cours.','Le contour de la barbe.','La coupe terminée.']},
    }, manucure:{t2:manicure}};
  const get=(metier,version)=>Object.hasOwn(ex,metier)&&['t1','t2'].includes(version)?ex[metier][version]:null;
  const asset=(metier,version,file,base)=>{
    const x=get(metier,version);
    if(!x||!/^S[1-4]\.mp4$|^(?:film(?:-t[12])?\.mp4|affiche\.jpg)$/.test(file))return null;
    return new URL(`exemples/${x.dir}/${file}`,base);
  };
  const filmFile=(metier,version)=>metier==='coiffure'?'film.mp4':`film-${version}.mp4`;
  globalThis.VVExemples=Object.freeze({get,asset,filmFile});
})();
