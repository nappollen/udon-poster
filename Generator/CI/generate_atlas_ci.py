"""
Script pour générer les atlas dans le contexte de CI/CD
Utilisé par le workflow GitHub Actions
"""

import sys
import os
from pathlib import Path


def generate_atlases_ci(input_folder: str, output_folder: str):
    """
    Génère les atlas à partir des images sources pour CI
    
    Args:
        input_folder: Dossier contenant les images sources
        output_folder: Dossier de sortie pour les atlas
    """
    # Ajouter le dossier parent au path pour importer generate_posters
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from generate_posters import AtlasGenerator
    
    print(f"📂 Dossier d'entrée: {input_folder}")
    print(f"📂 Dossier de sortie: {output_folder}")
    
    # Vérifier que le dossier d'entrée existe
    if not os.path.exists(input_folder):
        print(f"❌ Erreur: Le dossier '{input_folder}' n'existe pas!")
        sys.exit(1)
    
    # Compter les images
    image_files = [
        f for f in os.listdir(input_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))
    ]
    print(f"🖼️ {len(image_files)} images trouvées")
    
    if not image_files:
        print("⚠️ Aucune image valide trouvée")
        sys.exit(1)
    
    # Créer le générateur d'atlas
    generator = AtlasGenerator(
        max_atlas_size=2048,
        input_folder=input_folder,
        output_folder=output_folder
    )
    
    # Générer les atlas
    atlas_data = generator.generate_atlases()
    
    # Afficher un résumé
    if atlas_data:
        print("\n✅ === RÉSUMÉ ===")
        print(f"📊 Images traitées: {atlas_data['total_images']}")
        print(f"📦 Atlas générés: {len(atlas_data['atlases'])}")
        
        # Grouper par niveau de downscale
        by_scale = {}
        for atlas in atlas_data['atlases']:
            scale = atlas['scale']
            if scale not in by_scale:
                by_scale[scale] = 0
            by_scale[scale] += 1
        
        for scale, count in sorted(by_scale.items()):
            print(f"   - Downscale x{scale}: {count} atlas")
        
        return atlas_data
    else:
        print("❌ Échec de la génération des atlas")
        sys.exit(1)


def generate_static_ci(atlas_folder: str, output_static_folder: str):
    """
    Génère la version statique pour GitHub Pages dans le contexte de CI
    
    Args:
        atlas_folder: Dossier contenant les atlas générés
        output_static_folder: Dossier de sortie pour la version statique
    """
    # Ajouter le dossier parent au path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Charger les fonctions du script generate_static
    with open(Path(__file__).parent.parent / 'generate_static.py', 'r', encoding='utf-8') as f:
        exec(f.read(), globals())
    
    import json
    import shutil
    
    atlas_folder = Path(atlas_folder)
    output_static_folder = Path(output_static_folder)
    output_static_folder.mkdir(exist_ok=True)
    
    json_file = atlas_folder / 'atlas_data.json'
    
    if not json_file.exists():
        print(f"❌ Erreur: Le fichier {json_file} n'existe pas")
        print("Les atlas n'ont probablement pas été générés correctement")
        sys.exit(1)
    
    # Charger les données JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        atlas_data = json.load(f)
    print(f"✅ Données JSON chargées depuis: {json_file}")
    
    # Compresser les données
    compressed_data = compress_atlas_data(atlas_data)
    
    # Sauvegarder le JSON compressé
    atlas_json_file = output_static_folder / 'atlas.json'
    with open(atlas_json_file, 'w', encoding='utf-8') as f:
        json.dump(compressed_data, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON compressé sauvegardé: {atlas_json_file}")
    
    # Copier et renommer les images
    copied_files = copy_and_rename_images(atlas_folder, output_static_folder, atlas_data)
    
    print(f"\n✅ Version statique générée avec succès!")
    print(f"📊 Statistiques:")
    print(f"   - {len(copied_files)} images copiées")
    print(f"   - {len(compressed_data['atlases'])} atlas")
    print(f"   - {len(compressed_data['mapping'])} images dans le mapping")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Génération d\'atlas pour CI/CD')
    parser.add_argument('command', choices=['generate', 'static'], 
                       help='Commande à exécuter')
    parser.add_argument('--input', default='../../../images',
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
