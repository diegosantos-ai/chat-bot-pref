# Fase 10 — Multi-LLM, Fallback e Avaliação Comparativa de Provedores

## Bloco 1: Base Operacional e Contrato do Multi-LLM

Este documento define os princípios arquiteturais e operacionais para a adoção de múltiplos provedores de LLM, bem como o fluxo de fallback entre eles no **Chat Pref**. As diretrizes respeitam a separação metodológica das camadas de experimentação e de runtime.

### 1. Contrato Multi-LLM

O sistema não se acoplará diretamente à biblioteca cliente de cada provedor (ex: `google-generativeai`). Todo provedor deve implementar o `LLMProvider(Protocol)` e encapsular sua lógica.

#### Parâmetros de Entrada (`LLMGenerationRequest` já existente)
Além de receber `prompt`, `question` e `context_chunks`, o contexto para a geração passará a considerar (em fases futuras) uma abstração de `LLMConfig` associada ao `TenantProfile`, permitindo que um tenant defina, por exemplo, um modelo principal de alta qualidade e um modelo de fallback de menor custo ou de outra região.

#### Parâmetros de Retorno (`LLMGenerationResponse` já existente)
A estrutura de resposta continua devendo retornar explicitamente:
- `provider`: ex: `"gemini"`, `"mock"`, `"openai"`.
- `model`: ex: `"gemini-2.5-flash"`.
- `estimated_cost_usd` e `cost_estimation_status`: fundamentais para justificar a escolha orientada a custos.

#### Parâmetros Experimentais (Apenas MLflow/Tracking)
Parâmetros finos de roteamento ou de calibração que não importam ao domínio de negócio transacional (ex.: _temperature_, _top_k_, pesos híbridos) não devem poluir o banco operacional de histórico. Eles pertencem ao log da camada de tracking (ex.: MLflow `run` log).

### 2. Regras de Fallback

O fallback não deve mascarar problemas estruturais. A troca automática de modelo ocorrerá **exclusivamente sob falha do provedor externo**, obedecendo às constrições:

#### 2.1. Quando o fallback DEVE acontecer (Trigger válido)
- Erros classificados como `ProviderUnavailableError` (ex: 502, 503, Timeout após *x* segundos no request HTTP base).
- Erros classificados como `ProviderRateLimitError` (ex: 429 isolado e temporário).

#### 2.2. Quando o fallback NÃO DEVE acontecer (Máscara de erro ou domínio)
- Falhas de sintaxe na RAG, embutidas na formatação dos prompts (Erro técnico do nosso código).
- Recusa do modelo em responder devido às próprias **Politicas de Segurança** (Safety guardrails nativos do provedor). Fallback aqui violaria o guardrail.
- Auth falho de credenciais do provedor (Erro de infra/deploy e não erro transiente).

#### 2.3. Registro do Fenômeno
- **Auditoria Operacional:** O banco operacional registrará que a mensagem final foi respondida pelo `provider/model` B, anotando `fallback_triggered: True` no log da requisição para justificar a mudança. Não salva as réplicas falhas.
- **Experiment Tracking / Observabilidade:** Os traces do OpenTelemetry guardarão o _span_ do `provider A` que falhou (junto com o _status_code_) e o _span_ subsequente do `provider B` sucesso. O MLflow em execuções de avaliação offline considerará a falha do provider A como métrica de _reliability_.

### 3. Delimitação Experimental vs. Transacional

A adoção de múltiplos LLMs exige separação rígida de camadas para que o sistema de produção não perca rastreabilidade e performance.

| Contexto / Ferramenta | Propósito do Multi-LLM na Camada | Registro Obrigatório |
| --- | --- | --- |
| **Runtime Transacional** (FastAPI) | Encaminhar o `prompt_version` ativo para o LLM principal e disparar fallback caso dê timeout. | Qual o modelo final escolhido. Qual o custo da interação. |
| **Auditoria Operacional** (DB/Logs) | Registrar fato histórico para auditoria governamental / transparência do tenant. | O _provider_ de fato utilizado, flag de se o fallback ocorreu. |
| **Tracking Experimental** (MLflow) | Armazenar o A/B testing das respostas e as latências comparadas na fase de homologação offline do modelo. | Configurações granulares de temperatura, _top-k_, prompt version testados. |
| **Benchmark Offline** | Executar o pipeline _multi-LLM_ simultaneamente sob os mesmos datasets para escolher o novo padrão. | Score do avaliador estrutural. |

---
**Status da Implementação no Bloco 1 (Contrato)**: Contrato e delimitações propostos. Refino das estruturas de exceção no domínio sendo preparadas para não escalar escopo precipitadamente.

## Bloco 2: Implementação Comparativa e Fechamento

### 1. Provedores Integrados e Modo Controlado
Para evitar dependências inseguras ou exposição de segredos, a implementação adotada para este ciclo baseia-se em:
- **`GeminiLLMProvider`**: Abstração HTTP nativa.
- **`OpenAILLMProvider`**: Abstração HTTP nativa criada via `httpx` para não prender o projeto a bibliotecas de fornecedores específicos.
- **Modo Comparativo Controlado (`mock`)**: Usado ativamente nos pipelines offline via script `run_phase10_multi_llm_comparison.py`, medindo impacto simulado de _delays_ e latência através de _variants_ de mock.

### 2. Tracking e Recomendação Técnica

Através das validações rodadas em modo comparado:
- O painel experimental do MLflow consegue receber explicitamente as instâncias de `provider` ("openai", "gemini", "mock"), `model_name` e `temperature`.
- A arquitetura permite injetar `LLMComposeService` com _LLMProviders_ dinâmicos para avaliações futuras, separando o `runtime` síncrono da carga horária de benchmark.

**Recomendação Técnica Consolidada:**
O pipeline confirmou que é estável injetar múltiplos protocólos. Recomenda-se avançar com o Gemini _flash_ como modelo padrão principal (pelo custo historicamente menor no mercado atual de _Tier 1_) enquanto consolida-se a "OpenAI" como fallback primário (caso disponível a key) ativado via `LLMProviderUnavailableError`.

### 3. Status Fim-a-Fim (O que entrou vs O que não entrou)

- **Entregue:**
  - Contrato multi-LLM (`LLMProvider`) estruturador de exceções.
  - Integração do provedor OpenAI baseada puramente em `httpx`.
  - Exposição de `provider`, `model_name` e `temperature` nas chamadas ao MLflow local durante modo experimental.
  - Script offline que orquestra a variação customizada de construtores LLM para teste A/B (`scripts/run_phase10_multi_llm_comparison.py`).
- **Apenas preparado:** Implementação assíncrona automática (`retry` wrapper) ou disparo autônomo dentro no core do Uvicorn para não forçar roteamento em tempo real sem validação robusta de latências conjuntas.
- **Fora de Escopo:** Instalação de SDKs pesados (`openai-python`), UI visual de custo.

---
_A Fase 10 cumpre seu critério de aceite oferecendo a ponte entre comparação LLM modular e arquitetura transacional local._
