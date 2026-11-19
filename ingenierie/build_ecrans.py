#!/usr/bin/env python3
"""Compile le socle HTML T2 ; la structure A/B/C du T1 reste une référence en lecture seule."""
import argparse
from pathlib import Path
from core import ROOT, HERE, CASE, PLAN, compile_ui, load, save, sha, validate

SHA_SOURCE = 'a804a3fa8ad4f9bb70ca624417cdc5b547bf8e4cb9e0528b4c05734fa0f89ea9'
COMMIT = 'ad4ff15a76dcba7bd08b7e8f56052e842b3e794f'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path, nargs='?', help='Facultatif : HTML T1 épinglé à contrôler, jamais modifié')
    args = parser.parse_args()
    if args.reference and sha(args.reference) != SHA_SOURCE:
        parser.error('L’empreinte de la référence T1 ne correspond pas au commit épinglé.')
    case, plan = validate(load(CASE), load(PLAN))
    compile_ui(case, plan)
    source = HERE / 'simulation-t2.html'
    target = ROOT / 'simulation.html'
    target.write_bytes(source.read_bytes())
    save(HERE / 'provenance-ecrans.json', {
        'base_commit':COMMIT, 'base_path':'simulation/index.html', 'sha256_source':SHA_SOURCE,
        'adapter':'ingenierie/build_ecrans.py', 't2_markup':'ingenierie/simulation-t2.html',
        'behavior':['assets/fiche-t2.js','ingenierie/prises-web.js','assets/simulation-t2.js'],
        'output':'simulation.html', 'sha256_output':sha(target), 'etats':['A','B','C','montage','ad','end']})


if __name__ == '__main__':
    main()
