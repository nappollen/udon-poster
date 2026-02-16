"""
Utilitaires pour le CI/CD
"""

import os
import sys


def check_images_exist(images_folder: str = "images") -> bool:
    """
    Vérifie si le dossier d'images existe et contient des fichiers
    
    Args:
        images_folder: Chemin vers le dossier d'images
        
    Returns:
        True si des images existent, False sinon
    """
    if os.path.isdir(images_folder):
        files = os.listdir(images_folder)
        if files:
            print(f"✅ Dossier images trouvé avec {len(files)} fichiers")
            return True
    
    print("⚠️ Aucune image trouvée dans le dossier 'images/'")
    return False


def display_deployment_info(deployment_url: str):
    """
    Affiche les informations de déploiement
    
    Args:
        deployment_url: URL de déploiement GitHub Pages
    """
    print("🎉 Déploiement réussi!")
    print(f"📍 URL de base: {deployment_url}")
    print(f"📄 Atlas JSON: {deployment_url}atlas.json")
    print("")
    print("Utilisez cette URL dans votre monde VRChat!")
