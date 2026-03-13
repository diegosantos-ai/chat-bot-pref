"""
Prompt Loader — Nexo Basis Governador SaaS
==========================================
Versão: v2.0
Escopo: SAAS_MULTI_TENANT

Carrega e gerencia prompts do sistema com suporte a:
- Substituição de placeholders por variáveis do tenant ({{bot_name}}, {{client_name}}, etc.)
- Seleção aleatória de variações sem repetição por sessão

Uso básico (com variáveis de tenant injetadas automaticamente):
    from app.prompts import get_tenant_prompt
    text = await get_tenant_prompt("greeting")

Uso manual (sem tenant context, ex: testes):
    from app.prompts import get_prompt
    text = get_prompt("greeting", variables={"bot_name": "TestBot"})
"""

import os  # noqa: F401
import json
import random
import logging
from pathlib import Path
from typing import Optional, List, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)

# Diretório base dos prompts
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "v1"


class PromptVariationTracker:
    """
    Rastreia variações usadas para evitar repetição.
    Mantém histórico por sessão.
    """
    
    def __init__(self, max_history: int = 5):
        self.max_history = max_history
        self._history: Dict[str, List[int]] = {}  # {session_id: [índices usados]}
    
    def get_random_variation(
        self,
        variations: List[str],
        session_id: str,
        prompt_key: str,
    ) -> str:
        """
        Retorna uma variação aleatória evitando repetição recente.
        
        Args:
            variations: Lista de variações disponíveis
            session_id: ID da sessão para rastreamento
            prompt_key: Chave do prompt (ex: "public_ack")
            
        Returns:
            Texto da variação selecionada
        """
        key = f"{session_id}:{prompt_key}"
        
        if key not in self._history:
            self._history[key] = []
        
        used_indices = self._history[key]
        available_indices = [
            i for i in range(len(variations))
            if i not in used_indices
        ]
        
        # Se usou todas, reseta o histórico
        if not available_indices:
            available_indices = list(range(len(variations)))
            self._history[key] = []
        
        # Seleciona aleatoriamente
        selected_idx = random.choice(available_indices)
        
        # Atualiza histórico
        self._history[key].append(selected_idx)
        if len(self._history[key]) > self.max_history:
            self._history[key].pop(0)
        
        return variations[selected_idx]
    
    def clear_session(self, session_id: str) -> None:
        """Limpa histórico de uma sessão."""
        keys_to_remove = [k for k in self._history if k.startswith(f"{session_id}:")]
        for key in keys_to_remove:
            del self._history[key]


# Instância global do tracker
_variation_tracker = PromptVariationTracker()


def parse_variations_file(content: str) -> List[str]:
    """
    Parseia arquivo de variações.
    Linhas começando com "- " são variações.
    Linhas em branco ou com "#" são ignoradas.
    
    Args:
        content: Conteúdo do arquivo
        
    Returns:
        Lista de variações
    """
    variations = []
    
    for line in content.split("\n"):
        line = line.strip()
        
        # Ignora linhas vazias e comentários
        if not line or line.startswith("#"):
            continue
        
        # Variações começam com "- "
        if line.startswith("- "):
            variation = line[2:].strip()
            if variation:
                variations.append(variation)
    
    return variations


@lru_cache(maxsize=32)
def load_prompt(prompt_key: str) -> str:
    """
    Carrega um prompt do sistema de arquivos.
    Usa cache para evitar I/O repetido.
    
    Args:
        prompt_key: Chave do prompt (ex: "system", "fallback")
        
    Returns:
        Conteúdo do prompt
    """
    file_path = PROMPTS_DIR / f"{prompt_key}.txt"
    
    if not file_path.exists():
        logger.error(f"Prompt não encontrado: {file_path}")
        raise FileNotFoundError(f"Prompt '{prompt_key}' não encontrado")
    
    return file_path.read_text(encoding="utf-8")


