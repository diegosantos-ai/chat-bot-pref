import axios from 'axios';
import type { 
  LoginRequest, 
  LoginResponse, 
  DashboardStats,
  ConfigResponse,
  RAGQueryRequest,
  RAGQueryResponse,
  DocumentInfo,
  DocumentContent,
  AuditEvent,
  Conversa,
  ValidationResult,
  ScrapConfig,
  ScrapConfigCreate,
  ScrapPreviewRequest,
  ScrapPreviewResponse,
  ScrapInteractivePreviewResponse,
  ScrapLinkPreviewResponse,
  ScrapExecuteRequest,
  ScrapExecuteResponse,
  ScrapSchedule,
  ScrapScheduleCreate,
  ScrapResult,
  ConvertToRAGRequest,
  ConvertToRAGResponse,
  BoostConfig,
  BoostConfigCreate,
  BoostConfigUpdate,
  BoostTemplate
} from '../types';

const API_BASE = '/tereziapi/tereziadmin';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const auth = {
  login: (data: LoginRequest) => 
    api.post<LoginResponse>('/auth/login', data),
};

export const dashboard = {
  stats: () => 
    api.get<DashboardStats>('/dashboard/stats'),
};

export const config = {
  get: () => 
    api.get<ConfigResponse>('/config'),
  saveRagConfig: (data: {
    min_score: number;
    top_k: number;
    boost_enabled: boolean;
    boost_amount: number;
    model: string;
    model_temperature: number;
    model_max_tokens: number;
  }) => api.post('/config/rag', data),
};

export const rag = {
  query: (data: RAGQueryRequest) => 
    api.post<RAGQueryResponse>('/rag/query', data),
  
  documents: () => 
    api.get<{ base_id: string; version: string; documents: DocumentInfo[] }>('/rag/documents'),
  
  document: (docId: string) => 
    api.get<DocumentContent>('/rag/documents/' + docId),
  
  createDocument: (data: {
    title: string;
    content: string;
    keywords: string[];
    intents: string[];
  }) => api.post('/rag/documents', data),
  
  updateDocument: (docId: string, data: {
    title?: string;
    content?: string;
    keywords?: string[];
    intents?: string[];
  }) => api.put('/rag/documents/' + docId, data),
  
  deleteDocument: (docId: string) => 
    api.delete('/rag/documents/' + docId),
  
  ingest: (basePath: string = 'data/knowledge_base/BA-RAG-PILOTO-2026.01.v1', force: boolean = false) =>
    api.post('/rag/ingest', { base_path: basePath, force }),
};

export const logs = {
  events: (params: {
    data_inicio?: string;
    data_fim?: string;
    canal?: string;
    intent?: string;
    decision?: string;
    limit?: number;
    offset?: number;
  }) => api.get<{ events: AuditEvent[]; count: number }>('/logs/events', { params }),
  
  conversas: (params: {
    data_inicio?: string;
    data_fim?: string;
    canal?: string;
    intent?: string;
    decision?: string;
    busca_texto?: string;
    limit?: number;
    offset?: number;
  }) => api.get<{ conversas: Conversa[]; count: number }>('/logs/conversas', { params }),
};

export const ops = {
  validate: () => 
    api.post<ValidationResult>('/ops/validate'),
};

export const scrap = {
  configs: {
    list: () => api.get<ScrapConfig[]>('/scrap/configs'),
    get: (id: string) => api.get<ScrapConfig>('/scrap/configs/' + id),
    create: (data: ScrapConfigCreate) => api.post<ScrapConfig>('/scrap/configs', data),
    update: (id: string, data: Partial<ScrapConfigCreate> & { ativo?: boolean }) => 
      api.put<ScrapConfig>('/scrap/configs/' + id, data),
    delete: (id: string) => api.delete('/scrap/configs/' + id),
  },
  
  preview: (data: ScrapPreviewRequest) => api.post<ScrapPreviewResponse>('/scrap/preview', data),
  
  previewInteractive: (url: string) => api.post<ScrapInteractivePreviewResponse>('/scrap/preview/interactive', { url }),
  
  previewLink: (url: string, baseUrl: string = '') => 
    api.post<ScrapLinkPreviewResponse>('/scrap/preview/link', { url, base_url: baseUrl }),
  
  execute: (configId: string, data: ScrapExecuteRequest) => 
    api.post<ScrapExecuteResponse>('/scrap/execute/' + configId, data),
  
  schedules: {
    list: (configId?: string) => 
      api.get<ScrapSchedule[]>('/scrap/schedules', { params: { config_id: configId } }),
    create: (data: ScrapScheduleCreate) => api.post<ScrapSchedule>('/scrap/schedules', data),
    update: (id: string, enabled: boolean) => 
      api.put<ScrapSchedule>('/scrap/schedules/' + id, { enabled }),
    delete: (id: string) => api.delete('/scrap/schedules/' + id),
  },
  
  results: {
    list: (configId?: string, limit: number = 20) => 
      api.get<ScrapResult[]>('/scrap/results', { params: { config_id: configId, limit } }),
    get: (id: string) => api.get<ScrapResult>('/scrap/results/' + id),
  },
  
  toRag: (data: ConvertToRAGRequest) => 
    api.post<ConvertToRAGResponse>('/scrap/results/' + data.result_id + '/to-rag', data),
};

export const boosts = {
  list: (params?: { tipo?: string; ativo?: boolean }) =>
    api.get<BoostConfig[]>('/admin/boosts', { params }),
  
  create: (data: BoostConfigCreate) =>
    api.post<BoostConfig>('/admin/boosts', data),
  
  update: (id: string, data: BoostConfigUpdate) =>
    api.put<BoostConfig>('/admin/boosts/' + id, data),
  
  delete: (id: string) =>
    api.delete('/admin/boosts/' + id),
  
  templates: () =>
    api.get<BoostTemplate[]>('/admin/boosts/templates'),
  
  import: () =>
    api.post<{ imported: number; skipped: number }>('/admin/boosts/import'),
};

export default api;
