import React, { useState, useEffect, useCallback } from 'react';
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

  const carregarAbas = useCallback(async () => {
    try {
      const response = await resultadosAPI.listarAbas();
      const abasList = (response.data.abas || []).filter(aba => !ABAS_OCULTAS.includes(aba));
      setAbas(abasList);
      if (abasList.length > 0 && !abaAtiva) {
        setAbaAtiva(abasList[0]);
      }
    } catch (error) {
      message.error(`Erro ao carregar abas: ${error.message}`);
    }
  }, [abaAtiva]);

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

      const response = await resultadosAPI.lerAba(abaAtiva, params);
      const { data, total, columns } = response.data;

      setDados(data);
      setColunas(columns || []);
      setPagination((prev) => ({ ...prev, total }));
    } catch (error) {
      message.error(`Erro ao carregar dados: ${error.message}`);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [abaAtiva, pagination.current, pagination.pageSize, sortConfig.sortBy, sortConfig.sortOrder, filtrosAtivos]);

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
              <Table
                columns={colunasTabela}
                dataSource={dados.map((item, idx) => ({
                  ...item,
                  key: idx,
                }))}
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
              />
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

