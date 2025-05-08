/**
 * Subtopic Research Module
 * Handles the interactive selection and research of subtopics
 */

/**
 * Creates and displays the interactive subtopic selection UI
 * @param {string} guideId - The guide ID
 */
function createSubtopicSelectionUI(guideId) {
    // First, clear any existing subtopic container to ensure we start fresh
    const existingContainer = document.getElementById('subtopic-research-container');
    if (existingContainer) {
        existingContainer.remove();
    }

    // Create a loading container
    const loadingContainer = document.createElement('div');
    loadingContainer.id = 'subtopic-research-container';
    loadingContainer.className = 'card mt-4 mb-4';
    loadingContainer.innerHTML = `
        <div class="card-header">
            <h3>Explore Subtopics</h3>
        </div>
        <div class="card-body">
            <div class="alert alert-info">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                Loading research topics...
            </div>
        </div>
    `;

    // Find a good place to insert this in the document
    const resultContainer = document.getElementById('result-container');
    if (resultContainer) {
        resultContainer.appendChild(loadingContainer);
    } else {
        document.body.appendChild(loadingContainer);
    }
    
    // Initialize subtopic research directly
    initializeSubtopicResearch(guideId)
        .catch(error => {
            console.error("Error initializing subtopic research:", error);
            loadingContainer.innerHTML = `
                <div class="card-header">
                    <h3>Explore Subtopics</h3>
                </div>
                <div class="card-body">
                    <div class="alert alert-danger">
                        Error loading research topics. Please try refreshing the page.
                    </div>
                </div>
            `;
        });
}

/**
 * Initializes the subtopic research UI
 * @param {string} guideId - The guide ID
 */
async function initializeSubtopicResearch(guideId) {
    try {
        // Get research results
        const response = await fetch(`/api/research/results/${guideId}`);
        const data = await response.json();
        
        if (data.status === 'error') {
            console.error("Error fetching research results:", data.message);
            renderSubtopicSelector(guideId, [], [], false);
            return;
        }
        
        if (!data.research?.research_results) {
            console.log("No research results available");
            renderSubtopicSelector(guideId, [], [], false);
            return;
        }
        
        const researchData = data.research.research_results;
        const furtherTopics = researchData.further_research || [];
        const subtopicResults = data.research.children || [];
        
        // Create the subtopic selector UI
        renderSubtopicSelector(guideId, furtherTopics, subtopicResults, false);
        
    } catch (error) {
        console.error("Error in subtopic research initialization:", error);
        // If we can't initialize, render empty state
        renderSubtopicSelector(guideId, [], [], false);
    }
}

/**
 * Initializes a research document in the research collection if it doesn't exist
 * @param {string} guideId - The guide ID
 * @param {Array} furtherTopics - Topics for further research
 * @returns {Promise} - Promise that resolves when initialization is complete
 */
