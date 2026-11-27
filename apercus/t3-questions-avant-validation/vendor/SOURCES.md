# Mediabunny 1.66.1

- Auteur : Vanilagy. Licence : Mozilla Public License 2.0, texte dans `mediabunny-LICENSE.txt`.
- Source Correspondante, révision `134f1e29299ab4bb7e8609bb712c7166ca2c7496` : <https://github.com/Vanilagy/mediabunny/tree/134f1e29299ab4bb7e8609bb712c7166ca2c7496>.
- Paquet npm complet avec `src/` : <https://registry.npmjs.org/mediabunny/-/mediabunny-1.66.1.tgz>.
- Provenance : copie **inchangée** de `package/dist/bundles/mediabunny.min.mjs`, renommée `mediabunny-1.66.1.min.mjs`.
- SHA-256 du module distribué : `19062c195ea4d32bc4eefd3a7254ae0e8a901bc0607ac3a0174013e165980498`.
- SRI npm : `sha512-Jl+EfJbUASHtWVtOAGX8AK5WyNNG1RNJGjccAXcI2R6wQmIkdAzpyVgyCxvc5DXGSSRAuhGIevCPs43mXDq2ug==`.

Les appels ne font aucun chargement CDN à l’exécution ; le module vient du même hébergement que les pages T2.

T3 AAC encoder: @mediabunny/aac-encoder 1.66.1, MPL-2.0; FFmpeg AAC encoder WebAssembly under LGPL 2.1 or later. Source and rebuild instructions: https://github.com/Vanilagy/mediabunny/tree/v1.66.1/packages/aac-encoder and https://ffmpeg.org/ (corresponding source bundled at https://registry.npmjs.org/@mediabunny/aac-encoder/-/aac-encoder-1.66.1.tgz and upstream project). The browser module import path was changed to reference the locally supplied Mediabunny module. License texts are included alongside this notice.
Exact corresponding unmodified FFmpeg source: https://github.com/FFmpeg/FFmpeg/tree/60a2818f76dcd1fee3155b1791304af104a0fc1b ; Emscripten 4.0.21. The encoder's source, exact build flags, and method for rebuilding/replacing the FFmpeg binary are in `aac-source/`.
