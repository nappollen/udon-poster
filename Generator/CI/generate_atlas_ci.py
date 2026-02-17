"""
Script to generate atlases in CI/CD context
Used by GitHub Actions workflow
"""

import sys
import os
from pathlib import Path


def github_group(title):
    """Creates a log group in GitHub Actions"""
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print(f"::group::{title}", flush=True)


def github_endgroup():
    """Closes a log group in GitHub Actions"""
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print("::endgroup::", flush=True)


def github_summary(content):
    """Adds content to GitHub Actions summary (visible in interface)"""
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary_file:
            with open(summary_file, 'a', encoding='utf-8') as f:
                f.write(content + '\n')


def github_output(name, value):
    """Sets an output for GitHub Actions"""
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        output_file = os.environ.get('GITHUB_OUTPUT')
        if output_file:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{name}={value}\n")


def progress_callback(step, total, message):
    """Callback to display progress in GitHub Actions"""
    percentage = int((step / total) * 100) if total > 0 else 0
    progress_bar = '█' * (percentage // 5) + '░' * (20 - percentage // 5)
    
    # Display normal progress bar
    print(f"[{progress_bar}] {percentage}% - {message}", flush=True)
    
    # Also display as GitHub Actions notice for more visibility
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print(f"::notice title=Progress {percentage}%::{message}", flush=True)


def generate_atlases_ci(input_folder: str, output_folder: str):
    """
    Generates atlases from source images for CI
    
    Args:
        input_folder: Folder containing source images
        output_folder: Output folder for atlases
    """
    github_group("🎨 Generating atlases")
    
    # Add parent folder to path to import generate_posters
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from generate_posters import main as generate_atlases
    import json
    
    print(f"📂 Input folder: {input_folder}")
    print(f"📂 Output folder: {output_folder}")
    
    # Check input folder exists
    if not os.path.exists(input_folder):
        print(f"❌ Error: Folder '{input_folder}' does not exist!")
        github_endgroup()
        sys.exit(1)
    
    # Load configuration from manifest.json if it exists
    max_atlas_size = 2048  # Default
    padding = 2  # Default
    max_image_size = None  # Default (will use max_atlas_size)
    
    manifest_file = Path(input_folder) / 'manifest.json'
    if manifest_file.exists():
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Check if metadata contains generation parameters
            if 'metadata' in manifest:
                metadata = manifest['metadata']
                
                if 'max_atlas_size' in metadata:
                    max_atlas_size = int(metadata['max_atlas_size'])
                    print(f"📐 Using max_atlas_size from manifest: {max_atlas_size}")
                
                if 'padding' in metadata:
                    padding = int(metadata['padding'])
                    print(f"📐 Using padding from manifest: {padding}")
                
                if 'max_image_size' in metadata:
                    max_image_size = int(metadata['max_image_size'])
                    print(f"📐 Using max_image_size from manifest: {max_image_size}")
        except Exception as e:
            print(f"⚠️ Warning: Could not read generation parameters from manifest.json: {e}")
            print(f"   Using default values instead")
    
    # Count images
    image_files = [
        f for f in os.listdir(input_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))
    ]
    print(f"🖼️ {len(image_files)} images found")
    
    if not image_files:
        print("⚠️ No valid images found")
        github_endgroup()
        sys.exit(1)
    
    # Generate atlases using refactored function with callback and configuration
    atlas_data = generate_atlases(
        input_folder, 
        output_folder, 
        max_atlas_size=max_atlas_size,
        padding=padding,
        max_image_size=max_image_size,
        progress_callback=progress_callback
    )
    
    github_endgroup()
    
    if not atlas_data:
        print("❌ Atlas generation failed")
        sys.exit(1)
    
    # Export statistics for final summary
    num_atlases = len(atlas_data.get('atlases', []))
    num_images = atlas_data.get('total_images', 0)
    
    # Extract unique downscale levels from atlases
    scales = sorted(set(atlas.get('scale', 1) for atlas in atlas_data.get('atlases', [])))
    scales_str = ', '.join(f"{s}×" for s in scales)
    
    github_output('num_atlases', str(num_atlases))
    github_output('num_images', str(num_images))
    github_output('downscales', scales_str)
    
    return atlas_data


