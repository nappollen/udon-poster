/**
 * Atlas Viewer Application
 * Loads and displays image atlas data
 */

class AtlasViewer {
    constructor() {
        this.data = null;
        this.basePath = localStorage.getItem('atlasBasePath') || '';
        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        window.addEventListener('DOMContentLoaded', () => {
            this.loadAtlasData();
        });
    }

    /**
     * Load atlas data from JSON file
     */
    async loadAtlasData() {
        try {
            const url = this.getResourceUrl('atlas.json');
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.data = await response.json();
            this.displayAtlasData();
        } catch (error) {
            console.error('Error loading atlas data:', error);
            this.showError(error);
        }
    }

    /**
     * Display all atlas data
     */
    displayAtlasData() {
        // Hide loading indicator
        this.hideLoading();
        
        // Update statistics
        this.updateStats();
        
        // Display atlas endpoints
        this.displayAtlasEndpoints();
        
        // Update GitHub link if metadata available
        this.updateGithubLink();
        
        // Update base path if available
        this.updateBasePath();
        
        // Display image gallery
        this.displayGallery();
    }

    /**
     * Update statistics cards
     */
    updateStats() {
        const totalImages = this.data.mapping ? this.data.mapping.length : 0;
        const totalAtlases = this.data.atlases ? this.data.atlases.length : 0;
        const scaleFactors = this.data.atlases 
            ? [...new Set(this.data.atlases.map(a => a.scale))].length 
            : 0;

        this.setElementText('navTotalImages', totalImages);
        this.setElementText('navTotalAtlases', totalAtlases);
        this.setElementText('navScaleFactors', scaleFactors);
    }

    /**
     * Display atlas file endpoints
     */
    displayAtlasEndpoints() {
        const container = document.getElementById('atlasEndpoints');
        if (!this.data.atlases || this.data.atlases.length === 0) {
            container.innerHTML = '<p style="color: hsl(var(--muted-foreground));">No atlas files found.</p>';
            return;
        }

        // Group atlases by scale
        const byScale = this.groupAtlasesByScale();
        
        const atlasListDiv = document.createElement('div');
        atlasListDiv.className = 'atlas-list';
        
        // Sort scales numerically
        const sortedScales = Object.keys(byScale).sort((a, b) => parseInt(a) - parseInt(b));
        
        let globalIdx = 0;
        sortedScales.forEach((scale, scaleIdx) => {
            const atlases = byScale[scale];
            // Calculer une couleur basée sur le nombre total de scales
            const hue = (scaleIdx * 360 / sortedScales.length) % 360;
            const bgColor = `hsla(${hue}, 15%, 25%, 1)`;
            const borderColor = `hsla(${hue}, 25%, 40%, 1)`;
            
            atlases.forEach((atlas, idx) => {
                const filename = `atlas/${scale}x/${idx}.png`;
                const fullUrl = this.getAtlasUrl(globalIdx);
                
                const atlasItem = document.createElement('a');
                atlasItem.href = '#';
                atlasItem.className = 'atlas-item';
                atlasItem.title = filename;
                atlasItem.style.backgroundColor = bgColor;
                atlasItem.style.borderColor = borderColor;
                atlasItem.style.color = 'white';
                atlasItem.innerHTML = `
                    <span class="atlas-scale">${scale}x</span>
                    <span class="atlas-name">#${globalIdx}</span>
                `;
                
                atlasItem.onclick = (e) => {
                    e.preventDefault();
                    this.showLightbox(fullUrl, `Atlas ${scale}x #${globalIdx}`, '');
                };
                
                atlasListDiv.appendChild(atlasItem);
                globalIdx++;
            });
        });
        
        container.innerHTML = '';
        container.appendChild(atlasListDiv);
    }

    /**
     * Update GitHub link in navbar
     */
    updateGithubLink() {
        const metadata = this.data.metadata;
        if (!metadata || !metadata.ci) {
            return;
        }
        
        // Update commit link
        if (metadata.ci.commit) {
            const githubLink = document.getElementById('githubLink');
            const commitId = document.getElementById('commitId');
            
            if (githubLink && commitId) {
                const commit = metadata.ci.commit;
                githubLink.href = commit.url;
                commitId.textContent = commit.short_sha;
                githubLink.style.display = 'flex';
            }
        }
        
        // Update repository link
        if (metadata.ci.repository) {
            const repoLink = document.getElementById('repoLink');
            if (repoLink) {
                repoLink.href = metadata.ci.repository.url;
                repoLink.target = '_blank';
            }
        }
    }

