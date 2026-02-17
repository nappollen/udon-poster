import os
import json
import math
import hashlib
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
    
    def __init__(self, width: int, height: int, placement_strategy: str = 'best_area_fit'):
        self.width = width
        self.height = height
        self.placement_strategy = placement_strategy
        self.free_rectangles = [Rectangle(0, 0, width, height)]
        self.used_rectangles = []
    
    def insert(self, width: int, height: int) -> Rectangle:
        """Insère un rectangle et retourne sa position, ou None si impossible"""
        best_rect = None
        
        if self.placement_strategy == 'best_area_fit':
            # Minimise l'espace perdu
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
        
        elif self.placement_strategy == 'best_short_side_fit':
            # Minimise le plus petit côté restant
            best_short_side_fit = float('inf')
            best_long_side_fit = float('inf')
            
            for rect in self.free_rectangles:
                if rect.width >= width and rect.height >= height:
                    leftover_horizontal = rect.width - width
                    leftover_vertical = rect.height - height
                    short_side_fit = min(leftover_horizontal, leftover_vertical)
                    long_side_fit = max(leftover_horizontal, leftover_vertical)
                    
                    if short_side_fit < best_short_side_fit or (short_side_fit == best_short_side_fit and long_side_fit < best_long_side_fit):
                        best_rect = Rectangle(rect.x, rect.y, width, height)
                        best_short_side_fit = short_side_fit
                        best_long_side_fit = long_side_fit
        
        elif self.placement_strategy == 'best_long_side_fit':
            # Minimise le plus grand côté restant
            best_long_side_fit = float('inf')
            best_short_side_fit = float('inf')
            
            for rect in self.free_rectangles:
                if rect.width >= width and rect.height >= height:
                    leftover_horizontal = rect.width - width
                    leftover_vertical = rect.height - height
                    long_side_fit = max(leftover_horizontal, leftover_vertical)
                    short_side_fit = min(leftover_horizontal, leftover_vertical)
                    
                    if long_side_fit < best_long_side_fit or (long_side_fit == best_long_side_fit and short_side_fit < best_short_side_fit):
                        best_rect = Rectangle(rect.x, rect.y, width, height)
                        best_long_side_fit = long_side_fit
                        best_short_side_fit = short_side_fit
        
        elif self.placement_strategy == 'bottom_left':
            # Place en bas à gauche (plus petits y puis x)
            best_y = float('inf')
            best_x = float('inf')
            
            for rect in self.free_rectangles:
                if rect.width >= width and rect.height >= height:
                    if rect.y < best_y or (rect.y == best_y and rect.x < best_x):
                        best_rect = Rectangle(rect.x, rect.y, width, height)
                        best_y = rect.y
                        best_x = rect.x
        
        elif self.placement_strategy == 'contact_point':
            # Maximise le contact avec les rectangles déjà placés
            best_contact = -1
            best_area_fit = float('inf')
            
            for rect in self.free_rectangles:
                if rect.width >= width and rect.height >= height:
                    contact = 0
                    # Compter les points de contact
                    if rect.x == 0:
                        contact += height  # Contact avec le bord gauche
                    if rect.y == 0:
                        contact += width   # Contact avec le bord haut
                    
                    # Vérifier contact avec autres rectangles
                    for used in self.used_rectangles:
                        # Contact à droite
                        if used.x + used.width == rect.x and not (rect.y + height <= used.y or rect.y >= used.y + used.height):
                            contact += min(height, used.height)
                        # Contact en bas
                        if used.y + used.height == rect.y and not (rect.x + width <= used.x or rect.x >= used.x + used.width):
                            contact += min(width, used.width)
                    
                    area_fit = rect.width * rect.height - width * height
                    
                    if contact > best_contact or (contact == best_contact and area_fit < best_area_fit):
                        best_rect = Rectangle(rect.x, rect.y, width, height)
                        best_contact = contact
                        best_area_fit = area_fit
        
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
    def __init__(self, max_atlas_size: int = 2048, input_folder: str = "", output_folder: str = "", padding: int = 2, max_image_size: int = None):
        self.max_atlas_size = max_atlas_size
        self.input_folder = input_folder or "input_images"
        self.output_folder = output_folder or "output_atlases"
        self.padding = padding  # Espacement entre les images pour éviter les artefacts
        self.max_image_size = max_image_size if max_image_size is not None else max_atlas_size  # Résolution max des images avant traitement
        
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
    
    def _sort_images(self, images: List[Tuple[str, Image.Image]], sort_strategy: str) -> List[Tuple[str, Image.Image]]:
        """Trie les images selon la stratégie donnée
        
        Args:
            images: Liste des images à trier
            sort_strategy: Stratégie de tri
            
        Returns:
            Liste d'images triées
        """
        if sort_strategy == 'none':
            # Pas de tri, garder l'ordre existant
            return images[:]
        elif sort_strategy == 'area':
            return sorted(images, key=lambda x: x[1].size[0] * x[1].size[1], reverse=True)
        elif sort_strategy == 'area_asc':
            return sorted(images, key=lambda x: x[1].size[0] * x[1].size[1], reverse=False)
        elif sort_strategy == 'height':
            return sorted(images, key=lambda x: x[1].size[1], reverse=True)
        elif sort_strategy == 'height_asc':
            return sorted(images, key=lambda x: x[1].size[1], reverse=False)
        elif sort_strategy == 'width':
            return sorted(images, key=lambda x: x[1].size[0], reverse=True)
        elif sort_strategy == 'width_asc':
            return sorted(images, key=lambda x: x[1].size[0], reverse=False)
        elif sort_strategy == 'perimeter':
            return sorted(images, key=lambda x: x[1].size[0] + x[1].size[1], reverse=True)
        elif sort_strategy == 'max_side':
            return sorted(images, key=lambda x: max(x[1].size[0], x[1].size[1]), reverse=True)
        elif sort_strategy == 'min_side':
            return sorted(images, key=lambda x: min(x[1].size[0], x[1].size[1]), reverse=True)
        elif sort_strategy == 'ratio':
            return sorted(images, key=lambda x: x[1].size[0] / max(x[1].size[1], 1), reverse=True)
        elif sort_strategy == 'ratio_inv':
            return sorted(images, key=lambda x: x[1].size[1] / max(x[1].size[0], 1), reverse=True)
        elif sort_strategy == 'diagonal':
            return sorted(images, key=lambda x: (x[1].size[0]**2 + x[1].size[1]**2)**0.5, reverse=True)
        elif sort_strategy == 'pathological':
            sorted_by_area = sorted(images, key=lambda x: x[1].size[0] * x[1].size[1], reverse=True)
            result = []
            left, right = 0, len(sorted_by_area) - 1
            while left <= right:
                result.append(sorted_by_area[left])
                if left != right:
                    result.append(sorted_by_area[right])
                left += 1
                right -= 1
            return result
        else:
            return images[:]
    
    def pack_images_in_atlas(self, images: List[Tuple[str, Image.Image]], sort_strategy: str = 'area', placement_strategy: str = 'best_area_fit') -> Tuple[Image.Image, Dict[str, Dict[str, float]]]:
        """Pack les images dans un atlas en utilisant un algorithme optimisé
        
        Args:
            images: Liste de tuples (filename, Image)
            sort_strategy: Stratégie de tri (area, height, width, etc.)
            placement_strategy: Stratégie de placement (best_area_fit, best_short_side_fit, best_long_side_fit, bottom_left, contact_point)
        """
        if not images:
            return None, {}
        
        # Trier les images selon la stratégie
        sorted_images = self._sort_images(images, sort_strategy)
        
        # Créer l'atlas
        atlas_width = self.max_atlas_size
        atlas_height = self.max_atlas_size
        atlas = Image.new('RGBA', (atlas_width, atlas_height), (0, 0, 0, 0))
        
        # Initialiser le bin packer avec la stratégie de placement
        packer = BinPacker(atlas_width, atlas_height, placement_strategy)
        
        # Coordonnées UV pour chaque image
        uv_coords = {}
        max_right = 0
        max_bottom = 0
        
        for filename, img in sorted_images:
            img_width, img_height = img.size
            
            # Ajouter le padding aux dimensions
            padded_width = img_width + self.padding * 2
            padded_height = img_height + self.padding * 2
            
            # Essayer de placer l'image dans l'atlas
            rect = packer.insert(padded_width, padded_height)
            
            if rect is None:
                # Plus d'espace dans cet atlas
                break
            
            # Placer l'image dans l'atlas (avec offset du padding)
            atlas.paste(img, (rect.x + self.padding, rect.y + self.padding))
            
            # Calculer les coordonnées UV (coordonnées réelles de l'image, sans padding)
            uv_coords[filename] = {
                'x': rect.x + self.padding,
                'y': rect.y + self.padding,
                'width': img_width,
                'height': img_height
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
    
    def evaluate_atlas_configuration(self, atlas_list: List[Dict]) -> Dict[str, Any]:
        """Évalue la qualité d'une configuration d'atlas
        
        Returns:
            dict: Score avec nombre d'atlas, taille totale et efficacité
        """
        total_atlas_area = sum(a['width'] * a['height'] for a in atlas_list)
        total_image_area = sum(
            sum(uv['width'] * uv['height'] for uv in a['uv'].values())
            for a in atlas_list
        )
        
        # Calculer l'espace réservé au padding (padding * 2 par image sur chaque axe)
        total_padding_area = sum(
            sum(
                (uv['width'] + self.padding * 2) * (uv['height'] + self.padding * 2) - uv['width'] * uv['height']
                for uv in a['uv'].values()
            )
            for a in atlas_list
        )
        
        # Efficacité = surface images + padding / surface totale
        # Le padding est nécessaire donc on le compte comme "utilisé"
        used_area = total_image_area + total_padding_area
        efficiency = (used_area / total_atlas_area * 100) if total_atlas_area > 0 else 0
        
        return {
            'num_atlases': len(atlas_list),
            'total_area': total_atlas_area,
            'image_area': total_image_area,
            'efficiency': efficiency,
            'wasted_area': total_atlas_area - used_area
        }
    
    def test_packing_configuration(self, images: List[Tuple[str, Image.Image]], 
                                   atlas_size: int, sort_strategy: str, 
                                   reoptimize_each_atlas: bool = True) -> List[Dict]:
        """Teste une configuration spécifique de packing
        
        Args:
            images: Images à packer
            atlas_size: Taille max de l'atlas
            sort_strategy: Stratégie de tri
            reoptimize_each_atlas: Si True, réoptimise le tri pour chaque nouvel atlas
        
        Returns:
            list: Liste des atlas générés pour cette configuration
        """
        # Sauvegarder la taille d'atlas actuelle
        original_size = self.max_atlas_size
        self.max_atlas_size = atlas_size
        
        atlases = []
        remaining_images = images.copy()
        atlas_index = 0
        
        while remaining_images:
            # Réoptimiser le tri pour les images restantes (si activé)
            if reoptimize_each_atlas:
                atlas, uv_coords = self.pack_images_in_atlas(remaining_images, sort_strategy)
            else:
                # Mode classique: un seul tri au début
                if atlas_index == 0:
                    sorted_remaining = self._sort_images(remaining_images, sort_strategy)
                atlas, uv_coords = self.pack_images_in_atlas(sorted_remaining if not reoptimize_each_atlas else remaining_images, sort_strategy)
            
            if not atlas or not uv_coords:
                break
            
            atlases.append({
                'atlas': atlas,
                'width': atlas.width,
                'height': atlas.height,
                'uv': uv_coords,
                'count': len(uv_coords)
            })
            
            # Retirer les images traitées
            processed_filenames = set(uv_coords.keys())
            remaining_images = [(name, img) for name, img in remaining_images 
                              if name not in processed_filenames]
            
            atlas_index += 1
            
            # Sécurité
            if atlas_index > 100:
                break
        
        # Restaurer la taille originale
        self.max_atlas_size = original_size
        
        return atlases
    
    def find_best_single_atlas(self, images: List[Tuple[str, Image.Image]], use_random: bool = True, permutations_per_config: int = 5) -> Dict[str, Any]:
        """Trouve la meilleure configuration pour générer UN SEUL atlas avec les images données
        
        Args:
            images: Images à packer
            use_random: Utiliser aussi des permutations aléatoires
            permutations_per_config: Nombre de permutations aléatoires par configuration
            
        Returns:
            dict: Meilleur atlas avec sa configuration ou None
        """
        if not images:
            return None
        
        # Vérifier si les images sont trop grandes pour rentrer dans un atlas
        max_img_width = max(img.size[0] for _, img in images)
        max_img_height = max(img.size[1] for _, img in images)
        
        if max_img_width + self.padding * 2 > 2048 or max_img_height + self.padding * 2 > 2048:
            print(f"  ⚠️ Images trop grandes (max: {max_img_width}x{max_img_height}), impossible de packer")
            return None
        
        import random
        
        # Configurations à tester
        atlas_sizes = [2048, 1536, 1024]
        sort_strategies = ['area', 'height', 'width', 'perimeter', 'max_side', 
                          'min_side', 'ratio', 'ratio_inv', 'diagonal', 
                          'height_asc', 'width_asc', 'pathological']
        placement_strategies = ['best_area_fit', 'best_short_side_fit', 'best_long_side_fit', 
                               'bottom_left', 'contact_point']
        
        best_result = None
        best_score = None
        
        configs_tested = 0
        
        # Tester toutes les combinaisons placement × tri
        for atlas_size in atlas_sizes:
            for placement_strategy in placement_strategies:
                for sort_strategy in sort_strategies:
                    # Pour chaque config, tester l'ordre déterministe
                    configs_tested += 1
                    
                    original_size = self.max_atlas_size
                    self.max_atlas_size = atlas_size
                    
                    atlas, uv_coords = self.pack_images_in_atlas(images, sort_strategy, placement_strategy)
                    
                    self.max_atlas_size = original_size
                    
                    if atlas and uv_coords:
                        atlas_area = atlas.width * atlas.height
                        image_area = sum(uv['width'] * uv['height'] for uv in uv_coords.values())
                        efficiency = (image_area / atlas_area * 100) if atlas_area > 0 else 0
                        num_images = len(uv_coords)
                        
                        score = {
                            'num_images': num_images,
                            'efficiency': efficiency,
                            'total_area': atlas_area,
                            'image_area': image_area
                        }
                        
                        is_better = False
                        if best_score is None:
                            is_better = True
                        elif score['num_images'] > best_score['num_images']:
                            is_better = True
                        elif score['num_images'] == best_score['num_images']:
                            if score['total_area'] < best_score['total_area']:
                                is_better = True
                            elif score['total_area'] == best_score['total_area']:
                                if score['efficiency'] > best_score['efficiency']:
                                    is_better = True
                        
                        if is_better:
                            best_result = {
                                'atlas': atlas,
                                'uv': uv_coords,
                                'width': atlas.width,
                                'height': atlas.height,
                                'count': num_images,
                                'atlas_size': atlas_size,
                                'sort_strategy': sort_strategy,
                                'placement_strategy': placement_strategy,
                                'score': score
                            }
                            best_score = score
                
                # Permutations pour cette combinaison placement + tri (limité pour éviter l'explosion)
                if permutations_per_config > 0:
                    for perm_idx in range(min(2, permutations_per_config)):  # Seulement 2 permutations par combo
                        configs_tested += 1
                        
                        sorted_images = self._sort_images(images, sort_strategy)
                        block_size = max(3, len(sorted_images) // 10)
                        shuffled_images = sorted_images.copy()
                        random.seed(atlas_size + configs_tested + perm_idx * 1000)
                        
                        for i in range(0, len(shuffled_images) - block_size, block_size // 2):
                            block = shuffled_images[i:i + block_size]
                            random.shuffle(block)
                            shuffled_images[i:i + block_size] = block
                        
                        original_size = self.max_atlas_size
                        self.max_atlas_size = atlas_size
                        
                        atlas, uv_coords = self.pack_images_in_atlas(shuffled_images, 'none', placement_strategy)
                        
                        self.max_atlas_size = original_size
                        
                        if not atlas or not uv_coords:
                            continue
                        
                        atlas_area = atlas.width * atlas.height
                        image_area = sum(uv['width'] * uv['height'] for uv in uv_coords.values())
                        efficiency = (image_area / atlas_area * 100) if atlas_area > 0 else 0
                        num_images = len(uv_coords)
                        
                        score = {
                            'num_images': num_images,
                            'efficiency': efficiency,
                            'total_area': atlas_area,
                            'image_area': image_area
                        }
                        
                        is_better = False
                        if score['num_images'] > best_score['num_images']:
                            is_better = True
                        elif score['num_images'] == best_score['num_images']:
                            if score['total_area'] < best_score['total_area']:
                                is_better = True
                            elif score['total_area'] == best_score['total_area']:
                                if score['efficiency'] > best_score['efficiency']:
                                    is_better = True
                        
                        if is_better:
                            best_result = {
                                'atlas': atlas,
                                'uv': uv_coords,
                                'width': atlas.width,
                                'height': atlas.height,
                                'count': num_images,
                                'atlas_size': atlas_size,
                                'sort_strategy': f'{sort_strategy}_perm{perm_idx}',
                                'placement_strategy': placement_strategy,
                                'score': score
                            }
                            best_score = score
        
        # Recherche aléatoire globale supplémentaire
        if use_random and best_result:
            best_atlas_size = best_result['atlas_size']
            best_placement = best_result.get('placement_strategy', 'best_area_fit')
            num_random_tests = 10
            
            for i in range(num_random_tests):
                random_images = images.copy()
                random.seed(i + 5000)
                random.shuffle(random_images)
                
                original_size = self.max_atlas_size
                self.max_atlas_size = best_atlas_size
                
                atlas, uv_coords = self.pack_images_in_atlas(random_images, 'none', best_placement)
                
                self.max_atlas_size = original_size
                
                if not atlas or not uv_coords:
                    continue
                
                atlas_area = atlas.width * atlas.height
                image_area = sum(uv['width'] * uv['height'] for uv in uv_coords.values())
                efficiency = (image_area / atlas_area * 100) if atlas_area > 0 else 0
                num_images = len(uv_coords)
                
                score = {
                    'num_images': num_images,
                    'efficiency': efficiency,
                    'total_area': atlas_area,
                    'image_area': image_area
                }
                
                is_better = False
                if score['num_images'] > best_score['num_images']:
                    is_better = True
                elif score['num_images'] == best_score['num_images']:
                    if score['total_area'] < best_score['total_area']:
                        is_better = True
                    elif score['total_area'] == best_score['total_area']:
                        if score['efficiency'] > best_score['efficiency']:
                            is_better = True
                
                if is_better:
                    best_result = {
                        'atlas': atlas,
                        'uv': uv_coords,
                        'width': atlas.width,
                        'height': atlas.height,
                        'count': num_images,
                        'atlas_size': best_atlas_size,
                        'sort_strategy': f'random_{i}',
                        'placement_strategy': best_placement,
                        'score': score
                    }
                    best_score = score
        
        return best_result
    
    def find_best_packing(self, images: List[Tuple[str, Image.Image]], use_advanced_search: bool = True) -> Dict[str, Any]:
        """Teste plusieurs configurations et retourne la meilleure
        
        Args:
            images: Liste des images à packer
            use_advanced_search: Active la recherche avancée avec permutations aléatoires
        
        Returns:
            dict: Meilleure configuration avec tous les atlas générés
        """
        print("\n🔍 Génération adaptative : réoptimisation à chaque atlas...")
        
        atlases = []
        remaining_images = images.copy()
        atlas_index = 0
        
        while remaining_images:
            print(f"\n  Atlas #{atlas_index + 1} : {len(remaining_images)} images restantes")
            
            # Trouver la meilleure config pour UN atlas avec les images restantes
            best_atlas = self.find_best_single_atlas(remaining_images, use_random=use_advanced_search)
            
            if not best_atlas:
                print("  ⚠️ Impossible de générer un atlas avec les images restantes")
                break
            
            # Ajouter cet atlas
            atlases.append(best_atlas)
            
            print(f"  ✅ Config: size={best_atlas['atlas_size']}, placement={best_atlas.get('placement_strategy', 'N/A')}, sort={best_atlas['sort_strategy']}")
            print(f"     → {best_atlas['count']} images, {best_atlas['width']}x{best_atlas['height']}, "
                  f"{best_atlas['score']['efficiency']:.1f}% efficacité")
            
            # Retirer les images placées
            processed_filenames = set(best_atlas['uv'].keys())
            remaining_images = [(name, img) for name, img in remaining_images 
                              if name not in processed_filenames]
            
            atlas_index += 1
            
            # Sécurité
            if atlas_index > 100:
                print("  ⚠️ Limite de 100 atlas atteinte")
                break
        
        # Calculer le score global
        total_atlas_area = sum(a['width'] * a['height'] for a in atlases)
        total_image_area = sum(
            sum(uv['width'] * uv['height'] for uv in a['uv'].values())
            for a in atlases
        )
        efficiency = (total_image_area / total_atlas_area * 100) if total_atlas_area > 0 else 0
        
        result = {
            'atlases': atlases,
            'atlas_size': atlases[0]['atlas_size'] if atlases else self.max_atlas_size,
            'sort_strategy': 'adaptive',
            'score': {
                'num_atlases': len(atlases),
                'total_area': total_atlas_area,
                'image_area': total_image_area,
                'efficiency': efficiency,
                'wasted_area': total_atlas_area - total_image_area
            }
        }
        
        print(f"\n✅ Résultat final (adaptatif):")
        print(f"   → {len(atlases)} atlas, {efficiency:.1f}% efficacité, "
              f"{result['score']['wasted_area']:.0f}px² perdus")
        
        return result
    
    def create_individual_atlases(self, images: List[Tuple[str, Image.Image]]) -> List[Dict]:
        """Crée un atlas séparé pour chaque image (fallback)
        
        Chaque image est redimensionnée si nécessaire pour tenir dans max_atlas_size
        
        Returns:
            list: Liste des atlas générés (un par image)
        """
        atlases = []
        
        for filename, img in images:
            img_width, img_height = img.size
            
            # Calculer la taille max de l'image en tenant compte du padding
            max_image_width = self.max_atlas_size - self.padding * 2
            max_image_height = self.max_atlas_size - self.padding * 2
            
            # Vérifier si l'image dépasse la taille max et la redimensionner si nécessaire
            if img_width > max_image_width or img_height > max_image_height:
                ratio = min(max_image_width / img_width, max_image_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                img_width, img_height = new_width, new_height
            
            # Créer un atlas avec padding (maintenant garanti <= max_atlas_size)
            atlas_width = img_width + self.padding * 2
            atlas_height = img_height + self.padding * 2
            atlas = Image.new('RGBA', (atlas_width, atlas_height), (0, 0, 0, 0))
            
            # Placer l'image au centre avec padding
            atlas.paste(img, (self.padding, self.padding))
            
            # Coordonnées UV (l'image occupe tout l'atlas sauf le padding)
            uv_coords = {
                filename: {
                    'x': self.padding,
                    'y': self.padding,
                    'width': img_width,
                    'height': img_height
                }
            }
            
            # Calculer les coordonnées UV normalisées
            uv_coords[filename]['rect_x'] = self.padding / atlas_width
            uv_coords[filename]['rect_y'] = 1.0 - (self.padding + img_height) / atlas_height
            uv_coords[filename]['rect_width'] = img_width / atlas_width
            uv_coords[filename]['rect_height'] = img_height / atlas_height
            
            atlases.append({
                'atlas': atlas,
                'width': atlas_width,
                'height': atlas_height,
                'uv': uv_coords,
                'count': 1
            })
        
        return atlases
    
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
        image_sha_map = {}  # Stocker les SHA des images originales
        supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
        
        for filename in os.listdir(self.input_folder):
            if filename.lower().endswith(supported_formats):
                filepath = os.path.join(self.input_folder, filename)
                try:
                    # Calculer le SHA256 du fichier original
                    with open(filepath, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    image_sha_map[filename] = file_hash
                    
                    img = Image.open(filepath)
                    img = img.convert('RGBA')  # Assurer le format RGBA
                    
                    # Redimensionner l'image si elle dépasse max_image_size
                    width, height = img.size
                    if width > self.max_image_size or height > self.max_image_size:
                        ratio = min(self.max_image_size / width, self.max_image_size / height)
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        print(f"  📐 {filename}: {width}x{height} → {new_width}x{new_height}")
                    
                    image_files.append((filename, img))
                except Exception as e:
                    print(f"Erreur lors du chargement de {filename}: {e}")
        
        if not image_files:
            print("Aucune image trouvée dans le dossier d'entrée")
            return {}
        
        print(f"Images chargées: {len(image_files)}")
        
        # Résultats finaux
        atlas_data = {
            'version': 1,
            'atlases': [],
            'total_images': len(image_files),
            'max_atlas_size': self.max_atlas_size,
            'max_image_size': self.max_image_size,
            'padding': self.padding
        }
        
        # Ajouter les métadonnées des images si elles existent
        if images_metadata is not None:
            # Ajouter les SHA aux métadonnées
            enriched_metadata = {}
            for img_name, meta in images_metadata.items():
                enriched_meta = meta.copy()
                if img_name in image_sha_map:
                    enriched_meta['sha'] = image_sha_map[img_name]
                enriched_metadata[img_name] = enriched_meta
            atlas_data['images_metadata'] = enriched_metadata
        else:
            # Créer des métadonnées basiques avec SHA
            atlas_data['images_metadata'] = {
                img_name: {'sha': image_sha_map.get(img_name, '')}
                for img_name, _ in image_files
            }
        
        # Ajouter les métadonnées custom si elles existent
        if custom_metadata is not None and custom_metadata:
            atlas_data['metadata'] = custom_metadata
        
        # Générer des atlas pour différents niveaux de downscale
        scale_factors = [1, 2, 4, 8, 16]  # Niveaux de downscale
        
        for scale_factor in scale_factors:
            print(f"\n{'='*60}")
            print(f"📐 Génération des atlas avec downscale x{scale_factor}...")
            print(f"{'='*60}")
            
            # Downscaler toutes les images
            downscaled_images = []
            for filename, img in image_files:
                downscaled_img = self.downscale_image(img, scale_factor)
                downscaled_images.append((filename, downscaled_img))
            
            # Trouver la meilleure configuration de packing
            best_config = self.find_best_packing(downscaled_images)
            
            if not best_config or not best_config['atlases']:
                print(f"⚠️ Aucune configuration valide trouvée pour downscale x{scale_factor}")
                print(f"   → Création d'un atlas par image (mode fallback)...")
                
                # Créer un atlas individuel pour chaque image
                individual_atlases = self.create_individual_atlases(downscaled_images)
                
                if not individual_atlases:
                    print(f"❌ Échec de la création des atlas individuels")
                    continue
                
                # Utiliser ces atlas comme configuration
                best_config = {
                    'atlases': individual_atlases,
                    'atlas_size': self.max_atlas_size,
                    'sort_strategy': 'individual',
                    'score': self.evaluate_atlas_configuration(individual_atlases)
                }
                
                print(f"   ✅ {len(individual_atlases)} atlas individuels créés")
            
            # Trier les atlas par nombre d'images (décroissant) pour que les plus remplis soient en premier
            sorted_atlases = sorted(best_config['atlases'], key=lambda a: a['count'], reverse=True)
            
            # Sauvegarder les atlas de la meilleure configuration
            atlas_index = 0
            for atlas_info in sorted_atlases:
                atlas = atlas_info['atlas']
                uv_coords = atlas_info['uv']
                
                # Calculer l'efficacité individuelle de cet atlas
                atlas_area = atlas.width * atlas.height
                image_area = sum(uv['width'] * uv['height'] for uv in uv_coords.values())
                padding_area = sum(
                    (uv['width'] + self.padding * 2) * (uv['height'] + self.padding * 2) - uv['width'] * uv['height']
                    for uv in uv_coords.values()
                )
                individual_efficiency = ((image_area + padding_area) / atlas_area * 100) if atlas_area > 0 else 0
                
                # Sauvegarder l'atlas
                atlas_filename = f"atlas_x{scale_factor:02d}_{atlas_index:02d}.png"
                atlas_path = os.path.join(self.output_folder, atlas_filename)
                atlas.save(atlas_path, optimize=True)
                
                # Calculer le SHA256 de l'atlas sauvegardé
                with open(atlas_path, 'rb') as f:
                    atlas_hash = hashlib.sha256(f.read()).hexdigest()
                
                # Ajouter aux données avec métadonnées de configuration
                atlas_data_info = {
                    'file': atlas_filename,
                    'scale': scale_factor,
                    'index': atlas_index,
                    'width': atlas.width,
                    'height': atlas.height,
                    'uv': uv_coords,
                    'count': len(uv_coords),
                    'sha': atlas_hash,
                    'sort_strategy': atlas_info.get('sort_strategy', best_config['sort_strategy']),
                    'placement_strategy': atlas_info.get('placement_strategy', 'N/A'),
                    'efficiency': individual_efficiency
                }
                atlas_data['atlases'].append(atlas_data_info)
                
                print(f"💾 Atlas sauvegardé: {atlas_filename} ({len(uv_coords)} images, "
                      f"{atlas.width}x{atlas.height}, {individual_efficiency:.1f}% efficacité)")
                
                atlas_index += 1
            
            scale_atlas_count = len(best_config['atlases'])
            
            # Si ce niveau de downscale n'a produit qu'un seul atlas, arrêter
            if scale_atlas_count == 1:
                print(f"\n✋ Arrêt: Le downscale x{scale_factor} ne produit qu'un seul atlas (toutes les images rentrent)")
                break
        
        # Sauvegarder les données JSON
        json_path = os.path.join(self.output_folder, "manifest.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(atlas_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nGénération terminée!")
        print(f"Nombre total d'atlas générés: {len(atlas_data['atlases'])}")
        print(f"Données sauvegardées dans: {json_path}")
        
        return atlas_data


def main(input_folder='input_images', output_folder='output_atlases', max_atlas_size=2048, padding=2, max_image_size=None):
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
        max_atlas_size=max_atlas_size,
        padding=padding,
        max_image_size=max_image_size,
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
    parser.add_argument('--max_atlas_size', type=int, default=2048,
                       help='Taille maximale des atlas (par défaut: 2048)')
    parser.add_argument('--padding', type=int, default=2,
                       help='Padding entre les images dans l\'atlas (par défaut: 2)')
    parser.add_argument('--max_image_size', type=int, default=None,
                       help='Taille maximale des images avant traitement (par défaut: même que max_atlas_size)')
    
    args = parser.parse_args()
    main(args.input, args.output, args.max_atlas_size, args.padding, args.max_image_size)
