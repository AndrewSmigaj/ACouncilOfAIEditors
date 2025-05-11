/**
 * Research Card Component
 * Displays research content and handles research requests
 */

class ResearchCard {
    constructor(containerId) {
        console.log(`[DEBUG ResearchCard] Creating new ResearchCard with container ID: ${containerId}`);
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.eventHandlers = new Map();
        
        if (!this.container) {
            console.error(`[DEBUG ResearchCard] Container element #${containerId} not found!`);
            throw new Error(`Container element #${containerId} not found`);
        }
        
        console.log(`[DEBUG ResearchCard] ResearchCard initialized successfully`);
    }
    
    // Event handling
    on(event, handler) {
        console.log(`[DEBUG ResearchCard] Adding handler for event: ${event}`);
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, new Set());
        }
        this.eventHandlers.get(event).add(handler);
    }
    
    off(event, handler) {
        console.log(`[DEBUG ResearchCard] Removing handler for event: ${event}`);
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).delete(handler);
        }
    }
    
    _emit(event, data) {
        console.log(`[DEBUG ResearchCard] Emitting event: ${event}`, data);
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => {
                console.log(`[DEBUG ResearchCard] Calling handler for event: ${event}`);
                handler(data);
            });
        } else {
            console.warn(`[DEBUG ResearchCard] No handlers registered for event: ${event}`);
        }
    }
    
    updateContent(researchData) {
        console.log(`[DEBUG ResearchCard] Updating content with data:`, researchData);
        
        if (!researchData) {
            console.warn(`[DEBUG ResearchCard] No research data provided`);
            this.container.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <div class="alert alert-info">
                            No research data available for this topic.
                        </div>
                    </div>
                </div>
            `;
            return;
        }
        
        // Display the AI name if provided
        const aiName = researchData.ai ? `<span class="badge bg-primary">${researchData.ai.toUpperCase()}</span> ` : '';
        
        console.log(`[DEBUG ResearchCard] Rendering content for topic: ${researchData.topic}`);
        this.container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3>${aiName}${researchData.topic}</h3>
                </div>
                <div class="card-body">
                    ${this._renderResearchContent(researchData)}
                </div>
            </div>
        `;
        
        // Add event listeners to explore further buttons
        const exploreButtons = this.container.querySelectorAll('.explore-further-btn');
        console.log(`[DEBUG ResearchCard] Found ${exploreButtons.length} explore further buttons`);
        
        exploreButtons.forEach((button, index) => {
            console.log(`[DEBUG ResearchCard] Adding click listener to button ${index + 1}`);
            
            button.addEventListener('click', (event) => {
                console.log(`[DEBUG ResearchCard] Explore further button clicked:`, event.target);
                
                try {
                    const topicData = JSON.parse(event.target.dataset.topic);
                    console.log(`[DEBUG ResearchCard] Button has topic data:`, topicData);
                    this._emit('researchRequested', topicData);
                } catch (error) {
                    console.error(`[DEBUG ResearchCard] Error parsing topic data:`, error);
                    console.error(`[DEBUG ResearchCard] Raw topic data:`, event.target.dataset.topic);
                }
            });
        });
        
        console.log(`[DEBUG ResearchCard] Content update complete`);
    }
    
    _renderResearchContent(results) {
        console.log(`[DEBUG ResearchCard] Rendering research content sections`);
        
        // Log what sections are available in the data
        console.log(`[DEBUG ResearchCard] Available sections:`, 
            Object.keys(results).filter(key => 
                Array.isArray(results[key]) ? results[key].length > 0 : results[key]));
        
        return `
            ${results.summary ? `
                <div class="summary-section mb-4">
                    <h4>Summary</h4>
                    <p>${results.summary}</p>
                </div>
            ` : ''}
            
            ${results.key_points?.length ? `
                <div class="key-points-section mb-4">
                    <h4>Key Points</h4>
                    <ul class="list-group">
                        ${results.key_points.map(point => `
                            <li class="list-group-item">${point}</li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${results.entities?.length ? `
                <div class="entities-section mb-4">
                    <h4>Key Entities</h4>
                    <div class="row">
                        ${results.entities.map(entity => `
                            <div class="col-md-6 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h5 class="card-title">${entity.name}</h5>
                                        <h6 class="card-subtitle mb-2 text-muted">${entity.type}</h6>
                                        <p class="card-text">${entity.description}</p>
                                        <small class="text-muted">Relevance: ${entity.relevance}</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${results.subtopics?.length ? `
                <div class="subtopics-section mb-4">
                    <h4>Subtopics</h4>
                    <div class="row">
                        ${results.subtopics.map(subtopic => `
                            <div class="col-md-6 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h5 class="card-title">${subtopic.title}</h5>
                                        <p class="card-text">${subtopic.summary}</p>
                                        <small class="text-muted">Importance: ${subtopic.importance}</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${results.timeline?.length ? `
                <div class="timeline-section mb-4">
                    <h4>Timeline</h4>
                    <div class="timeline">
                        ${results.timeline.map(event => `
                            <div class="timeline-item">
                                <div class="timeline-date">${event.date}</div>
                                <div class="timeline-content">
                                    <h5>${event.event}</h5>
                                    <p>${event.significance}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${results.further_research?.length ? `
                <div class="further-research-section mb-4">
                    <h4>Further Research</h4>
                    <div class="list-group">
                        ${results.further_research.map((item, index) => {
                            console.log(`[DEBUG ResearchCard] Rendering further research item ${index}:`, item);
                            return `
                                <div class="list-group-item">
                                    <h5>${item.topic}</h5>
                                    <p>${item.reason || item.rationale}</p>
                                    <button class="btn btn-primary explore-further-btn" 
                                            data-topic='${JSON.stringify({topic: item.topic})}'>
                                        Explore Further
                                    </button>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${results.references?.length ? `
                <div class="references-section mb-4">
                    <h4>References</h4>
                    <ul class="list-group">
                        ${results.references.map(ref => `
                            <li class="list-group-item">
                                <h5>${ref.title}</h5>
                                <p>${ref.source || ''}</p>
                                ${ref.url ? `<a href="${ref.url}" target="_blank">View Source</a>` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${results.web_results?.length ? `
                <div class="web-results-section">
                    <h4>Web Results</h4>
                    <div class="list-group">
                        ${results.web_results.map(result => `
                            <a href="${result.link || result.url}" target="_blank" class="list-group-item list-group-item-action">
                                <h5>${result.title}</h5>
                                <p>${result.snippet || ''}</p>
                                <small class="text-muted">Source: ${result.source || 'Web'}</small>
                            </a>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
    }
    
    showLoading() {
        console.log(`[DEBUG ResearchCard] Showing loading state`);
        this.container.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <div class="d-flex justify-content-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                    <p class="text-center mt-3">Loading research data...</p>
                </div>
            </div>
        `;
    }
    
    showError(message) {
        console.error(`[DEBUG ResearchCard] Showing error: ${message}`);
        this.container.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <div class="alert alert-danger">
                        ${message}
                    </div>
                </div>
            </div>
        `;
    }
}

console.log('[DEBUG] ResearchCard class defined');

// Export for use in other modules
window.ResearchCard = ResearchCard; 