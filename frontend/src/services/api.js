import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Erro da API
      const message = error.response.data?.detail || error.response.data?.message || 'Erro desconhecido';
      throw new Error(message);
    } else if (error.request) {
      // Erro de rede
      throw new Error('Erro de conexão. Verifique se o servidor está rodando.');
    } else {
      throw error;
    }
  }
);

// ==================== REGRAS ====================

export const regrasAPI = {
  listarAbas: () => api.get('/regras/abas'),
  
  lerAba: (nomeAba, params = {}) => {
    const { page = 1, size = 20, sortBy, sortOrder, filters, allPages = false } = params;
    const queryParams = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (sortBy) {
      queryParams.append('sort_by', sortBy);
      queryParams.append('sort_order', sortOrder || 'asc');
    }
    if (filters) {
      queryParams.append('filters', JSON.stringify(filters));
    }
    if (allPages) {
      queryParams.append('all_pages', 'true');
    }
    return api.get(`/regras/aba/${nomeAba}?${queryParams}`);
  },
  
  obterValoresUnicos: (nomeAba, coluna) =>
    api.get(`/regras/aba/${nomeAba}/valores-unicos/${coluna}`),
  
  salvarAba: (nomeAba, data, preserveColumns = true) =>
    api.post(`/regras/aba/${nomeAba}/save`, {
      data,
      preserve_columns: preserveColumns,
    }),
  
  aplicarMassa: (nomeAba, request) =>
    api.post(`/regras/aba/${nomeAba}/apply-bulk`, request),
};

// ==================== UPLOADS ====================

export const uploadAPI = {
  analiseComercial: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/analise', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  finAdcli: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/fin_adcli', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  finConci: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/fin_conci', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  analiseFinanceira: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/analise_financeira', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// ==================== EXECUÇÃO ====================

export const execucaoAPI = {
  iniciar: (mes, ano) => api.post(`/calcular?mes=${mes}&ano=${ano}`),
  
  consultarProgresso: (jobId) => api.get(`/progresso/${jobId}`),
};

// ==================== RESULTADOS ====================

export const resultadosAPI = {
  listarAbas: () => api.get('/resultado/abas'),
  
  lerAba: (nomeAba, params = {}) => {
    const { page = 1, size = 20, sortBy, sortOrder, filters } = params;
    const queryParams = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (sortBy) {
      queryParams.append('sort_by', sortBy);
      queryParams.append('sort_order', sortOrder || 'asc');
    }
    if (filters) {
      queryParams.append('filters', JSON.stringify(filters));
    }
    return api.get(`/resultado/aba/${nomeAba}?${queryParams}`);
  },
  
  obterValoresUnicos: (nomeAba, coluna) =>
    api.get(`/resultado/aba/${nomeAba}/valores-unicos/${coluna}`),
  
  baixar: () => api.get('/baixar/resultado', { responseType: 'blob' }),
};

// ==================== HEALTH ====================

export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;