function initializeResearchDocument(guideId, furtherTopics) {
    return new Promise((resolve, reject) => {
        // Try to fetch the research document first
        fetch(`/api/research/results/${guideId}`)
            .then(res => {
                if (res.status === 404) {
                    // If 404, it doesn't exist yet, so we need to initialize it
                    console.log("Research document doesn't exist, initializing...");
                    return fetch(`/api/research/initialize/${guideId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ 
                            further_research_topics: furtherTopics 
                        })
                    });
                }
                // If it exists, we're good
                return new Response(JSON.stringify({ message: "Research document already exists" }), {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' }
                });
            })
            .then(res => res.json())
            .then(data => {
                console.log("Research initialization result:", data);
                resolve();
            })
            .catch(error => {
                console.error("Error in research initialization:", error);
                // Even if initialization fails, we'll try to continue
                resolve();
            });
    });
}

/**
 * Renders the subtopic selector UI with individual Explore Further buttons
 * @param {string} guideId - The guide ID
 * @param {Array} availableTopics - Topics available for research
 * @param {Array} completedSubtopics - Already researched subtopics
 * @param {boolean} inProgress - Whether research is in progress
 */
function renderSubtopicSelector(guideId, availableTopics, completedSubtopics, inProgress) {
    // Always create a new container to ensure we're starting fresh
    const container = document.createElement('div');
    container.id = 'subtopic-research-container';
    container.className = 'card mt-4 mb-4';
    
    // Find a good place to insert this in the document
    const resultContainer = document.getElementById('result-container');
    if (resultContainer) {
        // First, remove any existing container with the same ID
        const existingContainer = document.getElementById('subtopic-research-container');
        if (existingContainer) {
            existingContainer.remove();
        }
        resultContainer.appendChild(container);
    } else {
        document.body.appendChild(container);
    }
    
    // Create header and introductory content
    container.innerHTML = `
        <div class="card-header">
            <h3>Explore Research Topics</h3>
        </div>
        <div class="card-body">
            <div id="subtopic-selection-area" class="mb-3">
                ${availableTopics.length === 0 ? '<p>No more research topics available.</p>' : ''}
                ${availableTopics.map(topic => `
                    <div class="card mb-3">
                        <div class="card-body">
                            <h5 class="card-title">${topic.topic}</h5>
                            <p class="card-text">${topic.rationale}</p>
                            <button 
                                class="btn btn-primary explore-topic-btn" 
                                data-topic='${JSON.stringify(topic)}'
                                ${inProgress ? 'disabled' : ''}>
                                Explore Further
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            ${inProgress ? `
                <div class="alert alert-info mt-3">
                    <div class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    Research in progress...
                </div>
                <div class="progress mt-2">
                    <div id="subtopic-progress-bar" class="progress-bar" style="width: 0%"></div>
                </div>
                <div id="subtopic-progress-text" class="text-center">Initializing...</div>
            ` : ''}
        </div>
    `;
    
    // Add click handlers for Explore Further buttons
    container.querySelectorAll('.explore-topic-btn').forEach(button => {
        button.addEventListener('click', async (event) => {
            const topic = JSON.parse(event.target.dataset.topic);
            event.target.disabled = true;
            event.target.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Researching...
            `;
            
            try {
                await triggerSubtopicResearch(guideId, [topic]);
                // Refresh the UI after research is complete
                await initializeSubtopicResearch(guideId);
            } catch (error) {
                console.error('Error researching topic:', error);
                event.target.disabled = false;
                event.target.innerHTML = 'Explore Further';
                // Show error message
                const errorAlert = document.createElement('div');
                errorAlert.className = 'alert alert-danger mt-3';
                errorAlert.textContent = 'Failed to research topic. Please try again.';
                event.target.parentElement.appendChild(errorAlert);
            }
        });
    });
}

/**
 * Triggers research on selected topics
 * @param {string} guideId - The guide ID
 * @param {Array} selectedTopics - Array of selected topics
 */
async function triggerSubtopicResearch(guideId, selectedTopics) {
    const researchBtn = document.getElementById('research-selected-subtopics');
    if (researchBtn) {
        researchBtn.disabled = true;
        researchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    }
    
    try {
        // Process each topic individually
        for (const topicData of selectedTopics) {
            // Make POST request to trigger research for this topic
            const response = await fetch(`/api/research/${guideId}/subtopics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    topic: topicData.topic  // Send just the topic string
                })
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Check for API errors
            if (data.error) {
                throw new Error(data.error);
            }
            
            console.log("Research triggered for topic:", topicData.topic, data);
        }
        
        // Refresh the subtopic selector UI with new results
        await initializeSubtopicResearch(guideId);
        
    } catch (error) {
        console.error("Error triggering research:", error);
        
        // Show error alert
        alert(`Error starting research: ${error.message}`);
        
        // Re-enable research button
        if (researchBtn) {
            researchBtn.disabled = false;
            researchBtn.innerHTML = 'Research Selected Topics';
        }
    }
}

/**
 * Initializes research for a specific topic
 * @param {string} topicId - The topic ID
 * @param {string} topic - The topic text
 */
function initializeTopicResearch(topicId, topic) {
    // First, initialize the research document for this topic
    fetch(`/api/research/results/${topicId}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById(`topic-research-${topicId}`);
            if (container) {
                // Get the research data
                const researchData = data.research?.research_results || {};
                
                // Create the research content
                let content = `
                    <div class="card">
                        <div class="card-header">
                            <h4>Researching: ${topic}</h4>
                        </div>
                        <div class="card-body">
                            <div class="research-content">
                                ${researchData.summary ? `
                                    <div class="summary-section mb-4">
                                        <h5>Summary</h5>
                                        <p>${researchData.summary}</p>
                                    </div>
                                ` : ''}
                                
                                ${researchData.key_points?.length ? `
                                    <div class="key-points-section mb-4">
                                        <h5>Key Points</h5>
                                        <ul>
                                            ${researchData.key_points.map(point => `<li>${point}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                                
                                ${researchData.entities?.length ? `
                                    <div class="entities-section mb-4">
                                        <h5>Key Entities</h5>
                                        <div class="row">
                                            ${researchData.entities.map(entity => `
                                                <div class="col-md-6 mb-3">
                                                    <div class="card">
                                                        <div class="card-body">
                                                            <h6>${entity.name}</h6>
                                                            <p class="text-muted">${entity.type}</p>
                                                            <p>${entity.description}</p>
                                                            <small>Relevance: ${entity.relevance}</small>
                                                        </div>
                                                    </div>
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${researchData.timeline?.length ? `
                                    <div class="timeline-section mb-4">
                                        <h5>Timeline</h5>
                                        <div class="timeline">
                                            ${researchData.timeline.map(event => `
                                                <div class="timeline-item">
                                                    <div class="timeline-date">${event.date}</div>
                                                    <div class="timeline-content">
                                                        <h6>${event.event}</h6>
                                                        <p>${event.significance}</p>
                                                    </div>
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${researchData.further_research?.length ? `
                                    <div class="further-research-section mb-4">
                                        <h5>Further Research Topics</h5>
                                        <div class="row">
                                            ${researchData.further_research.map(topic => `
                                                <div class="col-md-6 mb-3">
                                                    <div class="card">
                                                        <div class="card-body">
                                                            <h6>${topic.topic}</h6>
                                                            <p>${topic.rationale}</p>
                                                            <button class="btn btn-primary explore-further-btn" 
                                                                    data-topic-id="${topicId}" 
                                                                    data-topic="${encodeURIComponent(topic.topic)}">
                                                                Explore Further
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${researchData.references?.length ? `
                                    <div class="references-section">
                                        <h5>References</h5>
                                        <ul class="list-unstyled">
                                            ${researchData.references.map(ref => `
                                                <li class="mb-2">
                                                    <strong>${ref.title}</strong>
                                                    <br>
                                                    <small>${ref.source}</small>
                                                    ${ref.url ? `<br><a href="${ref.url}" target="_blank">View Source</a>` : ''}
                                                </li>
                                            `).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
                
                // Update the container with the research content
                container.innerHTML = content;
                
                // Add event listeners to explore further buttons
                container.querySelectorAll('.explore-further-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        const newTopicId = e.target.getAttribute('data-topic-id');
                        const newTopic = decodeURIComponent(e.target.getAttribute('data-topic'));
                        if (newTopicId) {
                            // Create a new research container for this topic
                            const topicContainer = document.createElement('div');
                            topicContainer.id = `topic-research-${newTopicId}`;
                            topicContainer.className = 'topic-research-container mt-4';
                            
                            // Add a header showing the topic hierarchy
                            topicContainer.innerHTML = `
                                <div class="card">
                                    <div class="card-header">
                                        <h4>Researching: ${newTopic}</h4>
                                    </div>
                                    <div class="card-body">
                                        <div class="spinner-border" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                        <p>Loading research topics...</p>
                                    </div>
                                </div>
                            `;
                            
                            // Insert after the current topic element
                            e.target.closest('.card').after(topicContainer);
                            
                            // Initialize research for this topic
                            initializeTopicResearch(newTopicId, newTopic);
                        }
                    });
                });
            }
        })
        .catch(error => {
            console.error('Error initializing topic research:', error);
            const container = document.getElementById(`topic-research-${topicId}`);
            if (container) {
                container.innerHTML = `
                    <div class="card">
                        <div class="card-header">
                            <h4>Researching: ${topic}</h4>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-danger">
                                Error loading research data. Please try again later.
                            </div>
                        </div>
                    </div>
                `;
            }
        });
} 