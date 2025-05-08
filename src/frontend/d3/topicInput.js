/**
 * D3.js module for creating the topic input form
 * Task 1.1: Create a topic input form with D3.js
 */

/**
 * Creates a topic input form with a text input and submit button
 * @param {string} containerId - The ID of the container element
 * @param {string} apiEndpoint - The API endpoint for form submission
 */
function createTopicForm(containerId, apiEndpoint) {
    // Select the container element
    const container = d3.select(`#${containerId}`);
    
    // Create form element
    const form = container.append('form')
        .attr('class', 'topic-form')
        .attr('aria-label', 'Topic input form');
    
    // Create form header
    form.append('h2')
        .text('Enter Your Guide Topic');
    
    // Create form description
    form.append('p')
        .attr('class', 'form-description')
        .text('Provide a specific topic for your guide (at least 3 words)');
    
    // Create topic input field
    const inputGroup = form.append('div')
        .attr('class', 'input-group');
    
    inputGroup.append('label')
        .attr('for', 'topic-input')
        .attr('class', 'input-label')
        .text('Guide Topic:');
    
    inputGroup.append('input')
        .attr('type', 'text')
        .attr('id', 'topic-input')
        .attr('name', 'topic')
        .attr('class', 'topic-input')
        .attr('placeholder', 'e.g., How to start a podcast')
        .attr('aria-required', 'true')
        .attr('required', true);
    
    // Create submit button
    const buttonGroup = form.append('div')
        .attr('class', 'button-group');
    
    buttonGroup.append('button')
        .attr('type', 'submit')
        .attr('class', 'submit-button')
        .text('Start Guide Creation');
    
    // Create error message container
    const errorContainer = form.append('div')
        .attr('class', 'error-container')
        .attr('aria-live', 'polite')
        .style('display', 'none');
    
    // Create examples container
    const examplesContainer = form.append('div')
        .attr('class', 'examples-container');
    
    examplesContainer.append('h3')
        .text('Example Topics:');
    
    const examplesList = examplesContainer.append('ul')
        .attr('class', 'examples-list');
    
    // Add example topics
    const examples = [
        'How to start a podcast',
        'Building a sustainable garden',
        'Advanced techniques for digital photography',
        'Creating a personal financial plan'
    ];
    
    examples.forEach(example => {
        examplesList.append('li')
            .append('a')
            .attr('href', '#')
            .attr('class', 'example-link')
            .text(example)
            .on('click', function(event) {
                event.preventDefault();
                d3.select('#topic-input').property('value', example);
            });
    });
    
    // Add form submission handler
    form.on('submit', function(event) {
        event.preventDefault();
        
        // Get input value
        const topic = d3.select('#topic-input').property('value').trim();
        
        // Validate input (will be expanded in Task 1.2)
        if (!topic || topic.split(' ').length < 3) {
            errorContainer
                .style('display', 'block')
                .text('Topic too vague. Please provide at least 3 words.');
            return;
        }
        
        // Clear any previous errors
        errorContainer.style('display', 'none');
        
        // Submit form via API
        console.log(`Submitting topic: ${topic} to API endpoint: ${apiEndpoint}`);
        
        // Show loading indicator
        buttonGroup.select('button')
            .text('Processing...')
            .attr('disabled', true);
        
        try {
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ topic })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            
            // Display success message
            container.select('.topic-form').style('display', 'none');
            
            container.append('div')
                .attr('class', 'success-message')
                .html(`
                    <h2>Topic Submitted Successfully!</h2>
                    <p>Your guide on "<strong>${topic}</strong>" is being researched.</p>
                    <p>You will be redirected to the research approval page shortly.</p>
                `);
                
            // Redirect to research page with guide ID
            window.location.href = `/research?guide_id=${data.guide_id}`;
            
        } catch (error) {
            console.error('Failed to submit topic:', error);
            displayFeedback(containerId, {
                valid: false,
                error: `Failed to submit topic: ${error.message}`
            });
        } finally {
            // Restore button state
            buttonGroup.select('button')
                .text('Start Guide Creation')
                .attr('disabled', null);
        }
    });
    
    return form;
}

/**
 * Validates topic input
 * Task 1.2: Implement input validation logic
 * @param {string} topic - The topic input to validate
 * @returns {Object} - Validation result { valid: boolean, error: string }
 */
function validateInput(topic) {
    // Check if topic is empty
    if (!topic || topic.trim() === '') {
        return { 
            valid: false, 
            error: 'Topic cannot be empty' 
        };
    }
    
    // Check if topic is too vague (less than 3 words)
    const words = topic.trim().split(/\s+/);
    if (words.length < 3) {
        return { 
            valid: false, 
            error: 'Topic too vague. Please provide at least 3 words.' 
        };
    }
    
    // Topic is valid
    return { valid: true };
}

/**
 * Displays feedback for topic input with enhanced visual guidance
 * Task 2.1: Add error feedback and examples
 * @param {string} containerId - The ID of the container element
 * @param {Object} validation - Validation result from validateInput function
 */
