# Knowledge RAG Agents

A multi-agent Retrieval-Augmented Generation (RAG) system orchestrated with **LangGraph**, featuring a **Data Retriever Agent** and a **Report Generator Agent**.

## Overview

- **Data Retriever Agent** (`src/agents/nodes.py`): Translates user queries into domain search keywords and calls `search_knowledge_base` to retrieve relevant snippets from `knowledge_base.txt`.
- **Custom Retrieval Tool** (`src/tools/retriever_tool.py`): Performs TF-IDF keyword search with stemming, stopword removal, and section header boosting using standard Python libraries.
- **Report Generator Agent** (`src/agents/nodes.py`): Synthesizes the retrieved snippets into a clear, non-redundant answer streamed in real time.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your `OPENAI_API_KEY` to `.env`.

## Usage

```bash
# Run a single query
python main.py "What is the policy on international travel?"

# Start interactive CLI
python main.py

# Run test suite (also saves output screenshots to docs/screenshots/)
python tests/test_queries.py
```
