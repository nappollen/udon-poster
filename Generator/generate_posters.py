import os
import json
import math
from PIL import Image, ImageDraw
from typing import List, Tuple, Dict, Any

class Rectangle:
    """Représente un rectangle avec position et dimensions"""
    def __init__(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def fits_in(self, other: 'Rectangle') -> bool:
        """Vérifie si ce rectangle peut s'adapter dans un autre"""
        return self.width <= other.width and self.height <= other.height
    
    def contains_point(self, x: int, y: int) -> bool:
        """Vérifie si un point est dans ce rectangle"""
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

class BinPacker:
    """Algorithme de bin packing optimisé pour les atlas"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.free_rectangles = [Rectangle(0, 0, width, height)]
        self.used_rectangles = []
    
    def insert(self, width: int, height: int) -> Rectangle:
        """Insère un rectangle et retourne sa position, ou None si impossible"""
        best_rect = None
        best_area_fit = float('inf')
        best_short_side_fit = float('inf')
        
        for rect in self.free_rectangles:
            if rect.width >= width and rect.height >= height:
                area_fit = rect.width * rect.height - width * height
                leftover_horizontal = rect.width - width
                leftover_vertical = rect.height - height
                short_side_fit = min(leftover_horizontal, leftover_vertical)
                
                if area_fit < best_area_fit or (area_fit == best_area_fit and short_side_fit < best_short_side_fit):
                    best_rect = Rectangle(rect.x, rect.y, width, height)
                    best_area_fit = area_fit
                    best_short_side_fit = short_side_fit
        
        if best_rect:
            self._split_free_rectangle(best_rect)
            self.used_rectangles.append(best_rect)
        
        return best_rect
    
    def _split_free_rectangle(self, used_rect: Rectangle):
        """Divise les rectangles libres après insertion"""
        rectangles_to_process = self.free_rectangles[:]
        self.free_rectangles = []
        
        for rect in rectangles_to_process:
            if self._split_rectangle(rect, used_rect):
                continue
            self.free_rectangles.append(rect)
        
        self._prune_free_rectangles()
    
    def _split_rectangle(self, rect: Rectangle, used_rect: Rectangle) -> bool:
        """Divise un rectangle libre si il overlap avec le rectangle utilisé"""
        if (rect.x >= used_rect.x + used_rect.width or 
            rect.x + rect.width <= used_rect.x or
            rect.y >= used_rect.y + used_rect.height or
            rect.y + rect.height <= used_rect.y):
            return False
        
        # Rectangle à droite
        if rect.x < used_rect.x + used_rect.width and rect.x + rect.width > used_rect.x + used_rect.width:
            new_rect = Rectangle(used_rect.x + used_rect.width, rect.y, 
                               rect.x + rect.width - (used_rect.x + used_rect.width), rect.height)
            self.free_rectangles.append(new_rect)
        
        # Rectangle à gauche
        if rect.x < used_rect.x and rect.x + rect.width > used_rect.x:
            new_rect = Rectangle(rect.x, rect.y, used_rect.x - rect.x, rect.height)
            self.free_rectangles.append(new_rect)
        
        # Rectangle en bas
        if rect.y < used_rect.y + used_rect.height and rect.y + rect.height > used_rect.y + used_rect.height:
            new_rect = Rectangle(rect.x, used_rect.y + used_rect.height, 
                               rect.width, rect.y + rect.height - (used_rect.y + used_rect.height))
            self.free_rectangles.append(new_rect)
        
        # Rectangle en haut
        if rect.y < used_rect.y and rect.y + rect.height > used_rect.y:
            new_rect = Rectangle(rect.x, rect.y, rect.width, used_rect.y - rect.y)
            self.free_rectangles.append(new_rect)
        
        return True
    
    def _prune_free_rectangles(self):
        """Supprime les rectangles redondants"""
        i = 0
        while i < len(self.free_rectangles):
            j = i + 1
            while j < len(self.free_rectangles):
                rect1 = self.free_rectangles[i]
                rect2 = self.free_rectangles[j]
                
                if (rect1.x >= rect2.x and rect1.y >= rect2.y and 
                    rect1.x + rect1.width <= rect2.x + rect2.width and 
                    rect1.y + rect1.height <= rect2.y + rect2.height):
                    self.free_rectangles.pop(i)
                    i -= 1
                    break
                elif (rect2.x >= rect1.x and rect2.y >= rect1.y and 
                      rect2.x + rect2.width <= rect1.x + rect1.width and 
                      rect2.y + rect2.height <= rect1.y + rect1.height):
                    self.free_rectangles.pop(j)
                    j -= 1
                j += 1
            i += 1

class AtlasGenerator:
    def __init__(self, max_atlas_size: int = 2048, input_folder: str = "", output_folder: str = ""):
        self.max_atlas_size = max_atlas_size
        self.input_folder = input_folder or "input_images"
        self.output_folder = output_folder or "output_atlases"
        
        # Créer le dossier de sortie s'il n'existe pas
        os.makedirs(self.output_folder, exist_ok=True)
    
    def resize_image_if_needed(self, image: Image.Image) -> Image.Image:
        """Redimensionne l'image si elle dépasse 2048x2048 en gardant le ratio"""
        width, height = image.size
        
        if width <= self.max_atlas_size and height <= self.max_atlas_size:
            return image
        
        # Calculer le ratio de redimensionnement
        ratio = min(self.max_atlas_size / width, self.max_atlas_size / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def downscale_image(self, image: Image.Image, scale_factor: int) -> Image.Image:
        """Downscale l'image par un multiple de 2"""
        width, height = image.size
        new_width = width // scale_factor
        new_height = height // scale_factor
        
        if new_width < 1 or new_height < 1:
            new_width = max(1, new_width)
            new_height = max(1, new_height)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def pack_images_in_atlas(self, images: List[Tuple[str, Image.Image]]) -> Tuple[Image.Image, Dict[str, Dict[str, float]]]:
        """Pack les images dans un atlas en utilisant un algorithme optimisé"""
        if not images:
            return None, {}
        
        # Trier les images par aire décroissante (meilleur pour le bin packing)
        sorted_images = sorted(images, key=lambda x: x[1].size[0] * x[1].size[1], reverse=True)
        
        # Créer l'atlas
        atlas_width = self.max_atlas_size
        atlas_height = self.max_atlas_size
        atlas = Image.new('RGBA', (atlas_width, atlas_height), (0, 0, 0, 0))
        
        # Initialiser le bin packer
        packer = BinPacker(atlas_width, atlas_height)
        
        # Coordonnées UV pour chaque image
        uv_coords = {}
        max_right = 0
        max_bottom = 0
        
        for filename, img in sorted_images:
            img_width, img_height = img.size
            
            # Essayer de placer l'image dans l'atlas
            rect = packer.insert(img_width, img_height)
            
            if rect is None:
                # Plus d'espace dans cet atlas
                break
            
            # Placer l'image dans l'atlas
            atlas.paste(img, (rect.x, rect.y))
            
            # Calculer les coordonnées UV (on les calculera après redimensionnement)
            uv_coords[filename] = {
                'x': rect.x,
                'y': rect.y,
                'width': rect.width,
                'height': rect.height
            }
            
            # Suivre les dimensions maximales utilisées
            max_right = max(max_right, rect.x + rect.width)
            max_bottom = max(max_bottom, rect.y + rect.height)
        
        # Redimensionner l'atlas pour éliminer les marges vides
        if max_right > 0 and max_bottom > 0:
            # S'assurer que les dimensions sont au moins 1x1
            actual_width = max(1, max_right)
            actual_height = max(1, max_bottom)
            
            # Crop l'atlas aux dimensions réellement utilisées
            atlas = atlas.crop((0, 0, actual_width, actual_height))
            
            # Calculer les coordonnées UV avec les nouvelles dimensions (compatibles Unity)
            for filename in uv_coords:
                coord = uv_coords[filename]
                # Unity utilise l'origine en bas à gauche, donc on inverse l'axe Y
                uv_coords[filename] = {
                    'width': coord['width'],
                    'height': coord['height'],
                    # Ajouter les coordonnées pour Unity Rect (x, y, width, height normalisées)
                    'rect_x': coord['x'] / actual_width,
                    'rect_y': 1.0 - (coord['y'] + coord['height']) / actual_height,
                    'rect_width': coord['width'] / actual_width,
                    'rect_height': coord['height'] / actual_height
                }
        
        return atlas, uv_coords
    
    def generate_atlases(self) -> Dict[str, Any]:
        """Génère tous les atlas avec différents niveaux de downscale"""
        
        # Charger le fichier manifest.json s'il existe
        manifest_file = os.path.join(self.input_folder, "manifest.json")
        metadata_json = None
        images_metadata = None
        custom_metadata = None
        
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    metadata_json = json.load(f)
                
                # Support nouvelle structure
                if "images" in metadata_json:
                    images_metadata = metadata_json["images"]
                    custom_metadata = metadata_json.get("metadata", {})
                else:
                    # Ancienne structure (fallback)
                    images_metadata = metadata_json
                    custom_metadata = {}
                
                print(f"Métadonnées chargées depuis: {manifest_file}")
            except Exception as e:
                print(f"Erreur lors du chargement de {manifest_file}: {e}")
        
        # Charger toutes les images
        image_files = []
        supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
        
        for filename in os.listdir(self.input_folder):
            if filename.lower().endswith(supported_formats):
                filepath = os.path.join(self.input_folder, filename)
                try:
                    img = Image.open(filepath)
                    img = img.convert('RGBA')  # Assurer le format RGBA
                    img = self.resize_image_if_needed(img)  # Redimensionner si nécessaire
                    image_files.append((filename, img))
                except Exception as e:
                    print(f"Erreur lors du chargement de {filename}: {e}")
        
        if not image_files:
            print("Aucune image trouvée dans le dossier d'entrée")
            return {}
        
        print(f"Images chargées: {len(image_files)}")
        
        # Résultats finaux
        atlas_data = {
            'atlases': [],
            'total_images': len(image_files),
            'max_atlas_size': self.max_atlas_size
        }
        
        # Ajouter les métadonnées des images si elles existent
        if images_metadata is not None:
            atlas_data['images_metadata'] = images_metadata
        
        # Ajouter les métadonnées custom si elles existent
        if custom_metadata is not None and custom_metadata:
            atlas_data['metadata'] = custom_metadata
        
        # Générer des atlas pour différents niveaux de downscale
        scale_factors = [1, 2, 4, 8, 16]  # Niveaux de downscale
        
        for scale_factor in scale_factors:
            print(f"\nGénération des atlas avec downscale x{scale_factor}...")
            
            # Downscaler toutes les images
            downscaled_images = []
            for filename, img in image_files:
                downscaled_img = self.downscale_image(img, scale_factor)
                downscaled_images.append((filename, downscaled_img))
            
            # Créer autant d'atlas que nécessaire pour ce niveau de downscale
            remaining_images = downscaled_images.copy()
            atlas_index = 0
            scale_atlas_count = 0  # Compter les atlas pour ce niveau de downscale
            
            while remaining_images:
                atlas, uv_coords = self.pack_images_in_atlas(remaining_images)
                
                if not atlas or not uv_coords:
                    break
                
                # Sauvegarder l'atlas
                atlas_filename = f"atlas_scale{scale_factor}_{atlas_index}.png"
                atlas_path = os.path.join(self.output_folder, atlas_filename)
                atlas.save(atlas_path)
                
                # Ajouter aux données
                atlas_info = {
                    'file': atlas_filename,
                    'scale': scale_factor,
                    'index': atlas_index,
                    'width': atlas.width,
                    'height': atlas.height,
                    'uv': uv_coords,
                    'count': len(uv_coords)
                }
                atlas_data['atlases'].append(atlas_info)
                
                print(f"Atlas créé: {atlas_filename} ({len(uv_coords)} images)")
                
                # Retirer les images traitées de la liste
                processed_filenames = set(uv_coords.keys())
                remaining_images = [(name, img) for name, img in remaining_images 
                                  if name not in processed_filenames]
                
                atlas_index += 1
                scale_atlas_count += 1
                
                # Sécurité pour éviter les boucles infinies
                if atlas_index > 100:
                    print("Nombre maximum d'atlas atteint pour ce niveau de downscale")
                    break
            
            # Si ce niveau de downscale n'a produit qu'un seul atlas, arrêter
            if scale_atlas_count == 1:
                print(f"Arrêt: Le downscale x{scale_factor} ne produit qu'un seul atlas (toutes les images rentrent)")
                break
        
        # Sauvegarder les données JSON
        json_path = os.path.join(self.output_folder, "atlas_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(atlas_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nGénération terminée!")
        print(f"Nombre total d'atlas générés: {len(atlas_data['atlases'])}")
        print(f"Données sauvegardées dans: {json_path}")
        
        return atlas_data


def main(input_folder='input_images', output_folder='output_atlases'):
    """
    Fonction principale pour générer les atlas
    
    Args:
        input_folder: Dossier contenant les images sources
        output_folder: Dossier de sortie pour les atlas
        
    Returns:
        dict: Les données d'atlas générées ou None en cas d'erreur
    """
    
    # Vérifier que le dossier d'entrée existe
    if not os.path.exists(input_folder):
        print(f"Erreur: Le dossier '{input_folder}' n'existe pas!")
        return None
    
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
        print("\n=== RÉSUMÉ ===")
        print(f"Images traitées: {atlas_data['total_images']}")
        print(f"Atlas générés: {len(atlas_data['atlases'])}")
        
        # Grouper par niveau de downscale
        by_scale = {}
        for atlas in atlas_data['atlases']:
            scale = atlas['scale']
            if scale not in by_scale:
                by_scale[scale] = 0
            by_scale[scale] += 1
        
        for scale, count in sorted(by_scale.items()):
            print(f"  - Downscale x{scale}: {count} atlas")
    
    return atlas_data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Génère des atlas à partir d\'images sources')
    parser.add_argument('--input', default='input_images',
                       help='Dossier des images d\'entrée (par défaut: input_images)')
    parser.add_argument('--output', default='output_atlases',
                       help='Dossier de sortie pour les atlas (par défaut: output_atlases)')
    
    args = parser.parse_args()
    main(args.input, args.output)
