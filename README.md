# HR Policy Assistant --- Learning NeMo Guardrails

A beginner-friendly learning project for exploring **NVIDIA NeMo
Guardrails** in an AI application. It combines configurable guardrails,
retrieval-augmented generation (RAG), and a Streamlit interface to
demonstrate how safety checks can sit between a user's question and an
LLM response.

> **Learning/demo project:** This app uses illustrative Acme Corp HR
> policies. It is not an official HR system, and its safety checks
> cannot guarantee detection of every unsafe request or inaccurate
> answer. Do not use real employee data or confidential company
> information.

## Learning Goals

-   Understand what guardrails do in an LLM application.
-   Explore NeMo Guardrails configuration and conversational flows.
-   Experiment with input checks and custom actions.
-   Build a small RAG workflow with FAISS.
-   Retrieve relevant policy excerpts and use them as LLM context.
-   Inspect execution traces, retrieval results, latency, and errors.
-   Connect a Streamlit interface to a Python pipeline.

## Features

-   **Streamlit UI:** Chat interface, model selectors, and a policy
    browser.
-   **NeMo Guardrails:** Configurable flows and input checks.
-   **FAISS retrieval:** Searches the sample HR policy collection.
-   **Groq models:** Uses `ChatGroq` for guardrails and answer
    generation.
-   **Output checks:** Demonstrates regular-expression checks for
    selected sensitive content.
-   **Execution trace:** Captures timings, retrieved chunks, model
    details, and errors.

## Request Flow

``` text
User question
     |
     v
Input validation
     |
     v
NeMo Guardrails
  |          |
  | blocked  | allowed
  v          v
Safe reply   Retrieve policy excerpts (FAISS)
                 |
                 v
          Generate answer (Groq)
                 |
                 v
          Output pattern checks
                 |
                 v
             Final answer
```

This is the intended learning flow, not a security guarantee. Actual
behavior depends on your configured flows, NeMo version, and model
responses.

## Technology Stack

-   Python
-   Streamlit
-   NVIDIA NeMo Guardrails
-   LangChain and `langchain-groq`
-   FAISS vector store
-   FastEmbed embeddings: `BAAI/bge-small-en-v1.5`
-   Groq API

## Project Structure

``` text
.
├── app.py
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── src/
    ├── __init__.py
    ├── config.py       # Model choices, system prompt, output patterns
    ├── guards.py       # NeMo config, flows, PII action, response parsing
    ├── hr_docs.py      # Sample HR policy documents
    ├── pipeline.py     # Guardrails → retrieval → generation → output checks
    ├── rag.py          # Chunking, embeddings, FAISS index, retrieval
    └── ui/
        ├── __init__.py
        ├── landing.py
        ├── sidebar.py
        ├── tab_chat.py
        └── tab_docs.py
```

## Prerequisites

-   A Python version supported by the dependencies. Check
    `pyproject.toml` and `uv.lock`; Python 3.11 or 3.12 is a reasonable
    starting point if compatible.
