import os
import json
from PIL import Image

def generate_metadata(input_folder='input_images', progress_callback=None, auto_delete_missing=False):
    """
    Generates or updates the manifest.json file for images
    
    Args:
        input_folder: Folder containing images
        progress_callback: Progress callback function (step, total, message)
        auto_delete_missing: Automatically delete entries for missing files
        
    Returns:
        dict: Generated metadata or None on error
    """
    
    def report_progress(step, total, message):
        """Helper to call callback if it exists"""
        if progress_callback:
            progress_callback(step, total, message)
    if not os.path.exists(input_folder):
        print(f"Folder {input_folder} does not exist.")
        return None
    
    report_progress(1, 4, "Loading existing manifest")
        
    # Check if manifest.json file exists
    metadata_json = {"version": 1, "images": {}, "metadata": {}}
    manifest_file = f"{input_folder}/manifest.json"
    try:
        with open(manifest_file, 'r', encoding='utf-8') as file:
            metadata_json = json.load(file)
            # Ensure version exists
            if "version" not in metadata_json:
                metadata_json["version"] = 1
            print(f"Existing metadata loaded from {manifest_file}")
    except FileNotFoundError:
        print(f"File {manifest_file} does not exist. Creating new metadata file.")
    except json.JSONDecodeError:
        print(f"File {manifest_file} is not valid JSON. Creating new file.")
    
    # Supported image extensions
    supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif'}
    
    # Loop through all images in folder
    image_files = []
    for filename in sorted(os.listdir(input_folder)):
        if os.path.isfile(os.path.join(input_folder, filename)):
            _, ext = os.path.splitext(filename.lower())
            if ext in supported_extensions:
                image_files.append(filename)
    
    if not image_files:
        print(f"No images found in folder {input_folder}")
        return
    
    report_progress(2, 4, f"Processing {len(image_files)} images")
    
    print(f"\nImages found: {len(image_files)}")
    print("="*60)
    
    # Create a set of existing images for quick check
    existing_images = set(image_files)
    
    # Traiter chaque image automatiquement
    new_entries = 0
    updated_entries = 0
    missing_files = 0
    
    images_metadata = metadata_json["images"]
    
    # Vérifier les images dans le manifest qui n'existent plus
    for filename in list(images_metadata.keys()):
        if filename not in existing_images:
            # Fichier manquant
            if auto_delete_missing:
                # Supprimer l'entrée du manifest
                del images_metadata[filename]
                missing_files += 1
                print(f"🗑️ Entrée supprimée: {filename}")
            else:
                # Ajouter un commentaire d'erreur
                if "_comment" not in images_metadata[filename] or images_metadata[filename]["_comment"] != "ERROR: Image file not found":
                    images_metadata[filename]["_comment"] = "ERROR: Image file not found"
                    missing_files += 1
                    print(f"⚠️ Fichier manquant: {filename}")
        else:
            # Fichier existe, supprimer le commentaire d'erreur s'il y en a un
            if "_comment" in images_metadata[filename] and images_metadata[filename]["_comment"] == "ERROR: Image file not found":
                del images_metadata[filename]["_comment"]
                print(f"✓ Fichier retrouvé: {filename}")
    
    for filename in image_files:
        # Create or update entry with empty default values
        if filename not in images_metadata:
            images_metadata[filename] = {
                "title": "",
                "url": ""
            }
            new_entries += 1
            print(f"✓ New entry created for: {filename}")
        else:
            # Check if fields exist and create them if missing
            if "title" not in images_metadata[filename]:
                images_metadata[filename]["title"] = ""
                updated_entries += 1
            if "url" not in images_metadata[filename]:
                images_metadata[filename]["url"] = ""
                updated_entries += 1
            
            if updated_entries > 0:
                print(f"✓ Entry updated for: {filename}")
    
    report_progress(3, 4, "Saving manifest")
    
    # Save JSON file
    try:
        # Keep existing order and add new images at the end
        # Don't sort to preserve insertion order
        metadata_json["images"] = images_metadata
        
        with open(manifest_file, 'w', encoding='utf-8') as file:
            json.dump(metadata_json, file, indent=2, ensure_ascii=False)
        print(f"\n✓ Metadata saved in {manifest_file}")
        
        report_progress(4, 4, "Metadata generation complete")
        
        # Display summary
        total_images = len(images_metadata)
        
        print(f"\nSUMMARY:")
        print(f"  Total images: {total_images}")
        print(f"  New entries created: {new_entries}")
        if missing_files > 0:
            if auto_delete_missing:
                print(f"  🗑️ Deleted entries: {missing_files}")
            else:
                print(f"  ⚠️ Missing files: {missing_files}")
        
        return metadata_json
        
    except Exception as e:
        print(f"Error saving: {e}")
        return None


def main():
    """Main function for command line execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generates or updates manifest.json file for images')
    parser.add_argument('--input', default='input_images',
                       help='Input images folder (default: input_images)')
    parser.add_argument('--auto-delete-missing', action='store_true',
                       help='Automatically delete entries for missing files from manifest')
    
    args = parser.parse_args()
    generate_metadata(args.input, auto_delete_missing=args.auto_delete_missing)

if __name__ == "__main__":
    main()
