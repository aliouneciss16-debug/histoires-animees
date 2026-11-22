# Petites Fables

Mini-histoires animées avec une morale, pour enfants. Vidéos verticales (Shorts), sans voix ni musique : sous-titres français et anglais, bruitages seulement.
Personnages originaux dessinés en code : **Roux** le renard et **Pico** le hérisson.

## Shorts « faits sur les graines » (voix off + sous-titres + bruitages, sans musique)

```bash
pip install -r requirements.txt     # FFmpeg doit être installé
mkdir models && cd models
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
cd ..
python src/factshort.py stories/fact_001_graine_2000_ans.json out/fact_001.mp4
```

Chaque fait est un fichier JSON dans `stories/` (texte lu, légende, visuel, sources). Les faits sont vérifiés
avant écriture et les sources sont listées dans le fichier.

## Mini-histoires animées (prototype, sans voix)

## Générer une vidéo

```bash
pip install -r requirements.txt     # FFmpeg doit être installé
python src/render.py stories/001_la_pomme_partagee.json out/001.mp4
```

Image de contrôle (scène 1 à 6, temps en secondes) :

```bash
python src/render.py stories/001_la_pomme_partagee.json --still 3 2.0 out/image.png
```

## Structure

- `stories/` : une histoire = un fichier JSON (textes FR/EN, bruitages, morale)
- `src/sprites.py` : dessin des personnages et du décor
- `src/sfx.py` : bruitages générés par code
- `src/render.py` : animation, montage, son
- `exemples/` : vidéo d'exemple

## Prochaines étapes

1. Nouvelles histoires et nouvelles scènes
2. Publication automatique sur YouTube (API) via GitHub Actions
