/**
 * Research Tree Visualization
 * Displays a hierarchical tree of research topics with interactive features
 */

class ResearchTree {
    constructor(containerId) {
        console.log(`[DEBUG ResearchTree] Creating new ResearchTree with container ID: ${containerId}`);
        this.container = d3.select(`#${containerId}`);
        this.treeData = null;
        this.researchData = null;
        this.width = 800;
        this.height = 400;
        this.nodeRadius = 10;
        this.duration = 750;
        this.tree = d3.tree().size([this.height, this.width - 160]);
        this.selectedNode = null;
        this.eventHandlers = new Map();
        
        // Initialize the SVG
        this.svg = this.container.append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .append('g')
            .attr('transform', `translate(40,0)`);
            
        // Add zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.5, 2])
            .on('zoom', (event) => {
                this.svg.attr('transform', event.transform);
            });
            
        this.container.select('svg').call(this.zoom);
        console.log(`[DEBUG ResearchTree] Tree initialized with dimensions: ${this.width}x${this.height}`);
    }
    
    on(event, handler) {
        console.log(`[DEBUG ResearchTree] Adding handler for event: ${event}`);
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, new Set());
        }
        this.eventHandlers.get(event).add(handler);
    }
    
    _emit(event, data) {
        console.log(`[DEBUG ResearchTree] Emitting event: ${event}`, data);
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => {
                console.log(`[DEBUG ResearchTree] Calling handler for event: ${event}`);
                handler(data);
            });
        } else {
            console.warn(`[DEBUG ResearchTree] No handlers registered for event: ${event}`);
        }
    }
    
    async initialize(guideId) {
        console.log(`[DEBUG ResearchTree] Initializing tree for guide ID: ${guideId}`);
        try {
            const response = await fetch(`/api/research/results/${guideId}`);
            console.log(`[DEBUG ResearchTree] API response status: ${response.status}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log(`[DEBUG ResearchTree] Parsed JSON data:`, data);
            
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            
            this.researchData = data.research;
            this.treeData = this._buildTreeData(data.research);
            console.log(`[DEBUG ResearchTree] Built tree data:`, this.treeData);
            
            this._renderTree();
            console.log(`[DEBUG ResearchTree] Tree rendered successfully`);
            
        } catch (error) {
            console.error('[DEBUG ResearchTree] Failed to initialize tree:', error);
            throw error;
        }
    }
    
    /**
     * Initialize the tree with the provided data without HTTP calls
     * @param {Object} nodeData - The node data for the tree
     */
    initializeWithData(nodeData) {
        console.log(`[DEBUG ResearchTree] Initializing with provided data:`, nodeData);
        
        if (!nodeData) {
            console.warn('[DEBUG ResearchTree] No data provided to initialize tree');
            return;
        }
        
        // Convert node data to tree data format
        this.treeData = this._buildTreeDataFromNode(nodeData);
        console.log(`[DEBUG ResearchTree] Built tree data from node:`, this.treeData);
        
        // Render tree
        this._renderTree();
        console.log(`[DEBUG ResearchTree] Tree rendered with provided data`);
    }
    
    /**
     * Build tree data from a node object in the new format
     * @param {Object} node - The node object with node_id, topic, status, children, etc.
     */
    _buildTreeDataFromNode(node) {
        console.log(`[DEBUG ResearchTree] Building tree data from node:`, node);
        
        if (!node) {
            console.warn('[DEBUG ResearchTree] No node provided to build tree');
            return null;
        }
        
        // Create root node
        const root = {
            id: node.node_id,
            name: node.topic,
            status: node.status,
            topic: node.topic,
            node_id: node.node_id,
            research: node.research,
            children: []
        };
        
        // Add children if available
        if (node.children && node.children.length > 0) {
            console.log(`[DEBUG ResearchTree] Processing ${node.children.length} children nodes`);
            root.children = node.children.map(child => 
                this._buildTreeDataFromNode(child)
            );
        }
        
        return root;
    }
    
    updateData(data) {
        console.log(`[DEBUG ResearchTree] Updating tree with data:`, data);
        
        if (!data) {
            console.warn('[DEBUG ResearchTree] No data provided to update tree');
            return;
        }
        
        // Update research data
        this.researchData = data;
        
        // Build tree data
        this.treeData = this._buildTreeData(data);
        console.log(`[DEBUG ResearchTree] Built updated tree data:`, this.treeData);
        
        // Render tree
        this._renderTree();
        
        // If this is the selected node, update its appearance
        if (this.selectedNode === data.id) {
            console.log(`[DEBUG ResearchTree] Updating selected node: ${data.id}`);
            this.setSelectedNode(data.id);
        }
    }
    
    _buildTreeData(data) {
        console.log(`[DEBUG ResearchTree] Building tree data:`, data);
        
        if (!data) {
            console.warn('[DEBUG ResearchTree] No data provided to build tree');
            return null;
        }
        
        // Create root node
        const root = {
            id: data.id,
            name: data.topic,
            status: data.status,
            children: []
        };
        
        // Add children if available
        if (data.children && data.children.length > 0) {
            console.log(`[DEBUG ResearchTree] Processing ${data.children.length} children`);
            root.children = data.children.map(child => ({
                id: child._id || child.id,
                name: child.topic,
                status: child.status,
                children: []
            }));
        }
        
        return root;
    }
    
    _renderTree() {
        console.log(`[DEBUG ResearchTree] Rendering tree with data:`, this.treeData);
        
        if (!this.treeData) {
            console.warn('[DEBUG ResearchTree] No tree data to render');
            return;
        }
        
        // Clear existing tree
        this.svg.selectAll('*').remove();
        
        // Compute the new tree layout
        const root = d3.hierarchy(this.treeData);
        const treeData = this.tree(root);
        console.log(`[DEBUG ResearchTree] Computed tree layout with ${treeData.descendants().length} nodes`);
        
        // Add links
        const link = this.svg.selectAll('.link')
            .data(treeData.links())
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', d3.linkVertical()
                .x(d => d.x)
                .y(d => d.y));
                
        // Add nodes
        const node = this.svg.selectAll('.node')
            .data(treeData.descendants())
            .enter()
            .append('g')
            .attr('class', d => `node ${d.data.status}`)
            .attr('transform', d => `translate(${d.x},${d.y})`)
            .on('click', (event, d) => {
                console.log(`[DEBUG ResearchTree] Node clicked:`, d.data);
                this._handleNodeClick(d.data);
            });
            
        // Add circles to nodes
        node.append('circle')
            .attr('r', this.nodeRadius)
            .attr('class', d => `node-circle ${d.data.status}`);
            
        // Add labels to nodes
        node.append('text')
            .attr('dy', '.35em')
            .attr('x', d => d.children ? -13 : 13)
            .attr('text-anchor', d => d.children ? 'end' : 'start')
            .text(d => d.data.name)
            .attr('class', 'node-label');
            
        // Add status indicators
        node.append('text')
            .attr('dy', '1.5em')
            .attr('x', 0)
            .attr('text-anchor', 'middle')
            .text(d => d.data.status)
            .attr('class', 'status-label');
            
        console.log(`[DEBUG ResearchTree] Tree rendering complete`);
    }
    
    _handleNodeClick(nodeData) {
        console.log(`[DEBUG ResearchTree] Handling node click for:`, nodeData);
        this.setSelectedNode(nodeData.id);
        this._emit('nodeSelected', nodeData);
    }
    
    setSelectedNode(nodeId) {
        console.log(`[DEBUG ResearchTree] Setting selected node: ${nodeId}`);
        this.selectedNode = nodeId;
        
        // Update node appearance
        this.svg.selectAll('.node')
            .classed('selected', d => {
                const isSelected = d.data.id === nodeId;
                if (isSelected) {
                    console.log(`[DEBUG ResearchTree] Found and marked selected node: ${nodeId}`);
                }
                return isSelected;
            });
    }
    
    getNodeData(nodeId) {
        console.log(`[DEBUG ResearchTree] Getting node data for: ${nodeId}`);
        
        if (!this.treeData) {
            console.warn(`[DEBUG ResearchTree] No tree data available`);
            return null;
        }
        
        const findNode = (node) => {
            if (node.id === nodeId) {
                console.log(`[DEBUG ResearchTree] Found node with ID: ${nodeId}`, node);
                return node;
            }
            if (node.children) {
                for (const child of node.children) {
                    const found = findNode(child);
                    if (found) return found;
                }
            }
            return null;
        };
        
        const result = findNode(this.treeData);
        if (!result) {
            console.warn(`[DEBUG ResearchTree] Node with ID ${nodeId} not found in tree data`);
        }
        return result;
    }
    
    addNode(nodeData) {
        console.log(`[DEBUG ResearchTree] Adding new node:`, nodeData);
        
        if (!this.treeData) {
            console.warn(`[DEBUG ResearchTree] Cannot add node - tree data is not initialized`);
            return;
        }
        
        // Convert the node data to tree data format
        const newNode = this._buildTreeDataFromNode(nodeData);
        console.log(`[DEBUG ResearchTree] Converted node data to tree format:`, newNode);
        
        // Add node to tree data
        if (!this.treeData.children) {
            console.log(`[DEBUG ResearchTree] Creating children array for root node`);
            this.treeData.children = [];
        }
        this.treeData.children.push(newNode);
        console.log(`[DEBUG ResearchTree] Added node to tree data. New child count: ${this.treeData.children.length}`);
        
        // Re-render tree
        this._renderTree();
    }
    
    updateNodeStatus(nodeId, status) {
        console.log(`[DEBUG ResearchTree] Updating node ${nodeId} status to ${status}`);
        
        if (!this.treeData) {
            console.warn(`[DEBUG ResearchTree] Cannot update node - tree data is not initialized`);
            return;
        }
        
        const updateNode = (node) => {
            if (node.id === nodeId) {
                console.log(`[DEBUG ResearchTree] Found node ${nodeId}, updating status from ${node.status} to ${status}`);
                node.status = status;
                return true;
            }
            if (node.children) {
                for (const child of node.children) {
                    if (updateNode(child)) return true;
                }
            }
            return false;
        };
        
        if (updateNode(this.treeData)) {
            console.log(`[DEBUG ResearchTree] Node status updated, re-rendering tree`);
            this._renderTree();
        } else {
            console.warn(`[DEBUG ResearchTree] Node ${nodeId} not found for status update`);
        }
    }
}

console.log('[DEBUG] ResearchTree class defined');

// Export for use in other modules
window.ResearchTree = ResearchTree;

// Initialize research tree when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('[DEBUG ResearchTree] DOM Content Loaded, checking for research-tree container');
    const container = document.getElementById('research-tree');
    if (container) {
        console.log('[DEBUG ResearchTree] Found research-tree container');
        const tree = new ResearchTree('research-tree');
        const guideId = container.dataset.guideId;
        
        // Initialize tree if we have a guide ID
        if (guideId) {
            console.log(`[DEBUG ResearchTree] Initializing tree with guide ID: ${guideId}`);
            tree.initialize(guideId);
        } else {
            console.warn('[DEBUG ResearchTree] No guide ID found in container, tree not initialized');
        }
    } else {
        console.log('[DEBUG ResearchTree] No research-tree container found on page');
    }
}); 