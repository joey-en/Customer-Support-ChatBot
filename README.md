# Kairos Customer Support Chatbot (Streamlit + Mistral Lab)

This project is a lab implementation for building a simple Customer Support Chatbot using Mistral as the LLM and Streamlit as the UI. It also includes a Flask REST API for programmatic access.

### What Is Kairos?

Kairos is an AI-powered long-form video understanding and retrieval platform. It transforms long videos into searchable, conversationally accessible content by analyzing scenes, audio, and visual context, then enabling Q&A and clip retrieval.

The lab demonstrates how to build a practical support chatbot using LLMs and structured prompts. It focuses on:

- Classifying user intent
- Generating consistent, grounded answers
- Extracting structured issue details
- Summarizing long technical issues
- Deploying the experience as a web app and API

### LLM Features Demonstrated

- ClassificationRoutes a user message into one of four intents: `Technical Issue`, `Feature Explanation`, `System Architecture Explanation`, or `General Inquiry`.
- SummarizationCreates a short 2–3 sentence summary of long technical issue descriptions.
- Structured Extraction (JSON)Extracts issue details like error messages, stage of failure, and device context into a clean JSON payload.
- Grounded Response Generation
  Produces answers based strictly on provided documents and prompt instructions.

### Technologies Used

- **Streamlit**Used for the interactive chat UI and user experience.
- **Flask**Used to expose a REST API (`/chat`) so the chatbot can be consumed by other apps.
- **Mistral**
  The LLM that powers classification, summarization, extraction, and response generation.

### Project Structure

- `app.py` — Streamlit chat UI.
- `api.py` — Flask REST API.
- `core.py` — Shared LLM logic (classification, summarization, extraction, response generation).
- `prompts/` — Prompt templates for classification and response generation.
- `documents/` — Source documents (Kairos info, features, system architecture).

## How To Run

### 1) Install Dependencies

```bash
pip install -r requirements.txt
```

### 2) Set Environment Variables

Create a `.env` file with:

```
MISTRAL_API_KEY=your_key_here
```

Optional:

```
MISTRAL_MODEL=mistral-large-latest
```

### 3) Run the API (Flask)

```bash
python api.py
```

The API will run at `http://127.0.0.1:5000/chat`.

### 4) Run the Web App (Streamlit)

```bash
streamlit run app.py
```

Open the local Streamlit URL printed in the terminal.

## Example API Request

```bash
curl -X POST http://127.0.0.1:5000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"My video upload keeps failing at 70%\"}"
```
