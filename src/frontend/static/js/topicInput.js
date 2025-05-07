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
        
        // Validate input
        const validation = validateInput(topic);
        if (!validation.valid) {
            displayFeedback(containerId, validation);
            return;
        }
        
        // Clear any previous errors
        errorContainer.style('display', 'none');
        
        // UI elements for loading state
        const elements = {
            form: form,
            button: buttonGroup.select('button'),
            buttonGroup: buttonGroup,
            spinner: null
        };
        
        // Show loading state
        updateLoadingState(elements, true);
        
        // Submit to API
        submitTopicToAPI(apiEndpoint, topic)
            .then(response => {
                // Handle successful response
                updateLoadingState(elements, false);
                
                // Show success message and redirect
                showSuccessAndRedirect(container, topic, response.guide_id);
            })
            .catch(error => {
                // Handle error
                updateLoadingState(elements, false);
                displayAPIError(errorContainer, error);
            });
    });
    
    return form;
}

/**
 * Validates topic input with enhanced validation rules
 * Task 1.2: Implement input validation logic
 * @param {string} topic - The topic input to validate
 * @returns {Object} - Validation result { valid: boolean, error: string }
 */
function validateInput(topic) {
    // Check if topic is empty or only whitespace
    if (!topic || topic.trim() === '') {
        return { 
            valid: false, 
            error: 'Topic cannot be empty' 
        };
    }
    
    const trimmedTopic = topic.trim();
    const words = trimmedTopic.split(/\s+/);
    
    // Check if topic is too vague (less than 3 words)
    if (words.length < 3) {
        return { 
            valid: false, 
            error: 'Topic too vague. Please provide at least 3 words.' 
        };
    }
    
    // Check if topic is too long (more than 100 characters)
    if (trimmedTopic.length > 100) {
        return {
            valid: false,
            error: 'Topic too long. Please limit to 100 characters.'
        };
    }
    
    // Check if topic contains invalid characters (only allow alphanumeric, spaces, and basic punctuation)
    const validCharsRegex = /^[a-zA-Z0-9\s.,?!'"():-]+$/;
    if (!validCharsRegex.test(trimmedTopic)) {
        return {
            valid: false,
            error: 'Topic contains invalid characters. Please use only letters, numbers, and basic punctuation.'
        };
    }
    
    // Check if topic has at least 10 characters total (to ensure some substance)
    if (trimmedTopic.length < 10) {
        return {
            valid: false,
            error: 'Topic too short. Please be more specific (at least 10 characters).'
        };
    }
    
    // Check if any word is excessively long (potential spam or invalid input)
    const maxWordLength = 30;
    const longWord = words.find(word => word.length > maxWordLength);
    if (longWord) {
        return {
            valid: false,
            error: `Word "${longWord.substring(0, 10)}..." is too long. Please use natural language.`
        };
    }
    
    // Topic is valid
    return { valid: true };
}

/**
 * Displays feedback for topic input
 * Task 2.1: Add error feedback and examples
 * @param {string} containerId - The ID of the container element
 * @param {Object} validation - Validation result from validateInput function
 */
function displayFeedback(containerId, validation) {
    const container = d3.select(`#${containerId}`);
    const errorContainer = container.select('.error-container');
    
    if (!validation.valid) {
        // Show error message
        errorContainer
            .style('display', 'block')
            .text(validation.error);
    } else {
        // Hide error message
        errorContainer.style('display', 'none');
    }
}

/**
 * Sends a topic submission request to the API
 * @param {string} apiEndpoint - The API endpoint URL
 * @param {string} topic - The topic to submit
 * @returns {Promise} - A promise that resolves with the API response
 */
function submitTopicToAPI(apiEndpoint, topic) {
    return fetch(apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    });
}

/**
 * Updates the UI to show or hide loading state
 * @param {Object} elements - The DOM elements to update
 * @param {boolean} isLoading - Whether the form is in loading state
 */
function updateLoadingState(elements, isLoading) {
    if (isLoading) {
        elements.button
            .text('Processing...')
            .attr('disabled', true)
            .classed('loading', true);
            
        // Add a loading spinner if needed
        if (!elements.spinner) {
            elements.spinner = elements.buttonGroup.append('div')
                .attr('class', 'spinner')
                .attr('aria-hidden', 'true');
        }
    } else {
        elements.button
            .text('Start Guide Creation')
            .attr('disabled', null)
            .classed('loading', false);
            
        // Remove spinner if exists
        if (elements.spinner) {
            elements.spinner.remove();
            elements.spinner = null;
        }
    }
}

/**
 * Shows success message and redirects to research approval page
 * @param {d3.Selection} container - The container element
 * @param {string} topic - The submitted topic
 * @param {string} guideId - The guide ID returned from the API
 */
function showSuccessAndRedirect(container, topic, guideId) {
    // Hide the form
    container.select('.topic-form').style('display', 'none');
    
    // Show success message
    const successMessage = container.append('div')
        .attr('class', 'success-message')
        .attr('role', 'alert')
        .attr('aria-live', 'assertive');
        
    successMessage.append('h2')
        .text('Topic Submitted Successfully!');
        
    successMessage.append('p')
        .html(`Your guide on "<strong>${topic}</strong>" is being researched.`);
        
    successMessage.append('p')
        .text('You will be redirected to the research approval page shortly.');
        
    // Add a progress indicator
    const progressContainer = successMessage.append('div')
        .attr('class', 'redirect-progress-container');
        
    const progress = progressContainer.append('div')
        .attr('class', 'redirect-progress')
        .style('width', '0%');
        
    // Animate progress bar
    const duration = 3000; // 3 seconds until redirect
    const startTime = Date.now();
    
    const updateProgress = function() {
        const elapsed = Date.now() - startTime;
        const percentage = Math.min(100, (elapsed / duration) * 100);
        
        progress.style('width', `${percentage}%`);
        
        if (percentage < 100) {
            requestAnimationFrame(updateProgress);
        } else {
            // Redirect to research approval page
            window.location.href = `/guide/${guideId}/research`;
        }
    };
    
    // Start progress animation
    requestAnimationFrame(updateProgress);
}

/**
 * Displays an error message from API or network failure
 * @param {d3.Selection} errorContainer - The error container element
 * @param {Object|string} error - The error object or message
 */
function displayAPIError(errorContainer, error) {
    let errorMessage = 'An unexpected error occurred. Please try again.';
    
    if (typeof error === 'string') {
        errorMessage = error;
    } else if (error && error.error) {
        // Handle the expected Flask API error format: { "error": "Error message" }
        errorMessage = error.error;
    } else if (error && error.message) {
        errorMessage = error.message;
    }
    
    errorContainer
        .style('display', 'block')
        .attr('aria-hidden', 'false')
        .text(errorMessage);
}

// Export functions (for testing and reuse)
if (typeof module !== 'undefined') {
    module.exports = {
        createTopicForm,
        validateInput,
        displayFeedback,
        submitTopicToAPI,
        updateLoadingState,
        showSuccessAndRedirect,
        displayAPIError
    };
} 