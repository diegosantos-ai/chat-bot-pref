"""
Query Expander - Expande queries para melhorar busca RAG

Combina:
1. Expansão de sinônimos (postinho → PSF, UBS)
2. Normalização de texto (abreviações, erros)
3. Termos relacionados
"""

from dataclasses import dataclass, field

from app.nlp.synonyms import find_related_terms, get_canonical
from app.nlp.normalizer import normalize_text


@dataclass
class ExpandedQuery:
    """Resultado da expansão de query."""
    original: str
    normalized: str
    expanded_terms: list[str] = field(default_factory=list)
    canonical_terms: list[str] = field(default_factory=list)
    search_query: str = ""  # Query final para busca
    

class QueryExpander:
    """
    Expande queries de usuários para melhorar recuperação RAG.
    
    Estratégias:
    1. Normaliza texto (expande abreviações, corrige erros)
    2. Identifica termos com sinônimos
    3. Expande para incluir termos canônicos
    4. Gera query otimizada para busca vetorial
    """
    
    def __init__(self, add_canonical_only: bool = True):
        """
        Args:
            add_canonical_only: Se True, adiciona só termo canônico.
                              Se False, adiciona todos os sinônimos.
        """
        self.add_canonical_only = add_canonical_only
    
    def expand(self, query: str) -> ExpandedQuery:
        """
        Expande uma query de usuário.
        
        Args:
            query: Query original do usuário
            
        Returns:
            ExpandedQuery com termos expandidos
            
        Example:
            >>> expander = QueryExpander()
            >>> result = expander.expand("onde fica o postinho?")
            >>> result.canonical_terms
            ["PSF"]
            >>> result.search_query
            "onde fica o postinho PSF posto de saúde UBS"
        """
        # 1. Normaliza
        normalized = normalize_text(query, expand_abbrev=True, fix_typos=True)
        
        # 2. Encontra termos relacionados
        related = find_related_terms(normalized)
        
        # 3. Extrai termos canônicos e sinônimos úteis
        canonical_terms = []
        expanded_terms = []
        normalized_lower = normalized.lower()
        
        # Termos prioritários para busca (relacionados ao tema principal)
        priority_terms = []
        secondary_terms = []
        
        for found_term, synonyms in related.items():
            # Se o termo encontrado é um sinônimo, pega o canônico
            canonical = get_canonical(found_term)
            if canonical:
                canonical_terms.append(canonical)
            
            # Determina se este termo é "prioritário" (relacionado ao tema principal)
            # Termos de serviço específico são prioritários sobre localização genérica
            is_priority = any(kw in found_term.lower() for kw in [
                # Horários/Atendimento
                "horário", "horario", "funcionamento", "atendimento", "plantão",
                # Saúde
                "saúde", "saude", "vacina", "psf", "posto", "postinho",
                # Documentos/Tributos
                "documento", "imposto", "certidão", "certidao", "iptu",
                # Infraestrutura
                "obra", "obras", "asfalto", "paviment", "ilumina", "buraco", "lixo",
                # Contatos
                "telefone", "contato", "e-mail", "email", "endereço", "endereco",
            ])
            
            # Filtra sinônimos - prioriza termos DIFERENTES da query
            found_term_base = found_term.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
            
            for syn in synonyms:
                syn_lower = syn.lower()
                syn_base = syn_lower.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
                
                # Ignora sinônimos que são apenas variações do termo original
                if syn_base == found_term_base:
                    continue
                # Ignora sinônimos que já estão na query
                if syn_lower in normalized_lower:
                    continue
                # Ignora termos muito curtos ou muito longos
                if len(syn) < 3 or len(syn) > 30:
                    continue
                
                if is_priority:
                    priority_terms.append(syn)
                else:
                    secondary_terms.append(syn)
        
        # Combina: prioritários primeiro, depois secundários
        expanded_terms = priority_terms + secondary_terms
        
        # 4. Monta query de busca
        search_parts = [normalized]
        
        # Adiciona termos canônicos (termo principal)
        search_parts.extend(canonical_terms)
        
        # Adiciona sinônimos úteis: mais termos prioritários, menos secundários
        useful_synonyms = priority_terms[:3] + secondary_terms[:1]
        search_parts.extend(useful_synonyms)
        
        # Remove duplicatas mantendo ordem
        seen = set()
        unique_parts = []
        for part in search_parts:
            part_lower = part.lower()
            if part_lower not in seen:
                seen.add(part_lower)
                unique_parts.append(part)
        
        search_query = " ".join(unique_parts)
        
        return ExpandedQuery(
            original=query,
            normalized=normalized,
            expanded_terms=expanded_terms,
            canonical_terms=canonical_terms,
            search_query=search_query,
        )
    
    def expand_for_rag(self, query: str) -> str:
        """
        Versão simplificada que retorna apenas a query expandida.
        
        Args:
            query: Query original
            
        Returns:
            Query expandida para busca RAG
        """
        return self.expand(query).search_query


# Singleton
_expander: QueryExpander | None = None


def get_query_expander() -> QueryExpander:
    """Retorna instância singleton do expansor."""
    global _expander
    if _expander is None:
        _expander = QueryExpander()
    return _expander


def expand_query(query: str) -> str:
    """
    Função de conveniência para expandir query.
    
    Args:
        query: Query original
        
    Returns:
        Query expandida
        
    Example:
        >>> expand_query("onde fica o postinho de saude?")
        "Onde fica o postinho de saúde? PSF UBS"
    """
    return get_query_expander().expand_for_rag(query)
