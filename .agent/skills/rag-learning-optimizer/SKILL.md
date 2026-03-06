---
name: rag-learning-optimizer
description: Improve RAG systems, model training loops, and assistant learning quality. Use when optimizing retrieval precision/recall, reducing hallucination, designing evaluation datasets, improving prompt and response behavior, planning fine-tuning, or setting continuous feedback automation for chatbot performance.
---

# RAG Learning Optimizer

Execute a disciplined improvement loop for RAG quality, model behavior, and response outcomes.

## Workflow

1. Define target outcomes and constraints.
- Set objective metrics: `hit@k`, groundedness, factual accuracy, fallback rate, escalation rate, latency, and cost.
- Split goals by channel/surface and risk level.

2. Build an evidence baseline before changing anything.
- Collect recent failures and representative successes.
- Sample at least: in-domain FAQs, ambiguous queries, out-of-scope prompts, policy-sensitive prompts.
- Use `scripts/rag_eval_report.py` for a quick baseline summary.

3. Diagnose by layer, not by guess.
- Retrieval issues: low recall, wrong chunk granularity, stale docs, poor filters, weak embeddings.
- Generation issues: weak instruction hierarchy, missing citations, verbosity drift, bad refusal style.
- Guardrail issues: overblocking, underblocking, unsafe edge-case leakage.

4. Improve retrieval first.
- Normalize and enrich documents (titles, section headers, canonical IDs, timestamps).
- Tune chunking (`chunk_size`, overlap, semantic boundaries).
- Add hybrid retrieval (dense + lexical) and optional reranking.
- Calibrate `top_k` and minimum score thresholds using offline evaluation.

5. Improve generation and interaction policy.
- Force grounded answer style with source references.
- Add explicit uncertainty/fallback behaviors.
- Apply concise response templates per intent and channel.
- Keep safety and legal disclaimers deterministic where required.

6. Improve learning loop and training.
- Curate supervised pairs from audited interactions.
- Use hard negatives for retrieval training/evaluation.
- Prefer low-risk adaptation path:
  - Prompt + retrieval tuning first
  - Small adapter/SFT second
  - Preference optimization only with clear reward rubric
- Keep train/validation/test splits isolated by intent and period.

7. Automate quality gates.
- Block deploy if groundedness or safety regresses beyond tolerance.
- Track regression dashboards per release (`quality`, `latency`, `cost`).
- Schedule periodic drift checks (new policies, seasonal intent shifts).

## Output Contract

When using this skill, always deliver:

1. Diagnosis table by layer (`retrieval`, `generation`, `policy`, `data`).
2. Prioritized action plan with effort/impact/risk.
3. Evaluation plan (offline + online) with acceptance thresholds.
4. Rollout strategy (`canary`, rollback trigger, monitoring).

## References

- Retrieval, evaluation, and automation patterns: `references/rag-optimization-playbook.md`
- Training and continual-learning patterns: `references/model-training-playbook.md`

## Script

Use `scripts/rag_eval_report.py` to generate quick offline metrics from JSONL traces.