def load_manifest() -> dict:
    """Carrega o manifest de prompts."""
    manifest_path = PROMPTS_DIR / "manifest.json"
    
    if not manifest_path.exists():
        logger.error("Manifest de prompts não encontrado")
        raise FileNotFoundError("manifest.json não encontrado")
    
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def get_prompt(
    prompt_key: str,
    variables: Optional[Dict[str, str]] = None,
    session_id: Optional[str] = None,
) -> str:
    """
    Obtém um prompt, aplicando variáveis e selecionando variações.
    
    Args:
        prompt_key: Chave do prompt
        variables: Dicionário de variáveis para substituir
        session_id: ID da sessão (para variações sem repetição)
        
    Returns:
        Texto do prompt processado
    """
    content = load_prompt(prompt_key)
    manifest = load_manifest()
    
    prompt_config = manifest.get("prompts", {}).get(prompt_key, {})
    prompt_type = prompt_config.get("type", "single")
    
    # Se for tipo variações, seleciona uma
    if prompt_type == "variations":
        variations = parse_variations_file(content)
        
        if not variations:
            logger.warning(f"Nenhuma variação encontrada em {prompt_key}")
            return content
        
        selection_mode = prompt_config.get("selection_mode", "random")
        
        if selection_mode == "random_no_repeat" and session_id:
            content = _variation_tracker.get_random_variation(
                variations, session_id, prompt_key
            )
        else:
            content = random.choice(variations)
    
    # Aplica variáveis
    if variables:
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            content = content.replace(placeholder, str(value))
    
    return content


def get_public_ack(session_id: str) -> tuple[str, str]:
    """
    Obtém resposta de agradecimento público com ID da variação.
    Atalho para get_prompt("public_ack", ...) com rastreamento.
    
    Args:
        session_id: ID da sessão para evitar repetição
        
    Returns:
        Tupla (texto_ack, choice_id)
    """
    content = load_prompt("public_ack")
    variations = parse_variations_file(content)
    
    if not variations:
        return content, "ack_default"
    
    # Usa tracker para evitar repetição
    key = f"{session_id}:public_ack"
    
    if key not in _variation_tracker._history:
        _variation_tracker._history[key] = []
    
    used_indices = _variation_tracker._history[key]
    available_indices = [
        i for i in range(len(variations))
        if i not in used_indices
    ]
    
    # Se usou todas, reseta o histórico
    if not available_indices:
        available_indices = list(range(len(variations)))
        _variation_tracker._history[key] = []
    
    # Seleciona aleatoriamente
    selected_idx = random.choice(available_indices)
    
    # Atualiza histórico
    _variation_tracker._history[key].append(selected_idx)
    if len(_variation_tracker._history[key]) > _variation_tracker.max_history:
        _variation_tracker._history[key].pop(0)
    
    choice_id = f"ack_v{selected_idx + 1}"
    return variations[selected_idx], choice_id


def get_greeting() -> str:
    """Obtém saudação."""
    return get_prompt("greeting")


def get_fallback() -> str:
    """Obtém mensagem de fallback."""
    return get_prompt("fallback")


def get_blocked() -> str:
    """Obtém mensagem de bloqueio."""
    return get_prompt("blocked")


def get_escalate() -> str:
    """Obtém mensagem de escalonamento."""
    return get_prompt("escalate")


# ============================================================
# API MULTI-TENANT: prompts com vars do tenant injetadas
# ============================================================

async def get_tenant_prompt(
    prompt_key: str,
    session_id: Optional[str] = None,
    extra_vars: Optional[Dict[str, str]] = None,
) -> str:
    """
    Versão multi-tenant de `get_prompt`.

    Busca automaticamente as variáveis de identidade do tenant ativo
    (bot_name, client_name, contact_phone, etc.) e substitui os
    placeholders {{variable}} no template do prompt.

    Args:
        prompt_key: Chave do prompt (ex: "greeting", "fallback").
        session_id: ID de sessão para controle de variações sem repetição.
        extra_vars: Variáveis adicionais a injetar além das do tenant.

    Returns:
        Texto do prompt com todos os placeholders substituídos.
    """
    from app.tenant_config import get_prompt_vars

    tenant_vars = await get_prompt_vars()
    variables = {**tenant_vars, **(extra_vars or {})}

    return get_prompt(prompt_key, variables=variables, session_id=session_id)

