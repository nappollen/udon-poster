"""
Script pour générer les atlas dans le contexte de CI/CD
Utilisé par le workflow GitHub Actions
"""

import sys
import os
from pathlib import Path


def github_group(title):
    """Crée un groupe de logs dans GitHub Actions"""
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print(f"::group::{title}", flush=True)


def github_endgroup():
    """Ferme un groupe de logs dans GitHub Actions"""
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print("::endgroup::", flush=True)


def github_summary(content):
    """Ajoute du contenu au résumé GitHub Actions (visible dans l'interface)"""
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary_file:
            with open(summary_file, 'a', encoding='utf-8') as f:
                f.write(content + '\n')


def github_output(name, value):
    """Définit une sortie pour GitHub Actions"""
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        output_file = os.environ.get('GITHUB_OUTPUT')
        if output_file:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{name}={value}\n")


def progress_callback(step, total, message):
    """Callback pour afficher la progression dans GitHub Actions"""
    percentage = int((step / total) * 100) if total > 0 else 0
    progress_bar = '█' * (percentage // 5) + '░' * (20 - percentage // 5)
    
    # Afficher la barre de progression normale
    print(f"[{progress_bar}] {percentage}% - {message}", flush=True)
    
    # Afficher aussi comme notice GitHub Actions pour plus de visibilité
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print(f"::notice title=Progression {percentage}%::{message}", flush=True)


def generate_atlases_ci(input_folder: str, output_folder: str):
    """
    Génère les atlas à partir des images sources pour CI
    
    Args:
        input_folder: Dossier contenant les images sources
        output_folder: Dossier de sortie pour les atlas
    """
    github_group("🎨 Génération des atlas")
    
    # Ajouter le dossier parent au path pour importer generate_posters
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from generate_posters import main as generate_atlases
    
    print(f"📂 Dossier d'entrée: {input_folder}")
    print(f"📂 Dossier de sortie: {output_folder}")
    
    # Vérifier que le dossier d'entrée existe
    if not os.path.exists(input_folder):
        print(f"❌ Erreur: Le dossier '{input_folder}' n'existe pas!")
        github_endgroup()
        sys.exit(1)
    
    # Compter les images
    image_files = [
        f for f in os.listdir(input_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))
    ]
    print(f"🖼️ {len(image_files)} images trouvées")
    
    if not image_files:
        print("⚠️ Aucune image valide trouvée")
        github_endgroup()
        sys.exit(1)
    
    # Générer les atlas en utilisant la fonction refactorisée avec callback
    atlas_data = generate_atlases(input_folder, output_folder, progress_callback=progress_callback)
    
    github_endgroup()
    
    if not atlas_data:
        print("❌ Échec de la génération des atlas")
        sys.exit(1)
    
    # Créer le résumé pour GitHub Actions
    num_atlases = len(atlas_data.get('atlases', []))
    num_images = atlas_data.get('total_images', 0)
    
    summary = f"""## 🎨 Génération des atlas terminée
    
### 📊 Statistiques
- **Images traitées**: {num_images}
- **Atlas générés**: {num_atlases}
- **Niveaux de downscale**: 1×, 2×, 4×, 8×, 16×

### 📁 Fichiers générés
- `manifest.json` - Métadonnées des atlas
- Fichiers d'atlas aux différentes résolutions
"""
    
    github_summary(summary)
    github_output('num_atlases', str(num_atlases))
    github_output('num_images', str(num_images))
    
    return atlas_data


