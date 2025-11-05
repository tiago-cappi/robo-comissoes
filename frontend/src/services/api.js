import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de requisição para logs
api.interceptors.request.use(
  (config) => {
    console.log('[API] Requisição iniciada', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      timeout: config.timeout,
      timestamp: new Date().toISOString(),
    });
    return config;
  },
  (error) => {
    console.error('[API] Erro na configuração da requisição', error);
    return Promise.reject(error);
  }
);

// Interceptor de resposta para logs e tratamento de erros
api.interceptors.response.use(
  (response) => {
    console.log('[API] Resposta recebida', {
      status: response.status,
      url: response.config.url,
      elapsed: response.config.metadata?.startTime
        ? `${((Date.now() - response.config.metadata.startTime) / 1000).toFixed(1)}s`
        : 'N/A',
      dataType: typeof response.data,
      dataLength: Array.isArray(response.data) ? response.data.length : 'N/A',
    });
    return response;
  },
  (error) => {
    const elapsed = error.config?.metadata?.startTime
      ? `${((Date.now() - error.config.metadata.startTime) / 1000).toFixed(1)}s`
      : 'N/A';

    console.error('[API] Erro na resposta', {
      url: error.config?.url,
      elapsed,
      errorName: error.name,
      errorMessage: error.message,
      errorCode: error.code,
      hasResponse: !!error.response,
      hasRequest: !!error.request,
      responseStatus: error.response?.status,
      responseData: error.response?.data,
    });

    if (error.response) {
      // Erro da API
      const message = error.response.data?.detail || error.response.data?.message || 'Erro desconhecido';
      throw new Error(message);
    } else if (error.request) {
      // Erro de rede ou timeout
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        throw new Error('Timeout: A requisição demorou muito para responder. Tente novamente.');
      }
      throw new Error('Erro de conexão. Verifique se o servidor está rodando.');
    } else {
      throw error;
    }
  }
);

// Adicionar timestamp às requisições para cálculo de tempo decorrido
api.interceptors.request.use((config) => {
  config.metadata = { startTime: Date.now() };
  return config;
});

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

  // ===== Gerenciamento de Regras =====
  getPesosMetas: () => api.get('/api/regras/pesos-metas'),
  updatePesosMetas: (data) => api.post('/api/regras/pesos-metas', data),

  getRuleContextOptions: () => api.get('/api/regras/config-comissao/context-options'),
  getConfigComissao: (filters) => api.post('/api/regras/config-comissao/query', filters || {}),
  updateConfigComissaoInLine: (rowData) => api.put('/api/regras/config-comissao/update-line', rowData),
  dryRunConfigComissao: (batchData) => api.post('/api/regras/config-comissao/dry-run', batchData),
  applyBatchConfigComissao: (batchData) => api.post('/api/regras/config-comissao/apply-batch', batchData),
  validateConfigComissaoPE: (contexto) => api.post('/api/regras/config-comissao/validate-pe', contexto),
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

// ==================== EXECUÇÃO (Pré-Scan + Execução com Decisões) ====================

export const execucaoAPI2 = {
  executarPreScanCrossSelling: (mes, ano) =>
    api.post('/api/executar-prescan', { mes, ano }, {
      timeout: 30000, // 30 segundos de timeout para pré-scan
    }),
  executarCalculo: (mes, ano, decisoes) =>
    api.post('/api/executar-calculo', {
      mes,
      ano,
      decisoes_cross_selling: decisoes || [],
    }, {
      timeout: 600000, // 10 minutos de timeout para cálculo completo
    }),
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

// ==================== DEBUG ====================

export const debugAPI = {
  getLogs: (lines = 400) => api.get(`/debug/logs?lines=${lines}`, { responseType: 'text' }),
};

export default api;

