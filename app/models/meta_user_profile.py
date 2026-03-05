"""
Modelo de Cache de Perfis Meta — Pilot Atendimento MVE
=======================================================
Versão: v1.0
Escopo: Cache de perfis Instagram/Facebook

Modelo Pydantic para cache de perfis de usuários do Instagram/Facebook.
Usado para evitar chamadas repetidas à API da Meta.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MetaUserProfile(BaseModel):
    """
    Perfil de usuário do Instagram/Facebook cacheado.

    Armazena informações públicas do perfil para identificação
    em casos de escalation ou necessidade de contato humano.
    """

    id: Optional[int] = Field(None, description="ID interno no banco de dados")
    platform_user_id: str = Field(
        ...,
        description="ID do usuário na plataforma (Instagram/Facebook)",
        examples=["17841413792837146", "1234567890"],
    )
    platform: str = Field(
        ..., description="Plataforma de origem", examples=["instagram", "facebook"]
    )
    username: Optional[str] = Field(
        None,
        description="Username/handle do usuário",
        examples=["prefeitura_sto", "joaodasilva"],
    )
    name: Optional[str] = Field(
        None,
        description="Nome completo do perfil",
        examples=["João da Silva", "Prefeitura de Santa Tereza"],
    )
    profile_picture_url: Optional[str] = Field(
        None, description="URL da foto de perfil"
    )
    created_at: Optional[datetime] = Field(
        None, description="Data de criação do registro"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Data da última atualização"
    )

    class Config:
        """Configuração do modelo."""

        json_schema_extra = {
            "example": {
                "platform_user_id": "17841413792837146",
                "platform": "instagram",
                "username": "prefeitura_sto",
                "name": "Prefeitura de Santa Tereza do Oeste",
                "profile_picture_url": "https://instagram.com/...",
                "created_at": "2026-02-14T22:00:00Z",
                "updated_at": "2026-02-14T22:00:00Z",
            }
        }

    @property
    def display_name(self) -> str:
        """
        Retorna o nome de exibição do usuário.
        Prioridade: name > username > platform_user_id
        """
        if self.name:
            return self.name
        if self.username:
            return f"@{self.username}"
        return f"ID: {self.platform_user_id}"

    @property
    def contact_info(self) -> str:
        """
        Retorna informações de contato formatadas para email.
        """
        parts = []
        if self.username:
            parts.append(f"@{self.username}")
        if self.name and self.name != self.username:
            parts.append(f"({self.name})")
        if not parts:
            parts.append(f"ID: {self.platform_user_id}")

        platform_label = "Instagram" if self.platform == "instagram" else "Facebook"
        parts.append(f"- {platform_label}")

        return " ".join(parts)


class MetaUserProfileCreate(BaseModel):
    """Dados para criar um novo perfil cacheado."""

    platform_user_id: str
    platform: str
    username: Optional[str] = None
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None
