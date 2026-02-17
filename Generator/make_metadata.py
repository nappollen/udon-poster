import os
import json
from PIL import Image

def generate_metadata(input_folder='input_images'):
    """
    Génère ou met à jour le fichier manifest.json pour les images
    
    Args:
        input_folder: Dossier contenant les images
        
    Returns:
        dict: Les métadonnées générées ou None en cas d'erreur
    """
    if not os.path.exists(input_folder):
        print(f"Le dossier {input_folder} n'existe pas.")
        return None
        
    # Vérifier qu'il existe un fichier manifest.json
    metadata_json = {"images": {}, "metadata": {}}
    manifest_file = f"{input_folder}/manifest.json"
    try:
        with open(manifest_file, 'r', encoding='utf-8') as file:
            metadata_json = json.load(file)
            print(f"Métadonnées existantes chargées depuis {manifest_file}")
    except FileNotFoundError:
        print(f"Le fichier {manifest_file} n'existe pas. Création d'un nouveau fichier de métadonnées.")
    except json.JSONDecodeError:
        print(f"Le fichier {manifest_file} n'est pas un JSON valide. Création d'un nouveau fichier.")
    
    # Extensions d'images supportées
    supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif'}
    
    # Parcourir toutes les images dans le dossier
    image_files = []
    for filename in sorted(os.listdir(input_folder)):
        if os.path.isfile(os.path.join(input_folder, filename)):
            _, ext = os.path.splitext(filename.lower())
            if ext in supported_extensions:
                image_files.append(filename)
    
    if not image_files:
        print(f"Aucune image trouvée dans le dossier {input_folder}")
        return
    
    print(f"\nImages trouvées: {len(image_files)}")
    print("="*60)
    
    # Traiter chaque image automatiquement
    new_entries = 0
    updated_entries = 0
    
    images_metadata = metadata_json["images"]
    
    for filename in image_files:
        # Créer ou mettre à jour l'entrée avec des valeurs vides par défaut
        if filename not in images_metadata:
            images_metadata[filename] = {
                "title": "",
                "url": ""
            }
            new_entries += 1
            print(f"✓ Nouvelle entrée créée pour: {filename}")
        else:
            # Vérifier si les champs existent et les créer s'ils sont manquants
            if "title" not in images_metadata[filename]:
                images_metadata[filename]["title"] = ""
                updated_entries += 1
            if "url" not in images_metadata[filename]:
                images_metadata[filename]["url"] = ""
                updated_entries += 1
            
            if updated_entries > 0:
                print(f"✓ Entrée mise à jour pour: {filename}")
    
    # Sauvegarder le fichier JSON
    try:
        # Trier les métadonnées des images par nom de clé
        metadata_json["images"] = dict(sorted(images_metadata.items()))
        
        with open(manifest_file, 'w', encoding='utf-8') as file:
            json.dump(metadata_json, file, indent=2, ensure_ascii=False)
        print(f"\n✓ Métadonnées sauvegardées dans {manifest_file}")
        
        # Afficher un résumé
        total_images = len(images_metadata)
        
        print(f"\nRÉSUMÉ:")
        print(f"  Total d'images: {total_images}")
        print(f"  Nouvelles entrées créées: {new_entries}")
        
        return metadata_json
        
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        return None


def main():
    """Fonction principale pour l'exécution en ligne de commande"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Génère ou met à jour le fichier manifest.json pour les images')
    parser.add_argument('--input', default='input_images',
                       help='Dossier des images d\'entrée (par défaut: input_images)')
    
    args = parser.parse_args()
    generate_metadata(args.input)

if __name__ == "__main__":
    main()
