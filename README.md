# Agent Evaluations Labs

This repository contains hands-on labs teaching agent evaluation patterns for the Applied Generative AI course (DSAN 6725). Learn how to evaluate AI agents using ground truth comparison, automated metrics, and evaluation frameworks.

## Available Labs

### Lab 1: Simple Agent Evals with Braintrust

Build a multi-tool agent and evaluate it using Braintrust autoevals and custom scorers.

**What You'll Learn**:
- Building a Strands agent with search, weather, and directions tools
- Designing evaluation datasets for multi-tool agents
- Using Braintrust `Eval()` for offline evaluation
- Built-in LLM-as-judge scorers (Factuality, ClosedQA)
- Writing custom heuristic scorers (tool selection, response completeness, latency)

### Lab 2: Multi-Turn Agent Evals with ActorSimulator

Evaluate a customer support agent through realistic multi-turn conversations
using Strands ActorSimulator and diverse user personas.

**What You'll Learn**:
- Building a customer support agent with mock backend tools
- Using Strands ActorSimulator to simulate user personas (polite, demanding, confused)
- Multi-turn conversation evaluation with goal completion detection
- Custom scorers for conversation quality, policy adherence, and turn efficiency
- tau-bench-style evaluation patterns for customer service domains

## Overview

Evaluating AI agents is significantly harder than evaluating standard LLM outputs. Agents have multi-step reasoning, tool usage, and non-deterministic execution paths. These labs teach you practical approaches to agent evaluation using both manual ground truth comparison and automated frameworks.

## Prerequisites

- Python 3.11+
- Anthropic API key: https://console.anthropic.com/
- Braintrust account (free tier): https://www.braintrust.dev/

## Quick Start

### 1. Install uv (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### 2. Clone and Install Dependencies

```bash
cd agents-evals
uv sync
```

### 3. Lab 1 - Simple Agent Evals

1. Get API keys:
   - Anthropic: https://console.anthropic.com/
   - Braintrust: https://www.braintrust.dev/
2. Configure:
   ```bash
   cd simple-agent-evals
   cp .env.example .env
   # Edit .env and add:
   #   ANTHROPIC_API_KEY
   #   BRAINTRUST_API_KEY
   #   BRAINTRUST_PROJECT
   ```
3. Run the agent:
   ```bash
   uv run python agent.py
   ```
4. Run evaluations:
   ```bash
   uv run python eval.py 2>&1 | tee debug.log
   ```

### 4. Lab 2 - Multi-Turn Agent Evals

1. Configure:
   ```bash
   cd multi-turn-agent-evals
   cp .env.example .env
   # Edit .env with your API keys
   ```
2. Run evaluations:
   ```bash
   uv run python eval.py 2>&1 | tee debug.log
   ```

## Project Structure

```
agents-evals/
├── README.md                              # This file
├── pyproject.toml                         # Shared dependencies
│
├── simple-agent-evals/                    # Lab 1: Braintrust Evals
│   ├── agent.py                           # Multi-tool agent (search, weather, directions)
│   ├── eval.py                            # Braintrust evals with autoevals + custom scorers
│   ├── dataset.json                       # 25 test cases across tool categories
│   ├── README.md                          # Setup and usage guide
│   └── .env.example                       # Environment template
│
├── multi-turn-agent-evals/                # Lab 2: Multi-Turn Conversation Evals
│   ├── agent.py                           # Customer support agent (5 tools)
│   ├── eval.py                            # Multi-turn eval with ActorSimulator
│   ├── tools.py                           # Mock backend tools (orders, products, returns)
│   ├── scenarios.json                     # 10 conversation scenarios with personas
│   ├── README.md                          # Setup and usage guide
│   └── .env.example                       # Environment template
│
└── agent-evaluation-theory.md             # Theory: online/offline evals, scorer types
```

## Key Concepts

For a deep dive into evaluation theory, scoring approaches, and framework comparisons, see [Agent Evaluation Theory](agent-evaluation-theory.md).

### Why Agent Evaluations Are Hard

- **Non-deterministic execution**: Agents may take different paths to the same answer
- **Multi-step reasoning**: Evaluating intermediate steps, not just final output
- **Tool use correctness**: Did the agent call the right tools with the right parameters?
- **Partial credit**: Agent may get some steps right but not others
- **Statefulness**: Agent behavior depends on conversation history
- **Cost vs quality tradeoffs**: More tool calls may improve quality but increase cost

### Evaluation Approaches

- **Ground Truth Comparison**: Compare agent outputs against known correct answers
- **LLM-as-Judge**: Use a capable LLM to assess agent outputs for quality, relevance, and correctness
- **Custom Evaluators**: Build domain-specific evaluators tailored to your use case (e.g., medical accuracy, legal compliance, financial reasoning)
- **Heuristic Metrics**: Programmatic checks like exact match, keyword presence, JSON validity, latency, and token usage

## Resources

- [Strands Documentation](https://strandsagents.com/)
- [Braintrust Documentation](https://www.braintrust.dev/docs)
- [OpenTelemetry GenAI Semantics](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Anthropic Claude Documentation](https://docs.anthropic.com/)
- [Amazon Bedrock AgentCore Evals](https://docs.aws.amazon.com/agentcore/latest/userguide/eval-metrics.html)
- [Princeton HAL (Holistic Agent Leaderboard)](https://hal.cs.princeton.edu/)
