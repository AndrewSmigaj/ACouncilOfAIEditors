/**
 * Subtopic Research Module
 * Handles the interactive selection and research of subtopics
 */

/**
 * Checks if a guide is ready for subtopic research
 * @param {string} guideId - The guide ID
 * @returns {Promise<boolean>} - Promise that resolves to true if guide is ready
 */
function isGuideReadyForSubtopicResearch(guideId) {
    return new Promise((resolve, reject) => {
        fetch(`/api/research/${guideId}`)
            .then(response => response.json())
            .then(data => {
                // Guide is ready if it's in paused_research state
                const isReady = data.status === 'paused_research';
                if (!isReady) {
                    console.log(`Guide not ready for subtopic research. Current status: ${data.status}`);
                }
                resolve(isReady);
            })
            .catch(error => {
                console.error("Error checking guide status:", error);
                reject(error);
            });
    });
}

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
                Initial research in progress. Please wait...
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
    
    // Check if guide is ready for subtopic research
    isGuideReadyForSubtopicResearch(guideId)
        .then(isReady => {
            if (!isReady) {
                // If not ready, start polling for status
                const pollInterval = setInterval(() => {
                    isGuideReadyForSubtopicResearch(guideId)
                        .then(isReady => {
                            if (isReady) {
                                clearInterval(pollInterval);
                                // Remove loading container and proceed with initialization
                                loadingContainer.remove();
                                initializeSubtopicResearch(guideId);
                            }
                        })
                        .catch(error => {
                            console.error("Error polling guide status:", error);
                            clearInterval(pollInterval);
                            loadingContainer.innerHTML = `
                                <div class="card-header">
                                    <h3>Explore Subtopics</h3>
                                </div>
                                <div class="card-body">
                                    <div class="alert alert-danger">
                                        Error checking guide status. Please try refreshing the page.
                                    </div>
                                </div>
                            `;
                        });
                }, 5000); // Check every 5 seconds
            } else {
                // If ready, proceed with initialization
                loadingContainer.remove();
                initializeSubtopicResearch(guideId);
            }
        })
        .catch(error => {
            console.error("Error checking guide status:", error);
            loadingContainer.innerHTML = `
                <div class="card-header">
                    <h3>Explore Subtopics</h3>
                </div>
                <div class="card-body">
                    <div class="alert alert-danger">
                        Error checking guide status. Please try refreshing the page.
                    </div>
                </div>
            `;
        });
}

/**
 * Initializes the subtopic research UI once the guide is ready
 * @param {string} guideId - The guide ID
 */
