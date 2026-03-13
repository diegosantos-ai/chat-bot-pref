import { useState } from 'react';
import { Search, Play, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { rag } from '../services/api';
import { Button } from '../components/Button';
import type { RAGQueryResponse } from '../types';
import styles from './RAGTester.module.css';

export default function RAGTester() {
  const [query, setQuery] = useState('');
  const [minScore, setMinScore] = useState(0.0);
  const [topK, setTopK] = useState(10);
  const [boostEnabled, setBoostEnabled] = useState(true);
  const [result, setResult] = useState<RAGQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set());

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError('');
    setResult(null);
    
    try {
      const response = await rag.query({
        query: query.trim(),
        min_score: minScore,
        top_k: topK,
        boost_enabled: boostEnabled,
      });
      setResult(response.data);
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
        <p className={styles.subtitle}>Teste queries com parâmetros customizados</p>
      </header>

      {/* Query Input */}
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
        <Button onClick={handleSearch} isLoading={loading} disabled={!query.trim()}>
          <Play size={16} />
          Executar
        </Button>
      </div>

      {/* Parameters */}
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
              <span className={styles.toggleLabel}>Boost de Siglas</span>
            </label>
            <p className={styles.toggleHint}>Aumenta score de chunks com siglas municipais</p>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className={styles.error}>{error}</div>
      )}

      {/* Results */}
      {result && (
        <div className={styles.resultsSection}>
          <div className={styles.resultsHeader}>
            <h3>Resultados</h3>
            <div className={styles.resultsMeta}>
              <span>{result.chunks.length} documentos</span>
              <span>•</span>
              <span>Best: {result.best_score.toFixed(4)}</span>
              <span>•</span>
              <span>Total: {result.total_chunks}</span>
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
              Nenhum documento encontrado com os parâmetros informados.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
