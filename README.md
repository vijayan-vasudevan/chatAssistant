# Chat Assistant Agent
This is a multi-agent "Chat Assistant Agent" system built on the Gemini API. It uses a Retrieval Augmented Generation (RAG) 
to build a knowledge base and a multi-agent system to provide intelligent, context-aware answers.

This system is designed with Evaluation-Driven Development(EDD).

## Core Features
1. File or Folder based Knowledge Ingestion
   * It reads provided pdf file or all the pdf files under the given folder.
   * It splits the data into multiple chunks using langchain_text_splitters
   * It embeds the chunked data using SentenceTransformer('all-MiniLM-L6-v2')
   * Stores the data into the collection(knowledge-docs) of chroma db
2. Answer using ingested knowledge of LLM
   * For any questions related to ingested content, bot can answer using the knowledge of ingested data

## Frontend
streamlit is used for frontend

## Multi Agent System
1. **CoordinatorAgent**: 
   * This agent will coordinate with other agent(SynthesizerAgent) and RAGService to fetch or store data to chroma db
2. **SynthesizerAgent**
   * This agent takes the user query, context from RAG, chat conversation in the memory
   * With all these details, it will query LLM to get the response.

## Evaluation-Driven Development(EDD)
All the below agent has pydantic eval cases to ensure that agents logic is evaluated properly with high level scenarios
1. agents/coordinatoragent/main.py
2. agents/synthesizeragent/main.py

## Observability
This application is fully instrumented with OpenTelemetry with langsmith
We can understand the entire flow and how the agents are interacted with each other using langsmith


## 🚀 Quick Start

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key
5. Set it as an environment variable:

### Set your Gemini API Key

```bash
# Store your API key in 1Password
op item create --category="API Credential" --title="GEMINI_API_KEY" credential="your-gemini-api-key"

# Use it in your shell
export GEMINI_API_KEY=$(op read "op://Private/GEMINI_API_KEY/credential")

# Or add to your shell profile (~/.zshrc or ~/.bashrc)
echo 'export GEMINI_API_KEY=$(op read "op://Private/GEMINI_API_KEY/credential")' >> ~/.zshrc
```

### SET config for langsmith

```bash
echo 'export LANGSMITH_API_KEY=<YOUR langsmith api key>'
echo 'export OTEL_EXPORTER_OTLP_ENDPOINT="https://api.smith.langchain.com/otel"'
echo 'export OTEL_EXPORTER_OTLP_HEADERS="x-api-key=${LANGSMITH_API_KEY}"'
```

### Running chat bot
```bash
# Sync dependencies
uv sync
# Activate virtual environment
source .venv/bin/activate

# Starts the chatbot application and it can be accessed using http://localhost:8501
streamlit run frontend/chatbot.py --server.port 8501 --server.headless true
```