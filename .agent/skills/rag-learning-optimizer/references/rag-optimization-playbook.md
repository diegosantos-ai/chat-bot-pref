# RAG Optimization Playbook

## 1. Objective Metrics

- Retrieval: `recall@k`, `precision@k`, `mrr`, coverage by intent
- Generation: groundedness, factual accuracy, citation correctness
- Operations: latency p95, cost/request, fallback rate
- Safety: policy violation rate, crisis/offensive false negatives

## 2. Standard Diagnosis Matrix

| Symptom | Probable Root Cause | First Fix |
|---|---|---|
| Correct docs rarely retrieved | embedding mismatch, poor chunking | retune chunk size + test alternate embedding |
| Relevant docs retrieved but answer wrong | prompt hierarchy weak | enforce grounded template + citation |
| Many hallucinations on sparse topics | low evidence threshold | add stricter fallback and confidence gate |
| Inconsistent public vs inbox responses | missing channel policy | split response templates by surface |
| Performance regresses after content update | stale index | incremental re-index + smoke set |

## 3. Retrieval Engineering Baseline

1. Keep chunks semantically coherent (headings + bullet groups).
2. Preserve metadata (`source_id`, `section`, `updated_at`, `intent`).
3. Apply hybrid retrieval (BM25 + vector) for recall stability.
4. Add reranking for precision on long documents.
5. Use hard-negative evaluation queries before production deploy.

## 4. Answer Composition Baseline

1. Follow strict order: answer -> evidence -> redirect/fallback when needed.
2. Prohibit unsupported claims.
3. Always disclose uncertainty when confidence is low.
4. Keep deterministic legal/safety disclaimers required by policy.
5. Prefer short, direct language for public channels.

## 5. Evaluation Protocol

1. Build a fixed benchmark set by intent and risk.
2. Evaluate offline on every major change.
3. Run online canary with guardrails and rollback thresholds.
4. Review failure clusters weekly and feed backlog.

## 6. Suggested Release Gates

- `recall@5 >= 0.80` on core intents
- groundedness >= 0.95 on policy-sensitive intents
- no increase in safety violations
- latency/cost increase within agreed budget
