export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  username: string;
  role: string;
  expires_in: number;
}

export interface RAGConfig {
  min_score: number;
  top_k: number;
  boost_enabled: boolean;
  boost_amount: number;
  model: string;
  model_temperature: number;
  model_max_tokens: number;
}

export interface RAGQueryRequest {
  tenant_id: string;
  query: string;
  min_score: number;
  top_k: number;
  boost_enabled: boolean;
}

export interface RetrievedChunk {
  id: string;
  text: string;
  source: string;
  title: string;
  section: string;
  score: number;
  tags: string[];
}

export interface RAGQueryResponse {
  tenant_id: string;
  query: string;
  status: string;
  message: string;
  chunks: RetrievedChunk[];
  total_chunks: number;
  best_score: number;
  params_used: {
    min_score: number;
    top_k: number;
    boost_enabled: boolean;
    collection: string;
  };
}

export interface DocumentInfo {
  id: string;
  tenant_id: string;
  title: string;
  file: string;
  tags: string[];
  intents: string[];
  updated_at: string;
}

export interface DocumentContent {
  id: string;
  tenant_id: string;
  title: string;
  file: string;
  content: string;
  keywords: string[];
  intents: string[];
  created_at: string;
  updated_at: string;
}

export interface RAGDocumentsResponse {
  tenant_id: string;
  source_dir: string;
  collection_name: string;
  ready: boolean;
  documents_count: number;
  chunks_count: number;
  last_ingested_at?: string | null;
  documents: DocumentInfo[];
}

export interface RAGStatusResponse {
  tenant_id: string;
  collection_name: string;
  source_dir: string;
  documents_count: number;
  chunks_count: number;
  ready: boolean;
  last_ingested_at?: string | null;
  message: string;
}

export interface RAGIngestResponse {
  tenant_id: string;
  collection_name: string;
  source_dir: string;
  documents_count: number;
  chunks_count: number;
  ready: boolean;
  reset_collection: boolean;
  last_ingested_at?: string | null;
  message: string;
}

export interface RAGResetResponse {
  tenant_id: string;
  collection_name: string;
  removed_collections: string[];
  removed_documents_count: number;
  source_dir: string;
  message: string;
}

export interface DashboardStats {
  total_conversas: number;
  total_sucesso: number;
  total_fallback: number;
  total_erro: number;
  hit_rate: number;
  intents_distribution: Record<string, number>;
  canais_distribution: Record<string, number>;
  ultimas_24h: { count: number };
}

export interface ConfigResponse {
  app_name: string;
  env: string;
  version: string;
  rag_config: RAGConfig;
  chroma_collections: string[];
  database_connected: boolean;
}

export interface AuditEvent {
  id_requisicao: string;
  id_sessao: string;
  canal: string;
  tipo_superficie: string;
  intencao: string;
  decisao: string;
  tipo_resposta: string;
  motivo_fallback: string | null;
  tempo_resposta_ms: number | null;
  criado_em: string;
}

export interface Conversa {
  id_conversa: number;
  id_requisicao: string;
  canal: string;
  tipo_superficie: string;
  mensagem_usuario: string;
  mensagem_resposta: string | null;
  intencao: string;
  decisao: string;
  tipo_resposta: string;
  motivo_fallback: string | null;
  sentimento: string | null;
  encontrou_docs: boolean | null;
  melhor_score: number | null;
  criado_em: string;
}

export interface ValidationResult {
  database: { status: string; message: string };
  chroma: { status: string; message: string };
  gemini: { status: string; message: string };
}

export interface FieldConfig {
  name: string;
  selector: string;
  type: 'text' | 'html' | 'attribute' | 'image';
  attribute?: string;
}

export interface PaginationConfig {
  enabled: boolean;
  type: 'none' | 'next_button' | 'page_param' | 'infinite_scroll';
  nextButtonSelector?: string;
  pageParamName?: string;
  maxPages?: number;
  stopWhenEmpty?: boolean;
}

