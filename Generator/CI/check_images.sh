#!/bin/bash
# Script pour vérifier la présence des images sources
# Utilisé par le workflow GitHub Actions

check_images() {
    if [ -d "images" ] && [ "$(ls -A images 2>/dev/null)" ]; then
        echo "images_exist=true"
        echo "✅ Dossier images trouvé avec $(ls -1 images | wc -l) fichiers"
        return 0
    else
        echo "images_exist=false"
        echo "⚠️ Aucune image trouvée dans le dossier 'images/'"
        return 1
    fi
}

# Exécuter la vérification
check_images
