(() => {
  'use strict';
  const ui=VVBeaute, fiche=VVFicheT2, test=window.CONSIGNES_T2;
  const ticket=new URLSearchParams(location.search).get('fiche'), job=fiche.restore(ticket), active=job?ticket:null;
  const metier=job?.metier||ui.readMetier();
  VVGalerie.init({version:'t1',metier,job,scenes:ui.scenes(test.scenes,metier,'t1'),
    makeLink:ecran=>fiche.href('simulation.html',active,{metier,ecran,test:test.id}),
    returnLink:fiche.href('index.html',active,{metier}),essaiLink:ui.link('index.html',metier,{essai:'1'})});
})();
