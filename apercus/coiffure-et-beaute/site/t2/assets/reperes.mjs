// Ces boutons aident à lire l'export de la galerie, sans participer au montage.
const video=document.getElementById('film');
const panel=document.getElementById('reperesT2');
for(const button of panel.querySelectorAll('button[data-debut]')){
  button.addEventListener('click',()=>{
    if(!video.currentSrc)return;
    video.currentTime=Number(button.dataset.debut);
    video.scrollIntoView({block:'nearest'});
    video.play().catch(()=>{}); // Les commandes natives restent utilisables.
  });
}
