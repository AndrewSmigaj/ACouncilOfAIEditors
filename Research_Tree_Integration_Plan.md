# Research-Tree Integration Plan for Guides

> This file was generated automatically to consolidate the agreed-upon design for **separate per-AI research trees inside each guide** and the corresponding UI behaviour (tree visualisation + single research card).  All sections are written so that Claude 3.7 can follow them step-by-step.

---

## 0 – Quick Summary
* **Goal** – Display, on one page, a set of research trees (one per AI) and a single research-card showing the node that the user selects in any tree.
* **Scope** – Only the *Research* stage.  Outline / writing stages remain unchanged.
* **Impact** – DB schema, backend routes, JSON shape, frontend JS (tree + card), minor CSS.

---

## 1 – MongoDB Data Model
A guide document now embeds all AI research trees under a new top-level field `trees`.

```jsonc
{
  _id: ObjectId,
  topic: "How to \"vibe code\" with Cursor and Claude",
  status: "completed",          // root research status
  metadata: { created, updated, ais: ["grok", "claude"] },
  trees: {
    grok:   <Node>,             // root node for Grok's tree
    claude: <Node>,             // root node for Claude's tree (disabled → null)
    …etc
  }
}
```

### Node schema (embedded recursively)
```jsonc
{
  node_id: "<uuid>|<bson>",    // unique only inside its guide
  topic: "…",
  status: "initializing"|"completed"|"error",
  research: { /* summary, key_points, …  – single AI payload */ },
  children: [ <Node>, … ],
  created_at: ISODate,
  updated_at: ISODate
}
```
*No extra collection is required; one Mongo read fetches the entire guide with all trees.*

---

## 2 – Backend Adjustments
1. **`ResearchService.research_topic`**  
   *After `AICouncil.conduct_research` returns `{ ai_name: result }`*  
   • build a root Node for each enabled AI and return:
   ```python
   return {
       "topic": topic,
       "trees": { ai: root_node for ai, root_node in root_nodes.items() }
   }
   ```
2. **`MongoDBService.store_research`**  
   • `insert` if `guide_id is None`; otherwise `$set` the `trees` field.
3. **Sub-topic endpoint**  
   Path: `POST /api/research/subtopic`  
   Body:
   ```json
   { "topic": "LLM embeddings", "ai": "grok", "guide_id": "…", "parent_node_id": "…" }
   ```
   Logic: run research with that one AI, build child Node, `$push` it to `trees.<ai>.children`.
4. **Results endpoint**  
   `GET /api/research/results/<guide_id>`  → `{ status, trees }`.
5. **Render route**  
   `/guide/<id>/research` must `render_template("research.html", guide_id=id)` instead of returning JSON.

---

## 3 – Frontend (D3 + Vanilla JS)
### DOM skeleton
```html
<div id="trees-row"></div>   <!-- one column per AI -->
<div id="research-card"></div>
```

### Boot-strap logic (pseudo-code)
```js
const { trees } = await fetch(`/api/research/results/${guideId}`).then(r=>r.json());
Object.entries(trees).forEach(([ai, root]) => {
  const div = document.createElement('div');
  div.id = `tree-${ai}`;
  div.className = 'tree-col';
  document.getElementById('trees-row').appendChild(div);

  const tree = new ResearchTree(div.id);
  tree.initializeWithData(root);        // no extra HTTP
  tree.on('nodeClicked', node => showCard(ai, node));
});
showCard(Object.keys(trees)[0], trees[Object.keys(trees)[0]]); // default
```

### `showCard()`
```js
function showCard(ai, node) {
  const card = new ResearchCard('research-card');
  card.updateContent({ ai, topic: node.topic, ...node.research });
}
```

### "Explore further" button
* Sends the payload described in **§2.3**; on success, update the corresponding tree and call `showCard`.

---

## 4 – Routing Table (new vs existing)
| Purpose | Method & Path | Returns |
|---------|---------------|---------|
| create guide | POST `/api/research` | `{ guide_id }` |
| get results  | GET  `/api/research/results/<guide_id>` | `{ trees }` |
| add subtopic | POST `/api/research/subtopic` | `{ status }` |
| research page| GET  `/guide/<id>/research` | **HTML page** |

---

## 5 – Acceptance Checklist
- [ ] Creating a topic redirects to `/guide/<id>/research`.
- [ ] Page shows one D3 tree per AI (Grok only for now).
- [ ] Card shows root-node research.
- [ ] Clicking any node switches the card.
- [ ] "Explore further" adds a child node, tree updates, card updates after research completes.
- [ ] No JSON is shown directly in the browser (only HTML+JS UI).

---

## 6 – Implementation Order (for Claude 3.7)
1. **DB / backend**: update models, `store_research`, endpoints.  
2. **Route fix**: `/guide/<id>/research` renders template.  
3. **Frontend bootstrap**: new DOM layout + per-AI tree initialisation.  
4. **Card renderer**: accept `{ ai, topic, … }`.  
5. **Subtopic flow** alignment.  
6. **CSS tweaks**.

---

## 7 – Comments / Tips for Claude
* Use embedded documents; avoids multiple queries.
* Generate `node_id` via `uuid4().hex` if not using ObjectId.
* When updating nested arrays in Mongo, use positional filters or `$[]`.  Example:
  ```python
  db.guides.update_one(
      {"_id": gid, "trees.grok.node_id": parent},
      {"$push": {"trees.grok.children": new_node}}
  )
  ```
* Keep the existing D3 `ResearchTree` class; just add an `initializeWithData(data)` helper that skips HTTP.
* Polling can stay for now; switch to WebSockets later.
* For any change that breaks old guides, write a one-off migration script (see §4 of previous answer).

---

_End of file_ 