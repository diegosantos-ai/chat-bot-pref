import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';
import { ops } from '../services/api';
import { Button } from '../components/Button';
import type { ValidationResult } from '../types';
import styles from './Ops.module.css';

export default function Ops() {
  const [validating, setValidating] = useState(false);
  const [result, setResult] = useState<ValidationResult | null>(null);

  const handleValidate = async () => {
    setValidating(true);
    setResult(null);
    try {
      const response = await ops.validate();
      setResult(response.data);
    } catch (err) {
      console.error('Validation failed:', err);
    } finally {
      setValidating(false);
    }
  };

  useEffect(() => {
    handleValidate();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ok': return <CheckCircle size={20} className={styles.iconOk} />;
      case 'error': return <XCircle size={20} className={styles.iconError} />;
      case 'warning': return <AlertCircle size={20} className={styles.iconWarning} />;
      default: return <AlertCircle size={20} className={styles.iconUnknown} />;
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Operações</h1>
        <p className={styles.subtitle}>Validação e ferramentas do sistema</p>
      </header>

      {/* Validate Section */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <h2>Validação de Infraestrutura</h2>
            <p>Verifique o status dos componentes do sistema</p>
          </div>
          <Button onClick={handleValidate} isLoading={validating}>
            <Loader2 size={16} />
            Validar
          </Button>
        </div>

        {result && (
          <div className={styles.validationGrid}>
            <div className={styles.validationCard}>
              <div className={styles.validationHeader}>
                {getStatusIcon(result.database.status)}
                <span>Database</span>
              </div>
              <p className={styles.validationMessage}>{result.database.message}</p>
            </div>

            <div className={styles.validationCard}>
              <div className={styles.validationHeader}>
                {getStatusIcon(result.chroma.status)}
                <span>ChromaDB</span>
              </div>
              <p className={styles.validationMessage}>{result.chroma.message}</p>
            </div>

            <div className={styles.validationCard}>
              <div className={styles.validationHeader}>
                {getStatusIcon(result.gemini.status)}
                <span>Google Gemini</span>
              </div>
              <p className={styles.validationMessage}>{result.gemini.message}</p>
            </div>
          </div>
        )}
      </section>

      {/* Info Section */}
      <section className={styles.section}>
        <h2>Scripts Disponíveis</h2>
        <div className={styles.scriptsList}>
          <div className={styles.scriptCard}>
            <h4>Criar Usuário Admin</h4>
            <code>python scripts/admin_create_user.py</code>
            <p>Cria um novo usuário para o painel administrativo</p>
          </div>
          <div className={styles.scriptCard}>
            <h4>Remover Usuário Admin</h4>
            <code>python scripts/admin_delete_user.py</code>
            <p>Remove um usuário administrativo</p>
          </div>
          <div className={styles.scriptCard}>
            <h4>Ingestão RAG</h4>
            <code>python -m app.rag.ingest &lt;caminho&gt;</code>
            <p>Ingere documentos na base de conhecimento</p>
          </div>
        </div>
      </section>
    </div>
  );
}
