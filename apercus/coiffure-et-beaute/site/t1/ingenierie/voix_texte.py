"""Synthèse locale en français / anglais, sans envoyer le texte à un tiers."""
from functools import lru_cache
from importlib.util import find_spec
from pathlib import Path
import argparse
import os
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen

from core import sha
from mix_voix import MediaError

VOICES = {
 'fr': dict(label='Français', model='fr_FR-siwis-medium', path='fr/fr_FR/siwis/medium',
    rev='0ca208afc2a2ee102b1e961e72e0a7e4907be3d0',
    sha='b1d946fd68d0347155fa59bce0a018924abbef3c1561181db45ca463d83963ef',
    config='3b3efdbcdcae930c40d8255527170ec5c87bf05e510b67f53d75fd028df40f43',
    credit='Piper · SIWIS French Speech Synthesis Database (CC BY 4.0).'),
 'en': dict(label='English',model='en_US-ljspeech-medium',path='en/en_US/ljspeech/medium',
    rev='bae641dcb5a608cff81ccaf7ff018baaca1a33e1',
    sha='6f52a751e2349abe7a76735eb09dc1875298c77ea2342ffd2fef79ff81b87f22',
    config='141d612cc0a95ed7efc1ca936b845c2364967f2e9217c5dbfcf69fc4d6c65860',
    credit='Piper · LJ Speech Dataset (public domain).'),
}


def folder():
    return Path(os.environ.get('VV_TTS_MODELS') or Path.home()/'.cache/vv-signature/tts')


def model_link(row):
    return f"https://huggingface.co/rhasspy/piper-voices/tree/{row['rev']}/{row['path']}"


@lru_cache(maxsize=10)
def intact(path, size, mtime_ns, digest):
    return sha(path)==digest


def check(path,digest):
    if not path.is_file(): return False
    st=path.stat(); return intact(str(path),st.st_size,st.st_mtime_ns,digest)


def available():
    if find_spec('piper') is None: return []
    results=[]
    for lang,r in VOICES.items():
        b=folder()/(r['model']+'.onnx')
        if check(b,r['sha']) and check(b.with_suffix('.onnx.json'),r['config']):
            results.append({'code':lang,'label':r['label'],'credit':r['credit'],'source':model_link(r)})
    return results


def tts(text,lang,dest):
    if lang not in {r['code'] for r in available()}:
        raise MediaError('La lecture du texte n’est pas disponible dans cette langue. Enregistre-le avec ta propre voix.')
    if not isinstance(text,str) or not 3<=len(text.strip())<=550 or any(ord(k)<32 and k not in '\n\t\r' for k in text):
        raise MediaError('Écris un texte de 3 à 550 caractères. Pour 30 secondes, commence par 45 à 55 mots.')
    row=VOICES[lang]; model=folder()/(row['model']+'.onnx')
    # Seul le texte saisi pour ce montage est lu, avec son rythme de phrase.
    try:
        z=subprocess.run([sys.executable,'-m','piper','-m',str(model),'-f',str(dest),
                          '--length-scale','1.06','--sentence-silence','0.24'],
                         input=' '.join(text.split()).encode('utf-8'),capture_output=True,timeout=38,
                         env={**os.environ,'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'1'})
    except subprocess.TimeoutExpired as e:
        raise MediaError('La voix a mis trop de temps à se générer. Réessaie ou enregistre-la.') from e
    if z.returncode or not Path(dest).is_file() or Path(dest).stat().st_size<1024:
        raise MediaError('La synthèse n’a pas produit de voix exploitable. Réessaie ou importe une prise.')
    return {'code':lang,'credit':row['credit'],'source':model_link(row)}


def install(lang):
    row=VOICES[lang]; d=folder();d.mkdir(parents=True,exist_ok=True)
    for suffix,key in (('.onnx.json','config'),('.onnx','sha')):
        f=d/(row['model']+suffix)
        if check(f,row[key]): continue
        url=f"https://huggingface.co/rhasspy/piper-voices/resolve/{row['rev']}/{row['path']}/{f.name}"
        with tempfile.TemporaryDirectory(dir=d) as temp:
            tmp=Path(temp)/f.name
            with urlopen(Request(url,headers={'User-Agent':'Vitrine-Video/1.0'}),timeout=40) as src, tmp.open('wb') as dst:
                count=0
                while block:=src.read(1<<17):
                    count+=len(block)
                    if count>70_000_000: raise RuntimeError('Modèle hors taille attendue')
                    dst.write(block)
            if sha(tmp)!=row[key]: raise RuntimeError('Empreinte du modèle inattendue')
            tmp.replace(f)
    print(f"Voix installée : {row['label']} · {row['credit']}",flush=True)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--installer',nargs='+',choices=VOICES,required=True)
    for code in cli.parse_args().installer: install(code)
