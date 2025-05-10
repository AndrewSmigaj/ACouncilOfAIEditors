/**
 * Research Card Component
 * Displays research content and handles research requests
 */

class ResearchCard {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.eventHandlers = new Map();
        
        if (!this.container) {
            throw new Error(`Container element #${containerId} not found`);
        }
    }
    
    // Event handling
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, new Set());
        }
        this.eventHandlers.get(event).add(handler);
    }
    
    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).delete(handler);
        }
    }
    
    _emit(event, data) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => handler(data));
        }
    }
    
    updateContent(researchData) {
        if (!researchData) {
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
        this.container.querySelectorAll('.explore-further-btn').forEach(button => {
            button.addEventListener('click', (event) => {
                const topic = JSON.parse(event.target.dataset.topic);
                this._emit('researchRequested', topic);
            });
        });
    }
    
    _renderResearchContent(results) {
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
                        ${results.further_research.map(item => `
                            <div class="list-group-item">
                                <h5>${item.topic}</h5>
                                <p>${item.reason || item.rationale}</p>
                                <button class="btn btn-primary explore-further-btn" 
                                        data-topic='${JSON.stringify({topic: item.topic})}'>
                                    Explore Further
                                </button>
                            </div>
                        `).join('')}
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

// Export for use in other modules
window.ResearchCard = ResearchCard; 