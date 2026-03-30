# PowerPoint AI Presentation Coach — Actionable Project Blueprint

## Goal

Build a **PowerPoint-integrated AI presentation coach** that can:

- read deck context from PowerPoint
- accept or coordinate rehearsal recordings
- analyze speech, slide content, and later video/nonverbal delivery
- return structured coaching feedback inside PowerPoint

The recommended architecture is:

- **PowerPoint add-in** for in-app UI and PowerPoint integration
- **Python backend** for AI analysis and orchestration

---

## Key decision

Do **not** try to make a raw Python script the PowerPoint add-in.

Use this split instead:

- **Inside PowerPoint:** Office Add-in built with **TypeScript/React + Office.js**
- **Backend services:** **Python + FastAPI**

This is the cleanest path for a real PoC and aligns with Microsoft’s supported add-in model.

---

## Project scope for v1

### In scope
- Read slide text and basic deck metadata from PowerPoint
- Send deck context to backend
- Upload or reference rehearsal recording
- Analyze:
  - slide content quality
  - speaking quality
  - transcript quality
- Show feedback in PowerPoint task pane
- Return:
  - overall score
  - top issues
  - slide-by-slide suggestions

### Out of scope for v1
- Full real-time multimodal live coaching
- Deep gesture/facial-expression analysis during live presentation
- Marketplace/AppSource public publishing
- Full enterprise security hardening
- Cross-platform parity for every PowerPoint client/version

---

## Recommended system architecture

```text
PowerPoint
  -> Office Add-in (TypeScript/React, task pane + ribbon)
  -> Backend API (Python FastAPI)
  -> Analysis services
       - speech/transcript scoring
       - slide-content scoring
       - optional video analysis later
  -> Result store
  -> Feedback back into task pane
```

---

## Tech stack

## Front end / PowerPoint integration
- TypeScript
- React
- Office.js
- PowerPoint JavaScript API
- HTML/CSS
- Office Add-in manifest

## Backend
- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic

## Storage
- PostgreSQL or Azure SQL for metadata
- Blob/object storage for video/audio/transcript files

## Optional later
- Redis / background jobs
- WebSocket progress updates
- CV/nonverbal analysis pipeline

---

## Core product flow

### User flow
1. User opens PowerPoint
2. User launches the AI Coach add-in
3. Add-in reads current deck context
4. User starts a rehearsal session
5. User uploads or links recording artifacts
6. Backend runs analysis
7. Add-in shows:
   - overall score
   - top improvements
   - slide-by-slide comments
   - jump-to-slide actions

### Data flow
1. Add-in extracts deck metadata
2. Add-in sends deck payload to backend
3. Backend stores session
4. User uploads recording
5. Backend runs transcript/speech/slide analysis
6. Backend stores structured feedback
7. Add-in requests and renders results

---

## Proposed API contract

## 1. Create rehearsal
**POST** `/api/rehearsals`

Request:
```json
{
  "presentationId": "ppt-123",
  "title": "Project Update",
  "slides": [
    {
      "slideNumber": 1,
      "title": "Executive Summary",
      "text": ["Point A", "Point B"],
      "speakerNotes": "Open with business context."
    }
  ],
  "recordingMode": "upload_later",
  "analysisOptions": {
    "analyzeSpeech": true,
    "analyzeSlides": true,
    "analyzeVideo": false
  }
}
```

Response:
```json
{
  "rehearsalId": "rh_001",
  "status": "created"
}
```

## 2. Upload media
**POST** `/api/rehearsals/{id}/media`

Request:
```json
{
  "audioUrl": "https://storage/.../audio.mp3",
  "videoUrl": "https://storage/.../video.mp4",
  "transcript": null
}
```

## 3. Trigger analysis
**POST** `/api/rehearsals/{id}/analyze`

Request:
```json
{
  "priority": "normal"
}
```

## 4. Fetch results
**GET** `/api/rehearsals/{id}/results`

Response:
```json
{
  "rehearsalId": "rh_001",
  "overallScore": 78,
  "summary": {
    "strengths": ["Strong structure"],
    "topImprovements": ["Reduce filler words", "Simplify slide 4"]
  },
  "speech": {
    "paceWpm": 162,
    "fillerWords": 14
  },
  "slides": [
    {
      "slideNumber": 4,
      "score": 62,
      "issues": ["Too text-heavy"],
      "suggestions": ["Cut body text by 40%"]
    }
  ]
}
```

---

## Suggested repository structure

```text
project-root/
  powerpoint-addin/
    src/
    public/
    manifest.xml
    package.json

  backend/
    app/
      main.py
      api/
      models/
      services/
      schemas/
    requirements.txt

  infra/
    docker/
    deployment/

  docs/
    architecture.md
    api-contract.md
```

