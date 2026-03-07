/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from 'react';
import { Trash2, Edit2, Zap, Tag, FileText, Folder } from 'lucide-react';
import { boosts } from '../services/api';
import type { BoostConfig, BoostConfigCreate, BoostTemplate } from '../types';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import styles from './Boosts.module.css';

const TIPO_ICONS: Record<string, typeof Zap> = {
  sigla: Tag,
  palavra_chave: FileText,
  categoria: Folder,
};

const TIPO_LABELS: Record<string, string> = {
  sigla: 'Sigla',
  palavra_chave: 'Palavra-chave',
  categoria: 'Categoria',
};

export default function BoostsPage() {
  const [boostsList, setBoostsList] = useState<BoostConfig[]>([]);
  const [templates, setTemplates] = useState<BoostTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterTipo, setFilterTipo] = useState<string>('');
  const [filterAtivo, setFilterAtivo] = useState<string>('');
  const [showModal, setShowModal] = useState(false);
  const [editingBoost, setEditingBoost] = useState<BoostConfig | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);

  const [formData, setFormData] = useState<BoostConfigCreate>({
    nome: '',
    tipo: 'sigla',
    valor: '',
    boost_value: 0.2,
    prioridade: 0,
    ativo: true,
  });

  useEffect(() => {
    loadBoosts();
    loadTemplates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadBoosts = async () => {
    try {
      const params: { tipo?: string; ativo?: boolean } = {};
      if (filterTipo) params.tipo = filterTipo;
      if (filterAtivo === 'true') params.ativo = true;
      if (filterAtivo === 'false') params.ativo = false;

      const response = await boosts.list(params);
      setBoostsList(response.data);
    } catch (err) {
      console.error('Failed to load boosts:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await boosts.templates();
      setTemplates(response.data);
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingBoost) {
        await boosts.update(editingBoost.id, formData);
      } else {
        await boosts.create(formData);
      }
      setShowModal(false);
      setEditingBoost(null);
      resetForm();
      loadBoosts();
    } catch (err) {
      console.error('Failed to save boost:', err);
    }
  };

  const handleEdit = (boost: BoostConfig) => {
    setEditingBoost(boost);
    setFormData({
      nome: boost.nome,
      tipo: boost.tipo,
      valor: boost.valor,
      boost_value: boost.boost_value,
      prioridade: boost.prioridade,
      ativo: boost.ativo,
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja remover este boost?')) return;
    try {
      await boosts.delete(id);
      loadBoosts();
    } catch (err) {
      console.error('Failed to delete boost:', err);
    }
  };

  const handleToggle = async (boost: BoostConfig) => {
    try {
      await boosts.update(boost.id, { ativo: !boost.ativo });
      loadBoosts();
    } catch (err) {
      console.error('Failed to toggle boost:', err);
    }
  };

  const handleImport = async () => {
    try {
      const response = await boosts.import();
      alert(`Importado: ${response.data.imported}, Já existiam: ${response.data.skipped}`);
      loadBoosts();
    } catch (err) {
      console.error('Failed to import:', err);
    }
  };

  const handleQuickAdd = (template: BoostTemplate) => {
    setFormData({
      nome: template.sigla,
      tipo: 'sigla',
      valor: template.sigla,
      boost_value: 0.2,
      prioridade: boostsList.length + 1,
      ativo: true,
    });
    setShowModal(true);
    setShowTemplates(false);
  };

  const resetForm = () => {
    setFormData({
      nome: '',
      tipo: 'sigla',
      valor: '',
      boost_value: 0.2,
      prioridade: 0,
      ativo: true,
    });
  };

  const openNewModal = () => {
    setEditingBoost(null);
    resetForm();
    setShowModal(true);
  };

  const filteredBoosts = boostsList;

  const siglas = filteredBoosts.filter(b => b.tipo === 'sigla');
  const palavras = filteredBoosts.filter(b => b.tipo === 'palavra_chave');
  const categorias = filteredBoosts.filter(b => b.tipo === 'categoria');

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>⚡ Boosts</h1>
        <p className={styles.subtitle}>Configure boosts para melhorar relevância das buscas RAG</p>
      </header>

      <div className={styles.toolbar}>
        <div className={styles.filters}>
          <select
            value={filterTipo}
            onChange={(e) => { setFilterTipo(e.target.value); loadBoosts(); }}
            className={styles.select}
          >
            <option value="">Todos os tipos</option>
            <option value="sigla">Siglas</option>
            <option value="palavra_chave">Palavras-chave</option>
            <option value="categoria">Categorias</option>
          </select>

          <select
            value={filterAtivo}
            onChange={(e) => { setFilterAtivo(e.target.value); loadBoosts(); }}
            className={styles.select}
          >
            <option value="">Todos</option>
            <option value="true">Ativos</option>
            <option value="false">Inativos</option>
          </select>
        </div>

        <div className={styles.actions}>
          <Button variant="secondary" onClick={() => setShowTemplates(!showTemplates)}>
            Templates ({templates.length})
          </Button>
          <Button variant="secondary" onClick={handleImport}>
            Importar Siglas
          </Button>
          <Button onClick={openNewModal}>
            + Adicionar Boost
          </Button>
        </div>
      </div>

      {showTemplates && (
        <div className={styles.templatesPanel}>
          <h3>Siglas Disponíveis (clique para adicionar)</h3>
          <div className={styles.templatesList}>
            {templates.map((t) => (
              <button
                key={t.sigla}
                className={styles.templateTag}
                onClick={() => handleQuickAdd(t)}
              >
                {t.sigla}
              </button>
            ))}
          </div>
        </div>
      )}

      {loading ? (
        <div className={styles.loading}>Carregando...</div>
      ) : (
        <div className={styles.sections}>
          {siglas.length > 0 && (
            <section className={styles.section}>
              <h2><Tag size={18} /> Siglas ({siglas.length})</h2>
              <div className={styles.list}>
                {siglas.map((boost) => (
                  <BoostCard
                    key={boost.id}
                    boost={boost}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onToggle={handleToggle}
                  />
                ))}
              </div>
            </section>
          )}

          {palavras.length > 0 && (
            <section className={styles.section}>
              <h2><FileText size={18} /> Palavras-chave ({palavras.length})</h2>
              <div className={styles.list}>
                {palavras.map((boost) => (
                  <BoostCard
                    key={boost.id}
                    boost={boost}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onToggle={handleToggle}
                  />
                ))}
              </div>
            </section>
          )}

          {categorias.length > 0 && (
            <section className={styles.section}>
              <h2><Folder size={18} /> Categorias ({categorias.length})</h2>
              <div className={styles.list}>
                {categorias.map((boost) => (
                  <BoostCard
                    key={boost.id}
                    boost={boost}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onToggle={handleToggle}
                  />
                ))}
              </div>
            </section>
          )}

          {filteredBoosts.length === 0 && (
            <div className={styles.empty}>
              Nenhum boost configurado. Clique em "Adicionar Boost" para começar.
            </div>
          )}
        </div>
      )}

      {showModal && (
        <div className={styles.modalOverlay} onClick={() => setShowModal(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2>{editingBoost ? 'Editar Boost' : 'Novo Boost'}</h2>
            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label>Tipo</label>
                <select
                  value={formData.tipo}
                  onChange={(e) => setFormData({ ...formData, tipo: e.target.value as any })}
                  className={styles.select}
                >
                  <option value="sigla">Sigla</option>
                  <option value="palavra_chave">Palavra-chave</option>
                  <option value="categoria">Categoria</option>
                </select>
              </div>

              <Input
                label="Nome"
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                placeholder={formData.tipo === 'sigla' ? 'REFIS' : 'Vacinação'}
                required
              />

              <Input
                label={formData.tipo === 'sigla' ? 'Sigla (valor)' : 'Valor'}
                value={formData.valor}
                onChange={(e) => setFormData({ ...formData, valor: e.target.value })}
                placeholder={
                  formData.tipo === 'sigla'
                    ? 'REFIS'
                    : formData.tipo === 'palavra_chave'
                      ? 'vacina, covid, imunização'
                      : 'saude, educacao'
                }
                required
              />

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label>Boost (+)</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={formData.boost_value}
                    onChange={(e) => setFormData({ ...formData, boost_value: parseFloat(e.target.value) })}
                    className={styles.input}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>Prioridade</label>
                  <input
                    type="number"
                    value={formData.prioridade}
                    onChange={(e) => setFormData({ ...formData, prioridade: parseInt(e.target.value) })}
                    className={styles.input}
                  />
                </div>
              </div>

              <label className={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={formData.ativo}
                  onChange={(e) => setFormData({ ...formData, ativo: e.target.checked })}
                />
                Ativo
              </label>

              <div className={styles.modalActions}>
                <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>
                  Cancelar
                </Button>
                <Button type="submit">
                  Salvar
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function BoostCard({
  boost,
  onEdit,
  onDelete,
  onToggle
}: {
  boost: BoostConfig;
  onEdit: (b: BoostConfig) => void;
  onDelete: (id: string) => void;
  onToggle: (b: BoostConfig) => void;
}) {
  const Icon = TIPO_ICONS[boost.tipo] || Tag;

  return (
    <div className={`${styles.card} ${!boost.ativo ? styles.inactive : ''}`}>
      <div className={styles.cardIcon}>
        <Icon size={16} />
      </div>
      <div className={styles.cardContent}>
        <div className={styles.cardHeader}>
          <strong>{boost.nome}</strong>
          <span className={styles.tipoBadge}>{TIPO_LABELS[boost.tipo]}</span>
        </div>
        <div className={styles.cardValue}>{boost.valor}</div>
        <div className={styles.cardMeta}>
          <span className={styles.boostValue}>+{boost.boost_value.toFixed(2)}</span>
          <span>Prioridade: {boost.prioridade}</span>
        </div>
      </div>
      <div className={styles.cardActions}>
        <button
          className={`${styles.toggleBtn} ${boost.ativo ? styles.active : ''}`}
          onClick={() => onToggle(boost)}
          title={boost.ativo ? 'Desativar' : 'Ativar'}
        >
          <Zap size={14} />
        </button>
        <button className={styles.editBtn} onClick={() => onEdit(boost)}>
          <Edit2 size={14} />
        </button>
        <button className={styles.deleteBtn} onClick={() => onDelete(boost.id)}>
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
}
