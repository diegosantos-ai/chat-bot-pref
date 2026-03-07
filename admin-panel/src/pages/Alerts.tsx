import { useState } from 'react';
import { Send, Megaphone, Smartphone, BellRing } from 'lucide-react';
import styles from './Alerts.module.css';

export default function Alerts() {
    const [targetAudience, setTargetAudience] = useState('all');
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!message) return;

        setLoading(true);
        // Mock the send action
        setTimeout(() => {
            setLoading(false);
            setSuccess(true);
            setMessage('');
            setTimeout(() => setSuccess(false), 3000);
        }, 1500);
    };

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Megaphone size={28} color="var(--accent-primary)" />
                    Disparo de Alertas
                </h1>
                <p className={styles.subtitle}>Comunicação em massa proativa para os cidadãos (MÓDULO DEMO)</p>
            </header>

            <div className={styles.grid}>
                {/* Formulário */}
                <section className={styles.panel}>
                    <h2>Configurar Alerta</h2>
                    <form onSubmit={handleSubmit}>
                        <div className={styles.formGroup}>
                            <label htmlFor="audience">Público Alvo</label>
                            <select
                                id="audience"
                                value={targetAudience}
                                onChange={(e) => setTargetAudience(e.target.value)}
                            >
                                <option value="all">Todos os contatos base Meta</option>
                                <option value="bairro_centro">Moradores - Bairro Centro</option>
                                <option value="bairro_norte">Moradores - Região Norte</option>
                                <option value="grupo_risco">Cadastrados - Grupo de Risco</option>
                            </select>
                            <span className={styles.helperText}>Filtro de cidadãos ativos nos últimos 90 dias.</span>
                        </div>

                        <div className={styles.formGroup}>
                            <label htmlFor="urgency">Nível de Urgência</label>
                            <select id="urgency">
                                <option value="normal">Informativo Normal</option>
                                <option value="alert">Alerta (Defesa Civil, Trânsito)</option>
                                <option value="emergency">Emergência Crítica</option>
                            </select>
                        </div>

                        <div className={styles.formGroup}>
                            <label htmlFor="message">Mensagem do Bot</label>
                            <textarea
                                id="message"
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                placeholder="Ex: 🚨 ALERTA DEFESA CIVIL: Previsão de chuvas fortes..."
                                required
                            />
                            <span className={styles.helperText}>Máx 1024 caracteres. Links serão renderizados normalmente.</span>
                        </div>

                        <button
                            type="submit"
                            className={styles.submitBtn}
                            disabled={loading || !message}
                            style={{ background: success ? 'var(--success)' : '' }}
                        >
                            {loading ? 'Preparando Disparo...' :
                                success ? 'DISPARADO COM SUCESSO' :
                                    <><Send size={18} /> DISPARAR ALERTA (MOCK)</>}
                        </button>
                    </form>
                </section>

                {/* Preview */}
                <section className={styles.panel} style={{ background: '#000', borderColor: '#333' }}>
                    <h2 style={{ color: '#fff' }}><Smartphone size={20} /> Preview Whatsapp/Meta</h2>
                    <div className={styles.phonePreview}>
                        <div className={styles.phoneHeader}>
                            <div className={styles.avatar}>🏛️</div>
                            <span className={styles.phoneTitle}>Prefeitura Bot</span>
                        </div>
                        <div className={styles.phoneBody}>
                            {message ? (
                                <div className={styles.messageBubble}>
                                    {message}
                                </div>
                            ) : (
                                <div className={styles.emptyState}>
                                    <BellRing size={32} opacity={0.5} style={{ margin: '0 auto 16px' }} />
                                    Digite uma mensagem para ver o preview aqui
                                </div>
                            )}
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