---

## PowerPoint add-in responsibilities

The PowerPoint add-in should:

- expose ribbon commands like **Start AI Rehearsal**
- open a task pane UI
- read current presentation context
- send deck data to backend
- poll for analysis results
- render feedback inside PowerPoint
- allow slide navigation from feedback

Keep the add-in thin. Do not place heavy AI logic here.

---

## Python backend responsibilities

The backend should:

- create rehearsal sessions
- validate incoming payloads
- store deck context
- store recording references
- run analysis orchestration
- return structured feedback JSON

Start simple:
- transcript and speech scoring first
- slide-content scoring second
- video analysis third

---

## Development phases

## Phase 0 — setup
- Create Git repo
- Create PowerPoint add-in scaffold
- Create FastAPI backend scaffold
- Confirm local PowerPoint add-in sideloading works
- Confirm backend can receive requests from add-in

**Deliverable:** add-in button opens task pane and calls local backend

## Phase 1 — deck ingestion
- Read slide titles, text, and notes from PowerPoint
- Convert deck to backend payload
- Store rehearsal session
- Show successful sync in task pane

**Deliverable:** add-in can sync current deck to backend

## Phase 2 — manual analysis pipeline
- Support upload of transcript or recording reference
- Run slide-content analysis
- Run speech/transcript analysis
- Store output in structured JSON

**Deliverable:** feedback JSON returned for one rehearsal

## Phase 3 — feedback UX
- Show:
  - overall score
  - top issues
  - strengths
  - per-slide comments
- Add “jump to slide” interaction

**Deliverable:** usable in-PowerPoint review experience

## Phase 4 — polish
- Add job status/progress
- Add result history
- Improve prompt/model logic
- Add export to markdown or PDF

**Deliverable:** internal demo-ready PoC

## Phase 5 — optional advanced enhancements
- Video/nonverbal analysis
- Real-time rehearsal mode
- Enterprise auth
- Admin deployment
- Compliance review
- AppSource/public distribution if ever needed

---

## Two-week PoC plan

## Week 1
### Day 1–2
- Scaffold Office Add-in
- Scaffold FastAPI backend
- Wire local communication

### Day 3–4
- Implement deck extraction from PowerPoint
- Implement `POST /api/rehearsals`

### Day 5
- Validate payload schema and persistence

## Week 2
### Day 6–7
- Implement transcript/speech analysis
- Implement slide-content analysis

### Day 8–9
- Implement results endpoint
- Build task pane feedback UI

### Day 10
- Demo end-to-end flow:
  - open PowerPoint
  - sync deck
  - upload rehearsal artifact
  - run analysis
  - view feedback

---

## Immediate first tasks

### Today
- Decide project name
- Create repo
- Split into:
  - `powerpoint-addin`
  - `backend`

### This week
- Build hello-world PowerPoint add-in
- Build hello-world FastAPI endpoint
- Prove add-in can send current deck metadata to backend

### First success milestone
> “From inside PowerPoint, I can click a button and send slide content to my Python backend, then receive and display structured feedback.”

---

## Risks to watch

### Technical
- PowerPoint API feature differences by client/version
- Office add-in sideloading/deployment friction
- CORS/localhost issues between add-in and backend
- Recording workflow complexity

### Product
- Over-scoping v1
- Trying to solve live multimodal coaching too early
- Weak feedback UX inside task pane

### Governance
- Sending slide/audio/video data to external AI providers
- Retention/privacy requirements
- Internal tenant/admin controls for add-ins

---

## v1 success criteria

The PoC is successful if it can do all of the following:

- launch from PowerPoint
- read slide content from the current deck
- send deck context to backend
- ingest a rehearsal artifact
- generate structured feedback
- show that feedback inside PowerPoint
- allow user to navigate improvement areas slide by slide

---

## Recommended build order

1. **PowerPoint integration shell**
2. **Python backend**
3. **Deck sync**
4. **Transcript/speech analysis**
5. **Slide feedback**
6. **Task pane UX**
7. **Optional video analysis**

This order minimizes risk and gets to demo value quickly.

---

## Final recommendation

Use this architecture:

- **PowerPoint Add-in = UI + PowerPoint integration**
- **Python Backend = AI engine + orchestration**

Do **not** try to force Python to be the native PowerPoint add-in.

Build the thinnest possible in-PowerPoint layer, and keep the intelligence in Python.

That gives you the fastest path to:
- a real PoC
- a clean architecture
- a future enterprise deployment path
