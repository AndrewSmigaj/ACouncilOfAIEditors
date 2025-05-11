/**
 * Research Container
 * Manages the overall research state and coordinates between tree and card views
 */

class ResearchContainer {
    constructor(containerId, guideId) {
        this.containerId = containerId;
        this.guideId = guideId;
        this.currentNode = null;
        this.researchHistory = new Map();
        this.tree = null;
        this.card = null;
        
        // Initialize container
        this._initializeContainer();
    }
    
    async initialize() {
        try {
            // Create and initialize tree
            this.tree = new ResearchTree(`${this.containerId}-tree`);
            
            // Create and initialize card
            this.card = new ResearchCard(`${this.containerId}-card`);
            
            // Set up event listeners
            this._setupEventListeners();
            
            // Load initial research data
            await this._loadInitialResearch();
            
        } catch (error) {
            console.error('Failed to initialize research container:', error);
            this._showError('Failed to initialize research interface. Please try refreshing the page.');
        }
    }
    
    _initializeContainer() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            throw new Error(`Container element #${this.containerId} not found`);
        }
        
        // Create tree container
        const treeContainer = document.createElement('div');
        treeContainer.id = `${this.containerId}-tree`;
        treeContainer.className = 'research-tree-container mb-4';
        container.appendChild(treeContainer);
        
        // Create card container
        const cardContainer = document.createElement('div');
        cardContainer.id = `${this.containerId}-card`;
        cardContainer.className = 'research-card-container';
        container.appendChild(cardContainer);
    }
    
    _setupEventListeners() {
        // Tree events
        this.tree.on('nodeSelected', (nodeId) => this._handleNodeSelection(nodeId));
        this.tree.on('researchRequested', (nodeData) => this._handleResearchRequest(nodeData));
        
        // Card events
        this.card.on('researchRequested', (topic) => this._handleResearchRequest(topic));
        this.card.on('navigationRequested', (nodeId) => this._handleNavigationRequest(nodeId));
    }
    
    async _loadInitialResearch() {
        try {
            const response = await fetch(`/api/research/results/${this.guideId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            
            // Initialize tree first
            await this.tree.initialize(this.guideId);
            
            // Create initial node data
            const nodeData = {
                id: this.guideId,
                topic: data.research?.topic || 'Loading...',
                status: data.research?.status || 'initializing',
                children: data.research?.children || [],
                research_results: data.research?.research_results || {}
            };
            
            // Update tree with initial data
            this.tree.updateData(nodeData);
            
            // Show loading state in card
            this.card.updateContent({
                status: nodeData.status,
                topic: nodeData.topic,
                research_results: nodeData.research_results
            });
            
            // Start polling for updates if research is in progress
            if (nodeData.status === 'initializing' || nodeData.status === 'in_progress') {
                this._startPollingForUpdates();
            } else if (nodeData.status === 'completed') {
                // If research is already complete, show the results
                this._handleNodeSelection(this.guideId);
            }
            
        } catch (error) {
            console.error('Failed to load initial research:', error);
            this._showError('Failed to load research data. Please try refreshing the page.');
        }
    }
    
    async _startPollingForUpdates() {
        const pollInterval = 5000; // 5 seconds between polls
        const maxAttempts = 60; // 5 minutes total (60 attempts * 5 seconds)
        
        let attempts = 0;
        const poll = async () => {
            try {
                const response = await fetch(`/api/research/results/${this.guideId}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                if (data.status === 'error') {
                    throw new Error(data.message);
                }
                
                // Update tree with latest data
                const nodeData = {
                    id: this.guideId,
                    topic: data.research?.topic || 'Loading...',
                    status: data.research?.status || 'initializing',
                    children: data.research?.children || [],
                    research_results: data.research?.research_results || {}
                };
                
                this.tree.updateData(nodeData);
                
                if (data.research?.status === 'completed') {
                    console.log('Research completed, updating UI');
                    this._handleNodeSelection(this.guideId);
                    return;
                } else if (data.research?.status === 'error') {
                    console.error('Research failed:', data.research.error_message);
                    this._showError(data.research.error_message || 'Research failed. Please try again.');
                    return;
                }
                
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(poll, pollInterval);
                } else {
                    this._showError('Research is taking longer than expected. Please refresh the page or try again later.');
                }
            } catch (error) {
                console.error('Polling error:', error);
                this._showError('Error checking research status. Please refresh the page.');
            }
        };
        
        poll();
    }
    
    async _handleNodeSelection(nodeId) {
        try {
            // Get node data from tree
            const nodeData = this.tree.getNodeData(nodeId);
            if (!nodeData) {
                console.warn(`Node ${nodeId} not found in tree data`);
                return;
            }
            
            // Update current node
            this.currentNode = nodeId;
            
            // Get research data
            let researchData;
            if (this.researchHistory.has(nodeId)) {
                researchData = this.researchHistory.get(nodeId);
            } else {
                const response = await fetch(`/api/research/results/${nodeId}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                if (data.status === 'error') {
                    throw new Error(data.message);
                }
                
                researchData = data.research;
                this.researchHistory.set(nodeId, researchData);
            }
            
            // Update card with research data
            this.card.updateContent(researchData);
            
            // Update tree selection
            this.tree.setSelectedNode(nodeId);
            
        } catch (error) {
            console.error('Failed to handle node selection:', error);
            this._showError('Failed to load research data for selected topic.');
        }
    }
    
    async _handleResearchRequest(topic) {
        try {
            // Start research
            const response = await fetch(`/api/research/${this.guideId}/subtopics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    topic: topic.topic,
                    ai: topic.ai || 'grok', // Default to grok if AI not specified
                    parent_node_id: this.currentNode
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            
            // Update tree with new node
            this.tree.addNode(topic);
            
            // Wait for research results
            await this._waitForResults(topic.id);
            
        } catch (error) {
            console.error('Failed to handle research request:', error);
            this._showError('Failed to start research. Please try again.');
        }
    }
    
    async _waitForResults(nodeId) {
        try {
            const response = await fetch(`/api/research/results/${nodeId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            
            // Update research history
            this.researchHistory.set(nodeId, data.research);
            
            // Update tree node status
            this.tree.updateNodeStatus(nodeId, 'completed');
            
            // If this is the current node, update card
            if (this.currentNode === nodeId) {
                this.card.updateContent(data.research);
            }
            
        } catch (error) {
            console.error('Failed to wait for results:', error);
            this._showError('Failed to get research results. Please try again.');
        }
    }
    
    _handleNavigationRequest(nodeId) {
        this._handleNodeSelection(nodeId);
    }
    
    _showError(message) {
        const container = document.getElementById(this.containerId);
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger mt-3';
        errorAlert.textContent = message;
        container.appendChild(errorAlert);
        
        // Remove error after 5 seconds
        setTimeout(() => {
            errorAlert.remove();
        }, 5000);
    }
}

// Export for use in other modules
window.ResearchContainer = ResearchContainer; 