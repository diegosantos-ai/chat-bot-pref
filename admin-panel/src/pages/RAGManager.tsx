import { useState, useEffect } from 'react';
import { X, Save, Plus, Trash2, FileText, Loader2 } from 'lucide-react';
import MDEditor from '@uiw/react-md-editor';
import { rag } from '../services/api';
import { Button } from '../components/Button';
import type { DocumentInfo, DocumentContent } from '../types';
import styles from './RAGManager.module.css';

export default function RAGManager() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [baseId, setBaseId] = useState('');
  const [version, setVersion] = useState('');
  const [loading, setLoading] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [ingestMessage, setIngestMessage] = useState('');
  
  const [editingDoc, setEditingDoc] = useState<DocumentContent | null>(null);
  const [isNewDoc, setIsNewDoc] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newKeywords, setNewKeywords] = useState('');
  const [newIntents, setNewIntents] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const docsRes = await rag.documents();
      setDocuments(docsRes.data.documents);
      setBaseId(docsRes.data.base_id);
      setVersion(docsRes.data.version);
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async (force: boolean = false) => {
    setIngesting(true);
    setIngestMessage('');
    try {
      const response = await rag.ingest(undefined, force);
      setIngestMessage(response.data.message);
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

  const handleEdit = async (docId: string) => {
    try {
      const response = await rag.document(docId);
      setEditingDoc(response.data);
      setIsNewDoc(false);
    } catch (err) {
      console.error('Failed to load document:', err);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('Tem certeza que deseja excluir este documento?')) return;
    try {
      await rag.deleteDocument(docId);
      fetchData();
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  const handleSave = async () => {
    if (!editingDoc && !isNewDoc) return;
    
    setSaving(true);
    try {
      if (isNewDoc) {
        await rag.createDocument({
          title: newTitle,
          content: newContent,
          keywords: newKeywords.split(',').map(k => k.trim()).filter(Boolean),
          intents: newIntents.split(',').map(i => i.trim()).filter(Boolean),
        });
      } else if (editingDoc) {
        await rag.updateDocument(editingDoc.id, {
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
      fetchData();
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

  if (loading) {
    return <div className={styles.loading}>Carregando...</div>;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>RAG Manager</h1>
        <p className={styles.subtitle}>Gerencie a base de conhecimento</p>
      </header>

      {/* Editor Modal */}
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

      {/* Base Info */}
      <section className={styles.section}>
        <div className={styles.baseInfo}>
          <div className={styles.baseMeta}>
            <FileText size={20} />
            <div>
              <h3>{baseId}</h3>
              <span>Versão {version}</span>
            </div>
          </div>
          <div className={styles.actions}>
            <Button variant="primary" onClick={handleNew}>
              <Plus size={16} />
              Novo Documento
            </Button>
            <Button variant="secondary" onClick={() => handleIngest(false)} isLoading={ingesting}>
              <Loader2 size={16} />
              Re-ingest
            </Button>
            <Button variant="secondary" onClick={() => handleIngest(true)} isLoading={ingesting}>
              Force Re-ingest
            </Button>
          </div>
        </div>
        
        {ingestMessage && (
          <div className={styles.ingestMessage}>{ingestMessage}</div>
        )}
      </section>

      {/* Documents List */}
      <section className={styles.section}>
        <h2>Documentos ({documents.length})</h2>
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
