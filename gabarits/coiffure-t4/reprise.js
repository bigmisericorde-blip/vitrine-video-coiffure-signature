/* Reprise locale volontaire : aucune donnée envoyée au serveur. */
(()=>{'use strict';
 const NAME='vv-t4-draft-v1', STORE='draft', ids=['S1','S2','S3','S4'];
 function open(){return new Promise((resolve,reject)=>{if(!window.indexedDB)return reject(Error('Stockage local indisponible.'));const r=indexedDB.open(NAME,1);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error||Error('Stockage local indisponible.'));r.onblocked=()=>reject(Error('Stockage local bloqué par un autre onglet.'));});}
 async function transaction(mode,fn){let db=await open();return await new Promise((resolve,reject)=>{let tx;try{tx=db.transaction(STORE,mode);const result=fn(tx.objectStore(STORE));tx.oncomplete=()=>{db.close();resolve(typeof result==='function'?result():result)};tx.onerror=()=>{db.close();reject(tx.error||Error('Sauvegarde impossible.'))};tx.onabort=()=>{db.close();reject(tx.error||Error('Sauvegarde interrompue.'))};}catch(e){db.close();reject(e)}})}
 window.T4Draft={
  async exists(){return transaction('readonly',s=>{let r=s.get('fiche');return ()=>!!r.result})},
  async create(value){return transaction('readwrite',s=>{let r=s.get('fiche');r.onsuccess=()=>{if(r.result){s.transaction.abort();return;}s.clear();s.put(value,'fiche')}})},
  async updateFiche(value){return transaction('readwrite',s=>{let r=s.get('fiche');r.onsuccess=()=>{if(!r.result){s.transaction.abort();return;}s.put(value,'fiche')}})},
  async saveTake(id,blob){if(!ids.includes(id)||!(blob instanceof Blob)||!blob.size||blob.size>48*1024*1024)throw Error('Prise invalide.');return transaction('readwrite',s=>{let r=s.get('fiche');r.onsuccess=()=>{if(!r.result){s.transaction.abort();return;}s.put(blob,id)}})},
  async read(){return transaction('readonly',s=>{const keys=['fiche',...ids],requests=keys.map(k=>s.get(k));return ()=>Object.fromEntries(keys.map((k,i)=>[k,requests[i].result]))})},
  async clear(){return transaction('readwrite',s=>s.clear())}
 };
})();