    /**
     * Update base path copy button
     */
    updateBasePath() {
        const metadata = this.data.metadata;
        if (!metadata || !metadata.base_url) {
            return;
        }
        
        const section = document.getElementById('basePathSection');
        const button = document.getElementById('copyBasePath');
        const text = document.getElementById('basePathText');
        
        if (!section || !button || !text) return;
        
        text.textContent = metadata.base_url;
        section.style.display = 'block';
        
        button.onclick = async () => {
            try {
                await navigator.clipboard.writeText(metadata.base_url);
                const originalText = text.textContent;
                text.textContent = 'Copied!';
                button.classList.add('copied');
                
                setTimeout(() => {
                    text.textContent = originalText;
                    button.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
                text.textContent = 'Failed to copy';
                setTimeout(() => {
                    text.textContent = metadata.base_url;
                }, 2000);
            }
        };
    }

    /**
     * Group atlases by scale factor
     */
    groupAtlasesByScale() {
        const byScale = {};
        this.data.atlases.forEach(atlas => {
            if (!byScale[atlas.scale]) {
                byScale[atlas.scale] = [];
            }
            byScale[atlas.scale].push(atlas);
        });
        return byScale;
    }

    /**
     * Display image gallery
     */
    displayGallery() {
        const gallery = document.getElementById('gallery');
        
        if (!this.data.mapping || this.data.mapping.length === 0) {
            gallery.innerHTML = '<p style="text-align: center; padding: 2.5rem; color: hsl(var(--muted-foreground));">No images found in atlas.</p>';
            return;
        }

        gallery.innerHTML = '';
        
        this.data.mapping.forEach((metadata, index) => {
            const card = this.createImageCard(metadata, index);
            gallery.appendChild(card);
        });
    }

    /**
     * Create an image card element
     */
    createImageCard(metadata, index) {
        const card = document.createElement('div');
        card.className = 'image-card';
        
        // Find the atlas containing this image
        const atlasIndex = this.findAtlasForImage(index);
        const imageSrc = atlasIndex !== -1 ? this.getAtlasUrl(atlasIndex) : this.getPlaceholderImage();
        
        const title = metadata.title || `Image ${index + 1}`;
        const url = metadata.url || '';
        
        card.innerHTML = `
            <div class="image-wrapper">
                <img src="${imageSrc}" 
                     alt="${this.escapeHtml(title)}" 
                     loading="lazy" 
                     onerror="this.src='${this.getPlaceholderImage()}'">
                <div class="image-overlay">
                    <div class="image-title">${this.escapeHtml(title)}</div>
                    ${url ? `<div class="image-url">${this.escapeHtml(url)}</div>` : ''}
                </div>
            </div>
        `;
        
        // Make card clickable to show image
        card.style.cursor = 'pointer';
        card.onclick = (e) => {
            e.preventDefault();
            this.showLightbox(imageSrc, title, url);
        };
        
        return card;
    }

    /**
     * Show image in lightbox
     */
    showLightbox(imageSrc, title, url) {
        const lightbox = document.createElement('div');
        lightbox.className = 'lightbox';
        lightbox.innerHTML = `
            <button class="lightbox-close" aria-label="Close">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
            <div class="lightbox-content">
                <img src="${imageSrc}" alt="${this.escapeHtml(title)}">
                <div class="lightbox-info">
                    <div class="lightbox-title">${this.escapeHtml(title)}</div>
                    ${url ? `<a href="${url}" target="_blank" class="lightbox-link">${this.escapeHtml(url)}</a>` : ''}
                    <a href="${imageSrc}" target="_blank" class="lightbox-link" style="margin-top: 0.5rem; display: block; opacity: 0.7;">${this.escapeHtml(imageSrc)}</a>
                </div>
            </div>
        `;
        
        // Close on click
        lightbox.onclick = () => {
            lightbox.remove();
        };
        
        // Close on Escape key
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') {
                lightbox.remove();
                document.removeEventListener('keydown', handleKeyDown);
            }
        };
        document.addEventListener('keydown', handleKeyDown);
        
        document.body.appendChild(lightbox);
    }

    /**
     * Find the atlas index containing a specific image
     */
    findAtlasForImage(imageIndex) {
        for (let i = 0; i < this.data.atlases.length; i++) {
            if (this.data.atlases[i].uv && this.data.atlases[i].uv[imageIndex] !== undefined) {
                return i;
            }
        }
        return -1;
    }

    /**
     * Get atlas URL (either from data or construct it)
     */
    getAtlasUrl(atlasIndex) {
        // Check if atlas has a url field
        if (this.data.atlases[atlasIndex] && this.data.atlases[atlasIndex].url) 
            return this.data.atlases[atlasIndex].url;
        // Otherwise construct it
        return this.getResourceUrl(`atlas/${atlasIndex}.png`);
    }

    /**
     * Get resource URL with base path
     */
    getResourceUrl(path) {
        if (!this.basePath) return path;
        const separator = this.basePath.endsWith('/') ? '' : '/';
        return `${this.basePath}${separator}${path}`;
    }

    /**
     * Get placeholder image SVG
     */
    getPlaceholderImage() {
        return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%23f5f5f5' width='200' height='200'/%3E%3Ctext fill='%23737373' x='50%25' y='50%25' text-anchor='middle' dy='.3em' font-family='sans-serif'%3ENo Image%3C/text%3E%3C/svg%3E";
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    /**
     * Show error message
     */
    showError(error) {
        this.hideLoading();
        
        const errorDiv = document.getElementById('error');
        if (errorDiv) {
            errorDiv.style.display = 'block';
            errorDiv.innerHTML = `
                <h3>❌ Error Loading Atlas Data</h3>
                <p>${this.escapeHtml(error.message)}</p>
                <p>Make sure atlas.json exists and is accessible.</p>
            `;
        }
    }

    /**
     * Set text content of an element
     */
    setElementText(id, text) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = text;
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application
const atlasViewer = new AtlasViewer();
