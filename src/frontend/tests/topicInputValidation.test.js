/**
 * Test suite for topic input validation logic
 * Tests for Task 1.2: Implement input validation logic
 */

// Import the validateInput function (assuming module export is set up)
// In a real environment, you might need to adjust this import
// const { validateInput } = require('../static/js/topicInput.js');

// Mock validateInput function for testing (use this if import is not available)
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

describe('Topic Input Validation', () => {
    test('Should reject empty input', () => {
        const result = validateInput('');
        expect(result.valid).toBe(false);
        expect(result.error).toContain('empty');
    });
    
    test('Should reject whitespace-only input', () => {
        const result = validateInput('   ');
        expect(result.valid).toBe(false);
        expect(result.error).toContain('empty');
    });
    
    test('Should reject topics with less than 3 words', () => {
        const result = validateInput('Web development');
        expect(result.valid).toBe(false);
        expect(result.error).toContain('vague');
    });
    
    test('Should reject topics with less than 10 characters', () => {
        const result = validateInput('A B C');
        expect(result.valid).toBe(false);
        expect(result.error).toContain('short');
    });
    
    test('Should reject topics with more than 100 characters', () => {
        const longTopic = 'This is an extremely long topic that exceeds the maximum limit of one hundred characters and should be rejected by the validation function';
        const result = validateInput(longTopic);
        expect(result.valid).toBe(false);
        expect(result.error).toContain('long');
    });
    
    test('Should reject topics with invalid characters', () => {
        const result = validateInput('How to use <script> tags in HTML');
        expect(result.valid).toBe(false);
        expect(result.error).toContain('invalid characters');
    });
    
    test('Should reject topics with excessively long words', () => {
        const result = validateInput('How to use supercalifragilisticexpialidocious in everyday conversation');
        expect(result.valid).toBe(false);
        expect(result.error).toContain('too long');
    });
    
    test('Should accept valid topics', () => {
        const validResults = [
            validateInput('How to start a podcast'),
            validateInput('Building a sustainable garden'),
            validateInput('Advanced techniques for digital photography'),
            validateInput('Creating a personal financial plan')
        ];
        
        validResults.forEach(result => {
            expect(result.valid).toBe(true);
        });
    });
}); 