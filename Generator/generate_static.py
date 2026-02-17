#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour générer une version statique des atlas
Copie les images avec un renommage par index et génère un JSON équivalent à l'API /atlas
"""

import json
import os
import shutil
from pathlib import Path


def compress_atlas_data(data):
    """
    Compresse les données JSON (remplace les clés string par des index)
    Équivalent de la fonction PHP compressAtlasData
    """
    compressed_data = {
        'version': data.get('version', 1),
        'mapping': [],
        'atlases': []
    }
    
    # Ajouter les métadonnées custom si elles existent
    if 'metadata' in data and data['metadata']:
        compressed_data['metadata'] = data['metadata']
    
    # Créer un mapping des noms d'images vers des index basé sur l'ordre des métadonnées
    image_name_to_index = {}
    image_index = 0

    # Utiliser l'ordre des métadonnées pour déterminer les index
    for image_name, metadata in data['images_metadata'].items():
        image_name_to_index[image_name] = image_index
        compressed_data['mapping'].append(metadata)
        image_index += 1

    # Compresser les atlas
    for atlas in data['atlases']:
        compressed_atlas = {
            'scale': atlas['scale'],
            'width': atlas['width'],
            'height': atlas['height'],
            'sha': atlas.get('sha', ''),
            'uv': {}
        }

        # Remplacer les clés string par des index numériques
        for image_name, uv in atlas['uv'].items():
            index = image_name_to_index[image_name]
            compressed_atlas['uv'][str(index)] = uv

        compressed_data['atlases'].append(compressed_atlas)
    
    return compressed_data


def copy_and_rename_images(atlas_folder, output_static_folder, atlas_data):
    """
    Copie les images des atlas en les renommant avec leur index
    """
    images_folder = output_static_folder / 'atlas'
    images_folder.mkdir(exist_ok=True)
    
    copied_files = []
    
    for index, atlas in enumerate(atlas_data['atlases']):
        if 'file' in atlas:
            source_file = atlas_folder / atlas['file']
            if source_file.exists():
                # Obtenir l'extension du fichier original
                extension = source_file.suffix
                # Nouveau nom avec l'index
                new_filename = f"{index}{extension}"
                destination_file = images_folder / new_filename
                
                # Copier le fichier
                shutil.copy2(source_file, destination_file)
                copied_files.append({
                    'original': atlas['file'],
                    'new': new_filename,
                    'index': index
                })
                print(f"Copié: {atlas['file']} -> {new_filename}")
            else:
                print(f"Attention: Fichier non trouvé: {source_file}")
    
    return copied_files


def generate_static_version(input_path=None, output_path=None):
    """
    Fonction principale pour générer la version statique
    
    Args:
        input_path: Dossier des atlas d'entrée (par défaut: 'output_atlases')
        output_path: Dossier de sortie (par défaut: 'output_static')
        
    Returns:
        dict: Résultat de la génération ou None en cas d'erreur
    """
    # Déterminer le dossier d'entrée
    if not input_path:
        # Utiliser le dossier par défaut
        script_dir = Path(__file__).parent
        atlas_folder = script_dir / 'output_atlases'
        print(f"Utilisation du dossier par défaut: {atlas_folder}")
    else:
        atlas_folder = Path(input_path)
    
    # Vérifier que le dossier d'entrée existe
    if not atlas_folder.exists():
        print(f"Erreur: Le dossier d'entrée {atlas_folder} n'existe pas")
        return None
    
    json_file = atlas_folder / 'manifest.json'
    if not json_file.exists():
        print(f"Erreur: Le fichier {json_file} n'existe pas")
        print("Assurez-vous que le dossier contient le fichier manifest.json")
        return None
    
    # Déterminer le dossier de sortie
    if not output_path:
        # Utiliser le dossier par défaut
        output_static_folder = Path('output_static')
        print(f"Utilisation du dossier de sortie par défaut: {output_static_folder}")
    else:
        output_static_folder = Path(output_path)
    output_static_folder.mkdir(exist_ok=True)
    print(f"Dossier de sortie: {output_static_folder}")
    
    # Charger les données JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            atlas_data = json.load(f)
        print(f"Données JSON chargées depuis: {json_file}")
    except Exception as e:
        print(f"Erreur lors du chargement du JSON: {e}")
        return None
    
    # Compresser les données (comme fait l'API PHP)
    compressed_data = compress_atlas_data(atlas_data)
    
    # Sauvegarder le JSON compressé (équivalent de la réponse /atlas)
    atlas_json_file = output_static_folder / 'atlas.json'
    try:
        with open(atlas_json_file, 'w', encoding='utf-8') as f:
            json.dump(compressed_data, f, indent=2, ensure_ascii=False)
        print(f"JSON compressé sauvegardé: {atlas_json_file}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du JSON: {e}")
        return None
    
    # Copier et renommer les images
    copied_files = copy_and_rename_images(atlas_folder, output_static_folder, atlas_data)
    
    print(f"\n✅ Version statique générée avec succès dans: {output_static_folder}")
    print(f"📁 Fichiers générés:")
    print(f"   - atlas.json (équivalent de l'API /atlas)")
    print(f"   - atlas/ (images renommées par index)")
    print(f"\n📊 Statistiques:")
    print(f"   - {len(copied_files)} images copiées")
    print(f"   - {len(compressed_data['atlases'])} atlas")
    print(f"   - {len(compressed_data['mapping'])} images dans le mapping")
    
    return {
        'output_folder': str(output_static_folder),
        'atlas_json': str(atlas_json_file),
        'copied_files': copied_files,
        'compressed_data': compressed_data
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Génère une version statique des atlas pour GitHub Pages')
    parser.add_argument('--input', default=None,
                       help='Dossier des atlas d\'entrée (par défaut: output_atlases)')
    parser.add_argument('--output', default=None,
                       help='Dossier de sortie (par défaut: output_static)')
    
    args = parser.parse_args()
    generate_static_version(args.input, args.output)
