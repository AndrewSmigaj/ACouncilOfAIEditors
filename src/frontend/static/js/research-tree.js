/**
 * Research Tree Visualization
 * Displays a hierarchical tree of research topics with interactive features
 */

class ResearchTree {
    constructor(containerId) {
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
    }
    
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, new Set());
        }
        this.eventHandlers.get(event).add(handler);
    }
    
    _emit(event, data) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => handler(data));
        }
    }
    
    async initialize(guideId) {
        try {
            const response = await fetch(`/api/research/results/${guideId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            
            this.researchData = data.research;
            this.treeData = this._buildTreeData(data.research);
            this._renderTree();
            
        } catch (error) {
            console.error('Failed to initialize tree:', error);
            throw error;
        }
    }
    
    updateData(data) {
        if (!data) {
            console.warn('No data provided to update tree');
            return;
        }
        
        console.log('Updating tree with data:', data);
        
        // Update research data
        this.researchData = data;
        
        // Build tree data
        this.treeData = this._buildTreeData(data);
        
        // Render tree
        this._renderTree();
        
        // If this is the selected node, update its appearance
        if (this.selectedNode === data.id) {
            this.setSelectedNode(data.id);
        }
    }
    
    _buildTreeData(data) {
        if (!data) {
            console.warn('No data provided to build tree');
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
        if (!this.treeData) {
            console.warn('No tree data to render');
            return;
        }
        
        // Clear existing tree
        this.svg.selectAll('*').remove();
        
        // Compute the new tree layout
        const root = d3.hierarchy(this.treeData);
        const treeData = this.tree(root);
        
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
            .on('click', (event, d) => this._handleNodeClick(d.data));
            
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
    }
    
    _handleNodeClick(nodeData) {
        this.setSelectedNode(nodeData.id);
        this._emit('nodeSelected', nodeData.id);
    }
    
    setSelectedNode(nodeId) {
        this.selectedNode = nodeId;
        
        // Update node appearance
        this.svg.selectAll('.node')
            .classed('selected', d => d.data.id === nodeId);
    }
    
    getNodeData(nodeId) {
        if (!this.treeData) return null;
        
        const findNode = (node) => {
            if (node.id === nodeId) return node;
            if (node.children) {
                for (const child of node.children) {
                    const found = findNode(child);
                    if (found) return found;
                }
            }
            return null;
        };
        
        return findNode(this.treeData);
    }
    
    addNode(nodeData) {
        if (!this.treeData) return;
        
        // Add node to tree data
        const newNode = {
            id: nodeData.id,
            name: nodeData.topic,
            status: 'initializing',
            children: []
        };
        
        this.treeData.children.push(newNode);
        
        // Re-render tree
        this._renderTree();
    }
    
    updateNodeStatus(nodeId, status) {
        if (!this.treeData) return;
        
        const updateNode = (node) => {
            if (node.id === nodeId) {
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
            this._renderTree();
        }
    }
}

// Export for use in other modules
window.ResearchTree = ResearchTree;

// Initialize research tree when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('research-tree');
    if (container) {
        const tree = new ResearchTree('research-tree');
        const guideId = container.dataset.guideId;
        
        // Initialize tree if we have a guide ID
        if (guideId) {
            tree.initialize(guideId);
        }
    }
}); 