def generate_static_ci(atlas_folder: str, output_static_folder: str):
    """
    Generates static version for GitHub Pages in CI context
    
    Args:
        atlas_folder: Folder containing generated atlases
        output_static_folder: Output folder for static version
    """
    github_group("📦 Generating static version")
    
    # Add parent folder to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from generate_static import generate_static_version
    import json
    from datetime import datetime, timezone
    
    print(f"📂 Atlas folder: {atlas_folder}")
    print(f"📂 Output folder: {output_static_folder}")
    
    # Check atlas folder exists
    if not os.path.exists(atlas_folder):
        print(f"❌ Error: Folder '{atlas_folder}' does not exist!")
        github_endgroup()
        sys.exit(1)
    
    json_file = Path(atlas_folder) / 'manifest.json'
    if not json_file.exists():
        print(f"❌ Error: File {json_file} does not exist")
        print("Atlases were probably not generated correctly")
        github_endgroup()
        sys.exit(1)
    
    # Load atlas data and add CI/CD metadata
    with open(json_file, 'r', encoding='utf-8') as f:
        atlas_data = json.load(f)
    
    # Get GitHub Actions information from environment variables
    github_sha = os.environ.get('GITHUB_SHA', '')
    github_repo = os.environ.get('GITHUB_REPOSITORY', '')
    github_server = os.environ.get('GITHUB_SERVER_URL', 'https://github.com')
    github_run_id = os.environ.get('GITHUB_RUN_ID', '')
    github_run_number = os.environ.get('GITHUB_RUN_NUMBER', '')
    github_workflow = os.environ.get('GITHUB_WORKFLOW', '')
    github_ref = os.environ.get('GITHUB_REF', '')
    github_actor = os.environ.get('GITHUB_ACTOR', '')
    
    # Build GitHub Pages URL
    github_pages_url = ''
    if github_repo:
        # Format: https://<username>.github.io/<repo>/
        parts = github_repo.split('/')
        if len(parts) == 2:
            github_pages_url = f"https://{parts[0]}.github.io/{parts[1]}/"
    
    # Create CI/CD metadata
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
    
    # Add or merge with existing metadata
    if 'metadata' not in atlas_data:
        atlas_data['metadata'] = {}
    
    atlas_data['metadata']['base_url'] = github_pages_url
    atlas_data['metadata']['ci'] = ci_metadata
    
    print(f"✅ CI/CD metadata added:")
    print(f"   - Base URL: {github_pages_url}")
    print(f"   - Commit: {ci_metadata['commit']['short_sha']}")
    print(f"   - Workflow: {github_workflow} #{github_run_number}")
    print(f"   - Repository: {github_repo}")
    
    # Save modified data
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(atlas_data, f, indent=2, ensure_ascii=False)
    
    # Generate static version using refactored function with callback
    result = generate_static_version(atlas_folder, output_static_folder, progress_callback=progress_callback)
    
    github_endgroup()
    
    if not result:
        print("❌ Failed to generate static version")
        sys.exit(1)
    
    # Export URL for final summary
    github_output('atlas_url', f"{github_pages_url}atlas.json")
    github_output('github_pages_url', github_pages_url)
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate atlases for CI/CD')
    parser.add_argument('command', choices=['generate', 'static'], 
                       help='Command to execute')
    parser.add_argument('--input', default='../images',
                       help='Source images folder')
    parser.add_argument('--output', default='output_atlases',
                       help='Atlas output folder')
    parser.add_argument('--static-output', default='output_static',
                       help='Static version output folder')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        generate_atlases_ci(args.input, args.output)
    elif args.command == 'static':
        generate_static_ci(args.output, args.static_output)
