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
        
        let html = '<h3>Atlas Files</h3>';
        
        // Sort scales numerically
        const sortedScales = Object.keys(byScale).sort((a, b) => parseInt(a) - parseInt(b));
        
        sortedScales.forEach(scale => {
            const atlases = byScale[scale];
            html += `<div class="scale-group">
                <strong>Scale ${scale}x (${atlases.length} atlas${atlases.length > 1 ? 'es' : ''})</strong>`;
            
            atlases.forEach((atlas, idx) => {
                const filename = `atlas/${idx}.png`;
                const fullUrl = this.getResourceUrl(filename);
                html += `<div class="api-endpoint">
                    <code>${filename}</code>
                    <a href="${fullUrl}" target="_blank">View</a>
                </div>`;
            });
            
            html += '</div>';
        });
        
        container.innerHTML = html;
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
        const imageSrc = atlasIndex !== -1 ? this.getResourceUrl(`atlas/${atlasIndex}.png`) : this.getPlaceholderImage();
        
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
            <div class="lightbox-content">
                <img src="${imageSrc}" alt="${this.escapeHtml(title)}">
                <div class="lightbox-info">
                    <div class="lightbox-title">${this.escapeHtml(title)}</div>
                    ${url ? `<a href="${url}" target="_blank" class="lightbox-link">${this.escapeHtml(url)}</a>` : ''}
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
