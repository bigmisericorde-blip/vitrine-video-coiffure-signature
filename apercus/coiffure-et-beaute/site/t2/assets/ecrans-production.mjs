import '../../commun/metiers.js';
import '../../commun/exemples.js';
import '../../commun/galerie.js';
import {loadCore} from './engine/resources.mjs';
import {href,restoreFiche} from './engine/fiche.mjs';
const {VVBeaute:ui,VVGalerie:gallery}=globalThis;
loadCore().then(core=>{
  const ticket=new URLSearchParams(location.search).get('fiche'),job=restoreFiche(ticket,core),active=job?ticket:null;
  const metier=job?.metier||ui.readMetier();
  gallery.init({version:'t2',metier,job,scenes:ui.scenes(core.guide.scenes,metier,'t2'),
    makeLink:ecran=>href('simulation.html',active,{metier,ecran}),
    returnLink:href('index.html',active,{metier}),essaiLink:ui.link('index.html',metier,{essai:'1'})});
}).catch(()=>{document.getElementById('galleryCase').textContent='Les ressources de la galerie n’ont pas chargé.';document.documentElement.dataset.ready='error';});