function displayFeedback(containerId, validation) {
    const container = d3.select(`#${containerId}`);
    const errorContainer = container.select('.error-container');
    const examplesContainer = container.select('.examples-container');
    const inputField = container.select('#topic-input');
    
    if (!validation.valid) {
        // Show enhanced error message with icon
        errorContainer
            .style('display', 'block')
            .attr('role', 'alert')
            .attr('aria-hidden', 'false')
            .html('');  // Clear previous content
        
        // Add icon and styled message
        errorContainer.append('span')
            .attr('class', 'error-icon')
            .attr('aria-hidden', 'true')
            .html('&#9888;'); // Warning icon
        
        errorContainer.append('span')
            .attr('class', 'error-message')
            .text(validation.error);
        
        // Highlight input field with error styling
        inputField
            .classed('input-error', true)
            .attr('aria-invalid', 'true');
        
        // Highlight examples container to draw attention to valid options
        examplesContainer
            .classed('highlight', true)
            .attr('aria-label', 'Suggested example topics')
            .style('opacity', '1');
        
        // Ensure the examples list has proper accessibility
        container.select('.examples-list')
            .attr('aria-labelledby', 'examples-heading');
        
        // Make sure the examples heading has an ID for ARIA labeling
        const examplesHeading = container.select('.examples-container h3');
        if (!examplesHeading.attr('id')) {
            examplesHeading.attr('id', 'examples-heading');
        }
        
        // Make example links more accessible and interactive
        container.selectAll('.example-link')
            .attr('role', 'button')
            .attr('tabindex', '0')
            .attr('aria-label', d => `Use example topic: ${d}`)
            .on('keydown', function(event) {
                // Allow activation with Enter or Space key for accessibility
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    const example = d3.select(this).text();
                    inputField.property('value', example);
                    inputField.node().focus();
                    // Clear error state since we've selected a valid example
                    displayFeedback(containerId, {valid: true});
                }
            })
            .on('click', function(event) {
                event.preventDefault();
                const example = d3.select(this).text();
                inputField.property('value', example);
                inputField.node().focus();
                // Clear error state since we've selected a valid example
                displayFeedback(containerId, {valid: true});
            });
    } else {
        // Hide error message
        errorContainer
            .style('display', 'none')
            .attr('aria-hidden', 'true');
        
        // Remove error styling from input
        inputField
            .classed('input-error', false)
            .attr('aria-invalid', 'false');
        
        // Return examples container to normal styling
        examplesContainer
            .classed('highlight', false)
            .style('opacity', '0.9');
    }
    
    // Add real-time validation to input field if not already added
    if (!inputField.property('__hasValidation')) {
        inputField.on('input', function() {
            const value = d3.select(this).property('value').trim();
            if (value.length > 0) {
                // Only validate if there's some content
                const result = validateInput(value);
                displayFeedback(containerId, result);
            }
        });
        inputField.property('__hasValidation', true);
    }
    
    // Add CSS styles for feedback components if not already present
    if (!document.getElementById('feedback-styles')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'feedback-styles';
        styleEl.textContent = `
            .error-container {
                margin: 10px 0;
                padding: 12px;
                background-color: rgba(231, 76, 60, 0.1);
                border-left: 4px solid #e74c3c;
                border-radius: 4px;
                display: flex;
                align-items: center;
            }
            
            .error-icon {
                margin-right: 10px;
                color: #e74c3c;
                font-size: 18px;
            }
            
            .error-message {
                color: #c0392b;
                font-weight: 500;
            }
            
            .input-error {
                border-color: #e74c3c !important;
                box-shadow: 0 0 0 1px #e74c3c;
            }
            
            .examples-container {
                margin-top: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 4px;
                transition: all 0.3s ease;
            }
            
            .examples-container.highlight {
                background-color: rgba(241, 196, 15, 0.1);
                border-left: 4px solid #f1c40f;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            
            .examples-container h3 {
                margin-top: 0;
                margin-bottom: 10px;
                font-size: 16px;
                color: #555;
            }
            
            .examples-list {
                list-style-type: none;
                padding: 0;
                margin: 0;
            }
            
            .examples-list li {
                margin-bottom: 5px;
            }
            
            .example-link {
                display: inline-block;
                padding: 5px 10px;
                color: #3498db;
                text-decoration: none;
                border-radius: 3px;
                transition: background-color 0.2s ease;
            }
            
            .example-link:hover, .example-link:focus {
                background-color: rgba(52, 152, 219, 0.1);
                text-decoration: none;
                outline: none;
                box-shadow: 0 0 0 2px #3498db;
            }
        `;
        document.head.appendChild(styleEl);
    }
}

// Export functions (for testing and reuse)
if (typeof module !== 'undefined') {
    module.exports = {
        createTopicForm,
        validateInput,
        displayFeedback
    };
} 