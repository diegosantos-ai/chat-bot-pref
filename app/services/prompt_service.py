from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.settings import settings


@dataclass(frozen=True)
class PromptArtifact:
    version: str
    path: Path
    content: str


class PromptService:
    def __init__(
        self,
        *,
        prompts_dir: Path | None = None,
        base_version: str | None = None,
        fallback_version: str | None = None,
        policy_version: str | None = None,
    ) -> None:
        self.prompts_dir = prompts_dir or Path(__file__).resolve().parents[1] / "prompts"
        self.base_version = (base_version or settings.PROMPT_BASE_VERSION).strip()
        self.fallback_version = (fallback_version or settings.PROMPT_FALLBACK_VERSION).strip()
        self.policy_version = (policy_version or settings.POLICY_TEXT_VERSION).strip()

    def load_base_prompt(self) -> PromptArtifact:
        return self._load_prompt(self.base_version)

    def load_fallback_prompt(self) -> PromptArtifact:
        return self._load_prompt(self.fallback_version)

    def load_policy_text(self) -> PromptArtifact:
        return self._load_prompt(self.policy_version)

    def render_base_prompt(
        self,
        *,
        bot_name: str,
        client_name: str,
        question: str,
        context_block: str,
        institutional_voice: str,
    ) -> PromptArtifact:
        artifact = self.load_base_prompt()
        rendered = artifact.content.format(
            bot_name=bot_name,
            client_name=client_name,
            question=question,
            context_block=context_block,
            institutional_voice=institutional_voice,
        )
        return PromptArtifact(version=artifact.version, path=artifact.path, content=rendered)

    def render_fallback_prompt(
        self,
        *,
        bot_name: str,
        client_name: str,
        question: str,
        reason_code: str,
        policy_summary: str,
    ) -> PromptArtifact:
        artifact = self.load_fallback_prompt()
        rendered = artifact.content.format(
            bot_name=bot_name,
            client_name=client_name,
            question=question,
            reason_code=reason_code,
            policy_summary=policy_summary,
        )
        return PromptArtifact(version=artifact.version, path=artifact.path, content=rendered)

    def _load_prompt(self, version: str) -> PromptArtifact:
        candidates = [
            self.prompts_dir / f"{version}.txt",
            self.prompts_dir / f"{version}.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                return PromptArtifact(
                    version=version,
                    path=candidate,
                    content=candidate.read_text(encoding="utf-8"),
                )
        raise FileNotFoundError(f"Prompt/policy versionado nao encontrado: {version}")
