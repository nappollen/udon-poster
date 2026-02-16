# Scripts CI pour GitHub Actions

Ce dossier contient les scripts utilisés par le workflow GitHub Actions pour générer et déployer les atlas.

## Fichiers

### `generate_atlas_ci.py`
Script principal pour générer les atlas dans le contexte CI/CD.

**Commandes:**
- `python generate_atlas_ci.py generate --input ../../../images --output output_atlases`
  - Génère les atlas à partir des images sources
- `python generate_atlas_ci.py static --output output_atlases --static-output output_static`
  - Génère la version statique pour GitHub Pages

### `create_index.py`
Script pour créer la page d'accueil et l'atlas vide.

**Commandes:**
- `python create_index.py create-index --output output_static`
  - Crée la page index.html pour GitHub Pages
- `python create_index.py empty-atlas --output output_static`
  - Crée un atlas vide (fallback quand aucune image n'est trouvée)

### `check_images.sh`
Script bash pour vérifier la présence d'images sources.

**Usage:**
```bash
./check_images.sh
```

Retourne:
- `images_exist=true` si des images sont trouvées
- `images_exist=false` sinon

### `ci_utils.py`
Fonctions utilitaires pour le CI/CD.

**Fonctions:**
- `check_images_exist(images_folder)`: Vérifie la présence d'images
- `display_deployment_info(deployment_url)`: Affiche les infos de déploiement

## Utilisation dans GitHub Actions

Ces scripts sont utilisés par le workflow `.github/workflows/generate-atlas.yml`.

Le workflow:
1. Vérifie la présence d'images avec `check_images.sh`
2. Génère les atlas avec `generate_atlas_ci.py generate`
3. Crée la version statique avec `generate_atlas_ci.py static`
4. Crée l'index.html avec `create_index.py create-index`
5. Déploie sur GitHub Pages

## Structure des dossiers

```
Generator/
├── CI/                          # Scripts CI (ce dossier)
│   ├── generate_atlas_ci.py
│   ├── create_index.py
│   ├── check_images.sh
│   ├── ci_utils.py
│   └── README.md
├── generate_posters.py          # Générateur d'atlas principal
├── generate_static.py           # Générateur de version statique
└── requirements.txt             # Dépendances Python
```