function initializeSubtopicResearch(guideId) {
    // Check if further research topics are available
    fetch(`/api/research/structured/${guideId}`)
        .then(response => response.json())
        .then(data => {
            if (!data.structured_data?.deep_research?.further_research) {
                console.log("No further research topics available");
                return;
            }
            
            const furtherTopics = data.structured_data.deep_research.further_research;
            
            // Initialize research document if it doesn't exist
            initializeResearchDocument(guideId, furtherTopics)
                .then(() => {
                    // Get any existing subtopic research results
                    fetch(`/api/research/subtopics/${guideId}/results`)
                        .then(res => {
                            if (res.status === 404) {
                                // If research not found in the research collection, use topics from structured data
                                console.log("No subtopic research results found, using topics from structured data");
                                renderSubtopicSelector(guideId, furtherTopics, [], false);
                                return null;
                            }
                            return res.json();
                        })
                        .then(subtopicData => {
                            if (!subtopicData) return; // Handle case where we got a 404 and returned null
                            
                            const availableTopics = subtopicData.available_topics || furtherTopics;
                            const subtopicResults = subtopicData.subtopic_results || [];
                            const inProgress = subtopicData.in_progress;
                            
                            // Create the subtopic selector UI
                            renderSubtopicSelector(guideId, availableTopics, subtopicResults, inProgress);
                        })
                        .catch(error => {
                            console.error("Error fetching subtopic results:", error);
                            // Fall back to all topics from structured data
                            renderSubtopicSelector(guideId, furtherTopics, [], false);
                        });
                })
                .catch(error => {
                    console.error("Error initializing research document:", error);
                    // If we can't initialize, still try to render what we have
                    renderSubtopicSelector(guideId, furtherTopics, [], false);
                });
        })
        .catch(error => {
            console.error("Error fetching structured research:", error);
        });
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
        fetch(`/api/research/subtopics/${guideId}/results`)
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
 * Renders the subtopic selector UI with checkboxes
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
            <h3>Explore Subtopics</h3>
        </div>
        <div class="card-body">
            <p>Select specific subtopics you want to research further:</p>
            <div id="subtopic-selection-area" class="mb-3">
                ${availableTopics.length === 0 ? '<p>No more subtopics available to research.</p>' : ''}
            </div>
            
            ${availableTopics.length > 0 ? `
                <div class="subtopic-selector-controls mb-3">
                    <button id="select-all-subtopics" class="btn btn-sm btn-outline-secondary me-2">Select All</button>
                    <button id="deselect-all-subtopics" class="btn btn-sm btn-outline-secondary">Deselect All</button>
                </div>
                
                <button id="research-selected-subtopics" class="btn btn-primary" ${inProgress ? 'disabled' : ''}>
                    Research Selected Subtopics
                </button>
            ` : ''}
            
            ${inProgress ? `
                <div class="alert alert-info mt-3">
                    <div class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    Subtopic research in progress...
                </div>
                <div class="progress mt-2">
                    <div id="subtopic-progress-bar" class="progress-bar" style="width: 0%"></div>
                </div>
                <div id="subtopic-progress-text" class="text-center">Initializing...</div>
            ` : ''}
        </div>
        
        <div class="card-header mt-3">
            <h3>Completed Subtopic Research</h3>
        </div>
        <div class="card-body">
            <div id="completed-subtopics-area">
                ${completedSubtopics.length === 0 ? '<p>No subtopics have been researched yet.</p>' : ''}
            </div>
        </div>
    `;
    
    // Populate available topics with checkboxes
    const selectionArea = document.getElementById('subtopic-selection-area');
    if (selectionArea && availableTopics.length > 0) {
        availableTopics.forEach((topic, index) => {
            const topicElement = document.createElement('div');
            topicElement.className = 'form-check subtopic-option mb-2 p-2 border rounded';
            
            topicElement.innerHTML = `
                <input class="form-check-input subtopic-checkbox" type="checkbox" id="subtopic-${index}" 
                       data-topic='${JSON.stringify(topic).replace(/'/g, "&#39;")}'>
                <label class="form-check-label w-100" for="subtopic-${index}">
                    <div class="d-flex justify-content-between align-items-center">
                        <strong>${topic.topic}</strong>
                    </div>
                    <div class="subtopic-rationale text-muted mt-1">${topic.rationale}</div>
                </label>
            `;
            
            selectionArea.appendChild(topicElement);
        });
    }
    
    // Populate completed subtopics
    const completedArea = document.getElementById('completed-subtopics-area');
    if (completedArea && completedSubtopics.length > 0) {
        completedSubtopics.forEach(subtopic => {
            const subtopicElement = document.createElement('div');
            subtopicElement.className = 'completed-subtopic mb-3 p-3 border rounded';
            
            let statusBadge = '';
            if (subtopic.status === 'completed') {
                statusBadge = '<span class="badge bg-success">Completed</span>';
            } else if (subtopic.status === 'error') {
                statusBadge = '<span class="badge bg-danger">Error</span>';
            }
            
            subtopicElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h4 class="m-0">${subtopic.topic}</h4>
                    ${statusBadge}
                </div>
                <div class="subtopic-rationale text-muted mb-2">${subtopic.rationale || ''}</div>
                <div class="subtopic-summary">
                    ${subtopic.research_summary || 'No summary available'}
                </div>
                <div class="mt-2">
                    <a href="#" class="view-subtopic-link" data-guide-id="${subtopic.guide_id}">
                        View Full Research
                    </a>
                </div>
            `;
            
            completedArea.appendChild(subtopicElement);
        });
        
        // Add event listeners to view subtopic links
        document.querySelectorAll('.view-subtopic-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const subtopicGuideId = e.target.getAttribute('data-guide-id');
                if (subtopicGuideId) {
                    // Redirect to the research page for this subtopic
                    window.location.href = `/?guide_id=${subtopicGuideId}`;
                }
            });
        });
    }
    
    // Add event listeners for select/deselect all buttons
    const selectAllBtn = document.getElementById('select-all-subtopics');
    const deselectAllBtn = document.getElementById('deselect-all-subtopics');
    const researchBtn = document.getElementById('research-selected-subtopics');
    
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            document.querySelectorAll('.subtopic-checkbox').forEach(checkbox => {
                checkbox.checked = true;
            });
        });
    }
    
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', () => {
            document.querySelectorAll('.subtopic-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
        });
    }
    
    if (researchBtn) {
        researchBtn.addEventListener('click', () => {
            const selectedTopics = [];
            document.querySelectorAll('.subtopic-checkbox:checked').forEach(checkbox => {
                try {
                    const topicData = JSON.parse(checkbox.getAttribute('data-topic'));
                    selectedTopics.push(topicData);
                } catch (e) {
                    console.error("Error parsing topic data", e);
                }
            });
            
            if (selectedTopics.length === 0) {
                alert("Please select at least one subtopic to research.");
                return;
            }
            
            // Trigger research for selected subtopics
            triggerSubtopicResearch(guideId, selectedTopics);
        });
    }
    
    // If research is in progress, start polling for status
    if (inProgress) {
        pollSubtopicResearchStatus(guideId);
    }
}

