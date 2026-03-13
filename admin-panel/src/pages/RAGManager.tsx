import { useEffect, useState } from 'react';
import { X, Save, Plus, Trash2, FileText, Loader2, RotateCcw } from 'lucide-react';
import MDEditor from '@uiw/react-md-editor';
import { rag } from '../services/api';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import type { DocumentInfo, DocumentContent } from '../types';
import styles from './RAGManager.module.css';

export default function RAGManager() {
  const [tenantId, setTenantId] = useState('');
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [collectionName, setCollectionName] = useState('');
  const [sourceDir, setSourceDir] = useState('');
  const [chunksCount, setChunksCount] = useState(0);
  const [documentsCount, setDocumentsCount] = useState(0);
  const [ready, setReady] = useState(false);
  const [lastIngestedAt, setLastIngestedAt] = useState('');
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [ingestMessage, setIngestMessage] = useState('');
  const [loadingError, setLoadingError] = useState('');

  const [editingDoc, setEditingDoc] = useState<DocumentContent | null>(null);
  const [isNewDoc, setIsNewDoc] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newKeywords, setNewKeywords] = useState('');
  const [newIntents, setNewIntents] = useState('');

  useEffect(() => {
    if (!tenantId.trim()) {
      setDocuments([]);
      setCollectionName('');
      setSourceDir('');
      setChunksCount(0);
      setDocumentsCount(0);
      setReady(false);
      setLastIngestedAt('');
      setLoading(false);
      setLoadingError('');
      return;
    }
    fetchData(tenantId.trim());
  }, [tenantId]);

  const fetchData = async (currentTenantId: string) => {
    setLoading(true);
    setLoadingError('');
    try {
      const [docsRes, statusRes] = await Promise.all([
        rag.documents(currentTenantId),
        rag.status(currentTenantId),
      ]);
      setDocuments(docsRes.data.documents);
      setCollectionName(docsRes.data.collection_name);
      setSourceDir(docsRes.data.source_dir);
      setDocumentsCount(docsRes.data.documents_count);
      setChunksCount(statusRes.data.chunks_count);
      setReady(statusRes.data.ready);
      setLastIngestedAt(statusRes.data.last_ingested_at || '');
      setIngestMessage(statusRes.data.message);
    } catch (err: unknown) {
      console.error('Failed to fetch data:', err);
      setLoadingError('Não foi possível carregar o estado do tenant informado.');
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async (resetCollection: boolean) => {
    if (!tenantId.trim()) {
      setIngestMessage('tenant_id obrigatório');
      return;
    }
    setIngesting(true);
    setIngestMessage('');
    try {
      const response = await rag.ingest(tenantId.trim(), resetCollection);
      setIngestMessage(response.data.message);
      await fetchData(tenantId.trim());
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setIngestMessage(axiosError.response?.data?.detail || 'Erro ao executar ingestão');
      } else {
        setIngestMessage('Erro ao executar ingestão');
      }
    } finally {
      setIngesting(false);
    }
  };

  const handleReset = async () => {
    if (!tenantId.trim()) {
      setIngestMessage('tenant_id obrigatório');
      return;
    }
    setResetting(true);
    setIngestMessage('');
    try {
      const response = await rag.reset(tenantId.trim(), false);
      setIngestMessage(response.data.message);
      await fetchData(tenantId.trim());
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setIngestMessage(axiosError.response?.data?.detail || 'Erro ao executar reset');
      } else {
        setIngestMessage('Erro ao executar reset');
      }
    } finally {
      setResetting(false);
    }
  };

  const handleEdit = async (docId: string) => {
    if (!tenantId.trim()) return;
    try {
      const response = await rag.document(tenantId.trim(), docId);
      setEditingDoc(response.data);
      setIsNewDoc(false);
    } catch (err) {
      console.error('Failed to load document:', err);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!tenantId.trim()) {
      setIngestMessage('tenant_id obrigatório');
      return;
    }
    if (!confirm('Tem certeza que deseja excluir este documento?')) return;
    try {
      await rag.deleteDocument(tenantId.trim(), docId);
      await fetchData(tenantId.trim());
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  const handleSave = async () => {
    if (!tenantId.trim()) {
      setIngestMessage('tenant_id obrigatório');
      return;
    }
    if (!editingDoc && !isNewDoc) return;

    setSaving(true);
    try {
      if (isNewDoc) {
        await rag.createDocument({
          tenant_id: tenantId.trim(),
          title: newTitle,
          content: newContent,
          keywords: newKeywords.split(',').map(k => k.trim()).filter(Boolean),
          intents: newIntents.split(',').map(i => i.trim()).filter(Boolean),
        });
      } else if (editingDoc) {
        await rag.updateDocument(editingDoc.id, {
          tenant_id: tenantId.trim(),
          title: editingDoc.title,
          content: editingDoc.content,
          keywords: editingDoc.keywords,
          intents: editingDoc.intents,
        });
      }
      setEditingDoc(null);
      setIsNewDoc(false);
      setNewTitle('');
      setNewContent('');
      setNewKeywords('');
      setNewIntents('');
      await fetchData(tenantId.trim());
    } catch (err) {
      console.error('Failed to save document:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleNew = () => {
    setIsNewDoc(true);
    setEditingDoc(null);
    setNewTitle('');
    setNewContent('');
    setNewKeywords('');
    setNewIntents('');
  };

  const handleClose = () => {
    setEditingDoc(null);
    setIsNewDoc(false);
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>RAG Manager</h1>
        <p className={styles.subtitle}>Gerencie documentos e ingestão por tenant</p>
      </header>

      {(editingDoc || isNewDoc) && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h2>{isNewDoc ? 'Novo Documento' : 'Editar Documento'}</h2>
              <button onClick={handleClose} className={styles.closeBtn}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.modalBody}>
              <div className={styles.formGroup}>
                <label>Tenant</label>
                <Input value={tenantId} disabled />
              </div>

              <div className={styles.formGroup}>
                <label>Título</label>
                {isNewDoc ? (
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="Título do documento"
                    className={styles.input}
                  />
                ) : (
                  <input
                    type="text"
                    value={editingDoc?.title || ''}
                    onChange={(e) => setEditingDoc(prev => prev ? { ...prev, title: e.target.value } : null)}
                    className={styles.input}
                  />
                )}
              </div>

              <div className={styles.formGroup} data-color-mode="dark">
                <label>Conteúdo (Markdown)</label>
                <div className={styles.editorWrapper}>
                  <MDEditor
                    value={isNewDoc ? newContent : editingDoc?.content || ''}
                    onChange={(val) => {
                      if (isNewDoc) {
                        setNewContent(val || '');
                      } else {
                        setEditingDoc(prev => prev ? { ...prev, content: val || '' } : null);
                      }
                    }}
                    preview="edit"
                    height="100%"
                  />
                </div>
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>Keywords (separadas por vírgula)</label>
                  <input
                    type="text"
                    value={isNewDoc ? newKeywords : editingDoc?.keywords.join(', ') || ''}
                    onChange={(e) => isNewDoc ? setNewKeywords(e.target.value) : setEditingDoc(prev => prev ? { ...prev, keywords: e.target.value.split(',').map(k => k.trim()).filter(Boolean) } : null)}
                    placeholder="saude, horarios, atendimento"
                    className={styles.input}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>Intents (separados por vírgula)</label>
                  <input
                    type="text"
                    value={isNewDoc ? newIntents : editingDoc?.intents.join(', ') || ''}
                    onChange={(e) => isNewDoc ? setNewIntents(e.target.value) : setEditingDoc(prev => prev ? { ...prev, intents: e.target.value.split(',').map(i => i.trim()).filter(Boolean) } : null)}
                    placeholder="INFO_REQUEST, SCHEDULE_QUERY"
                    className={styles.input}
                  />
                </div>
              </div>
            </div>

            <div className={styles.modalFooter}>
              <Button variant="secondary" onClick={handleClose}>Cancelar</Button>
              <Button onClick={handleSave} isLoading={saving}>
                <Save size={16} />
                Salvar
              </Button>
            </div>
          </div>
        </div>
      )}

      <section className={styles.section}>
        <div className={styles.tenantBar}>
          <Input
            label="Tenant ID"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            placeholder="prefeitura-demo"
          />
          <div className={styles.tenantHint}>
            O fluxo de ingestão da base nova exige `tenant_id` explícito.
          </div>
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.baseInfo}>
          <div className={styles.baseMeta}>
            <FileText size={20} />
            <div>
              <h3>{collectionName || 'Sem tenant selecionado'}</h3>
              <span>{sourceDir || 'Informe um tenant para carregar a base.'}</span>
            </div>
          </div>
          <div className={styles.actions}>
            <Button variant="primary" onClick={handleNew} disabled={!tenantId.trim()}>
              <Plus size={16} />
              Novo Documento
            </Button>
            <Button variant="secondary" onClick={() => handleIngest(true)} isLoading={ingesting} disabled={!tenantId.trim()}>
              <Loader2 size={16} />
              Ingerir
            </Button>
            <Button variant="secondary" onClick={handleReset} isLoading={resetting} disabled={!tenantId.trim()}>
              <RotateCcw size={16} />
              Resetar Collection
            </Button>
          </div>
        </div>

        <div className={styles.statusMeta}>
          <span className={ready ? styles.statusReady : styles.statusPending}>
            {ready ? 'Base pronta' : 'Base pendente'}
          </span>
          <span>{documentsCount} documento(s)</span>
          <span>{chunksCount} chunk(s)</span>
          <span>{lastIngestedAt ? `Última ingestão: ${new Date(lastIngestedAt).toLocaleString()}` : 'Nenhuma ingestão executada'}</span>
        </div>

        {loading && <div className={styles.ingestMessage}>Carregando estado do tenant...</div>}
        {loadingError && <div className={styles.ingestMessage}>{loadingError}</div>}
        {ingestMessage && <div className={styles.ingestMessage}>{ingestMessage}</div>}
      </section>

      <section className={styles.section}>
        <h2>Documentos ({documents.length})</h2>
        {!tenantId.trim() && (
          <div className={styles.emptyState}>Informe um tenant para listar documentos.</div>
        )}
        {tenantId.trim() && documents.length === 0 && !loading && (
          <div className={styles.emptyState}>Nenhum documento cadastrado para este tenant.</div>
        )}
        <div className={styles.docsList}>
          {documents.map((doc) => (
            <div key={doc.id} className={styles.docCard}>
              <div className={styles.docIcon}>
                <FileText size={20} />
              </div>
              <div className={styles.docInfo}>
                <h4>{doc.title}</h4>
                <span className={styles.docFile}>{doc.file}</span>
                <div className={styles.docTags}>
                  {doc.intents.map((intent) => (
                    <span key={intent} className={styles.intentTag}>{intent}</span>
                  ))}
                  {doc.tags.map((tag) => (
                    <span key={tag} className={styles.keywordTag}>{tag}</span>
                  ))}
                </div>
              </div>
              <div className={styles.docActions}>
                <Button variant="ghost" size="sm" onClick={() => handleEdit(doc.id)}>Editar</Button>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(doc.id)}>
                  <Trash2 size={14} />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
