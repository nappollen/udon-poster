"""
Script pour créer la page index.html pour GitHub Pages
Utilisé par le workflow GitHub Actions
"""

import sys
from pathlib import Path


def create_index_html(output_folder: str):
    """
    Crée la page index.html pour GitHub Pages
    
    Args:
        output_folder: Dossier où créer l'index.html
    """
    output_path = Path(output_folder) / 'index.html'
    
    html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Atlas Server - GitHub Pages</title>
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background: #0d1117;
            color: #c9d1d9;
        }
        h1 {
            color: #58a6ff;
            border-bottom: 1px solid #21262d;
            padding-bottom: 10px;
        }
        .info {
            background: #161b22;
            padding: 20px;
            border-radius: 6px;
            border: 1px solid #30363d;
            margin: 20px 0;
        }
        code {
            background: #0d1117;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #79c0ff;
        }
        pre {
            background: #0d1117;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
        }
        a {
            color: #58a6ff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #161b22;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #30363d;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #58a6ff;
        }
        .badge {
            display: inline-block;
            background: #1f6feb;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            margin-left: 8px;
        }
    </style>
</head>
<body>
    <h1>🖼️ Atlas Server - GitHub Pages</h1>
    
    <div class="info">
        <h2>📊 API Endpoints</h2>
        <ul>
            <li><strong>Atlas JSON:</strong> <a href="atlas.json" target="_blank"><code>atlas.json</code></a> <span class="badge">GET</span></li>
            <li><strong>Images:</strong> <code>atlas/{index}.png</code> <span class="badge">GET</span></li>
        </ul>
    </div>
    
    <div id="stats-container"></div>
    
    <div class="info">
        <h2>🚀 Utilisation dans VRChat</h2>
        <p>Utilisez cette URL de base dans votre monde VRChat :</p>
        <pre><code id="base-url"></code></pre>
        
        <h3>Exemples d'URLs :</h3>
        <ul id="example-urls"></ul>
    </div>
    
    <div class="info">
        <h2>📝 Format de l'API</h2>
        <p>Le fichier <code>atlas.json</code> contient :</p>
        <pre><code>{
  "mapping": [
    { "name": "image1.png", "width": 1024, "height": 1024 },
    { "name": "image2.png", "width": 512, "height": 512 }
  ],
  "atlases": [
    {
      "scale": 1.0,
      "width": 2048,
      "height": 2048,
      "uv": {
        "0": [0, 0, 0.5, 0.5],
        "1": [0.5, 0, 1.0, 0.5]
      }
    }
  ]
}</code></pre>
    </div>
    
    <script>
        // Afficher l'URL de base
        const baseUrl = window.location.origin + window.location.pathname.replace('index.html', '');
        document.getElementById('base-url').textContent = baseUrl;
        
        // Générer des exemples d'URLs
        const exampleUrls = document.getElementById('example-urls');
        exampleUrls.innerHTML = `
            <li><code>${baseUrl}atlas.json</code> - Données des atlas</li>
            <li><code>${baseUrl}atlas/0.png</code> - Premier atlas</li>
            <li><code>${baseUrl}atlas/1.png</code> - Deuxième atlas</li>
        `;
        
        // Charger les statistiques
        fetch('atlas.json')
            .then(response => response.json())
            .then(data => {
                const statsContainer = document.getElementById('stats-container');
                
                // Calculer les statistiques
                const numAtlases = data.atlases ? data.atlases.length : 0;
                const numImages = data.mapping ? data.mapping.length : 0;
                
                // Calculer les échelles
                const scales = {};
                if (data.atlases) {
                    data.atlases.forEach(atlas => {
                        const scale = atlas.scale || 1.0;
                        scales[scale] = (scales[scale] || 0) + 1;
                    });
                }
                
                let scaleInfo = '';
                for (const [scale, count] of Object.entries(scales)) {
                    scaleInfo += `<div class="stat-card"><div class="stat-value">${count}</div><div>Downscale x${scale}</div></div>`;
                }
                
                statsContainer.innerHTML = `
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-value">${numAtlases}</div>
                            <div>Atlas générés</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${numImages}</div>
                            <div>Images sources</div>
                        </div>
                        ${scaleInfo}
                    </div>
                `;
            })
            .catch(err => {
                console.error('Erreur lors du chargement des stats:', err);
                document.getElementById('stats-container').innerHTML = `
                    <div class="info">
                        <p>⚠️ Impossible de charger les statistiques. L'atlas est peut-être vide.</p>
                    </div>
                `;
            });
    </script>
</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Page index.html créée: {output_path}")


def create_empty_atlas(output_folder: str):
    """
    Crée un atlas vide (fallback)
    
    Args:
        output_folder: Dossier où créer l'atlas vide
    """
    import json
    
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    empty_atlas = {
        "mapping": [],
        "atlases": []
    }
    
    with open(output_path / 'atlas.json', 'w', encoding='utf-8') as f:
        json.dump(empty_atlas, f, indent=2)
    
    print("⚠️ Atlas vide créé (aucune image source trouvée)")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Création de l\'index.html pour GitHub Pages')
    parser.add_argument('command', choices=['create-index', 'empty-atlas'],
                       help='Commande à exécuter')
    parser.add_argument('--output', default='output_static',
                       help='Dossier de sortie')
    
    args = parser.parse_args()
    
    if args.command == 'create-index':
        create_index_html(args.output)
    elif args.command == 'empty-atlas':
        create_empty_atlas(args.output)