-   A [Groq API key](https://console.groq.com/).
-   [`uv`](https://docs.astral.sh/uv/getting-started/installation/).
-   Internet access on first run to download the embedding model and
    call the Groq API.

## Setup

### 1. Get the project

If cloning from a repository, replace the placeholders with your
repository URL and folder name:

``` bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_PROJECT_DIRECTORY>
```

If the project is already on your computer, open a terminal in its root
directory.

### 2. Install dependencies with `uv`

If `pyproject.toml` and `uv.lock` are current:

``` bash
uv sync
```

Alternatively, install from `requirements.txt`:

``` bash
uv venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Activate the environment when running commands directly:

``` bash
source .venv/bin/activate
```

Use one dependency-management approach consistently. If installation
fails, check the Python version and dependency versions in
`pyproject.toml`, `requirements.txt`, and `uv.lock`.

### 3. Run the application

``` bash
streamlit run app.py
```

The app normally opens at <http://localhost:8501>.

### 4. Add your Groq API key

Enter the key in the **Groq API Key** field in the sidebar. The current
UI passes this key to both the guardrails and answer-generation calls.

**Never commit API keys** or paste them into source files, screenshots,
issue reports, or Git history. If a key is exposed, revoke it and create
a replacement.

### 5. Check model IDs

Model IDs are configured in `src/config.py`. Choose IDs currently
supported by your Groq account. Provider model availability changes;
unsupported IDs may cause API errors.

## Using the Application

1.  Start the app with `streamlit run app.py`.
2.  Enter your Groq API key in the sidebar.
3.  Choose models for the guardrails and answer-generation steps.
4.  In the Chat tab, ask a question about one of the sample HR policies.
5.  Inspect retrieved excerpts and the execution trace.
6.  Browse the sample policies in the Documents/Policies tab.
7.  Test allowed, blocked, off-topic, and unsupported-policy questions.

Example questions:

-   "How many annual leave days are provided in the sample policy?"
-   "What does the remote-work policy say?"
-   "What process is described for performance reviews?"
-   "Can you answer a question that is not covered by the supplied
    policies?"

Answers depend on the sample policy content, retrieval quality, model
behavior, and application logic.

## Explore NeMo Guardrails

Start with `src/guards.py`:

-   **`COLANG_CONTENT`:** Defines conversational flows and selected
    block, direct-response, and pass-through behavior.
-   **`YAML_CONTENT`:** Defines NeMo Guardrails configuration, including
    model and rail settings.
-   **`detect_pii`:** Demonstrates a custom action that checks text for
    selected PII-like patterns.
-   **`build_rails`:** Creates the configuration, initializes
    `LLMRails`, and registers the custom action.
-   **`parse_nemo_response`:** Interprets the response format to decide
    whether to block, return a direct response, or continue to RAG.

NeMo APIs and Colang syntax may vary by version. If configuration fails
to load, check the installed version and consult the official
documentation.

## Pipeline Overview

### 1. Input validation

`src/pipeline.py` checks that a question and API key are provided.

### 2. NeMo Guardrails

Configured flows run before retrieval. Depending on the response, the
pipeline may return a blocked message, return a direct response, or
continue to retrieval.

### 3. Retrieval-augmented generation

`src/rag.py` splits sample policies into chunks, embeds them, builds a
FAISS index, and retrieves excerpts relevant to the question.

### 4. Answer generation

Retrieved excerpts are inserted into the HR system prompt from
`src/config.py`. The prompt instructs the model to answer using the
supplied policy context and to direct employees to the configured HR
contact if the answer is not covered.

### 5. Output checks

`check_output()` applies regular-expression checks to generated text.
These checks are educational examples, not a substitute for robust
privacy controls, authorization, or security testing.

## Troubleshooting

### Groq returns a 404 or model-not-found error

-   Check the model ID in `src/config.py`.
-   Confirm that the model is available to your Groq account.
-   Select a supported model in the sidebar.

### NeMo configuration fails

-   Review `YAML_CONTENT` and `COLANG_CONTENT` in `src/guards.py`.
-   Confirm the installed NeMo Guardrails version supports the syntax.
-   Read the complete terminal traceback.
-   Verify compatibility between the configured model and the `ChatGroq`
    instance passed to `LLMRails`.

### Python cannot import a module

Run commands from the project root and check that the environment is
active:

``` bash
source .venv/bin/activate
python -c "import streamlit; print(streamlit.__version__)"
```

Reinstall dependencies using the dependency manager selected for the
project.

### First run is slow

The first run may download the embedding model and build the FAISS
index. Streamlit caching can reuse the vector store while the cache
remains valid.

### No relevant policy excerpt is returned

Try a more specific question and check that the policy exists in
`src/hr_docs.py`. Retrieval depends on document wording, chunk size,
overlap, embeddings, and similarity search.

## Learning Exercises

1.  **Observe the baseline:** Ask several HR-policy questions and
    inspect retrieved chunks.
2.  **Change a flow:** Modify one flow in `COLANG_CONTENT`, restart the
    app, and compare behavior.
3.  **Test PII checks:** Use synthetic examples only; never use real
    personal data.
4.  **Compare models:** Compare latency and behavior using models
    available to your account.
5.  **Tune retrieval:** Experiment with chunk size, overlap, and `k` in
    `src/rag.py`.
6.  **Add observability:** Instrument the pipeline with structured
    logging or Logfire, without logging API keys, personal data, or
    confidential prompts.
7.  **Build an evaluation set:** Record expected outcomes for allowed,
    blocked, off-topic, PII-like, and unsupported-policy questions.
8.  **Study failure modes:** Test provider outages and guardrails
    errors. The application should fail safely rather than silently
    bypassing the safety step.

## Security and Limitations

-   This is a learning project, not a production HR assistant.
-   The company and policy content are illustrative examples.
-   Pattern-based PII detection can miss sensitive data and can flag
    harmless text.
-   Guardrails do not guarantee that a model will follow policy or
    resist prompt injection.
-   Retrieved content and model output should be treated as untrusted
    until validated.
-   Use synthetic data; do not upload real employee records or
    confidential documents.
-   Before production use, add authentication, authorization, secret
    management, privacy-aware logging, evaluation, monitoring, and human
    review.
-   Follow the provider's terms and your organization's policies.

## Resources

-   [NVIDIA NeMo Guardrails
    documentation](https://docs.nvidia.com/nemo/guardrails/latest/)
-   [NeMo Guardrails GitHub
    repository](https://github.com/NVIDIA/NeMo-Guardrails)
-   [Groq Console](https://console.groq.com/)
-   [LangChain documentation](https://python.langchain.com/docs/)
-   [Streamlit documentation](https://docs.streamlit.io/)
-   [uv documentation](https://docs.astral.sh/uv/)

## License

Add a license before distributing the project publicly. Until a license
is added, do not assume others have permission to reuse, modify, or
redistribute the code.