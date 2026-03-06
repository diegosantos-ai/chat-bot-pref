# Model Training Playbook

## 1. Data Strategy

1. Log structured traces: user query, retrieved docs, final answer, policy decision, feedback.
2. Label failures by category: retrieval miss, hallucination, policy error, bad UX.
3. Build training sets with balanced intents and edge cases.
4. Keep separate time-based splits to detect drift.

## 2. Training Ladder (Low Risk to High Risk)

1. Prompt and retrieval tuning.
2. Supervised fine-tuning with high-quality corrected answers.
3. Preference optimization (DPO/RLAIF) only with stable rubric and reviewer alignment.
4. Full retraining only if architecture shift is required.

## 3. Quality Rubric for Supervision

- Groundedness: statement backed by retrieved evidence.
- Completeness: directly answers the user request.
- Safety: no prohibited medical/legal/administrative commitment.
- Tone: clear, concise, public-sector appropriate.
- Actionability: includes correct redirect when transactional handling is needed.

## 4. Continuous Learning Loop

1. Capture live feedback and unresolved escalations.
2. Batch weekly triage of top failure clusters.
3. Convert validated fixes into:
- knowledge-base updates
- prompt changes
- new training examples
4. Re-evaluate benchmark and compare against last release.

## 5. Governance

- Version datasets, prompts, and model configs.
- Store experiment cards with: hypothesis, changes, metrics, decision.
- Require rollback plan before online rollout.
