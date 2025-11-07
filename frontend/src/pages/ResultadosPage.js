import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  Tabs,
  Table,
  Space,
  Button,
  Input,
  Select,
  message,
  Modal,
  Tooltip,
  Tag,
} from 'antd';
import {
  DownloadOutlined,
  ReloadOutlined,
  FilterOutlined,
  EyeOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import { resultadosAPI } from '../services/api';
import DetalhesCalculoModal from '../components/DetalhesCalculoModal';
import ResumoColaboradorModal from '../components/ResumoColaboradorModal';
import RecebimentoModal from '../components/RecebimentoModal';
import ReconProcessoModal from '../components/ReconProcessoModal';
import EstadoModal from '../components/EstadoModal';
import MetricasProcessoModal from '../components/MetricasProcessoModal';

const { TabPane } = Tabs;
const { Search } = Input;
const { Option } = Select;

// Abas de debug que devem ser ocultas
const ABAS_OCULTAS = ['VALIDACAO', 'DEBUG_RECEBIMENTOS_RAW', 'DEBUG_ENV', 'DEBUG_ANALISE_INFO', 'DEBUG_ANALISE_SAMPLE'];

// Glossário de colunas (simplificado - pode ser expandido)
const GLOSSARIO = {
  'fator_correcao_fc': 'Fator de Correção - ajuste baseado em metas alcançadas',
  'taxa_rateio_aplicada': 'Taxa de rateio do cargo no contexto',
  'percentual_elegibilidade_pe': 'Percentual de Elegibilidade - fatia do cargo',
  'comissao_calculada': 'Valor final da comissão calculada',
  'comissao_potencial_maxima': 'Valor potencial antes dos ajustes',
  'faturamento_item': 'Valor do item faturado ou recebido',
};

// Presets de colunas
const PRESETS_COLUNAS = {
  fc_detalhado: {
    nome: 'FC Detalhado',
    descricao: 'Exibe todas as colunas de Fator de Correção expandidas',
  },
  financeiro: {
    nome: 'Financeiro',
    descricao: 'Colunas relacionadas a valores e comissões',
  },
  operacional: {
    nome: 'Operacional',
    descricao: 'Colunas relacionadas a processos e produtos',
  },
};

const formatCurrencyBR = (value) => {
  const num = Number(value);
  if (Number.isNaN(num)) return '-';
  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const formatPercent = (value) => {
  const num = Number(value);
  if (Number.isNaN(num)) return '-';
  return `${(num * 100).toFixed(2)}%`;
};

const groupData = (data = [], keyGetter, options = {}) => {
  const { createMaster, childProcessor, finalize } = options;
  const map = new Map();

  data.forEach((item, itemIndex) => {
    const key = keyGetter(item, itemIndex);
    if (!map.has(key)) {
      const master = createMaster ? createMaster(item, key) : { ...item };
      map.set(key, { ...master, children: [] });
    }

    const group = map.get(key);
    const childIndex = group.children.length;
    const processedChild = childProcessor ? childProcessor(item, group, childIndex) : item;
    group.children.push(processedChild);
  });

  return Array.from(map.entries()).map(([key, group]) => {
    if (finalize) {
      return finalize(group, key);
    }
    return { ...group, key };
  });
};

const groupFaturamentoData = (rawData = []) => {
  const processMap = new Map();

  const normalize = (v) => String(v ?? '').trim().toUpperCase();

  for (const row of rawData) {
    const processoKey = row.processo || '';
    if (!processMap.has(processoKey)) {
      processMap.set(processoKey, {
        key: processoKey,
        processo: processoKey,
        total_faturado_processo: 0,
        comissao_total_processo: 0,
        linhas_envolvidas: new Set(),
        itemMap: new Map(),
      });
    }
    const processoEntry = processMap.get(processoKey);

    const itemKey = normalize(row.cod_produto) || `ITEM_${normalize(row.descricao_produto)}`;
    if (!processoEntry.itemMap.has(itemKey)) {
      processoEntry.itemMap.set(itemKey, {
        key: `${processoKey}-${itemKey}`,
        processo: processoKey,
        cod_produto: row.cod_produto,
        descricao_produto: row.descricao_produto,
        linha: row.linha,
        grupo: row.grupo,
        subgrupo: row.subgrupo,
        tipo_mercadoria: row.tipo_mercadoria,
        faturamento_item: Number(row.faturamento_item || 0),
        item_key: itemKey,
        comissao_total_item: 0,
        colaboradores: [],
      });
    }
    const itemEntry = processoEntry.itemMap.get(itemKey);
    itemEntry.colaboradores.push({
      ...row,
      key: `${processoKey}-${itemKey}-${row.id_colaborador || row.nome_colaborador || (itemEntry.colaboradores || []).length}`,
    });
  }

  const resultado = [];
  for (const processoEntry of processMap.values()) {
    for (const itemEntry of processoEntry.itemMap.values()) {
      itemEntry.comissao_total_item = itemEntry.colaboradores.reduce(
        (acc, child) => acc + Number(child.comissao_calculada || 0),
        0
      );
      processoEntry.linhas_envolvidas.add(itemEntry.linha);
    }
    processoEntry.items = Array.from(processoEntry.itemMap.values());
    processoEntry.total_faturado_processo = processoEntry.items.reduce(
      (acc, item) => acc + Number(item.faturamento_item || 0),
      0
    );
    processoEntry.comissao_total_processo = processoEntry.items.reduce(
      (acc, item) => acc + Number(item.comissao_total_item || 0),
      0
    );
    processoEntry.linhas_envolvidas_array = Array.from(processoEntry.linhas_envolvidas).filter(Boolean);
    delete processoEntry.itemMap;
    delete processoEntry.linhas_envolvidas;
    resultado.push(processoEntry);
  }
  return resultado;
};

const groupRecebimentoData = (data = []) =>
  groupData(
    data,
    (item) => {
      const processo = item.processo || '';
      const dataRecebimento = item.DATA_RECEBIMENTO || '';
      const fallback = `valor_${item.valor_recebido_total || 0}`;
      return `${processo}__${dataRecebimento || fallback}`;
    },
    {
      createMaster: (item) => ({
        processo: item.processo,
        DATA_RECEBIMENTO: item.DATA_RECEBIMENTO,
        valor_recebido_total: Number(item.valor_recebido_total || 0),
      }),
      childProcessor: (item, _group, index) => ({
        ...item,
        key: `${item.processo || ''}_${item.DATA_RECEBIMENTO || ''}_${item.id_colaborador || item.nome_colaborador || index}`,
      }),
      finalize: (group, key) => ({
        ...group,
        key,
        comissao_total_adiantada: group.children.reduce((acc, child) => acc + Number(child.comissao_total || 0), 0),
        total_comissionados: group.children.length,
      }),
    }
  );

const groupReconciliacaoData = (data = []) => {
  const resumos = data.filter((item) => item.SALDO_FINAL_RECONCILIACAO !== undefined && item.SALDO_FINAL_RECONCILIACAO !== null);
  const linhas = data.filter((item) => item.SALDO_FINAL_RECONCILIACAO === undefined || item.SALDO_FINAL_RECONCILIACAO === null);

  return resumos.map((resumo, index) => {
    const processo = resumo.PROCESSO || resumo.processo;
    const comissaoCorretaTotal = resumo.COMISSAO_CORRETA_TOTAL ?? resumo.COMISSOES_CORRETA_TOTAL;
    const totalAdiantamentos = resumo.TOTAL_ADIANTAMENTOS_PAGOS ?? resumo.TOTAL_ADIANTADO ?? resumo.total_adiantamentos_pagos;

    const itemMap = new Map();
    linhas
      .filter((r) => (r.processo || r.PROCESSO) === processo)
      .forEach((r, idx) => {
        const cod = r.cod_produto || '';
        const key = cod || `item_${r.descricao_produto || ''}`;
        if (!itemMap.has(key)) {
          itemMap.set(key, {
            key: `${processo}-${key}`,
            processo,
            cod_produto: r.cod_produto,
            descricao_produto: r.descricao_produto,
            linha: r.linha,
            comissao_total_item: 0,
            colaboradores: [],
          });
        }
        const itemEntry = itemMap.get(key);
        itemEntry.colaboradores.push({ ...r, key: `${processo}-${key}-${r.id_colaborador || idx}` });
      });

    const items = Array.from(itemMap.values()).map((it) => ({
      ...it,
      comissao_total_item: it.colaboradores.reduce((acc, c) => acc + Number(c.comissao_calculada || 0), 0),
      total_colaboradores: it.colaboradores.length,
    }));

    const saldo = Number(resumo.SALDO_FINAL_RECONCILIACAO || 0);
    let statusRecon = 'Quitado';
    if (saldo > 0) statusRecon = 'A Pagar';
    else if (saldo < 0) statusRecon = 'A Descontar';

    return {
      ...resumo,
      key: `resumo_${processo || index}_${index}`,
      PROCESSO: processo,
      statusRecon,
      COMISSAO_CORRETA_TOTAL: comissaoCorretaTotal,
      TOTAL_ADIANTAMENTOS_PAGOS: totalAdiantamentos,
      items,
    };
  });
};

// Agrupamento hierárquico para COMISSOES_RECEBIMENTO (Processo -> Item -> Colaboradores)
const groupRecebimentoHierarquicoData = (raw = []) => {
  const processos = new Map();
  const tipoDe = (row) => row.TIPO_PAGAMENTO || row.tipo_lancamento || '';
  raw.forEach((row, idx) => {
    const processo = row.processo || `PROC_${idx}`;
    if (!processos.has(processo)) {
      processos.set(processo, { key: processo, processo, items: [] });
    }
    const proc = processos.get(processo);
    const tp = String(tipoDe(row) || '');
    const descr = tp === 'Antecipação'
      ? `Adiantamento ${row.DATA_RECEBIMENTO || ''}`
      : `Pagamento ${row.DATA_PAGAMENTO || row.DATA_RECEBIMENTO || row.documento_nf || ''}`;
    const item = {
      key: `${processo}-${proc.items.length + 1}-${tp}`,
      processo,
      item_tipo: tp,
      item_descr: descr,
      valor_item: Number(row.valor_recebido_total || row.faturamento_item || row.VALOR_PAGO || 0),
      comissao_item: 0,
      colaboradores: [],
    };
    const child = {
      key: `${item.key}-${row.id_colaborador || row.nome_colaborador || idx}`,
      nome_colaborador: row.nome_colaborador,
      cargo: row.cargo,
      tcmp_aplicado: row.tcmp_aplicado,
      fcmp_aplicado: row.fator_correcao_fc,
      taxa_rateio_aplicada: row.taxa_rateio_aplicada,
      percentual_elegibilidade_pe: row.percentual_elegibilidade_pe,
      comissao_calculada: Number(row.comissao_calculada || row.comissao_total || 0),
      valor_recebido_total: row.valor_recebido_total,
      originalData: row,
    };
    item.colaboradores.push(child);
    item.comissao_item += child.comissao_calculada;
    proc.items.push(item);
  });
  return Array.from(processos.values());
};

// Nova: Agrupador para MÉTRICAS_PROCESSOS (Processo -> colaboradores com TCMP/FCMP)
const parseJSONSafe = (val) => {
  if (!val) return {};
  try { return typeof val === 'string' ? JSON.parse(val) : val; } catch (_) { return {}; }
};

const groupMetricasProcessosData = (data = [], isDebug = false) => {
  try {
    const map = new Map();
    data.forEach((row, idx) => {
      const processo = row.PROCESSO || row.processo || `PROC_${idx}`;
      if (!map.has(processo)) {
        map.set(processo, {
          key: processo,
          processo,
          MES_ANO_FATURAMENTO: row.MES_ANO_FATURAMENTO || row.mes_ano_faturamento,
          STATUS_CALCULO_MEDIAS: row.STATUS_CALCULO_MEDIAS || row.status_calculo_medias,
          __colaboradores_metricas: [],
        });
      }
      const entry = map.get(processo);
      const tcmp = parseJSONSafe(row.TCMP || row.tcmp);
      const fcmp = parseJSONSafe(row.FCMP || row.fcmp);
      const nomes = new Set([...Object.keys(tcmp || {}), ...Object.keys(fcmp || {})]);
      nomes.forEach((nome) => {
        entry.__colaboradores_metricas.push({
          key: `${processo}-${nome}`,
          nome_colaborador: nome,
          tcmp: Number(tcmp?.[nome] || 0),
          fcmp: Number(fcmp?.[nome] || 0),
          fonte: 'ESTADO',
        });
      });
    });
    const out = Array.from(map.values());
    if (isDebug) console.debug('[Resultados] Métricas agrupadas', { total: out.length, sample: out.slice(0, 2) });
    return out;
  } catch (e) {
    if (isDebug) console.debug('[Resultados][ERRO] Agrupar métricas', e);
    return [];
  }
};

const ResultadosPage = () => {
  const [abas, setAbas] = useState([]);
  const [abaAtiva, setAbaAtiva] = useState('');
  const [dados, setDados] = useState([]);
  const [colunas, setColunas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [sortConfig, setSortConfig] = useState({ sortBy: null, sortOrder: null });
  const [filtrosAtivos, setFiltrosAtivos] = useState({});
  const [valoresUnicosCache, setValoresUnicosCache] = useState({});
  const [modalVisible, setModalVisible] = useState(false);
  const [modalData, setModalData] = useState(null);
  const [presetAtivo, setPresetAtivo] = useState(null);
  const [colunasVisiveis, setColunasVisiveis] = useState(null);
  const isDebug = useMemo(() => {
    try {
      return new URLSearchParams(window.location.search).get('debug') === '1';
    } catch (_) {
      return false;
    }
  }, []);

  const carregarAbas = useCallback(async () => {
    try {
      const response = await resultadosAPI.listarAbas();
      const abasList = (response.data.abas || []).filter(aba => !ABAS_OCULTAS.includes(aba));
      if (isDebug) console.debug('[Resultados] Abas carregadas', abasList);
      // Garantir presença da aba MÉTRICAS_PROCESSOS (mapeia dados da aba ESTADO)
      try {
        const temMetricas = abasList.some((a) => String(a).toUpperCase() === 'MÉTRICAS_PROCESSOS');
        if (!temMetricas) {
          abasList.push('MÉTRICAS_PROCESSOS');
          if (isDebug) console.debug('[Resultados] Aba MÉTRICAS_PROCESSOS adicionada (forçada)');
        }
      } catch (_) { /* noop */ }
      setAbas(abasList);
      if (abasList.length > 0 && !abaAtiva) {
        setAbaAtiva(abasList[0]);
      }
    } catch (error) {
      message.error(`Erro ao carregar abas: ${error.message}`);
    }
  }, [abaAtiva, isDebug]);

  const carregarDados = useCallback(async () => {
    if (!abaAtiva) return;

    setLoading(true);
    try {
      // Converter filtros ativos em padrão de busca (OR) para o backend
      const filtersParam = {};
      Object.keys(filtrosAtivos).forEach((key) => {
        const values = filtrosAtivos[key];
        if (Array.isArray(values) && values.length > 0) {
          filtersParam[key] = values.join('|');
        }
      });

      const params = {
        page: pagination.current,
        size: pagination.pageSize,
        sortBy: sortConfig.sortBy,
        sortOrder: sortConfig.sortOrder,
        filters: Object.keys(filtersParam).length > 0 ? filtersParam : undefined,
      };

      // Mapear aba de métricas para leitura da aba ESTADO
      const nomeAbaReal = (abaAtiva || '').toString().trim().toUpperCase() === 'MÉTRICAS_PROCESSOS' ? 'ESTADO' : abaAtiva;
      if (isDebug && nomeAbaReal !== abaAtiva) console.debug('[Resultados] Mapeando leitura', { solicitada: abaAtiva, real: nomeAbaReal });
      const response = await resultadosAPI.lerAba(nomeAbaReal, params);
      const { data, total, columns } = response.data;

      if (isDebug) console.debug('[Resultados] Dados lidos', { aba: abaAtiva, total: (data || []).length, sample: (data || []).slice(0, 2) });
      setDados(data);
      setColunas(columns || []);
      setPagination((prev) => ({ ...prev, total }));
    } catch (error) {
      message.error(`Erro ao carregar dados: ${error.message}`);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [abaAtiva, pagination.current, pagination.pageSize, sortConfig.sortBy, sortConfig.sortOrder, filtrosAtivos, isDebug]);

  useEffect(() => {
    carregarAbas();
  }, [carregarAbas]);

  useEffect(() => {
    if (abaAtiva) {
      // Resetar paginação e ordenação ao trocar de aba
      setPagination({ current: 1, pageSize: 20, total: 0 });
      setSortConfig({ sortBy: null, sortOrder: null });
      carregarDados();
    }
  }, [abaAtiva]);

  useEffect(() => {
    if (abaAtiva) {
      carregarDados();
    }
  }, [abaAtiva, pagination.current, pagination.pageSize, sortConfig, carregarDados]);

  const handleTableChange = (paginationNew, filters, sorter) => {
    // Atualizar paginação
    setPagination({
      ...pagination,
      current: paginationNew.current,
      pageSize: paginationNew.pageSize,
    });

    // Atualizar ordenação
    if (sorter.field) {
      setSortConfig({
        sortBy: sorter.field,
        sortOrder: sorter.order === 'ascend' ? 'asc' : sorter.order === 'descend' ? 'desc' : null,
      });
    } else {
      setSortConfig({ sortBy: null, sortOrder: null });
    }

    // Atualizar filtros ativos e resetar para a primeira página quando mudarem
    const novosFiltros = {};
    Object.keys(filters || {}).forEach((key) => {
      if (filters[key] && filters[key].length > 0) {
        novosFiltros[key] = filters[key];
      }
    });

    const filtrosMudaram = JSON.stringify(novosFiltros) !== JSON.stringify(filtrosAtivos);
    if (filtrosMudaram) {
      setPagination((prev) => ({ ...prev, current: 1 }));
    }
    setFiltrosAtivos(novosFiltros);
  };

  const obterValoresUnicos = useCallback(async (coluna) => {
    if (!abaAtiva || !coluna) return [];

    // Verificar se a coluna existe nas colunas disponíveis
    if (!colunas.includes(coluna)) {
      return [];
    }

    const cacheKey = `${abaAtiva}_${coluna}`;
    if (valoresUnicosCache[cacheKey]) {
      return valoresUnicosCache[cacheKey];
    }

    try {
      const response = await resultadosAPI.obterValoresUnicos(abaAtiva, coluna);
      const valores = response.data.valores || [];
      setValoresUnicosCache((prev) => ({ ...prev, [cacheKey]: valores }));
      return valores;
    } catch (error) {
      // Erro 404 (coluna não encontrada) é esperado e não deve ser mostrado
      // Outros erros também serão silenciosos para não poluir a interface
      return [];
    }
  }, [abaAtiva, colunas, valoresUnicosCache]);

  const aplicarPreset = useCallback((preset) => {
    if (preset === 'fc_detalhado') {
      // Mostrar todas as colunas relacionadas a FC
      const colunasFC = colunas.filter((col) =>
        col.includes('peso_') ||
        col.includes('realizado_') ||
        col.includes('meta_') ||
        col.includes('ating_') ||
        col.includes('comp_fc_') ||
        col.includes('moeda_') ||
        col === 'fator_correcao_fc'
      );
      setColunasVisiveis([...colunas.slice(0, 10), ...colunasFC]);
    } else {
      setColunasVisiveis(null); // Mostrar todas
    }
  }, [colunas]);

  const handleDetalhesClick = (record) => {
    setModalData(record);
    setModalVisible(true);
  };

  const abaAtivaKey = (abaAtiva || '').toString().trim().toUpperCase();
  const isComissoesCalculadas = abaAtivaKey === 'COMISSOES_CALCULADAS';
  const isComissoesRecebimento = abaAtivaKey === 'COMISSOES_RECEBIMENTO';
  const isReconciliacao = abaAtivaKey === 'RECONCILIACAO';
  const isAbaMetricas = abaAtivaKey === 'MÉTRICAS_PROCESSOS';

  const dadosProcessados = useMemo(() => {
    if (isComissoesCalculadas) return groupFaturamentoData(dados);
    if (isComissoesRecebimento) return groupRecebimentoHierarquicoData(dados);
    if (isReconciliacao) return groupReconciliacaoData(dados);
    if (isAbaMetricas) return groupMetricasProcessosData(dados, isDebug);
    return dados;
  }, [dados, isComissoesCalculadas, isComissoesRecebimento, isReconciliacao, isAbaMetricas, isDebug]);

  useEffect(() => {
    try {
      if (isDebug && isComissoesCalculadas) {
        // eslint-disable-next-line no-console
        console.debug('[Resultados] Faturamento agrupado', { total: Array.isArray(dadosProcessados) ? dadosProcessados.length : 0 });
      }
    } catch (_) { }
  }, [isDebug, isComissoesCalculadas, dadosProcessados]);

  const colunasMestreComissoesCalculadas = useMemo(
    () => [
      {
        title: 'Processo',
        dataIndex: 'processo',
        key: 'processo',
        width: 140,
        fixed: 'left',
      },
      {
        title: 'Total Faturado (Processo)',
        dataIndex: 'total_faturado_processo',
        key: 'total_faturado_processo',
        width: 200,
        align: 'right',
        render: (value) => formatCurrencyBR(value),
      },
      {
        title: 'Total Comissões (Processo)',
        dataIndex: 'comissao_total_processo',
        key: 'comissao_total_processo',
        width: 200,
        align: 'right',
        render: (value) => formatCurrencyBR(value),
      },
      {
        title: 'Linhas Envolvidas',
        dataIndex: 'linhas_envolvidas_array',
        key: 'linhas_envolvidas_array',
        width: 240,
        render: (arr) => (Array.isArray(arr) ? arr.map((l) => <Tag key={l}>{l}</Tag>) : null),
      },
    ],
    []
  );

  const colunasItensComissoesCalculadas = useMemo(
    () => [
      {
        title: 'Item',
        key: 'item',
        width: 260,
        render: (_, record) => {
          const cod = record.cod_produto ? String(record.cod_produto) : '-';
          const descricao = record.descricao_produto ? String(record.descricao_produto) : '-';
          return `${cod} - ${descricao}`;
        },
      },
      { title: 'Linha', dataIndex: 'linha', key: 'linha', width: 160 },
      { title: 'Grupo', dataIndex: 'grupo', key: 'grupo', width: 160 },
      { title: 'Subgrupo', dataIndex: 'subgrupo', key: 'subgrupo', width: 160 },
      { title: 'Tipo Mercadoria', dataIndex: 'tipo_mercadoria', key: 'tipo_mercadoria', width: 180 },
      { title: 'Valor Faturado (Item)', dataIndex: 'faturamento_item', key: 'faturamento_item', width: 180, align: 'right', render: (v) => formatCurrencyBR(v) },
      { title: 'Comissão (Item)', dataIndex: 'comissao_total_item', key: 'comissao_total_item', width: 180, align: 'right', render: (v) => formatCurrencyBR(v) },
    ],
    []
  );

  const colunasDetalheComissoesCalculadas = useMemo(
    () => [
      {
        title: 'Colaborador',
        dataIndex: 'nome_colaborador',
        key: 'nome_colaborador',
        width: 220,
      },
      {
        title: 'Cargo',
        dataIndex: 'cargo',
        key: 'cargo',
        width: 200,
      },
      {
        title: 'FC Aplicado',
        dataIndex: 'fator_correcao_fc',
        key: 'fator_correcao_fc',
        width: 160,
        render: (value) => formatPercent(value),
      },
      {
        title: 'Comissão Calculada',
        dataIndex: 'comissao_calculada',
        key: 'comissao_calculada',
        width: 180,
        align: 'right',
        render: (value) => formatCurrencyBR(value),
      },
      {
        title: 'Ações',
        key: 'acoes',
        width: 140,
        render: (_, childRecord) => (
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleDetalhesClick(childRecord)}
            size="small"
          >
            Ver Detalhes
          </Button>
        ),
      },
    ],
    [handleDetalhesClick]
  );

  const colunasMestreComissoesRecebimento = useMemo(
    () => [
      {
        title: 'Processo',
        dataIndex: 'processo',
        key: 'processo',
        width: 140,
        fixed: 'left',
      },
      {
        title: 'Data Recebimento',
        dataIndex: 'DATA_RECEBIMENTO',
        key: 'DATA_RECEBIMENTO',
        width: 180,
      },
      {
        title: 'Valor Recebido',
        dataIndex: 'valor_recebido_total',
        key: 'valor_recebido_total',
        width: 180,
        align: 'right',
        render: (value) => formatCurrencyBR(value),
      },
      {
        title: 'Comissão Total (Adiantada)',
        dataIndex: 'comissao_total_adiantada',
        key: 'comissao_total_adiantada',
        width: 200,
        align: 'right',
        render: (value) => formatCurrencyBR(value),
      },
      {
        title: 'Comissionados',
        dataIndex: 'total_comissionados',
        key: 'total_comissionados',
        width: 150,
        render: (value) => <Tag color="blue">{value}</Tag>,
      },
    ],
    []
  );

  const colunasDetalheComissoesRecebimento = useMemo(
    () => [
      {
        title: 'Colaborador',
        dataIndex: 'nome_colaborador',
        key: 'nome_colaborador',
        width: 220,
      },
      {
        title: 'Cargo',
        dataIndex: 'cargo',
        key: 'cargo',
        width: 200,
      },
      { title: 'TCMP', dataIndex: 'tcmp_aplicado', key: 'tcmp_aplicado', width: 120, render: (v) => (v !== undefined ? formatPercent(v) : '-') },
      { title: 'FCMP', dataIndex: 'fcmp_aplicado', key: 'fcmp_aplicado', width: 120, render: (v) => (v !== undefined ? formatPercent(v) : '-') },
      {
        title: '% Aplicada',
        key: 'percentual_aplicado',
        width: 160,
        render: (_, record) => {
          const taxaRateio = Number(record.taxa_rateio_aplicada || 0);
          const percentualElegibilidade = Number(record.percentual_elegibilidade_pe || 0);
          const val = taxaRateio * percentualElegibilidade;
          return val ? formatPercent(val) : '-';
        },
      },
      {
        title: 'Adiantamento Calculado',
        dataIndex: 'comissao_total',
        key: 'comissao_total',
        width: 200,
        align: 'right',
        render: (value) => formatCurrencyBR(value),
      },
      {
        title: 'Ações',
        key: 'acoes',
        width: 140,
        render: (_, childRecord) => (
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleDetalhesClick(childRecord)}
            size="small"
          >
            Ver Detalhes
          </Button>
        ),
      },
    ],
    [handleDetalhesClick]
  );

  // Colunas para itens (Adiantamento/Parcela) em COMISSOES_RECEBIMENTO
  const colunasItensComissoesRecebimento = useMemo(
    () => [
      {
        title: 'Tipo',
        dataIndex: 'item_tipo',
        key: 'item_tipo',
        width: 140,
        render: (v) => <Tag color={v === 'Antecipação' ? 'orange' : 'green'}>{v || '-'}</Tag>,
      },
      { title: 'Descrição', dataIndex: 'item_descr', key: 'item_descr', width: 320 },
      { title: 'Valor', dataIndex: 'valor_item', key: 'valor_item', width: 160, align: 'right', render: (v) => formatCurrencyBR(v) },
      { title: 'Comissão', dataIndex: 'comissao_item', key: 'comissao_item', width: 160, align: 'right', render: (v) => formatCurrencyBR(v) },
      { title: 'Colaboradores', key: 'total_colaboradores', width: 160, render: (_, r) => <Tag color="blue">{Array.isArray(r.colaboradores) ? r.colaboradores.length : 0}</Tag> },
    ],
    []
  );

  const colunasMestreReconciliacao = useMemo(
    () => [
      {
        title: 'Processo',
        dataIndex: 'PROCESSO',
        key: 'PROCESSO',
        width: 140,
        fixed: 'left',
      },
      {
        title: 'Status',
        dataIndex: 'statusRecon',
        key: 'statusRecon',
        width: 150,
        render: (value) => {
          let color = 'default';
          if (value === 'A Pagar') color = 'green';
          if (value === 'A Descontar') color = 'red';
          return <Tag color={color}>{value}</Tag>;
        },
      },
      {
        title: 'Comissão Correta (c/ FC)',
        dataIndex: 'COMISSAO_CORRETA_TOTAL',
        key: 'COMISSAO_CORRETA_TOTAL',
        width: 200,
        align: 'right',
        render: (value) => formatCurrencyBR(value),
      },
      {
        title: 'Total Adiantado (pago)',
        dataIndex: 'TOTAL_ADIANTAMENTOS_PAGOS',
        key: 'TOTAL_ADIANTAMENTOS_PAGOS',
        width: 200,
        align: 'right',
        render: (value) => formatCurrencyBR(value),
      },
      {
        title: 'Saldo Final',
        dataIndex: 'SALDO_FINAL_RECONCILIACAO',
        key: 'SALDO_FINAL_RECONCILIACAO',
        width: 180,
        align: 'right',
        render: (value) => {
          const saldo = Number(value || 0);
          let color = undefined;
          if (saldo > 0) color = 'green';
          if (saldo < 0) color = 'red';
          return <span style={{ color }}>{formatCurrencyBR(value)}</span>;
        },
      },
      {
        title: 'Ações',
        key: 'acoes',
        width: 150,
        fixed: 'right',
        render: (_, record) => (
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleDetalhesClick(record)}
            size="small"
          >
            Ver Balanço
          </Button>
        ),
      },
    ],
    [handleDetalhesClick]
  );

  // Colunas para MÉTRICAS_PROCESSOS
  const colunasMestreMetricas = useMemo(
    () => [
      { title: 'Processo', dataIndex: 'processo', key: 'processo', width: 140, fixed: 'left' },
      { title: 'Mês/Ano Faturamento', dataIndex: 'MES_ANO_FATURAMENTO', key: 'MES_ANO_FATURAMENTO', width: 180 },
      { title: 'Status Métricas', dataIndex: 'STATUS_CALCULO_MEDIAS', key: 'STATUS_CALCULO_MEDIAS', width: 180, render: (v) => <Tag color={String(v).toUpperCase() === 'REALIZADO' ? 'green' : 'default'}>{v || '-'}</Tag> },
      { title: 'Colab. c/ Métricas', key: 'qtd_colab', width: 180, render: (_, r) => <Tag color="blue">{Array.isArray(r.__colaboradores_metricas) ? r.__colaboradores_metricas.length : 0}</Tag> },
      {
        title: 'Ações', key: 'acoes', width: 140, fixed: 'right', render: (_, record) => (
          <Button type="link" icon={<EyeOutlined />} onClick={() => handleDetalhesClick(record)} size="small">Ver Detalhes</Button>
        )
      },
    ],
    [handleDetalhesClick]
  );

  const expandableMetricas = useMemo(
    () => ({
      expandedRowRender: (procRecord) => (
        <Table
          columns={[
            { title: 'Colaborador', dataIndex: 'nome_colaborador', key: 'nome_colaborador', width: 260 },
            { title: 'TCMP', dataIndex: 'tcmp', key: 'tcmp', width: 120, render: (v) => formatPercent(v) },
            { title: 'FCMP', dataIndex: 'fcmp', key: 'fcmp', width: 120, render: (v) => formatPercent(v) },
            { title: 'Fonte', dataIndex: 'fonte', key: 'fonte', width: 160 },
          ]}
          dataSource={Array.isArray(procRecord.__colaboradores_metricas) ? procRecord.__colaboradores_metricas : []}
          rowKey="key"
          pagination={false}
          size="small"
          scroll={{ x: 'max-content' }}
        />
      ),
      rowExpandable: (procRecord) => Array.isArray(procRecord.__colaboradores_metricas) && procRecord.__colaboradores_metricas.length > 0,
    }),
    []
  );

  const colunasDetalheReconciliacao = useMemo(
    () => [
      {
        title: 'Colaborador',
        dataIndex: 'nome_colaborador',
        key: 'nome_colaborador',
        width: 220,
      },
      {
        title: 'Cargo',
        dataIndex: 'cargo',
        key: 'cargo',
        width: 200,
      },
      {
        title: 'Item',
        dataIndex: 'descricao_produto',
        key: 'descricao_produto',
        width: 220,
      },
      {
        title: 'FC Histórico',
        dataIndex: 'fator_correcao_fc',
        key: 'fator_correcao_fc',
        width: 160,
        render: (value) => formatPercent(value),
      },
      {
        title: 'Comissão Correta (Item)',
        dataIndex: 'comissao_calculada',
        key: 'comissao_calculada',
        width: 200,
        align: 'right',
        render: (value) => formatCurrencyBR(value),
      },
      {
        title: 'Ações',
        key: 'acoes',
        width: 150,
        render: (_, childRecord) => (
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleDetalhesClick(childRecord)}
            size="small"
          >
            Ver Detalhes
          </Button>
        ),
      },
    ],
    [handleDetalhesClick]
  );

  const expandableComissoesCalculadas = useMemo(
    () => ({
      expandedRowRender: (processoRecord) => {
        const normalize = (v) => String(v ?? '').trim().toUpperCase();
        const items = Array.isArray(processoRecord.items) ? processoRecord.items : [];
        // Mesclar itens idênticos por segurança (evita repetições visuais por linha de colaborador)
        const mergedMap = new Map();
        items.forEach((it) => {
          const k = `${normalize(it.cod_produto)}|${normalize(it.descricao_produto)}`;
          if (!mergedMap.has(k)) {
            mergedMap.set(k, {
              ...it,
              colaboradores: Array.isArray(it.colaboradores) ? [...it.colaboradores] : [],
            });
          } else {
            const acc = mergedMap.get(k);
            acc.colaboradores = acc.colaboradores.concat(Array.isArray(it.colaboradores) ? it.colaboradores : []);
            acc.comissao_total_item = Number(acc.comissao_total_item || 0) + Number(it.comissao_total_item || 0);
          }
        });
        const mergedItems = Array.from(mergedMap.values());

        if (isDebug && String(processoRecord.processo || processoRecord.PROCESSO) === '999999') {
          try {
            // Consola completa
            // eslint-disable-next-line no-console
            console.group('DEBUG COMISSOES_CALCULADAS - Processo 999999');
            // eslint-disable-next-line no-console
            console.table(items.map((it) => ({ key: it.key, item_key: it.item_key, cod: it.cod_produto, desc: it.descricao_produto, colaboradores_len: (it.colaboradores || []).length, fat_item: it.faturamento_item, comissao_total_item: it.comissao_total_item })));
            // eslint-disable-next-line no-console
            console.table(mergedItems.map((it) => ({ key: it.key, merged_key: `${normalize(it.cod_produto)}|${normalize(it.descricao_produto)}`, item_key: it.item_key, colaboradores_len: (it.colaboradores || []).length, fat_item: it.faturamento_item, comissao_total_item: it.comissao_total_item })));
            // eslint-disable-next-line no-console
            console.groupEnd();
          } catch (_) { }
        }

        return (
          <div>
            {isDebug && String(processoRecord.processo || processoRecord.PROCESSO) === '999999' && (
              <div style={{ background: '#fffbe6', border: '1px solid #ffe58f', padding: 8, marginBottom: 8, fontFamily: 'monospace', fontSize: 12 }}>
                <div><b>DEBUG Processo 999999</b></div>
                <div>items(raw): {items.length} · items(merged): {mergedItems.length}</div>
                <div>raw keys: {items.map((it) => it.item_key || it.key).join(', ')}</div>
                <div>merged keys: {mergedItems.map((it) => it.item_key || it.key).join(', ')}</div>
              </div>
            )}
            <Table
              columns={colunasItensComissoesCalculadas}
              dataSource={mergedItems}
              rowKey="key"
              pagination={false}
              size="small"
              scroll={{ x: 'max-content' }}
              expandable={{
                expandedRowRender: (itemRecord) => {
                  const colaboradores = Array.isArray(itemRecord.colaboradores)
                    ? itemRecord.colaboradores.map((colab) => ({
                      key: colab.key,
                      nome_colaborador: colab.nome_colaborador,
                      cargo: colab.cargo,
                      fator_correcao_fc: colab.fator_correcao_fc,
                      comissao_calculada: colab.comissao_calculada,
                      originalData: colab,
                    }))
                    : [];
                  return (
                    <Table
                      columns={colunasDetalheComissoesCalculadas.map((col) => {
                        if (col.key === 'acoes') {
                          return {
                            ...col,
                            render: (_, record) => (
                              <Button
                                type="link"
                                icon={<EyeOutlined />}
                                onClick={() => handleDetalhesClick(record.originalData || record)}
                                size="small"
                              >
                                Ver Detalhes
                              </Button>
                            ),
                          };
                        }
                        return col;
                      })}
                      dataSource={colaboradores}
                      rowKey="key"
                      pagination={false}
                      size="small"
                      scroll={{ x: 'max-content' }}
                    />
                  );
                },
                rowExpandable: (itemRecord) => Array.isArray(itemRecord.colaboradores) && itemRecord.colaboradores.length > 0,
              }}
            />
          </div>
        );
      },
      rowExpandable: (processoRecord) => Array.isArray(processoRecord.items) && processoRecord.items.length > 0,
    }),
    [colunasItensComissoesCalculadas, colunasDetalheComissoesCalculadas]
  );

  const expandableComissoesRecebimento = useMemo(
    () => ({
      expandedRowRender: (processoRecord) => (
        <Table
          columns={colunasItensComissoesRecebimento}
          dataSource={processoRecord.items}
          rowKey="key"
          pagination={false}
          size="small"
          scroll={{ x: 'max-content' }}
          expandable={{
            expandedRowRender: (itemRecord) => (
              <Table
                columns={colunasDetalheComissoesRecebimento}
                dataSource={itemRecord.colaboradores}
                rowKey="key"
                pagination={false}
                size="small"
                scroll={{ x: 'max-content' }}
              />
            ),
            rowExpandable: (itemRecord) => Array.isArray(itemRecord.colaboradores) && itemRecord.colaboradores.length > 0,
          }}
        />
      ),
      rowExpandable: (processoRecord) => Array.isArray(processoRecord.items) && processoRecord.items.length > 0,
    }),
    [colunasItensComissoesRecebimento, colunasDetalheComissoesRecebimento]
  );

  const colunasItensReconciliacao = useMemo(
    () => [
      {
        title: 'Item',
        key: 'item',
        width: 260,
        render: (_, record) => {
          const cod = record.cod_produto ? String(record.cod_produto) : '';
          const descricao = record.descricao_produto ? String(record.descricao_produto) : '-';
          return cod ? `${cod} - ${descricao}` : descricao;
        },
      },
      { title: 'Comissão Correta (Item)', dataIndex: 'comissao_total_item', key: 'comissao_total_item', width: 200, align: 'right', render: (v) => formatCurrencyBR(v) },
      { title: 'Colaboradores', dataIndex: 'total_colaboradores', key: 'total_colaboradores', width: 160, render: (v) => <Tag color="blue">{v}</Tag> },
    ],
    []
  );

  const expandableReconciliacao = useMemo(
    () => ({
      expandedRowRender: (resumoRecord) => (
        <Table
          columns={colunasItensReconciliacao}
          dataSource={resumoRecord.items}
          rowKey="key"
          pagination={false}
          size="small"
          scroll={{ x: 'max-content' }}
          expandable={{
            expandedRowRender: (itemRecord) => {
              const colaboradores = Array.isArray(itemRecord.colaboradores)
                ? itemRecord.colaboradores.map((colab) => ({
                  key: colab.key,
                  nome_colaborador: colab.nome_colaborador,
                  cargo: colab.cargo,
                  descricao_produto: colab.descricao_produto,
                  fator_correcao_fc: colab.fator_correcao_fc,
                  comissao_calculada: colab.comissao_calculada,
                  originalData: colab,
                }))
                : [];
              return (
                <Table
                  columns={colunasDetalheReconciliacao.map((col) => {
                    if (col.key === 'acoes') {
                      return {
                        ...col,
                        render: (_, record) => (
                          <Button
                            type="link"
                            icon={<EyeOutlined />}
                            onClick={() => handleDetalhesClick(record.originalData || record)}
                            size="small"
                          >
                            Ver Detalhes
                          </Button>
                        ),
                      };
                    }
                    return col;
                  })}
                  dataSource={colaboradores}
                  rowKey="key"
                  pagination={false}
                  size="small"
                  scroll={{ x: 'max-content' }}
                />
              );
            },
            rowExpandable: (itemRecord) => Array.isArray(itemRecord.colaboradores) && itemRecord.colaboradores.length > 0,
          }}
        />
      ),
      rowExpandable: (resumoRecord) => Array.isArray(resumoRecord.items) && resumoRecord.items.length > 0,
    }),
    [colunasItensReconciliacao, colunasDetalheReconciliacao]
  );

  const renderModalContent = () => {
    if (!modalData) return null;
    switch (abaAtivaKey) {
      case 'COMISSOES_CALCULADAS':
        return <DetalhesCalculoModal rowData={modalData} />;
      case 'RESUMO_COLABORADOR':
        return <ResumoColaboradorModal rowData={modalData} />;
      case 'COMISSOES_RECEBIMENTO':
        return <RecebimentoModal rowData={modalData} />;
      case 'RECONCILIACAO':
        if (modalData && modalData.SALDO_FINAL_RECONCILIACAO !== undefined) {
          return <ReconProcessoModal rowData={modalData} />;
        }
        return <DetalhesCalculoModal rowData={modalData} isHistorico={true} />;
      case 'ESTADO':
        return <EstadoModal rowData={modalData} />;
      case 'MÉTRICAS_PROCESSOS':
        return <MetricasProcessoModal rowData={modalData} />;
      default:
        return null;
    }
  };

  const handleBaixarExcel = async () => {
    try {
      const response = await resultadosAPI.baixar();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      const contentDisposition = response.headers['content-disposition'];
      let filename = 'Comissoes_Calculadas.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      message.success('Arquivo baixado com sucesso!');
    } catch (error) {
      message.error(`Erro ao baixar: ${error.message}`);
    }
  };

  // Componente de filtro com dropdown de valores únicos
  const criarFilterDropdown = (col) => {
    const FilterDropdownComponent = ({ setSelectedKeys, selectedKeys, confirm }) => {
      const [valoresUnicos, setValoresUnicos] = useState([]);
      const [carregando, setCarregando] = useState(false);
      const [buscaTexto, setBuscaTexto] = useState('');

      useEffect(() => {
        const carregar = async () => {
          setCarregando(true);
          const valores = await obterValoresUnicos(col);
          setValoresUnicos(valores);
          setCarregando(false);
        };
        carregar();
        // eslint-disable-next-line react-hooks/exhaustive-deps
      }, [col]);

      const valoresFiltrados = valoresUnicos.filter((val) =>
        String(val).toLowerCase().includes(buscaTexto.toLowerCase())
      );

      return (
        <div style={{ padding: 8, minWidth: 200 }}>
          <Input
            placeholder="Buscar..."
            value={buscaTexto}
            onChange={(e) => setBuscaTexto(e.target.value)}
            style={{ marginBottom: 8 }}
            allowClear
          />
          <Select
            mode="multiple"
            placeholder={`Selecione valores para ${col}`}
            value={selectedKeys}
            onChange={(values) => setSelectedKeys(values || [])}
            style={{ width: '100%', marginBottom: 8 }}
            loading={carregando}
            showSearch
            filterOption={false}
            maxTagCount="responsive"
            notFoundContent={carregando ? 'Carregando...' : 'Nenhum valor encontrado'}
          >
            {valoresFiltrados.map((val) => (
              <Option key={String(val)} value={String(val)}>
                {val}
              </Option>
            ))}
          </Select>
          <Space>
            <Button
              type="primary"
              onClick={confirm}
              size="small"
              style={{ width: 90 }}
            >
              Filtrar
            </Button>
            <Button
              onClick={() => {
                setSelectedKeys([]);
                setBuscaTexto('');
                confirm();
              }}
              size="small"
              style={{ width: 90 }}
            >
              Limpar
            </Button>
          </Space>
        </div>
      );
    };
    return FilterDropdownComponent;
  };

  const colunasTabela = (colunasVisiveis || colunas).filter(col => col !== 'id_colaborador').map((col) => {
    const temGlossario = GLOSSARIO[col.toLowerCase()];

    return {
      title: (
        <Space>
          {col}
          {temGlossario && (
            <Tooltip title={temGlossario}>
              <QuestionCircleOutlined style={{ color: '#1890ff' }} />
            </Tooltip>
          )}
        </Space>
      ),
      dataIndex: col,
      key: col,
      width: 150,
      sorter: true,
      sortOrder: sortConfig.sortBy === col ? (sortConfig.sortOrder === 'asc' ? 'ascend' : 'descend') : null,
      ellipsis: true,
      fixed: ['processo', 'nome_colaborador', 'cargo'].includes(col) ? 'left' : undefined,
      filterDropdown: criarFilterDropdown(col),
      filterIcon: (filtered) => (
        <FilterOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
      ),
      onFilter: (value, record) => {
        if (!value || value.length === 0) return true;
        return value.includes(String(record[col] || ''));
      },
      render: (text) => {
        // Coluna 'processo' não deve ser formatada como monetário
        if (col === 'processo') {
          return text || '-';
        }
        // Formatação para valores numéricos
        if (typeof text === 'number' || (typeof text === 'string' && !isNaN(text) && text !== '')) {
          const num = parseFloat(text);
          if (!isNaN(num)) {
            return num.toLocaleString('pt-BR', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            });
          }
        }
        return text || '-';
      },
    };
  });

  // Adicionar coluna de ações
  colunasTabela.push({
    title: 'Ações',
    key: 'acoes',
    width: 100,
    fixed: 'right',
    render: (_, record) => (
      <Button
        type="link"
        icon={<EyeOutlined />}
        onClick={() => handleDetalhesClick(record)}
        size="small"
      >
        Detalhes
      </Button>
    ),
  });

  const colunasTabelaGenerica = colunasTabela;

  return (
    <div>
      <Card
        title="Resultados do Cálculo"
        extra={
          <Space>
            <Select
              placeholder="Preset de colunas"
              style={{ width: 200 }}
              value={presetAtivo}
              onChange={(value) => {
                setPresetAtivo(value);
                if (value) {
                  aplicarPreset(value);
                } else {
                  setColunasVisiveis(null);
                }
              }}
              allowClear
            >
              {Object.entries(PRESETS_COLUNAS).map(([key, preset]) => (
                <Option key={key} value={key}>
                  {preset.nome}
                </Option>
              ))}
            </Select>
            <Search
              placeholder="Buscar..."
              onSearch={(value) => {
                // Busca será aplicada via filtros da tabela
                message.info('Use os filtros da tabela para buscar');
              }}
              style={{ width: 250 }}
              allowClear
            />
            <Button icon={<ReloadOutlined />} onClick={carregarDados} loading={loading}>
              Atualizar
            </Button>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleBaixarExcel}
            >
              Baixar Excel
            </Button>
          </Space>
        }
      >
        <Tabs activeKey={abaAtiva} onChange={setAbaAtiva} type="card">
          {abas.map((aba) => (
            <TabPane tab={aba} key={aba}>
              {(() => {
                const abaKey = (aba || '').toString().trim().toUpperCase();
                const isAbaCalculadas = abaKey === 'COMISSOES_CALCULADAS';
                const isAbaRecebimento = abaKey === 'COMISSOES_RECEBIMENTO';
                const isAbaReconciliacao = abaKey === 'RECONCILIACAO';
                const isAbaMetricasLocal = abaKey === 'MÉTRICAS_PROCESSOS';

                const colunasTabelaAtual = isAbaCalculadas
                  ? colunasMestreComissoesCalculadas
                  : isAbaRecebimento
                    ? colunasMestreComissoesRecebimento
                    : isAbaReconciliacao
                      ? colunasMestreReconciliacao
                      : isAbaMetricasLocal
                        ? colunasMestreMetricas
                        : colunasTabelaGenerica;

                const expandableAtual = isAbaCalculadas
                  ? expandableComissoesCalculadas
                  : isAbaRecebimento
                    ? expandableComissoesRecebimento
                    : isAbaReconciliacao
                      ? expandableReconciliacao
                      : isAbaMetricasLocal
                        ? expandableMetricas
                        : undefined;

                const dadosParaTabela = abaKey === abaAtivaKey
                  ? isAbaCalculadas || isAbaRecebimento || isAbaReconciliacao
                    ? dadosProcessados
                    : dados.map((item, idx) => ({ ...item, key: idx }))
                  : [];

                return (
                  <Table
                    columns={colunasTabelaAtual}
                    dataSource={dadosParaTabela}
                    loading={loading}
                    onChange={handleTableChange}
                    pagination={{
                      current: pagination.current,
                      pageSize: pagination.pageSize,
                      total: pagination.total,
                      showSizeChanger: true,
                      showTotal: (total) => `Total: ${total} linhas`,
                      pageSizeOptions: ['20', '50', '100'],
                    }}
                    scroll={{ x: 'max-content', y: 600 }}
                    size="small"
                    expandable={expandableAtual}
                    rowKey="key"
                  />
                );
              })()}
            </TabPane>
          ))}
        </Tabs>
      </Card>

      <Modal
        title="Detalhes"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={860}
        destroyOnClose
      >
        {renderModalContent()}
      </Modal>
    </div>
  );
};

export default ResultadosPage;

