"""
Analytics & Metrics Module — Pilot Atendimento MVE
==================================================
Coleta dados sobre sucesso/falha das buscas RAG para identificar gaps.

Responsabilidades:
- Registrar cada query + resultado da busca
- Rastrear taxa de sucesso (hits vs misses)
- Identificar termos não compreendidos
- Medir confiança média das respostas
- Exportar relatórios para melhorias
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import defaultdict

from app.contracts.dto import RequestContext, ChatResponse
from app.settings import settings
from app.metrics import statsd

logger = logging.getLogger(__name__)

# Diretório de analytics
ANALYTICS_DIR = Path(settings.BASE_DIR) / "analytics" / "v1"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

# Arquivo de queries (JSON Lines - um JSON por linha)
QUERIES_LOG_FILE = ANALYTICS_DIR / "queries.jsonl"
SUMMARY_FILE = ANALYTICS_DIR / "summary.json"


class QueryAnalytics:
    """
    Registra análises sobre queries e respostas.
    Útil para:
    - Identificar gaps na RAG
    - Ver quais perguntas falham
    - Entender como o usuário fala
    - Melhorar expansão de queries
    """
    
    @staticmethod
    def log_query(
        ctx: RequestContext,
        response: ChatResponse,
    ) -> None:
        """
        Registra uma query e seu resultado.
        
        Persiste em JSONL para análise posterior.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": ctx.request_id,
            "session_id": ctx.session_id,
            "surface": ctx.surface.value if ctx.surface else None,
            "channel": ctx.channel.value if ctx.channel else None,
            
            # Input
            "user_message": ctx.user_message,
            "expanded_query": ctx.expanded_query,
            
            # Classificação
            "intent": ctx.intent.value if ctx.intent else None,
            "confidence": ctx.confidence,
            "sentiment": ctx.sentiment,
            "emotion": ctx.emotion,
            
            # RAG
            "docs_found": ctx.docs_found,
            "best_score": ctx.rag_retrieve.best_score if ctx.rag_retrieve else None,
            "num_docs": ctx.rag_retrieve.docs_count if ctx.rag_retrieve else 0,
            
            # Resposta
            "decision": response.decision.value,
            "response_type": response.response_type.value,
            "has_message": bool(response.message),
            "message_length": len(response.message) if response.message else 0,
            
            # Métricas
            "fallback_used": response.fallback_used,
            "fallback_reason": response.fallback_reason.value if response.fallback_reason else None,
            "policy_decision_pre": ctx.policy_decision_pre.value if ctx.policy_decision_pre else None,
        }
        
        try:
            # Append em JSONL
            with open(QUERIES_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
            logger.debug(f"[ANALYTICS] Query registrada: {ctx.request_id}")

            # Métricas rápidas (StatsD)
            try:
                statsd.incr(f"chat.decision.{response.decision.value.lower()}")
                statsd.incr(f"chat.response_type.{response.response_type.value.lower()}")
                if response.fallback_used:
                    reason = (response.fallback_reason.value if response.fallback_reason else "unknown").lower()
                    statsd.incr(f"chat.fallback.{reason}")
                if ctx.channel:
                    statsd.incr(f"chat.channel.{ctx.channel.value.lower()}")
            except Exception:
                # Não quebra fluxo de logging
                pass
            
        except Exception as e:
            logger.error(f"[ANALYTICS] Erro ao registrar query: {e}")


class RAGMetrics:
    """
    Analisa logs de queries para gerar métricas sobre RAG.
    """
    
    @staticmethod
    def generate_summary() -> Dict[str, Any]:
        """
        Analisa QUERIES_LOG_FILE e gera relatório.
        
        Retorna:
        {
            "total_queries": int,
            "hit_rate": float,  # % de respostas bem-sucedidas
            "avg_confidence": float,
            "avg_best_score": float,
            "fallback_distribution": dict,
            "intent_distribution": dict,
            "missed_queries": list,  # Queries com fallback
            "low_confidence_queries": list,  # Queries com confiança baixa
        }
        """
        
        if not QUERIES_LOG_FILE.exists():
            logger.warning("[METRICS] Arquivo de queries ainda não existe")
            return {"status": "no_data"}
        
        metrics = {
            "total_queries": 0,
            "successful_responses": 0,
            "fallback_responses": 0,
            "no_reply_responses": 0,
            
            "avg_confidence": 0.0,
            "avg_best_score": 0.0,
            "avg_message_length": 0.0,
            
            "fallback_distribution": defaultdict(int),
            "intent_distribution": defaultdict(int),
            "decision_distribution": defaultdict(int),
            "sentiment_distribution": defaultdict(int),
            
            "missed_queries": [],
            "low_confidence_queries": [],
            "no_docs_queries": [],
        }
        
        confidences = []
        scores = []
        message_lengths = []
        
        try:
            with open(QUERIES_LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        metrics["total_queries"] += 1
                        
                        # Distribuições
                        intent = entry.get("intent")
                        if intent:
                            metrics["intent_distribution"][intent] += 1
                        
                        decision = entry.get("decision")
                        if decision:
                            metrics["decision_distribution"][decision] += 1
                        
                        sentiment = entry.get("sentiment")
                        if sentiment:
                            metrics["sentiment_distribution"][sentiment] += 1
                        
                        # Resultados
                        if entry.get("decision") == "FALLBACK":
                            metrics["fallback_responses"] += 1
                            reason = entry.get("fallback_reason")
                            if reason:
                                metrics["fallback_distribution"][reason] += 1
                            
                            # Captura query perdida
                            metrics["missed_queries"].append({
                                "query": entry.get("user_message"),
                                "expanded": entry.get("expanded_query"),
                                "reason": reason,
                                "confidence": entry.get("confidence"),
                            })
                        
                        elif entry.get("decision") == "NO_REPLY":
                            metrics["no_reply_responses"] += 1
                        
                        else:
                            metrics["successful_responses"] += 1
                        
                        # Métricas numéricas
                        conf = entry.get("confidence")
                        if conf is not None:
                            confidences.append(conf)
                            if conf < 0.5:
                                metrics["low_confidence_queries"].append({
                                    "query": entry.get("user_message"),
                                    "confidence": conf,
                                    "intent": intent,
                                })
                        
                        score = entry.get("best_score")
                        if score is not None:
                            scores.append(score)
                        
                        # Registra queries sem documentos
                        if not entry.get("docs_found"):
                            metrics["no_docs_queries"].append({
                                "query": entry.get("user_message"),
                                "expanded": entry.get("expanded_query"),
                            })
                        
                        msg_len = entry.get("message_length", 0)
                        if msg_len > 0:
                            message_lengths.append(msg_len)
                    
                    except json.JSONDecodeError:
                        logger.warning(f"[METRICS] Linha inválida: {line}")
                        continue
            
            # Calcula médias
            if confidences:
                metrics["avg_confidence"] = sum(confidences) / len(confidences)
            
            if scores:
                metrics["avg_best_score"] = sum(scores) / len(scores)
            
            if message_lengths:
                metrics["avg_message_length"] = sum(message_lengths) / len(message_lengths)
            
            # Converte defaultdicts para dicts
            metrics["fallback_distribution"] = dict(metrics["fallback_distribution"])
            metrics["intent_distribution"] = dict(metrics["intent_distribution"])
            metrics["decision_distribution"] = dict(metrics["decision_distribution"])
            metrics["sentiment_distribution"] = dict(metrics["sentiment_distribution"])
            
            # Calcula hit rate
            if metrics["total_queries"] > 0:
                metrics["hit_rate"] = (
                    metrics["successful_responses"] / metrics["total_queries"]
                )
            
            # Limita listas para não ficar gigante
            metrics["missed_queries"] = metrics["missed_queries"][-100:]
            metrics["low_confidence_queries"] = metrics["low_confidence_queries"][-50:]
            metrics["no_docs_queries"] = metrics["no_docs_queries"][-50:]
            
            logger.info("[METRICS] Resumo gerado com sucesso")
            
        except Exception as e:
            logger.error(f"[METRICS] Erro ao gerar resumo: {e}")
        
        return metrics
    
    @staticmethod
    def save_summary() -> None:
        """Salva resumo em JSON."""
        summary = RAGMetrics.generate_summary()
        
        try:
            with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[METRICS] Resumo salvo: {SUMMARY_FILE}")
            
        except Exception as e:
            logger.error(f"[METRICS] Erro ao salvar resumo: {e}")
    
    @staticmethod
    def get_top_missed_intents(limit: int = 10) -> List[tuple]:
        """
        Retorna top N intents que mais geram fallbacks.
        
        Útil para saber em que áreas a RAG tá fraca.
        """
        summary = RAGMetrics.generate_summary()
        
        # Conta intents em missed queries
        intent_counts = defaultdict(int)
        for missed in summary.get("missed_queries", []):
            intent_counts["unknown"] += 1  # Não temos intent guardado nas queries perdidas
        
        return sorted(
            intent_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
    
    @staticmethod
    def export_csv_report(filepath: Optional[str] = None) -> str:
        """Exporta relatório em CSV para análise em Excel."""
        import csv
        
        if filepath is None:
            filepath = ANALYTICS_DIR / "report.csv"
        
        try:
            with open(QUERIES_LOG_FILE, "r", encoding="utf-8") as infile, \
                 open(filepath, "w", newline="", encoding="utf-8") as outfile:
                
                # Lê primeira linha para pegar headers
                first_line = infile.readline()
                if not first_line:
                    logger.warning("[METRICS] Arquivo de queries vazio")
                    return str(filepath)
                
                first_entry = json.loads(first_line)
                fieldnames = list(first_entry.keys())
                
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(first_entry)
                
                # Processa resto do arquivo
                for line in infile:
                    if line.strip():
                        entry = json.loads(line)
                        writer.writerow(entry)
            
            logger.info(f"[METRICS] CSV exportado: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"[METRICS] Erro ao exportar CSV: {e}")
            return ""
