import { useState, useEffect, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from '@xyflow/react';
import type { Connection, Node, Edge, NodeTypes } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { scrap } from '../services/api';
import type { 
  ScrapConfig, 
  ScrapExecuteResponse,
  ScrapResult,
  ScrapSchedule
} from '../types';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import styles from './Scrap.module.css';

type ScrapNodeData = {
  label: string;
  url?: string;
  listSelector?: string;
  itemSelector?: string;
  fields?: { name: string; selector: string; type: string }[];
  followLinks?: boolean;
  linkSelector?: string;
  maxPages?: number;
  pageParam?: string;
  paginationType?: 'none' | 'next' | 'param';
};

const nodeStyles: React.CSSProperties = {
  padding: '12px 16px',
  borderRadius: '8px',
  background: '#1e1e22',
  border: '1px solid #333',
  color: '#e5e5e5',
  minWidth: '180px',
  fontSize: '13px',
};

function SourceNode({ data, selected }: { data: ScrapNodeData; selected?: boolean }) {
  return (
    <div style={{ 
      ...nodeStyles, 
      border: selected ? '2px solid #a78bfa' : '1px solid #333',
      background: '#1a1a2e'
    }}>
      <Handle type="source" position={Position.Right} style={{ background: '#a78bfa' }} />
      <div style={{ fontWeight: 600, marginBottom: 4 }}>🌐 URL</div>
      <div style={{ fontSize: 11, color: '#888' }}>{data.url || 'Não definido'}</div>
    </div>
  );
}

function ListNode({ data, selected }: { data: ScrapNodeData; selected?: boolean }) {
  return (
    <div style={{ 
      ...nodeStyles, 
      border: selected ? '2px solid #a78bfa' : '1px solid #333',
      background: '#1a2a1a'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: '#22c55e' }} />
      <Handle type="source" position={Position.Right} style={{ background: '#22c55e' }} />
      <div style={{ fontWeight: 600, marginBottom: 4 }}>📋 Lista</div>
      <div style={{ fontSize: 10, color: '#888' }}>
        {data.listSelector || 'Sem seletor'}
      </div>
    </div>
  );
}

function ItemNode({ data, selected }: { data: ScrapNodeData; selected?: boolean }) {
  return (
    <div style={{ 
      ...nodeStyles, 
      border: selected ? '2px solid #a78bfa' : '1px solid #333',
      background: '#2a1a2a'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: '#f472b6' }} />
      <Handle type="source" position={Position.Right} style={{ background: '#f472b6' }} />
      <div style={{ fontWeight: 600, marginBottom: 4 }}>📄 Itens</div>
      <div style={{ fontSize: 10, color: '#888' }}>
        {data.itemSelector || 'Sem seletor'}
      </div>
      {data.fields && data.fields.length > 0 && (
        <div style={{ fontSize: 10, color: '#22c55e', marginTop: 4 }}>
          {data.fields.length} campo(s)
        </div>
      )}
    </div>
  );
}

function DetailNode({ data, selected }: { data: ScrapNodeData; selected?: boolean }) {
  return (
    <div style={{ 
      ...nodeStyles, 
      border: selected ? '2px solid #a78bfa' : '1px solid #333',
      background: '#1a2a2a'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: '#38bdf8' }} />
      <div style={{ fontWeight: 600, marginBottom: 4 }}>🔗 Detalhe</div>
      <div style={{ fontSize: 10, color: '#888' }}>
        {data.url || 'Segue do item'}
      </div>
      {data.fields && data.fields.length > 0 && (
        <div style={{ fontSize: 10, color: '#22c55e', marginTop: 4 }}>
          {data.fields.length} campo(s)
        </div>
      )}
    </div>
  );
}

const nodeTypes: NodeTypes = {
  source: SourceNode,
  list: ListNode,
  item: ItemNode,
  detail: DetailNode,
};

export default function ScrapPage() {
  const [configs, setConfigs] = useState<ScrapConfig[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<ScrapConfig | null>(null);
  const [configName, setConfigName] = useState('');
  const [nodes, setNodes, onNodesChange] = useNodesState([] as any[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as any[]);
  const [activeTab, setActiveTab] = useState<'builder' | 'results' | 'schedules'>('builder');
  const [loading, setLoading] = useState(false);
  const [executeResult, setExecuteResult] = useState<ScrapExecuteResponse | null>(null);
  const [schedules, setSchedules] = useState<ScrapSchedule[]>([]);
  const [results, setResults] = useState<ScrapResult[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [showInteractive, setShowInteractive] = useState(false);
  const [interactiveData, setInteractiveData] = useState<any>(null);

  const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const addNode = (type: string) => {
    const id = `${type}_${Date.now()}`;
    const newNode: Node = {
      id,
      type,
      position: { x: 250 + Math.random() * 200, y: 100 + nodes.length * 120 },
      data: { 
        label: type.charAt(0).toUpperCase() + type.slice(1),
        url: type === 'source' ? 'https://...' : undefined,
        listSelector: type === 'list' ? '.lista > li' : undefined,
        itemSelector: type === 'item' ? 'li' : undefined,
        fields: [],
        paginationType: 'none',
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const updateSelectedNode = (key: string, value: any) => {
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === selectedNode.id) {
          return { ...node, data: { ...node.data, [key]: value } };
        }
        return node;
      })
    );
  };

  const deleteSelectedNode = () => {
    if (!selectedNode || selectedNode.type === 'source') return;
    setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
    setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
    setSelectedNode(null);
  };

  const loadConfigs = async () => {
    try {
      const response = await scrap.configs.list();
      setConfigs(response.data);
    } catch (err) {
      console.error('Failed to load configs:', err);
    }
  };

  const handleSaveConfig = async () => {
    if (!configName) return;
    
    const workflow: any = {
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.type,
        label: n.data.label,
        url: n.data.url,
        listSelector: n.data.listSelector,
        itemSelector: n.data.itemSelector,
        fields: n.data.fields,
        followLinks: n.data.followLinks,
        linkSelector: n.data.linkSelector,
        paginationType: n.data.paginationType,
        maxPages: n.data.maxPages,
      })),
      edges: edges.map(e => ({ source: e.source, target: e.target })),
    };

    try {
      await scrap.configs.create({
        nome: configName,
        url_base: nodes.find(n => n.type === 'source')?.data.url as string || '',
        workflow
      } as any);
      await loadConfigs();
      setConfigName('');
    } catch (err) {
      console.error('Save failed:', err);
    }
  };

  const handleExecute = async () => {
    if (!selectedConfig) return;
    setLoading(true);
    try {
      const response = await scrap.execute(selectedConfig.id, { limit: 20 });
      setExecuteResult(response.data);
      loadResults();
    } catch (err) {
      console.error('Execute failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadResults = async () => {
    if (!selectedConfig) return;
    try {
      const response = await scrap.results.list(selectedConfig.id, 10);
      setResults(response.data);
    } catch (err) {
      console.error('Failed to load results:', err);
    }
  };

  const loadSchedules = async () => {
    if (!selectedConfig) return;
    try {
      const response = await scrap.schedules.list(selectedConfig.id);
      setSchedules(response.data);
    } catch (err) {
      console.error('Failed to load schedules:', err);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  useEffect(() => {
    if (selectedConfig) {
      loadSchedules();
      loadResults();
      setConfigName(selectedConfig.nome);
      
      if ((selectedConfig as any).workflow?.nodes) {
        const wf = (selectedConfig as any).workflow;
        const flowNodes: Node[] = (wf.nodes || []).map((n: any) => ({
          id: n.id,
          type: n.type || 'list',
          position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
          data: {
            label: n.label || n.type,
            url: n.url,
            listSelector: n.listSelector,
            itemSelector: n.itemSelector,
            fields: n.fields || [],
            followLinks: n.followLinks,
            linkSelector: n.linkSelector,
            paginationType: n.paginationType,
            maxPages: n.maxPages,
          }
        }));
        const flowEdges: Edge[] = (wf.edges || []).map((e: any) => ({
          id: `${e.source}-${e.target}`,
          source: e.source,
          target: e.target,
        }));
        setNodes(flowNodes);
        setEdges(flowEdges);
      }
    }
  }, [selectedConfig]);

  const handleInteractivePreview = async () => {
    const sourceNode = nodes.find(n => n.type === 'source');
    if (!sourceNode?.data?.url) return;
    setPreviewLoading(true);
    setShowInteractive(true);
    try {
      const response = await scrap.previewInteractive(sourceNode.data.url as string);
      setInteractiveData(response.data);
    } catch (err) {
      console.error('Interactive preview failed:', err);
    } finally {
      setPreviewLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>🕸️ Scraping</h1>
        <p className={styles.subtitle}>Workflow visual estilo n8n - arraste e conecte os nodes</p>
      </header>

      <div className={styles.layout}>
        <aside className={styles.sidebar}>
          <div className={styles.sidebarSection}>
            <h3>Configurações</h3>
            <Input
              placeholder="Nome da configuração"
              value={configName}
              onChange={(e) => setConfigName(e.target.value)}
            />
            <Button onClick={handleSaveConfig} disabled={!configName || nodes.length === 0}>
              Salvar
            </Button>
          </div>

          <div className={styles.sidebarSection}>
            <h3>Nodes</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <Button variant="secondary" onClick={() => addNode('source')} disabled={nodes.some(n => n.type === 'source')}>
                🌐 URL Base
              </Button>
              <Button variant="secondary" onClick={() => addNode('list')}>
                📋 Extrair Lista
              </Button>
              <Button variant="secondary" onClick={() => addNode('item')}>
                📄 Extrair Itens
              </Button>
              <Button variant="secondary" onClick={() => addNode('detail')}>
                🔗 Página Detalhe
              </Button>
            </div>
          </div>

          <div className={styles.sidebarSection}>
            <h3>Salvos</h3>
            <div className={styles.configList}>
              {configs.map((config) => (
                <div
                  key={config.id}
                  className={`${styles.configItem} ${selectedConfig?.id === config.id ? styles.active : ''}`}
                  onClick={() => setSelectedConfig(config)}
                >
                  <span>{config.nome}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <main className={styles.main}>
          <div className={styles.tabs}>
            <button
              className={`${styles.tab} ${activeTab === 'builder' ? styles.active : ''}`}
              onClick={() => setActiveTab('builder')}
            >
              Construtor
            </button>
            <button
              className={`${styles.tab} ${activeTab === 'results' ? styles.active : ''}`}
              onClick={() => setActiveTab('results')}
            >
              Resultados
            </button>
            <button
              className={`${styles.tab} ${activeTab === 'schedules' ? styles.active : ''}`}
              onClick={() => setActiveTab('schedules')}
            >
              Agendamentos
            </button>
          </div>

          {activeTab === 'builder' && (
            <div className={styles.builder}>
              <div className={styles.toolbar}>
                <Button variant="secondary" onClick={handleInteractivePreview} disabled={previewLoading || !nodes.find(n => n.type === 'source')?.data?.url}>
                  {previewLoading ? 'Carregando...' : '🎯 Preview Interativo'}
                </Button>
                <Button onClick={handleExecute} disabled={!selectedConfig || loading}>
                  {loading ? 'Executando...' : '▶ Executar'}
                </Button>
              </div>

              <div className={styles.flowWrapper}>
                <ReactFlow
                  nodes={nodes}
                  edges={edges}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  onConnect={onConnect}
                  onNodeClick={(_, node) => setSelectedNode(node)}
                  nodeTypes={nodeTypes}
                  fitView
                  style={{ background: '#0a0a0b' }}
                >
                  <Background color="#333" gap={20} />
                  <Controls />
                  <MiniMap nodeColor={() => '#a78bfa'} />
                </ReactFlow>
              </div>

              {selectedNode && (
                <div className={styles.nodeConfig}>
                  <div className={styles.nodeConfigHeader}>
                    <h4>Editar: {String(selectedNode.data?.label || '')}</h4>
                    {selectedNode.type !== 'source' && (
                      <Button variant="secondary" onClick={deleteSelectedNode}>🗑️ Excluir</Button>
                    )}
                  </div>
                  
                  {selectedNode.type === 'source' && (
                    <>
                      <Input
                        label="URL"
                        value={selectedNode.data.url as string || ''}
                        onChange={(e) => updateSelectedNode('url', e.target.value)}
                        placeholder="https://exemplo.com/noticias"
                      />
                    </>
                  )}

                  {selectedNode.type === 'list' && (
                    <>
                      <Input
                        label="Selector da Lista"
                        value={selectedNode.data.listSelector as string || ''}
                        onChange={(e) => updateSelectedNode('listSelector', e.target.value)}
                        placeholder=".noticias > li"
                      />
                      <label className={styles.checkbox}>
                        <input
                          type="checkbox"
                          checked={selectedNode.data.followLinks as boolean || false}
                          onChange={(e) => updateSelectedNode('followLinks', e.target.checked)}
                        />
                        Seguir Links
                      </label>
                      {selectedNode.data.followLinks && (
                        <Input
                          label="Selector do Link"
                          value={selectedNode.data.linkSelector as string || ''}
                          onChange={(e) => updateSelectedNode('linkSelector', e.target.value)}
                          placeholder="a@href"
                        />
                      )}
                      <div className={styles.paginationSection}>
                        <label className={styles.checkbox}>
                          <input
                            type="checkbox"
                            checked={(selectedNode.data.paginationType as string) !== 'none'}
                            onChange={(e) => updateSelectedNode('paginationType', e.target.checked ? 'param' : 'none')}
                          />
                          Paginação
                        </label>
                        {(selectedNode.data.paginationType as string) !== 'none' && (
                          <>
                            <select
                              value={selectedNode.data.paginationType as string || 'param'}
                              onChange={(e) => updateSelectedNode('paginationType', e.target.value)}
                              className={styles.select}
                            >
                              <option value="param">Parâmetro URL (?pag=2)</option>
                              <option value="next">Botão Próxima</option>
                            </select>
                            <Input
                              label="Máx páginas"
                              type="number"
                              value={selectedNode.data.maxPages as number || 5}
                              onChange={(e) => updateSelectedNode('maxPages', parseInt(e.target.value))}
                            />
                          </>
                        )}
                      </div>
                    </>
                  )}

                  {selectedNode.type === 'item' && (
                    <>
                      <Input
                        label="Selector do Item"
                        value={selectedNode.data.itemSelector as string || ''}
                        onChange={(e) => updateSelectedNode('itemSelector', e.target.value)}
                        placeholder="li, article, .item"
                      />
                      <div className={styles.fieldsSection}>
                        <h5>Campos</h5>
                        {((selectedNode.data.fields as any[]) || []).map((field: any, i: number) => (
                          <div key={i} className={styles.fieldRow}>
                            <Input
                              placeholder="Nome"
                              value={field.name}
                              onChange={(e) => {
                                const newFields = [...((selectedNode.data.fields as any[]) || [])];
                                newFields[i] = { ...field, name: e.target.value };
                                updateSelectedNode('fields', newFields);
                              }}
                            />
                            <Input
                              placeholder="Selector"
                              value={field.selector}
                              onChange={(e) => {
                                const newFields = [...((selectedNode.data.fields as any[]) || [])];
                                newFields[i] = { ...field, selector: e.target.value };
                                updateSelectedNode('fields', newFields);
                              }}
                            />
                            <select
                              value={field.type}
                              onChange={(e) => {
                                const newFields = [...((selectedNode.data.fields as any[]) || [])];
                                newFields[i] = { ...field, type: e.target.value };
                                updateSelectedNode('fields', newFields);
                              }}
                              className={styles.select}
                            >
                              <option value="text">Texto</option>
                              <option value="html">HTML</option>
                              <option value="image">Img</option>
                              <option value="attribute">Attr</option>
                            </select>
                            <button 
                              onClick={() => {
                                const newFields = ((selectedNode.data.fields as any[]) || []).filter((_, idx) => idx !== i);
                                updateSelectedNode('fields', newFields);
                              }}
                              className={styles.removeBtn}
                            >✕</button>
                          </div>
                        ))}
                        <Button 
                          variant="secondary" 
                          onClick={() => updateSelectedNode('fields', [...((selectedNode.data.fields as any[]) || []), { name: '', selector: '', type: 'text' }])}
                        >
                          + Campo
                        </Button>
                      </div>
                    </>
                  )}

                  {selectedNode.type === 'detail' && (
                    <>
                      <Input
                        label="URL (opcional - usa link se vazio)"
                        value={selectedNode.data.url as string || ''}
                        onChange={(e) => updateSelectedNode('url', e.target.value)}
                        placeholder="https://..."
                      />
                      <div className={styles.fieldsSection}>
                        <h5>Campos da Página de Detalhe</h5>
                        {((selectedNode.data.fields as any[]) || []).map((field: any, i: number) => (
                          <div key={i} className={styles.fieldRow}>
                            <Input
                              placeholder="Nome"
                              value={field.name}
                              onChange={(e) => {
                                const newFields = [...((selectedNode.data.fields as any[]) || [])];
                                newFields[i] = { ...field, name: e.target.value };
                                updateSelectedNode('fields', newFields);
                              }}
                            />
                            <Input
                              placeholder="Selector"
                              value={field.selector}
                              onChange={(e) => {
                                const newFields = [...((selectedNode.data.fields as any[]) || [])];
                                newFields[i] = { ...field, selector: e.target.value };
                                updateSelectedNode('fields', newFields);
                              }}
                            />
                            <select
                              value={field.type}
                              onChange={(e) => {
                                const newFields = [...((selectedNode.data.fields as any[]) || [])];
                                newFields[i] = { ...field, type: e.target.value };
                                updateSelectedNode('fields', newFields);
                              }}
                              className={styles.select}
                            >
                              <option value="text">Texto</option>
                              <option value="html">HTML</option>
                              <option value="image">Img</option>
                              <option value="attribute">Attr</option>
                            </select>
                            <button 
                              onClick={() => {
                                const newFields = ((selectedNode.data.fields as any[]) || []).filter((_, idx) => idx !== i);
                                updateSelectedNode('fields', newFields);
                              }}
                              className={styles.removeBtn}
                            >✕</button>
                          </div>
                        ))}
                        <Button 
                          variant="secondary" 
                          onClick={() => updateSelectedNode('fields', [...((selectedNode.data.fields as any[]) || []), { name: '', selector: '', type: 'text' }])}
                        >
                          + Campo
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              )}

              {showInteractive && (
                <div className={styles.interactiveModal}>
                  <div className={styles.interactiveHeader}>
                    <h3>🎯 Selecione os Elementos</h3>
                    <button className={styles.closeBtn} onClick={() => setShowInteractive(false)}>✕</button>
                  </div>
                  <div className={styles.interactiveContent}>
                    <div className={styles.interactivePreview}>
                      {interactiveData?.interactive_html ? (
                        <div 
                          className={styles.clickablePreview}
                          dangerouslySetInnerHTML={{ __html: interactiveData.interactive_html }}
                          onClick={(e) => {
                            const target = e.target as HTMLElement;
                            let el: HTMLElement | null = target;
                            while (el && !el.getAttribute('data-scrap-selector')) {
                              el = el.parentElement;
                            }
                            if (!el || !selectedNode) return;
                            
                            const selector = el.getAttribute('data-scrap-selector');
                            if (selectedNode.type === 'list') {
                              updateSelectedNode('listSelector', selector);
                            } else if (selectedNode.type === 'item') {
                              updateSelectedNode('itemSelector', selector);
                            } else if (selectedNode.type === 'detail') {
                              updateSelectedNode('linkSelector', selector);
                            }
                          }}
                        />
                      ) : (
                        <div className={styles.loadingPreview}>Carregando...</div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'results' && (
            <div className={styles.results}>
              {executeResult && (
                <div className={styles.resultSummary}>
                  <span className={styles.success}>✓ {executeResult.items_count} itens extraídos</span>
                </div>
              )}
              <div className={styles.resultsList}>
                {results.map((result) => (
                  <div key={result.id} className={styles.resultCard}>
                    <div className={styles.resultHeader}>
                      <span className={`${styles.status} ${styles[result.status]}`}>{result.status}</span>
                      <span>{new Date(result.executed_at).toLocaleString()}</span>
                      <span>{result.items_count} itens</span>
                    </div>
                    <div className={styles.resultData}>
                      {result.data.slice(0, 3).map((item: any, i: number) => (
                        <div key={i} className={styles.resultItem}>
                          {Object.entries(item).slice(0, 4).map(([k, v]) => (
                            <div key={k}><strong>{k}:</strong> {String(v)?.substring(0, 100)}</div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'schedules' && (
            <div className={styles.schedules}>
              {selectedConfig && (
                <div className={styles.scheduleActions}>
                  <Button variant="secondary" onClick={async () => {
                    await scrap.schedules.create({ config_id: selectedConfig.id, schedule_type: 'manual', enabled: true });
                    loadSchedules();
                  }}>
                    + Manual
                  </Button>
                  <Button variant="secondary" onClick={async () => {
                    await scrap.schedules.create({ config_id: selectedConfig.id, schedule_type: 'periodic', interval_minutes: 60, enabled: true });
                    loadSchedules();
                  }}>
                    + A cada hora
                  </Button>
                </div>
              )}
              <div className={styles.schedulesList}>
                {schedules.map((schedule) => (
                  <div key={schedule.id} className={styles.scheduleCard}>
                    <div className={styles.scheduleInfo}>
                      <span className={styles.scheduleType}>
                        {schedule.schedule_type === 'periodic' ? 'Periódico' : 'Manual'}
                      </span>
                      {schedule.interval_minutes && <span> a cada {schedule.interval_minutes} min</span>}
                    </div>
                    <label className={styles.checkbox}>
                      <input 
                        type="checkbox" 
                        checked={schedule.enabled}
                        onChange={async () => {
                          await scrap.schedules.update(schedule.id, !schedule.enabled);
                          loadSchedules();
                        }}
                      />
                      Ativo
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
