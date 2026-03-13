import { useEffect, useState } from 'react';
import { Search, Play, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { rag } from '../services/api';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import type { RAGQueryResponse } from '../types';
import styles from './RAGTester.module.css';

export default function RAGTester() {
  const [tenantId, setTenantId] = useState('');
  const [query, setQuery] = useState('');
  const [minScore, setMinScore] = useState(0.0);
  const [topK, setTopK] = useState(10);
  const [boostEnabled, setBoostEnabled] = useState(true);
  const [result, setResult] = useState<RAGQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!tenantId.trim()) {
      setStatusMessage('Informe um tenant para consultar a base RAG.');
      return;
    }
    const loadStatus = async () => {
      try {
        const response = await rag.status(tenantId.trim());
        setStatusMessage(response.data.message);
      } catch {
        setStatusMessage('Não foi possível carregar o status do tenant informado.');
      }
    };
    loadStatus();
  }, [tenantId]);

  const handleSearch = async () => {
    if (!tenantId.trim()) {
      setError('tenant_id obrigatório');
      return;
    }
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await rag.query({
        tenant_id: tenantId.trim(),
        query: query.trim(),
        min_score: minScore,
        top_k: topK,
        boost_enabled: boostEnabled,
      });
      setResult(response.data);
      setStatusMessage(response.data.message);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || 'Erro ao executar query');
      } else {
        setError('Erro ao executar query');
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleChunk = (index: number) => {
    const newExpanded = new Set(expandedChunks);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedChunks(newExpanded);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'var(--success)';
    if (score >= 0.5) return 'var(--accent-primary)';
    if (score >= 0.35) return 'var(--warning)';
    return 'var(--error)';
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>RAG Tester</h1>
        <p className={styles.subtitle}>Teste queries com parâmetros tenant-aware</p>
      </header>

      <div className={styles.tenantBar}>
        <Input
          label="Tenant ID"
          value={tenantId}
          onChange={(e) => setTenantId(e.target.value)}
          placeholder="prefeitura-demo"
        />
      </div>

      {statusMessage && (
        <div className={styles.statusNote}>{statusMessage}</div>
      )}

      <div className={styles.searchBox}>
        <div className={styles.searchInput}>
          <Search size={20} className={styles.searchIcon} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Digite uma pergunta para testar..."
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>
        <Button onClick={handleSearch} isLoading={loading} disabled={!query.trim() || !tenantId.trim()}>
          <Play size={16} />
          Executar
        </Button>
      </div>

      <div className={styles.paramsSection}>
        <h3>Parâmetros</h3>
        <div className={styles.paramsGrid}>
          <div className={styles.param}>
            <label>Min Score: {minScore.toFixed(2)}</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={minScore}
              onChange={(e) => setMinScore(parseFloat(e.target.value))}
            />
            <div className={styles.paramHints}>
              <span>0.0</span>
              <span>0.35</span>
              <span>0.5</span>
              <span>1.0</span>
            </div>
          </div>

          <div className={styles.param}>
            <label>Top K: {topK}</label>
            <input
              type="range"
              min="1"
              max="20"
              step="1"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value))}
            />
            <div className={styles.paramHints}>
              <span>1</span>
              <span>7</span>
              <span>15</span>
              <span>20</span>
            </div>
          </div>

          <div className={styles.paramToggle}>
            <label className={styles.toggle}>
              <input
                type="checkbox"
                checked={boostEnabled}
                onChange={(e) => setBoostEnabled(e.target.checked)}
              />
              <span className={styles.toggleSlider} />
              <span className={styles.toggleLabel}>Boost disponível</span>
            </label>
            <p className={styles.toggleHint}>Mantido por compatibilidade do contrato, sem fallback silencioso.</p>
          </div>
        </div>
      </div>

      {error && (
        <div className={styles.error}>{error}</div>
      )}

      {result && (
        <div className={styles.resultsSection}>
          <div className={styles.resultsHeader}>
            <h3>Resultados</h3>
            <div className={styles.resultsMeta}>
              <span>{result.chunks.length} documentos</span>
              <span>•</span>
              <span>Status: {result.status}</span>
              <span>•</span>
              <span>Best: {result.best_score.toFixed(4)}</span>
            </div>
          </div>

          <div className={styles.chunksList}>
            {result.chunks.map((chunk, index) => (
              <div
                key={chunk.id}
                className={`${styles.chunkCard} ${expandedChunks.has(index) ? styles.expanded : ''}`}
              >
                <div
                  className={styles.chunkHeader}
                  onClick={() => toggleChunk(index)}
                >
                  <div className={styles.chunkInfo}>
                    <FileText size={16} />
                    <span className={styles.chunkTitle}>{chunk.title}</span>
                    {chunk.section && (
                      <span className={styles.chunkSection}>› {chunk.section}</span>
                    )}
                  </div>
                  <div className={styles.chunkRight}>
                    <span
                      className={styles.chunkScore}
                      style={{ color: getScoreColor(chunk.score) }}
                    >
                      {chunk.score.toFixed(4)}
                    </span>
                    {expandedChunks.has(index) ? (
                      <ChevronUp size={18} />
                    ) : (
                      <ChevronDown size={18} />
                    )}
                  </div>
                </div>

                {expandedChunks.has(index) && (
                  <div className={styles.chunkContent}>
                    <pre>{chunk.text}</pre>
                    {chunk.tags.length > 0 && (
                      <div className={styles.chunkTags}>
                        {chunk.tags.map((tag) => (
                          <span key={tag} className={styles.tag}>{tag}</span>
                        ))}
                      </div>
                    )}
                    <div className={styles.chunkMeta}>
                      <span>ID: {chunk.id}</span>
                      <span>Source: {chunk.source}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {result.chunks.length === 0 && (
            <div className={styles.noResults}>
              {result.message}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
