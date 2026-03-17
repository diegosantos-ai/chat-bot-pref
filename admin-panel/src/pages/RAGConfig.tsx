import { useState, useEffect } from 'react';
import { Save, RotateCcw, Settings2, Cpu } from 'lucide-react';
import { config as configApi } from '../services/api';
import { Button } from '../components/Button';
import type { RAGConfig } from '../types';
import styles from './RAGConfig.module.css';

const GEMINI_MODELS = [
  { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash (Padrão)' },
  { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
  { value: 'gemini-1.5-flash-8b', label: 'Gemini 1.5 Flash 8B' },
  { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
  { value: 'gemini-pro', label: 'Gemini Pro (Legacy)' },
];

export default function RAGConfigPage() {
  const [ragConfig, setRagConfig] = useState<RAGConfig>({
    min_score: 0.35,
    top_k: 7,
    boost_enabled: true,
    boost_amount: 0.2,
    model: 'gemini-2.0-flash',
    model_temperature: 0.3,
    model_max_tokens: 1024,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await configApi.get();
      const config = response.data.rag_config;
      setRagConfig({
        min_score: config.min_score ?? 0.35,
        top_k: config.top_k ?? 7,
        boost_enabled: config.boost_enabled ?? true,
        boost_amount: config.boost_amount ?? 0.2,
        model: config.model ?? 'gemini-2.0-flash',
        model_temperature: config.model_temperature ?? 0.3,
        model_max_tokens: config.model_max_tokens ?? 1024,
      });
    } catch (err) {
      console.error('Failed to fetch config:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    setError('');
    try {
      await configApi.saveRagConfig(ragConfig);
      setMessage('Configuração salva com sucesso!');
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || 'Erro ao salvar');
      } else {
        setError('Erro ao salvar configuração');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setRagConfig({
      min_score: 0.35,
      top_k: 7,
      boost_enabled: true,
      boost_amount: 0.2,
      model: 'gemini-2.0-flash',
      model_temperature: 0.3,
      model_max_tokens: 1024,
    });
  };

  if (loading) {
    return <div className={styles.loading}>Carregando...</div>;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Configuração do RAG</h1>
        <p className={styles.subtitle}>Parâmetros do sistema de busca semântica e IA</p>
      </header>

      {message && <div className={styles.success}>{message}</div>}
      {error && <div className={styles.error}>{error}</div>}

      {/* Modelo IA Section */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <Cpu size={20} />
          <h2>Modelo de IA</h2>
        </div>

        <div className={styles.paramsGrid}>
          {/* Model Selection */}
          <div className={styles.paramCard}>
            <div className={styles.paramHeader}>
              <label>Modelo Gemini</label>
            </div>
            <select
              value={ragConfig.model}
              onChange={(e) => setRagConfig({ ...ragConfig, model: e.target.value })}
              className={styles.select}
            >
              {GEMINI_MODELS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
            <p className={styles.paramDesc}>
              Modelo utilizado para geração de respostas e classificação de intents.
            </p>
          </div>

          {/* Temperature */}
          <div className={styles.paramCard}>
            <div className={styles.paramHeader}>
              <label>Temperatura</label>
              <span className={styles.paramValue}>{ragConfig.model_temperature.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={ragConfig.model_temperature}
              onChange={(e) => setRagConfig({ ...ragConfig, model_temperature: parseFloat(e.target.value) })}
              className={styles.slider}
            />
            <div className={styles.paramHints}>
              <span>0.0 (mais determinístico)</span>
              <span>1.0 (mais criativo)</span>
            </div>
            <p className={styles.paramDesc}>
              Controla a aleatoriedade das respostas. 0.3 é recomendado para atendimento.
            </p>
          </div>

          {/* Max Tokens */}
          <div className={styles.paramCard}>
            <div className={styles.paramHeader}>
              <label>Tamanho Máximo da Resposta</label>
              <span className={styles.paramValue}>{ragConfig.model_max_tokens} tokens</span>
            </div>
            <input
              type="range"
              min="256"
              max="4096"
              step="256"
              value={ragConfig.model_max_tokens}
              onChange={(e) => setRagConfig({ ...ragConfig, model_max_tokens: parseInt(e.target.value) })}
              className={styles.slider}
            />
            <div className={styles.paramHints}>
              <span>256</span>
              <span>2048</span>
              <span>4096</span>
            </div>
            <p className={styles.paramDesc}>
              Limite máximo de tokens na resposta gerada.
            </p>
          </div>
        </div>
      </section>

      {/* Retriever Section */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <Settings2 size={20} />
          <h2>Parâmetros do Retriever</h2>
        </div>

        <div className={styles.paramsGrid}>
          {/* Min Score */}
          <div className={styles.paramCard}>
            <div className={styles.paramHeader}>
              <label>Score Mínimo (min_score)</label>
              <span className={styles.paramValue}>{ragConfig.min_score.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={ragConfig.min_score}
              onChange={(e) => setRagConfig({ ...ragConfig, min_score: parseFloat(e.target.value) })}
              className={styles.slider}
            />
            <div className={styles.paramHints}>
              <span>0.00 (mais permissivo)</span>
              <span>1.00 (mais restritivo)</span>
            </div>
            <p className={styles.paramDesc}>
              Documentos com score abaixo deste valor são descartados.
              Valor padrão recomendado: 0.35
            </p>
          </div>

          {/* Top K */}
          <div className={styles.paramCard}>
            <div className={styles.paramHeader}>
              <label>Quantidade de Documentos (top_k)</label>
              <span className={styles.paramValue}>{ragConfig.top_k}</span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              step="1"
              value={ragConfig.top_k}
              onChange={(e) => setRagConfig({ ...ragConfig, top_k: parseInt(e.target.value) })}
              className={styles.slider}
            />
            <div className={styles.paramHints}>
              <span>1</span>
              <span>10</span>
              <span>20</span>
            </div>
            <p className={styles.paramDesc}>
              Número máximo de documentos a recuperar por query.
              Valor padrão recomendado: 7
            </p>
          </div>

          {/* Boost Amount */}
          <div className={styles.paramCard}>
            <div className={styles.paramHeader}>
              <label>Valor do Boost (boost_amount)</label>
              <span className={styles.paramValue}>{ragConfig.boost_amount.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={ragConfig.boost_amount}
              onChange={(e) => setRagConfig({ ...ragConfig, boost_amount: parseFloat(e.target.value) })}
              className={styles.slider}
              disabled={!ragConfig.boost_enabled}
            />
            <div className={styles.paramHints}>
              <span>0.00</span>
              <span>0.50</span>
              <span>1.00</span>
            </div>
            <p className={styles.paramDesc}>
              Valor adicionado ao score quando há match de siglas municipais.
            </p>
          </div>

          {/* Boost Enabled */}
          <div className={styles.paramCard}>
            <div className={styles.paramToggle}>
              <label className={styles.toggle}>
                <input
                  type="checkbox"
                  checked={ragConfig.boost_enabled}
                  onChange={(e) => setRagConfig({ ...ragConfig, boost_enabled: e.target.checked })}
                />
                <span className={styles.toggleSlider} />
                <span className={styles.toggleLabel}>Boost de Siglas Ativado</span>
              </label>
            </div>
            <p className={styles.paramDesc}>
              Quando ativado, documentos que contêm siglas municipais (IPSU, REFIS, MEI, etc.)
              recibida um boost no score de relevância.
            </p>
          </div>
        </div>

        <div className={styles.actions}>
          <Button variant="secondary" onClick={handleReset}>
            <RotateCcw size={16} />
            Restaurar Padrões
          </Button>
          <Button onClick={handleSave} isLoading={saving}>
            <Save size={16} />
            Salvar Configuração
          </Button>
        </div>
      </section>

      {/* Info Section */}
      <section className={styles.section}>
        <h3>Sobre os Parâmetros</h3>
        <div className={styles.infoGrid}>
          <div className={styles.infoCard}>
            <h4>Modelo Gemini</h4>
            <p>
              O modelo de IA usado para processar queries e gerar respostas.
              Modelos mais novos (Flash) são mais rápidos, Pro é mais capaz.
            </p>
          </div>
          <div className={styles.infoCard}>
            <h4>Temperatura</h4>
            <p>
              0.0 = respostas mais consistentes e determinísticas.
              1.0 = mais variety e criatividade nas respostas.
            </p>
          </div>
          <div className={styles.infoCard}>
            <h4>Min Score</h4>
            <p>
              Controla a qualidade mínima dos documentos retornados.
              Scores mais altos = menos resultados, mas mais precisos.
            </p>
          </div>
          <div className={styles.infoCard}>
            <h4>Top K</h4>
            <p>
              Determina quantos documentos são considerados para compor a resposta.
              Mais documentos = mais contexto, mas pode diluir a relevância.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
