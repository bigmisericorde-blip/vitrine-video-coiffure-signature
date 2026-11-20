/* Une seule source de textes pour T1, T2 et leurs aperçus. Aucun renseignement personnel ici. */
(() => {
  'use strict';
  const rows = [
    ['coiffure','Coiffure et barbe','Coupe, couleur, tresses…', ['Mise en forme des boucles','Coupe et barbe','Balayage'], 'Soulever les mèches', 'Des boucles bien dessinées', [
      'Cadre les cheveux ou la barbe avant de commencer. Laisse de la place autour de la zone.',
      'Montre le peigne, les doigts ou l’outil et la mèche ou la zone travaillée dans le même cadre.',
      'Choisis une boucle, une séparation ou une ligne de barbe. Ne la cache pas avec ta main.',
      'Montre la coupe, la barbe ou la coiffure terminée, avec la même lumière qu’au départ.']],
    ['manucure','Manucure','Mains, ongles, vernis…', ['Pose de vernis','Manucure simple','Pose de gel'], 'Appliquer le vernis', 'Le bord net du vernis', [
      'Montre la main et les ongles avant la pose ou le soin. Pas besoin de filmer le visage.',
      'Montre la main et le pinceau ou la lime ensemble. Ne coupe pas les bouts des doigts.',
      'Approche le téléphone d’un ongle. Le bord du vernis ou la forme de l’ongle doit se voir nettement.',
      'Montre les ongles terminés sur la même main, sous le même angle et dans la même lumière.']],
    ['pedicure','Pédicure esthétique','Ongles et soins des pieds…', ['Pédicure esthétique','Pose de vernis aux pieds','Soin des pieds'], 'Limer le bord de l’ongle', 'Un bord net et régulier', [
      'Montre le pied et les ongles avant la prestation. Laisse les orteils entièrement visibles.',
      'Cadre le pied et la main ou l’outil au moment du geste, sans masquer les orteils.',
      'Rapproche-toi d’un ongle pour montrer la forme, le bord du vernis ou le détail choisi.',
      'Montre la finition sur le même pied, sous le même angle et dans la même lumière.']],
    ['visage','Soin du visage','Masque, nettoyage, massage…', ['Soin du visage','Pose d’un masque visage','Massage du visage'], 'Appliquer le masque au pinceau', 'Une couche régulière', [
      'Montre le visage ou la zone du soin avant le premier geste, avec l’accord de la personne.',
      'Cadre la main ou le pinceau et la zone du visage au moment de l’application.',
      'Montre la texture ou la façon dont le produit est étalé. Ne change pas la lumière pour accentuer l’effet.',
      'Montre le visage ou la zone à la fin du soin, dans la même lumière et sans filtre. Pour une pose de masque, le masque posé peut être le résultat.']],
    ['corps','Soin du corps','Gommage, modelage, soin du dos…', ['Gommage du corps','Soin du dos','Modelage esthétique'], 'Appliquer le gommage', 'Une application uniforme', [
      'Cadre seulement la zone du soin que la personne accepte de montrer. Garde le reste couvert.',
      'Cadre les mains et la zone du soin. Garde ton téléphone fixe pour que l’on voie le mouvement.',
      'Montre la texture du produit ou le détail d’application, sans filmer une zone que la personne veut garder privée.',
      'Reprends la même zone et la même lumière à la fin. Montre le résultat visible, sans promettre un effet.']],
    ['maquillage','Maquillage','Teint, yeux, lèvres…', ['Maquillage léger','Maquillage de cérémonie','Mise en valeur des yeux'], 'Estomper le fard', 'Un fondu régulier', [
      'Montre la zone à maquiller avant le premier geste. Choisis une lumière que tu pourras garder.',
      'Filme le pinceau, l’éponge ou la main au moment du geste, avec la zone maquillée bien visible.',
      'Montre le fondu d’un fard, un trait ou un contour des lèvres, sans filtre ni changement de lumière.',
      'Montre le maquillage fini dans la même lumière. Garde la zone maquillée entière dans le cadre.']],
    ['regard','Cils et sourcils','Mise en forme, finition…', ['Mise en forme des sourcils','Pose de cils','Brossage des sourcils'], 'Brosser les sourcils', 'Une ligne bien visible', [
      'Montre la ligne des sourcils ou les cils avant de commencer. Ne colle pas le téléphone au visage.',
      'Laisse voir à la fois la brosse ou l’outil et la zone travaillée, sans cacher l’œil ou le sourcil.',
      'Montre un détail de la ligne ou de la finition. Vérifie que l’image reste nette en gros plan.',
      'Reviens au même angle pour montrer le regard ou la ligne terminée.']],
    ['autre','Autre prestation','Écris le nom de ton activité', ['Épilation esthétique','Soin des mains','Une autre prestation'], 'Montrer un geste précis', 'Une finition bien visible', [
      'Choisis la zone à montrer avant de commencer. Laisse un peu de place autour.',
      'Montre ta main ou ton outil et la zone travaillée dans le même cadre.',
      'Choisis un détail que l’on voit vraiment à l’image et rapproche-toi doucement.',
      'Montre le résultat sur la même personne et la même zone, dans une lumière comparable.']]
  ];
  const titles=['Avant','Geste','Détail','Résultat'];
  const freeze=(x)=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};
  const profiles=freeze(rows.map(([id,label,sub,services,geste,preuve,aFilmer])=>({id,label,sub,services,geste,preuve,aFilmer})));
  const framing=Object.freeze({profil:'Le résultat dans son ensemble',contours:'Les bords ou les contours de près',couleur:'La couleur, les reflets ou la finition',detail:'Un détail de finition, vu de près'});
  const guides=freeze([
    ['Filme la zone avant de commencer.','Évite un cadre trop serré ou une lumière qui change.','Voit-on bien l’état de départ ?','Voici le point de départ.'],
    ['Filme un seul geste que l’on peut bien suivre.','Ne filme pas de trop loin et ne cache pas le geste.','Voit-on bien le geste choisi ?','Voici le geste.'],
    ['Montre de près le détail que tu veux faire remarquer.','Ne bouge pas brusquement et laisse le détail bien éclairé.','Le détail est-il net et bien visible ?','Regarde ce détail.'],
    ['Montre le résultat sur la même personne et la même zone.','Ne change pas de personne. Ne cache pas le résultat derrière la main ou l’outil.','Comprend-on le résultat sans texte ni musique ?','Voilà le résultat.']
  ]);
  const get=(id)=>profiles.find(x=>x.id===id)??profiles.at(-1);
  const readMetier=()=>get(new URLSearchParams(location.search).get('metier')).id;
  const link=(path,metier,extra={})=>`${path}?${new URLSearchParams({metier:get(metier).id,...extra})}`;
  const consent='Demande l’accord de la personne avant de filmer et de diffuser les images.';
  function scenes(base,metier,version){
    const profile=get(metier);
    return base.map((s,i)=>{
      const [consigne,avoid,question_relecture,exemple]=guides[i];
      const a_filmer=[profile.aFilmer[i],i===0||i===3?'Garde le sujet au milieu et un peu de place en bas pour le texte.':'Garde le geste ou le détail au milieu de l’image.'];
      if(version==='t2'&&i===1)a_filmer.push('Si tu veux réutiliser ce plan comme détail, garde le détail net jusqu’à la fin.');
      if(version==='t2'&&i===3)a_filmer.push('Montre le fini dès le début de la prise et jusqu’au bout : il ouvre aussi le film.');
      return {...s,titre:titles[i].toLocaleUpperCase('fr'),role:titles[i],consigne,a_filmer,a_eviter:[avoid],question_relecture,exemple};
    });
  }
  function populate(select,selected,{empty=false}={}){
    select.replaceChildren(...(empty?[new Option('Choisis une prestation','')]:[]),...profiles.map(x=>new Option(x.label,x.id)));
    select.value=empty&&!selected?'':get(selected).id;
  }
  globalThis.VVBeaute=Object.freeze({profiles,framing,guides,titles:freeze(titles),get,readMetier,link,populate,scenes,consent});
})();
