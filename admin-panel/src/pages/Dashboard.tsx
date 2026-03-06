import { useEffect, useState } from 'react';
import { 
  MessageSquare, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  TrendingUp,
  Clock
} from 'lucide-react';
import { dashboard, config } from '../services/api';
import type { DashboardStats, ConfigResponse } from '../types';
import styles from './Dashboard.module.css';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [configData, setConfigData] = useState<ConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, configRes] = await Promise.all([
          dashboard.stats(),
          config.get(),
        ]);
        setStats(statsRes.data);
        setConfigData(configRes.data);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <div className={styles.loading}>Carregando...</div>;
  }

  const statCards = [
    {
      label: 'Total de Conversas',
      value: stats?.total_conversas || 0,
      icon: MessageSquare,
      color: 'var(--text-primary)',
    },
    {
      label: 'Taxa de Sucesso',
      value: `${stats?.hit_rate || 0}%`,
      icon: TrendingUp,
      color: 'var(--success)',
    },
    {
      label: 'Últimas 24h',
      value: stats?.ultimas_24h?.count || 0,
      icon: Clock,
      color: 'var(--accent-primary)',
    },
  ];

  const responseCards = [
    { label: 'Sucesso', value: stats?.total_sucesso || 0, icon: CheckCircle, color: 'var(--success)' },
    { label: 'Fallback', value: stats?.total_fallback || 0, icon: AlertTriangle, color: 'var(--warning)' },
    { label: 'Erro', value: stats?.total_erro || 0, icon: XCircle, color: 'var(--error)' },
  ];

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Dashboard</h1>
        <p className={styles.subtitle}>Visão geral do assistente {bot_name}</p>
      </header>

      {/* Status Cards */}
      <div className={styles.statsGrid}>
        {statCards.map((card) => (
          <div key={card.label} className={styles.statCard}>
            <div className={styles.statIcon} style={{ color: card.color }}>
              <card.icon size={24} />
            </div>
            <div className={styles.statContent}>
              <span className={styles.statValue}>{card.value}</span>
              <span className={styles.statLabel}>{card.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Response Stats */}
      <section className={styles.section}>
        <h2>Respostas</h2>
        <div className={styles.responseGrid}>
          {responseCards.map((card) => (
            <div key={card.label} className={styles.responseCard}>
              <card.icon size={20} style={{ color: card.color }} />
              <span className={styles.responseValue}>{card.value}</span>
              <span className={styles.responseLabel}>{card.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Distributions */}
      <div className={styles.distributionsGrid}>
        {/* Intents Distribution */}
        <section className={styles.distributionCard}>
          <h3>Intentos</h3>
          {stats?.intents_distribution && Object.keys(stats.intents_distribution).length > 0 ? (
            <div className={styles.distributionList}>
              {Object.entries(stats.intents_distribution).map(([intent, count]) => (
                <div key={intent} className={styles.distributionItem}>
                  <span className={styles.distLabel}>{intent}</span>
                  <div className={styles.distBar}>
                    <div 
                      className={styles.distBarFill}
                      style={{ 
                        width: `${(count / (stats?.total_conversas || 1)) * 100}%` 
                      }}
                    />
                  </div>
                  <span className={styles.distValue}>{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className={styles.empty}>Nenhum dado disponível</p>
          )}
        </section>

        {/* Channels Distribution */}
        <section className={styles.distributionCard}>
          <h3>Canais</h3>
          {stats?.canais_distribution && Object.keys(stats.canais_distribution).length > 0 ? (
            <div className={styles.distributionList}>
              {Object.entries(stats.canais_distribution).map(([channel, count]) => (
                <div key={channel} className={styles.distributionItem}>
                  <span className={styles.distLabel}>{channel}</span>
                  <div className={styles.distBar}>
                    <div 
                      className={styles.distBarFill}
                      style={{ 
                        width: `${(count / (stats?.total_conversas || 1)) * 100}%`,
                        background: 'var(--accent-primary)'
                      }}
                    />
                  </div>
                  <span className={styles.distValue}>{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className={styles.empty}>Nenhum dado disponível</p>
          )}
        </section>
      </div>

      {/* System Status */}
      <section className={styles.statusSection}>
        <h3>Status do Sistema</h3>
        <div className={styles.statusGrid}>
          <div className={styles.statusItem}>
            <span className={styles.statusLabel}>Database</span>
            <span className={`${styles.statusBadge} ${configData?.database_connected ? styles.ok : styles.error}`}>
              {configData?.database_connected ? 'Conectado' : 'Erro'}
            </span>
          </div>
          <div className={styles.statusItem}>
            <span className={styles.statusLabel}>Ambiente</span>
            <span className={styles.statusValue}>{configData?.env}</span>
          </div>
          <div className={styles.statusItem}>
            <span className={styles.statusLabel}>Versão</span>
            <span className={styles.statusValue}>{configData?.version}</span>
          </div>
          <div className={styles.statusItem}>
            <span className={styles.statusLabel}>Collections RAG</span>
            <span className={styles.statusValue}>{configData?.chroma_collections?.length || 0}</span>
          </div>
        </div>
      </section>
    </div>
  );
}
