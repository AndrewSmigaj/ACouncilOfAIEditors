# Implementation Plan: Task 1.1 - Complete the Topic Input Form with D3.js

## Step 1: Update Form Submission Logic in topicInput.js

### Current Placeholder Code (to replace)
```javascript
// Submit form via API (placeholder - will be implemented fully in Task 1.1)
console.log(`Submitting topic: ${topic} to API endpoint: ${apiEndpoint}`);

// Show loading indicator (placeholder)
buttonGroup.select('button')
    .text('Processing...')
    .attr('disabled', true);

// Simulate API call (this would be a real fetch call in the implementation)
setTimeout(() => {
    // Restore button state
    buttonGroup.select('button')
        .text('Start Guide Creation')
        .attr('disabled', null);
    
    // Display success message (placeholder)
    container.select('.topic-form').style('display', 'none');
    
    container.append('div')
        .attr('class', 'success-message')
        .html(`
            <h2>Topic Submitted Successfully!</h2>
            <p>Your guide on "<strong>${topic}</strong>" is being researched.</p>
            <p>You will be redirected to the research approval page shortly.</p>
        `);
}, 1500);
```

### New Implementation Plan
1. Replace the setTimeout with an actual fetch call to the API endpoint
2. Add proper error handling for network failures and API errors
3. Implement better loading state with a spinner or progress indicator
4. Add proper success state with redirection to the research approval page

## Step 2: Create Helper Functions

### Add Fetch API Wrapper
Create a function to handle the API call with proper error handling:

```javascript
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
```

### Add Loading State Function
Create a function to manage loading states:

```javascript
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
```

### Add Success State and Redirect Function
Create a function to show success and handle redirection:

```javascript
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
```

### Add Error Handling Function
Create a function to display error messages:

```javascript
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
        errorMessage = error.error;
    } else if (error && error.message) {
        errorMessage = error.message;
    }
    
    errorContainer
        .style('display', 'block')
        .text(errorMessage);
}
```

## Step 3: Update the Form Submission Handler

Replace the placeholder submission handler with the new implementation using the helper functions:

```javascript
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
```

## Step 4: Add CSS for New UI Elements

Add CSS for the loading spinner and progress indicator in styles.css:

```css
/* Loading spinner */
.spinner {
    display: inline-block;
    margin-left: 1rem;
    width: 1.5rem;
    height: 1.5rem;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Submit button with loading state */
.submit-button.loading {
    background-color: var(--primary-dark);
    opacity: 0.8;
}

/* Redirect progress bar */
.redirect-progress-container {
    height: 4px;
    width: 100%;
    background-color: var(--border-color);
    margin-top: var(--spacing);
    overflow: hidden;
    border-radius: var(--border-radius);
}

.redirect-progress {
    height: 100%;
    background-color: var(--primary-color);
    transition: width 0.1s linear;
}
```

## Step 5: Testing Plan

### Manual Testing
1. Submit form with valid input (3+ words)
   - Verify loading state appears
   - Verify success message and redirect happens
   
2. Submit form with invalid input (less than 3 words)
   - Verify error message appears
   - Verify form does not submit
   
3. Test with network errors
   - Simulate network failure and verify error handling
   - Verify loading state disappears on error

### Integration Testing
1. Verify the API call format matches the backend expectations
2. Verify the redirect URL correctly points to the research approval page
3. Verify ARIA attributes maintain accessibility during loading and success states

## Step 6: Implementation Checklist

- [ ] Replace placeholder form submission code with actual API call
- [ ] Add helper functions for API calls, loading states, and success handling
- [ ] Update CSS with new styles for loading and progress indicators
- [ ] Test form submission with valid and invalid input
- [ ] Test error handling for API errors and network failures
- [ ] Verify accessibility with ARIA attributes during all states
- [ ] Final review for code consistency and comments 