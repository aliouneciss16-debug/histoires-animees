# Petites Fables

Mini-histoires animées avec une morale, pour enfants. Vidéos verticales (Shorts), sans voix ni musique : sous-titres français et anglais, bruitages seulement.
Personnages originaux dessinés en code : **Roux** le renard et **Pico** le hérisson.

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
