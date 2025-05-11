// Simple test script to check the research/subtopics API
const fetch = require('node-fetch');

async function testSubtopicAPI() {
  console.log('Testing subtopic API...');
  
  // Replace this with a valid guide ID from your database
  const guideId = 'PUT_VALID_GUIDE_ID_HERE';
  
  // Set up test data
  const testData = {
    topic: 'Test subtopic', 
    ai: 'grok',
    parent_node_id: guideId  // Using guide ID as parent node ID for simplicity
  };
  
  console.log(`Using guide ID: ${guideId}`);
  console.log(`Request body:`, testData);

  try {
    // Make the API call
    const response = await fetch(`http://localhost:5000/api/research/${guideId}/subtopics`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(testData)
    });
    
    console.log(`Response status: ${response.status}`);
    
    // Handle HTTP errors
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`HTTP error: ${response.status} - ${errorText}`);
      return;
    }
    
    // Parse and log the response
    const result = await response.json();
    console.log('API response:', JSON.stringify(result, null, 2));
    
    if (result.status === 'success') {
      console.log('Successfully created subtopic!');
      console.log(`New node ID: ${result.node.node_id}`);
    } else {
      console.error('API returned error:', result.error || 'Unknown error');
    }
  } catch (error) {
    console.error('Error calling API:', error);
  }
}

// Execute the test
testSubtopicAPI();

/*
Instructions:
1. Install node-fetch: npm install node-fetch@2
2. Replace the guide ID with a valid one from your database
3. Run the script: node test_subtopic.js
*/ 