export interface ScrapNode {
  id: string;
  label: string;
  url?: string;
  listSelector?: string;
  itemSelector?: string;
  fields: FieldConfig[];
  followLinks: boolean;
  linkSelector?: string;
  linkBaseUrl?: string;
  nextNode?: string;
  position?: { x: number; y: number };
  pagination?: PaginationConfig;
}

export interface ScrapWorkflow {
  nodes: ScrapNode[];
  startNodeId: string;
}

export interface ScrapConfig {
  id: string;
  nome: string;
  url_base: string;
  workflow: ScrapWorkflow;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface ScrapConfigCreate {
  nome: string;
  url_base: string;
  workflow: ScrapWorkflow;
}

export interface ScrapPreviewRequest {
  url: string;
  list_selector?: string;
  item_selector?: string;
  limit: number;
}

export interface ScrapPaginationInfo {
  has_pagination: boolean;
  suggestions: Array<{
    type: string;
    selector: string;
    text: string;
    href: string;
  }>;
  current_page?: string;
  page_param?: string;
}

export interface ScrapPreviewResponse {
  url: string;
  title: string;
  items_found?: number;
  selectors_suggestions?: Record<string, unknown>;
  html_preview?: string;
  body_html?: string;
  page_styles?: string[];
  pagination?: ScrapPaginationInfo;
  error?: string;
}

export interface ScrapInteractivePreviewResponse {
  url: string;
  title: string;
  interactive_html: string;
  elements: Array<{
    index: number;
    tag: string;
    id: string | null;
    classes: string[];
    text: string;
    selector: string;
    attributes: Record<string, string>;
    isLink?: boolean;
  }>;
  styles?: string[];
  base_url?: string;
}

export interface ScrapLinkPreviewResponse {
  url: string;
  title: string;
  html: string;
  styles?: string[];
  selectors_suggestions?: {
    title: Array<{ text: string; selector: string }>;
    content: Array<{ text: string; selector: string }>;
    date: Array<{ text: string; selector: string; datetime?: string }>;
    image: Array<{ src: string; selector: string }>;
  };
  error?: string;
}

export interface ScrapExecuteRequest {
  limit: number;
}

export interface ScrapItem {
  [key: string]: unknown;
  detail?: Record<string, unknown>;
}

export interface ScrapExecuteResponse {
  result_id: string;
  success: boolean;
  items_count: number;
  items: ScrapItem[];
  error?: string;
  nodes_executed: string[];
}

export interface ScrapSchedule {
  id: string;
  config_id: string;
  config_nome?: string;
  schedule_type: 'manual' | 'periodic';
  interval_minutes?: number;
  enabled: boolean;
  last_run?: string;
  next_run?: string;
  criado_em: string;
}

export interface ScrapScheduleCreate {
  config_id: string;
  schedule_type: 'manual' | 'periodic';
  interval_minutes?: number;
  enabled: boolean;
}

export interface ScrapResult {
  id: string;
  config_id: string;
  config_nome?: string;
  status: 'success' | 'error' | 'partial';
  items_count: number;
  data: ScrapItem[];
  executed_at: string;
}

export interface ConvertToRAGRequest {
  result_id: string;
  mode: 'create' | 'add';
  document_id?: string;
  title_template: string;
}

export interface ConvertToRAGResponse {
  mode: string;
  document_id?: string;
  content: string;
  items_count: number;
}

export interface BoostConfig {
  id: string;
  nome: string;
  tipo: 'sigla' | 'palavra_chave' | 'categoria';
  valor: string;
  boost_value: number;
  prioridade: number;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface BoostConfigCreate {
  nome: string;
  tipo: 'sigla' | 'palavra_chave' | 'categoria';
  valor: string;
  boost_value: number;
  prioridade: number;
  ativo: boolean;
}

export interface BoostConfigUpdate {
  nome?: string;
  valor?: string;
  boost_value?: number;
  prioridade?: number;
  ativo?: boolean;
}

export interface BoostTemplate {
  sigla: string;
  descricao: string;
}
