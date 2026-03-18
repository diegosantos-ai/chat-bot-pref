from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class ReasonCode(str, Enum):
    # Success/Normal
    SUCCESS_NORMAL = "SUCCESS_NORMAL"
    SUCCESS_FALLBACK = "SUCCESS_FALLBACK"

    # Limitations
    LIMIT_CONTEXT_INSUFFICIENT = "LIMIT_CONTEXT_INSUFFICIENT"

    # Blocks
    BLOCK_POLICY_PRE = "BLOCK_POLICY_PRE"
    BLOCK_POLICY_POST = "BLOCK_POLICY_POST"

    # Failures
    FAILURE_PROVIDER_TRANSITIVE = "FAILURE_PROVIDER_TRANSITIVE"
    FAILURE_INTERNAL = "FAILURE_INTERNAL"


class DecisionStatus(str, Enum):
    PASSED = "PASSED"
    BLOCKED = "BLOCKED"
    DEGRADED = "DEGRADED"


class PromptEvidence(BaseModel):
    version: str | None = None
    name: str | None = None


class PolicyEvidence(BaseModel):
    version: str | None = None
    applied_rules: list[str] = Field(default_factory=list)


class RetrievalEvidence(BaseModel):
    strategy: str | None = None
    documents_retrieved: int = 0
    version: str | None = None


class AuditEvidence(BaseModel):
    """
    Contrato da Trilha de Evidência Operacional.
    Esta estrutura deve focar na rastreabilidade e explicabilidade da decisão.
    Não mistura com experimental tracking metric (ex: não tem precision, relevancy, ou tempo em ms aqui).
    """
    request_id: str
    tenant_id: str
    decision_status: DecisionStatus
    reason_code: ReasonCode

    prompt: PromptEvidence = Field(default_factory=PromptEvidence)
    policy: PolicyEvidence = Field(default_factory=PolicyEvidence)
    retrieval: RetrievalEvidence = Field(default_factory=RetrievalEvidence)

    provider_metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
