import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  message,
  Space,
  Input,
  Modal,
  Select,
} from 'antd';
import {
  SaveOutlined,
  PlusOutlined,
  CopyOutlined,
  DeleteOutlined,
  ReloadOutlined,
  FilterOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { regrasAPI } from '../services/api';
import BulkApplyModal from '../components/BulkApplyModal';

const { TabPane } = Tabs;
const { Search } = Input;
const { Option } = Select;

// Abas que permitem aplicação em massa
const ABAS_COM_BULK = ['HIERARQUIA', 'ATRIBUICOES', 'CONFIG_COMISSAO'];

const RegrasPage = () => {
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
  const [linhasEditadas, setLinhasEditadas] = useState(new Set());
  const [dadosEditados, setDadosEditados] = useState({});
  const [modalBulkVisible, setModalBulkVisible] = useState(false);
  const [valoresUnicosCache, setValoresUnicosCache] = useState({});
  const [filtrosAtivos, setFiltrosAtivos] = useState({});

  const carregarAbas = useCallback(async () => {
    try {
      const response = await regrasAPI.listarAbas();
      const abasList = response.data.abas || [];
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
      // Converter filtros ativos em padrão OR para o backend
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

      const response = await regrasAPI.lerAba(abaAtiva, params);
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

    // Atualizar filtros ativos
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
      const response = await regrasAPI.obterValoresUnicos(abaAtiva, coluna);
      const valores = response.data.valores || [];
      setValoresUnicosCache((prev) => ({ ...prev, [cacheKey]: valores }));
      return valores;
    } catch (error) {
      // Erro 404 (coluna não encontrada) é esperado e não deve ser mostrado
      // Outros erros também serão silenciosos para não poluir a interface
      return [];
    }
  }, [abaAtiva, colunas, valoresUnicosCache]);

  const handleEditarCelula = (record, coluna, valor) => {
    const key = record.__key || Math.random();
    const dadosNovos = { ...dadosEditados };

    if (!dadosNovos[key]) {
      dadosNovos[key] = { ...record };
    }
    dadosNovos[key][coluna] = valor;

    setDadosEditados(dadosNovos);
    setLinhasEditadas(new Set([...linhasEditadas, key]));

    // Atualizar dados locais
    setDados((prev) =>
      prev.map((item) =>
        (item.__key || Math.random()) === key ? { ...item, [coluna]: valor } : item
      )
    );
  };

  const handleSalvar = async () => {
    if (linhasEditadas.size === 0) {
      message.warning('Nenhuma alteração para salvar');
      return;
    }

    setLoading(true);
    try {
      // Preparar dados para salvar (todas as linhas, não apenas editadas)
      const dadosParaSalvar = dados.map((item) => {
        const key = item.__key || Math.random();
        if (dadosEditados[key]) {
          return dadosEditados[key];
        }
        // Remover __key antes de salvar
        const { __key, ...rest } = item;
        return rest;
      });

      await regrasAPI.salvarAba(abaAtiva, dadosParaSalvar, true);

      message.success('Alterações salvas com sucesso!');
      setLinhasEditadas(new Set());
      setDadosEditados({});
      await carregarDados();
    } catch (error) {
      message.error(`Erro ao salvar: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAdicionarLinha = () => {
    const novaLinha = {};
    colunas.forEach((col) => {
      novaLinha[col] = '';
    });
    const key = `new_${Date.now()}`;
    novaLinha.__key = key;
    setDados([...dados, novaLinha]);
    setLinhasEditadas(new Set([...linhasEditadas, key]));
  };

  const handleDuplicarLinha = (record) => {
    const linhaDuplicada = { ...record };
    const novoKey = `dup_${Date.now()}`;
    linhaDuplicada.__key = novoKey;
    setDados([...dados, linhaDuplicada]);
    setLinhasEditadas(new Set([...linhasEditadas, novoKey]));
  };

  const handleExcluirLinha = (record) => {
    Modal.confirm({
      title: 'Confirmar exclusão',
      content: 'Deseja realmente excluir esta linha?',
      onOk: () => {
        const key = record.__key || Math.random();
        setDados(dados.filter((item) => (item.__key || Math.random()) !== key));
        setLinhasEditadas(new Set([...linhasEditadas].filter((k) => k !== key)));
      },
    });
  };

  const handleBuscaGlobal = async (value) => {
    if (!abaAtiva) return;

    if (value && value.trim()) {
      setLoading(true);
      try {
        // Buscar todas as páginas sem filtros
        const response = await regrasAPI.lerAba(abaAtiva, {
          allPages: true,
        });

        const todosDados = response.data.data || [];
        const termoBusca = value.trim().toLowerCase();

        // Filtrar no frontend: qualquer coluna que contenha o termo
        const dadosFiltrados = todosDados.filter((item) =>
          Object.values(item).some((val) =>
            String(val || '').toLowerCase().includes(termoBusca)
          )
        );

        setDados(dadosFiltrados);
        setPagination((prev) => ({ ...prev, total: dadosFiltrados.length, current: 1 }));
      } catch (error) {
        message.error(`Erro na busca: ${error.message}`);
      } finally {
        setLoading(false);
      }
    } else {
      // Limpar busca e recarregar dados normais
      setPagination({ current: 1, pageSize: 20, total: 0 });
      setSortConfig({ sortBy: null, sortOrder: null });
      carregarDados();
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

  const colunasTabela = colunas.map((col) => ({
      title: col,
      dataIndex: col,
      key: col,
      width: 150,
      sorter: true,
      sortOrder: sortConfig.sortBy === col ? (sortConfig.sortOrder === 'asc' ? 'ascend' : 'descend') : null,
      filterDropdown: criarFilterDropdown(col),
      filterIcon: (filtered) => (
        <FilterOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
      ),
      onFilter: (value, record) => {
        if (!value || value.length === 0) return true;
        return value.includes(String(record[col] || ''));
      },
      render: (text, record) => {
      const itemKey = record.__key || Math.random();
      const isEditado = linhasEditadas.has(itemKey);

      return (
        <Input
          value={text || ''}
          onChange={(e) => handleEditarCelula(record, col, e.target.value)}
          style={{
            border: isEditado ? '1px solid #1890ff' : undefined,
            backgroundColor: isEditado ? '#e6f7ff' : undefined,
          }}
          size="small"
        />
      );
    },
  }));

  // Adicionar coluna de ações
  colunasTabela.push({
    title: 'Ações',
    key: 'acoes',
    width: 120,
    fixed: 'right',
    render: (_, record) => (
      <Space size="small">
        <Button
          type="link"
          icon={<CopyOutlined />}
          onClick={() => handleDuplicarLinha(record)}
          size="small"
        />
        <Button
          type="link"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleExcluirLinha(record)}
          size="small"
        />
      </Space>
    ),
  });

  return (
    <div>
      <Card
        title="Editor de Regras"
        extra={
          <Space>
            <Search
              placeholder="Buscar..."
              onSearch={handleBuscaGlobal}
              style={{ width: 250 }}
              allowClear
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={carregarDados}
              loading={loading}
            >
              Atualizar
            </Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSalvar}
              disabled={linhasEditadas.size === 0}
              loading={loading}
            >
              Salvar ({linhasEditadas.size})
            </Button>
            <Button
              icon={<PlusOutlined />}
              onClick={handleAdicionarLinha}
            >
              Adicionar Linha
            </Button>
            {ABAS_COM_BULK.includes(abaAtiva) && (
              <Button
                icon={<ThunderboltOutlined />}
                onClick={() => setModalBulkVisible(true)}
                type="dashed"
              >
                Aplicar em Massa
              </Button>
            )}
          </Space>
        }
      >
        <Tabs
          activeKey={abaAtiva}
          onChange={setAbaAtiva}
          type="card"
        >
          {abas.map((aba) => (
            <TabPane tab={aba} key={aba}>
              <Table
                columns={colunasTabela}
                dataSource={dados.map((item, idx) => ({
                  ...item,
                  __key: item.__key || idx,
                  key: item.__key || idx,
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

      <BulkApplyModal
        visible={modalBulkVisible}
        onCancel={() => setModalBulkVisible(false)}
        onConfirm={() => {
          setModalBulkVisible(false);
          carregarDados();
        }}
        abaNome={abaAtiva}
        dados={dados}
        colunas={colunas}
      />
    </div>
  );
};

export default RegrasPage;

