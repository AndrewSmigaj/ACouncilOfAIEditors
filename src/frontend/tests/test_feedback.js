/**
 * QUnit tests for Task 2.1: Add error feedback and examples with D3.js
 */

// Import functions from topicInput.js
const { validateInput, displayFeedback } = require('../d3/topicInput');

QUnit.module('Task 2.1: Enhanced Feedback Display', hooks => {
    // Setup test environment before each test
    hooks.beforeEach(() => {
        // Create a container for testing
        document.body.innerHTML = '<div id="test-container"></div>';
        
        // Mock D3.js select functions
        window.d3 = {
            select: function(selector) {
                const element = document.querySelector(selector);
                
                // Return a D3-like selection object
                return {
                    node: () => element,
                    property: function(prop, value) {
                        if (value !== undefined) {
                            element[prop] = value;
                            return this;
                        }
                        return element[prop];
                    },
                    style: function(prop, value) {
                        if (value !== undefined) {
                            element.style[prop] = value;
                            return this;
                        }
                        return getComputedStyle(element)[prop];
                    },
                    attr: function(attr, value) {
                        if (value !== undefined) {
                            element.setAttribute(attr, value);
                            return this;
                        }
                        return element.getAttribute(attr);
                    },
                    classed: function(className, add) {
                        if (add !== undefined) {
                            if (add) {
                                element.classList.add(className);
                            } else {
                                element.classList.remove(className);
                            }
                            return this;
                        }
                        return element.classList.contains(className);
                    },
                    html: function(content) {
                        if (content !== undefined) {
                            element.innerHTML = content;
                            return this;
                        }
                        return element.innerHTML;
                    },
                    text: function(content) {
                        if (content !== undefined) {
                            element.textContent = content;
                            return this;
                        }
                        return element.textContent;
                    },
                    append: function(tagName) {
                        const newElement = document.createElement(tagName);
                        element.appendChild(newElement);
                        return d3.select(newElement);
                    },
                    select: function(selector) {
                        const child = element.querySelector(selector);
                        return d3.select(child);
                    },
                    selectAll: function(selector) {
                        const children = element.querySelectorAll(selector);
                        return Array.from(children).map(el => d3.select(el));
                    },
                    on: function(eventName, handler) {
                        element.addEventListener(eventName, handler);
                        return this;
                    },
                    empty: function() {
                        return !element;
                    }
                };
            }
        };
        
        // Setup necessary DOM structure for testing
        const container = document.getElementById('test-container');
        
        // Create a mock form element
        const form = document.createElement('form');
        form.className = 'topic-form';
        form.setAttribute('aria-label', 'Topic input form');
        container.appendChild(form);
        
        // Create input field
        const input = document.createElement('input');
        input.id = 'topic-input';
        input.className = 'topic-input';
        form.appendChild(input);
        
        // Create error container
        const errorContainer = document.createElement('div');
        errorContainer.className = 'error-container';
        errorContainer.style.display = 'none';
        form.appendChild(errorContainer);
        
        // Create examples container
        const examplesContainer = document.createElement('div');
        examplesContainer.className = 'examples-container';
        form.appendChild(examplesContainer);
        
        // Add heading to examples container
        const examplesHeading = document.createElement('h3');
        examplesHeading.textContent = 'Example Topics:';
        examplesContainer.appendChild(examplesHeading);
        
        // Add example list
        const examplesList = document.createElement('ul');
        examplesList.className = 'examples-list';
        examplesContainer.appendChild(examplesList);
        
        // Add some example topics
        const examples = [
            'How to start a podcast',
            'Building a sustainable garden'
        ];
        
        examples.forEach(example => {
            const li = document.createElement('li');
            examplesList.appendChild(li);
            
            const a = document.createElement('a');
            a.href = '#';
            a.className = 'example-link';
            a.textContent = example;
            li.appendChild(a);
        });
    });
    
    // Clean up after each test
    hooks.afterEach(() => {
        document.body.innerHTML = '';
        delete window.d3;
    });
    
    QUnit.test('displayFeedback shows error message with icon when validation fails', assert => {
        // Arrange
        const validation = { valid: false, error: 'Test error message' };
        
        // Act
        displayFeedback('test-container', validation);
        
        // Assert
        const errorContainer = document.querySelector('.error-container');
        assert.equal(errorContainer.style.display, 'block', 'Error container is visible');
        assert.equal(errorContainer.getAttribute('role'), 'alert', 'Error has role="alert" for accessibility');
        assert.equal(errorContainer.getAttribute('aria-hidden'), 'false', 'Error has aria-hidden="false"');
        
        const errorIcon = errorContainer.querySelector('.error-icon');
        assert.ok(errorIcon, 'Error icon is present');
        assert.equal(errorIcon.getAttribute('aria-hidden'), 'true', 'Icon is hidden from screen readers');
        
        const errorMessage = errorContainer.querySelector('.error-message');
        assert.ok(errorMessage, 'Error message element is present');
        assert.equal(errorMessage.textContent, 'Test error message', 'Error message content is correct');
    });
    
    QUnit.test('displayFeedback hides error message when validation passes', assert => {
        // Arrange
        const validation = { valid: true };
        
        // Act
        displayFeedback('test-container', validation);
        
        // Assert
        const errorContainer = document.querySelector('.error-container');
        assert.equal(errorContainer.style.display, 'none', 'Error container is hidden');
        assert.equal(errorContainer.getAttribute('aria-hidden'), 'true', 'Error has aria-hidden="true"');
    });
    
    QUnit.test('displayFeedback adds error styling to input field on validation failure', assert => {
        // Arrange
        const validation = { valid: false, error: 'Test error message' };
        
        // Act
        displayFeedback('test-container', validation);
        
        // Assert
        const inputField = document.getElementById('topic-input');
        assert.ok(inputField.classList.contains('input-error'), 'Input has error class');
        assert.equal(inputField.getAttribute('aria-invalid'), 'true', 'Input has aria-invalid="true"');
    });
    
    QUnit.test('displayFeedback removes error styling from input field on validation success', assert => {
        // Arrange - First add error styling
        displayFeedback('test-container', { valid: false, error: 'Test error message' });
        
        // Act - Then validate with success
        displayFeedback('test-container', { valid: true });
        
        // Assert
        const inputField = document.getElementById('topic-input');
        assert.notOk(inputField.classList.contains('input-error'), 'Input does not have error class');
        assert.equal(inputField.getAttribute('aria-invalid'), 'false', 'Input has aria-invalid="false"');
    });
    
    QUnit.test('displayFeedback highlights example container on validation failure', assert => {
        // Arrange
        const validation = { valid: false, error: 'Test error message' };
        
        // Act
        displayFeedback('test-container', validation);
        
        // Assert
        const examplesContainer = document.querySelector('.examples-container');
        assert.ok(examplesContainer.classList.contains('highlight'), 'Examples container has highlight class');
        assert.equal(examplesContainer.getAttribute('aria-label'), 'Suggested example topics', 'Examples container has proper aria label');
    });
    
    QUnit.test('displayFeedback adds proper ARIA attributes to examples heading and list', assert => {
        // Arrange
        const validation = { valid: false, error: 'Test error message' };
        
        // Act
        displayFeedback('test-container', validation);
        
        // Assert
        const examplesHeading = document.querySelector('.examples-container h3');
        assert.ok(examplesHeading.hasAttribute('id'), 'Examples heading has ID attribute');
        
        const examplesList = document.querySelector('.examples-list');
        assert.equal(examplesList.getAttribute('aria-labelledby'), examplesHeading.getAttribute('id'), 'Examples list is properly labelled');
    });
    
    QUnit.test('displayFeedback makes example links keyboard accessible', assert => {
        // Arrange
        const validation = { valid: false, error: 'Test error message' };
        
        // Act
        displayFeedback('test-container', validation);
        
        // Assert
        const exampleLinks = document.querySelectorAll('.example-link');
        exampleLinks.forEach(link => {
            assert.equal(link.getAttribute('role'), 'button', 'Example link has role="button"');
            assert.equal(link.getAttribute('tabindex'), '0', 'Example link has tabindex="0" for keyboard focus');
            assert.ok(link.getAttribute('aria-label').includes('Use example topic'), 'Example link has descriptive aria-label');
        });
    });
    
    QUnit.test('displayFeedback adds real-time validation to input field', assert => {
        // Arrange
        const validation = { valid: false, error: 'Test error message' };
        const inputField = document.getElementById('topic-input');
        let inputHandlerCalled = false;
        
        // Replace addEventListener to track calls
        const originalAddEventListener = inputField.addEventListener;
        inputField.addEventListener = function(eventName, handler) {
            if (eventName === 'input') {
                inputHandlerCalled = true;
            }
            originalAddEventListener.call(this, eventName, handler);
        };
        
        // Act
        displayFeedback('test-container', validation);
        
        // Assert
        assert.ok(inputHandlerCalled, 'Input event handler was added');
        assert.equal(inputField.__hasValidation, true, 'Input field is marked as having validation');
    });
    
    QUnit.test('displayFeedback adds required CSS styles', assert => {
        // Arrange
        const validation = { valid: false, error: 'Test error message' };
        
        // Act
        displayFeedback('test-container', validation);
        
        // Assert
        const styleElement = document.getElementById('feedback-styles');
        assert.ok(styleElement, 'Style element was created');
        assert.ok(styleElement.textContent.includes('.error-container'), 'Styles include error container');
        assert.ok(styleElement.textContent.includes('.examples-container'), 'Styles include examples container');
        assert.ok(styleElement.textContent.includes('.example-link'), 'Styles include example links');
    });
    
    QUnit.test('validateInput correctly identifies empty input', assert => {
        // Act
        const result = validateInput('');
        
        // Assert
        assert.equal(result.valid, false, 'Empty input is invalid');
        assert.equal(result.error, 'Topic cannot be empty', 'Error message is correct');
    });
    
    QUnit.test('validateInput correctly identifies too short input', assert => {
        // Act
        const result = validateInput('Too short');
        
        // Assert
        assert.equal(result.valid, false, 'Short input is invalid');
        assert.equal(result.error, 'Topic too vague. Please provide at least 3 words.', 'Error message is correct');
    });
    
    QUnit.test('validateInput accepts valid input', assert => {
        // Act
        const result = validateInput('This is a valid topic');
        
        // Assert
        assert.equal(result.valid, true, 'Valid input is accepted');
        assert.notOk(result.error, 'No error message for valid input');
    });
}); 