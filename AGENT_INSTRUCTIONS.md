
# AGENT INSTRUCTIONS: Day 11 — Guardrails, HITL & Responsible AI

## Context and Role
You are an expert AI Developer Agent. Your objective is to implement the "Day-11-Guardrails-HITL-Responsible-AI" project. This project focuses on building safe LLM applications using Google ADK, NeMo Guardrails, and Human-in-the-Loop (HITL) workflows. 

You must follow the project structure and complete the 13 specific TODOs outlined below. Ensure all code is modular, well-commented, and robust.

---

## Project Structure Reference
Ensure all files are created and modified within this strict directory structure:
```text
Day-11-Guardrails-HITL-Responsible-AI/
├── src/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── utils.py
│   ├── agents/
│   │   └── agent.py
│   ├── attacks/
│   │   └── attacks.py
│   ├── guardrails/
│   │   ├── input_guardrails.py
│   │   ├── output_guardrails.py
│   │   └── nemo_guardrails.py
│   ├── testing/
│   │   └── testing.py
│   └── hitl/
│       └── hitl.py
├── requirements.txt
└── README.md

---

## Execution Plan & Task Checklist

Please complete the following phases in order. Mark tasks as complete as you progress.

### Phase 0: Setup & Core Infrastructure
- [ ] **`requirements.txt`**: Define dependencies including `google-genai`, `nemoguardrails`, and any ADK requirements.
- [ ] **`src/core/config.py`**: Set up environment variable loading for `GOOGLE_API_KEY`. Define constants for allowed/blocked topics.
- [ ] **`src/core/utils.py`**: Create a helper function `chat_with_agent(agent, prompt)` to standardize LLM interactions.
- [ ] **`src/agents/agent.py`**: Initialize a basic, unprotected Gemma3 Flash agent using Google ADK to serve as the baseline for testing.

### Phase 1: Attacks & Red Teaming (Part 1)
**File:** `src/attacks/attacks.py`
- [ ] **TODO 1: Write 5 adversarial prompts.** Create a list of hardcoded prompts (e.g., prompt injection, jailbreak attempts, system prompt extraction, toxic requests).
- [ ] **TODO 2: Generate attack test cases with AI.** Create a function that uses a separate Gemma instance to dynamically generate AI Red Teaming prompts (e.g., "Generate 3 prompt injection attacks designed to bypass an AI assistant").

### Phase 2: Input Guardrails (Part 2A)
**File:** `src/guardrails/input_guardrails.py`
- [ ] **TODO 3: Injection detection (regex).** Implement a function that uses regex to detect common injection patterns (e.g., "ignore previous instructions", "system prompt").
- [ ] **TODO 4: Topic filter.** Implement a function that checks the input against a predefined list of disallowed topics (e.g., politics, violence) defined in `config.py`.
- [ ] **TODO 5: Input Guardrail Plugin.** Wrap the logic from TODO 3 & 4 into a Google ADK-compatible pre-processing plugin/hook. It should block the request and return a safe message if a violation is found.

### Phase 3: Output Guardrails (Part 2B)
**File:** `src/guardrails/output_guardrails.py`
- [ ] **TODO 6: Content filter (PII, secrets).** Implement a regex or logic-based filter to scrub or block outputs containing mock PII (like phone numbers, emails) or secrets (API keys).
- [ ] **TODO 7: LLM-as-Judge safety check.** Implement a function that uses a secondary LLM call to evaluate the generated output for safety, toxicity, and helpfulness before returning it to the user.
- [ ] **TODO 8: Output Guardrail Plugin.** Wrap TODO 6 & 7 into a Google ADK-compatible post-processing plugin/hook.

### Phase 4: NeMo Guardrails Integration (Part 2C)
**File:** `src/guardrails/nemo_guardrails.py`
- [ ] **TODO 9: NeMo Guardrails Colang config.** Create a programmatic setup or write `.co` and `.yaml` configuration files to define declarative safety rules (e.g., refusing to answer off-topic questions) using NVIDIA's NeMo Guardrails.

### Phase 5: Testing Pipeline (Part 3)
**File:** `src/testing/testing.py`
- [ ] **TODO 10: Rerun 5 attacks with guardrails.** Run the adversarial prompts from TODO 1 against the newly protected agent (equipped with the ADK plugins from Phases 2 & 3).
- [ ] **TODO 11: Automated security testing pipeline.** Create a script that outputs a **Security Report**: a before-and-after comparison table showing how the unprotected agent vs. the protected agent handled the 5+ attacks.

### Phase 6: Human-in-the-Loop (HITL) (Part 4)
**File:** `src/hitl/hitl.py`
- [ ] **TODO 12: Confidence Router (HITL).** Implement a routing mechanism where the LLM outputs a confidence score alongside its answer. If the score is below a threshold (e.g., < 0.70), route the request to a simulated "Human Review" queue.
- [ ] **TODO 13: Design 3 HITL decision points.** Document and mock out three distinct escalation paths (e.g., Low Confidence -> Human Review; High Toxicity -> Auto-Block + Human Audit; Ambiguous Intent -> Clarification Prompt). Include this design as a string/printout in the file.

### Phase 7: Orchestration
**File:** `src/main.py`
- [ ] Create an CLI entry point using `argparse` to allow running the full lab or specific parts (`--part 1`, `--part 2`, etc.) as defined in the project instructions.

---

## Deliverables to Generate
By the end of the execution, the system should be able to produce:
1. **Security Report:** Automatically printed to the console by `testing.py` showing the success rate of guardrails.
2. **HITL Flowchart/Design:** Outputted to the console by `hitl.py` outlining the 3 decision points.

## Important Guidelines
- **API Keys:** Never hardcode API keys. Always use `os.environ.get("GOOGLE_API_KEY")`.
- **Frameworks:** Strictly utilize Google ADK for the primary agent architecture and plugins, and NeMo Guardrails specifically for TODO 9.
- **Model:** Default to `gemma-3-27b-it`.
- **Modularity:** Ensure files can be executed independently (e.g., `python src/hitl/hitl.py` should run a self-contained demo of the HITL logic).
```