# AI Council Implementation Requirements

## Research Stage
- Each AI performs a deepsearch for each topic (root topic and subtopics)
- Google search is also performed for each topic
- No summary chain is needed - summaries are returned as part of research results
- Results in multiple research trees
- Currently using Grok, with plans to add other AIs
- All research topics are stored in MongoDB
- Deepsearch with Grok is already implemented
- User Interface:
  - Further research topics are displayed as clickable buttons
  - Clicking a topic button triggers a new research cycle for that topic
  - Each new research cycle follows the same process (deepsearch + Google search)

## Outline Stage
1. Leader AI:
   - Creates initial outline using all research topics
2. All AIs (including leader):
   - Provide feedback in the form of:
     - Suggestions
     - Problems
     - Questions for the leader
3. User:
   - Provides feedback
4. Process repeats:
   - Leader creates new outline
   - All AIs provide feedback
   - User provides feedback
   - Until final outline is approved

## Writing Stage
- Same process as outline stage:
  1. Leader AI writes each section
  2. All AIs (including leader) provide feedback:
     - Suggestions
     - Problems
     - Questions for the leader
  3. User provides feedback
  4. Process repeats until section is approved
- Process continues for each section of the guide 