/**
 * Triggers research on selected subtopics
 * @param {string} guideId - The guide ID
 * @param {Array} selectedTopics - Array of selected topics
 */
function triggerSubtopicResearch(guideId, selectedTopics) {
    // Disable the research button during research
    const researchBtn = document.getElementById('research-selected-subtopics');
    if (researchBtn) {
        researchBtn.disabled = true;
        researchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    }
    
    // Create a progress section to show research is in progress
    const progressSection = document.createElement('div');
    progressSection.id = 'subtopic-research-progress-container';
    progressSection.className = 'mt-4 p-3 border rounded';
    progressSection.innerHTML = `
        <h5>Research in Progress</h5>
        <div class="progress">
            <div id="subtopic-research-progress-bar" class="progress-bar" role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
        </div>
        <p id="subtopic-research-status" class="mt-2">Starting research on ${selectedTopics.length} topics...</p>
    `;
    
    const container = document.getElementById('subtopic-research-container');
    if (container) {
        container.appendChild(progressSection);
    }
    
    // Make POST request to trigger research
    fetch(`/api/research/subtopics/${guideId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            selected_topics: selectedTopics
        })
    })
    .then(response => {
        // Check for HTTP errors
        if (!response.ok) {
            const status = response.status;
            if (status === 404) {
                throw new Error("Research data not initialized. Try refreshing the page to ensure proper initialization.");
            }
            throw new Error(`Server returned ${status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // Check for API errors
        if (data.error) {
            throw new Error(data.error);
        }
        
        console.log("Research triggered:", data);
        
        // Start polling for progress updates
        pollSubtopicResearchStatus(guideId);
    })
    .catch(error => {
        console.error("Error triggering research:", error);
        
        // Remove progress section on error
        const progressSection = document.getElementById('subtopic-research-progress-container');
        if (progressSection) {
            progressSection.remove();
        }
        
        // Show error alert
        alert(`Error starting research: ${error.message}`);
        
        // Re-enable research button
        if (researchBtn) {
            researchBtn.disabled = false;
            researchBtn.innerHTML = 'Research Selected Subtopics';
        }
    });
}

/**
 * Polls for subtopic research status updates
 * @param {string} guideId - The guide ID
 */
function pollSubtopicResearchStatus(guideId) {
    const progressBar = document.getElementById('subtopic-research-progress-bar');
    const progressText = document.getElementById('subtopic-research-status');
    
    // Set up polling interval (check every 5 seconds)
    const pollInterval = setInterval(() => {
        fetch(`/api/research/subtopics/${guideId}/status`)
            .then(response => {
                if (response.status === 404) {
                    // If research not found in the research collection, stop polling
                    clearInterval(pollInterval);
                    if (progressText) {
                        progressText.textContent = 'No subtopic research data available yet';
                    }
                    return null;
                }
                return response.json();
            })
            .then(data => {
                if (!data) return; // Handle case where we got a 404 and returned null
                
                if (data.error) {
                    clearInterval(pollInterval);
                    if (progressText) {
                        progressText.textContent = `Error: ${data.error}`;
                    }
                    return;
                }
                
                // Update progress indicators
                const progress = data.progress || {};
                const percentage = progress.percentage || 0;
                const completedTopics = progress.completed_topics || 0;
                const totalTopics = progress.total_topics || 0;
                
                if (progressBar) {
                    progressBar.style.width = `${percentage}%`;
                }
                
                if (progressText) {
                    progressText.textContent = `${completedTopics}/${totalTopics} topics (${Math.round(percentage)}%)`;
                }
                
                // Check if research is complete
                if (data.status === 'completed' || !data.in_progress) {
                    clearInterval(pollInterval);
                    
                    if (progressText) {
                        progressText.textContent = 'Research completed!';
                    }
                    
                    // Reload the subtopic UI to show the new results
                    setTimeout(() => {
                        createSubtopicSelectionUI(guideId);
                    }, 1500);
                }
            })
            .catch(error => {
                console.error("Error polling subtopic status:", error);
            });
    }, 5000);
} 