def generate_static_ci(atlas_folder: str, output_static_folder: str):
    """
    Génère la version statique pour GitHub Pages dans le contexte de CI
    
    Args:
        atlas_folder: Dossier contenant les atlas générés
        output_static_folder: Dossier de sortie pour la version statique
    """
    github_group("📦 Génération de la version statique")
    
    # Ajouter le dossier parent au path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from generate_static import generate_static_version
    import json
    from datetime import datetime, timezone
    
    print(f"📂 Dossier d'atlas: {atlas_folder}")
    print(f"📂 Dossier de sortie: {output_static_folder}")
    
    # Vérifier que le dossier d'atlas existe
    if not os.path.exists(atlas_folder):
        print(f"❌ Erreur: Le dossier '{atlas_folder}' n'existe pas!")
        github_endgroup()
        sys.exit(1)
    
    json_file = Path(atlas_folder) / 'manifest.json'
    if not json_file.exists():
        print(f"❌ Erreur: Le fichier {json_file} n'existe pas")
        print("Les atlas n'ont probablement pas été générés correctement")
        github_endgroup()
        sys.exit(1)
    
    # Charger les données atlas et ajouter les métadonnées CI/CD
    with open(json_file, 'r', encoding='utf-8') as f:
        atlas_data = json.load(f)
    
    # Récupérer les informations GitHub Actions depuis les variables d'environnement
    github_sha = os.environ.get('GITHUB_SHA', '')
    github_repo = os.environ.get('GITHUB_REPOSITORY', '')
    github_server = os.environ.get('GITHUB_SERVER_URL', 'https://github.com')
    github_run_id = os.environ.get('GITHUB_RUN_ID', '')
    github_run_number = os.environ.get('GITHUB_RUN_NUMBER', '')
    github_workflow = os.environ.get('GITHUB_WORKFLOW', '')
    github_ref = os.environ.get('GITHUB_REF', '')
    github_actor = os.environ.get('GITHUB_ACTOR', '')
    
    # Construire l'URL GitHub Pages
    github_pages_url = ''
    if github_repo:
        # Format: https://<username>.github.io/<repo>/
        parts = github_repo.split('/')
        if len(parts) == 2:
            github_pages_url = f"https://{parts[0]}.github.io/{parts[1]}/"
    
    # Créer les métadonnées CI/CD
    ci_metadata = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'commit': {
            'sha': github_sha,
            'short_sha': github_sha[:7] if github_sha else '',
            'url': f"{github_server}/{github_repo}/commit/{github_sha}" if github_sha and github_repo else ''
        },
        'repository': {
            'name': github_repo,
            'url': f"{github_server}/{github_repo}" if github_repo else ''
        },
        'workflow': {
            'name': github_workflow,
            'run_number': github_run_number,
            'run_id': github_run_id,
            'run_url': f"{github_server}/{github_repo}/actions/runs/{github_run_id}" if github_run_id and github_repo else ''
        },
        'ref': github_ref,
        'actor': github_actor
    }
    
    # Ajouter ou fusionner avec les métadonnées existantes
    if 'metadata' not in atlas_data:
        atlas_data['metadata'] = {}
    
    atlas_data['metadata']['base_url'] = github_pages_url
    atlas_data['metadata']['ci'] = ci_metadata
    
    print(f"✅ Métadonnées CI/CD ajoutées:")
    print(f"   - Base URL: {github_pages_url}")
    print(f"   - Commit: {ci_metadata['commit']['short_sha']}")
    print(f"   - Workflow: {github_workflow} #{github_run_number}")
    print(f"   - Repository: {github_repo}")
    
    # Sauvegarder les données modifiées
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(atlas_data, f, indent=2, ensure_ascii=False)
    
    # Générer la version statique en utilisant la fonction refactorisée avec callback
    result = generate_static_version(atlas_folder, output_static_folder, progress_callback=progress_callback)
    
    github_endgroup()
    
    if not result:
        print("❌ Échec de la génération de la version statique")
        sys.exit(1)
    
    # Créer le résumé pour GitHub Actions
    num_atlases = len(result['compressed_data'].get('atlases', []))
    num_images = len(result['compressed_data'].get('mapping', []))
    
    summary = f"""## 📦 Version statique générée
    
### 📊 Contenu
- **Images**: {num_images}
- **Atlas**: {num_atlases}

### 🔗 Fichiers générés
- [`atlas.json`]({github_pages_url}atlas.json) - API JSON des atlas
- `atlas/` - Images d'atlas (indexées par numéro)

### 🌐 URLs d'accès
- **Base URL**: [{github_pages_url}]({github_pages_url})
- **API Atlas**: [{github_pages_url}atlas.json]({github_pages_url}atlas.json)

> ✅ Prêt pour le déploiement sur GitHub Pages!
"""
    
    github_summary(summary)
    github_output('atlas_url', f"{github_pages_url}atlas.json")
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Génération d\'atlas pour CI/CD')
    parser.add_argument('command', choices=['generate', 'static'], 
                       help='Commande à exécuter')
    parser.add_argument('--input', default='../images',
                       help='Dossier des images sources')
    parser.add_argument('--output', default='output_atlases',
                       help='Dossier de sortie des atlas')
    parser.add_argument('--static-output', default='output_static',
                       help='Dossier de sortie de la version statique')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        generate_atlases_ci(args.input, args.output)
    elif args.command == 'static':
        generate_static_ci(args.output, args.static_output)
