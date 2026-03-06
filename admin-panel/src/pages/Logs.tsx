import { useState, useEffect } from 'react';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { logs } from '../services/api';
import type { Conversa } from '../types';
import styles from './Logs.module.css';

export default function Logs() {
  const [conversas, setConversas] = useState<Conversa[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState({
    busca_texto: '',
    canal: '',
    intent: '',
    decision: '',
  });

  const limit = 20;

  useEffect(() => {
    fetchLogs();
  }, [page, filters]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await logs.conversas({
        ...filters,
        busca_texto: filters.busca_texto || undefined,
        canal: filters.canal || undefined,
        intent: filters.intent || undefined,
        decision: filters.decision || undefined,
        limit,
        offset: page * limit,
      });
      setConversas(response.data.conversas);
      setTotal(response.data.count);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(total / limit);

  const getStatusColor = (tipo: string) => {
    switch (tipo) {
      case 'SUCCESS': return 'var(--success)';
      case 'FALLBACK': return 'var(--warning)';
      case 'ERROR': return 'var(--error)';
      default: return 'var(--text-muted)';
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Logs de Conversas</h1>
        <p className={styles.subtitle}>Histórico de interações</p>
      </header>

      {/* Filters */}
      <div className={styles.filters}>
        <div className={styles.searchBox}>
          <Search size={18} />
          <input
            type="text"
            placeholder="Buscar no texto..."
            value={filters.busca_texto}
            onChange={(e) => setFilters({ ...filters, busca_texto: e.target.value })}
          />
        </div>
        <div className={styles.filterSelects}>
          <select
            value={filters.canal}
            onChange={(e) => setFilters({ ...filters, canal: e.target.value })}
          >
            <option value="">Todos os canais</option>
            <option value="web_widget">Web Widget</option>
            <option value="instagram_dm">Instagram DM</option>
            <option value="facebook_dm">Facebook DM</option>
          </select>
          <select
            value={filters.intent}
            onChange={(e) => setFilters({ ...filters, intent: e.target.value })}
          >
            <option value="">Todos os intents</option>
            <option value="GREETING">Greeting</option>
            <option value="INFO_REQUEST">Info Request</option>
            <option value="CONTACT_REQUEST">Contact Request</option>
            <option value="OUT_OF_SCOPE">Out of Scope</option>
          </select>
          <select
            value={filters.decision}
            onChange={(e) => setFilters({ ...filters, decision: e.target.value })}
          >
            <option value="">Todas as decisões</option>
            <option value="ANSWER_RAG">Answer RAG</option>
            <option value="FALLBACK">Fallback</option>
            <option value="ESCALATE">Escalate</option>
          </select>
        </div>
      </div>

      {/* Results */}
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Data</th>
              <th>Canal</th>
              <th>Intent</th>
              <th>Decisão</th>
              <th>Usuário</th>
              <th>Resposta</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className={styles.loading}>Carregando...</td>
              </tr>
            ) : conversas.length === 0 ? (
              <tr>
                <td colSpan={6} className={styles.empty}>Nenhum registro encontrado</td>
              </tr>
            ) : (
              conversas.map((conv) => (
                <tr key={conv.id_conversa}>
                  <td className={styles.date}>
                    {new Date(conv.criado_em).toLocaleString('pt-BR')}
                  </td>
                  <td>
                    <span className={styles.tag}>{conv.canal}</span>
                  </td>
                  <td>{conv.intencao}</td>
                  <td>
                    <span 
                      className={styles.status}
                      style={{ color: getStatusColor(conv.tipo_resposta) }}
                    >
                      {conv.tipo_resposta}
                    </span>
                  </td>
                  <td className={styles.message} title={conv.mensagem_usuario}>
                    {conv.mensagem_usuario.length > 50 
                      ? conv.mensagem_usuario.slice(0, 50) + '...' 
                      : conv.mensagem_usuario}
                  </td>
                  <td className={styles.message} title={conv.mensagem_resposta || ''}>
                    {conv.mensagem_resposta 
                      ? (conv.mensagem_resposta.length > 50 
                          ? conv.mensagem_resposta.slice(0, 50) + '...' 
                          : conv.mensagem_resposta)
                      : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className={styles.pagination}>
        <span className={styles.pageInfo}>
          Mostrando {page * limit + 1}-{Math.min((page + 1) * limit, total)} de {total}
        </span>
        <div className={styles.pageButtons}>
          <button 
            onClick={() => setPage(p => p - 1)} 
            disabled={page === 0}
          >
            <ChevronLeft size={18} />
          </button>
          <span>{page + 1} / {totalPages || 1}</span>
          <button 
            onClick={() => setPage(p => p + 1)} 
            disabled={page >= totalPages - 1}
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
