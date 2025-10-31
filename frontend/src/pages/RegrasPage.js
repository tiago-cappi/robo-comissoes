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
  const [linhasEditadas, setLinhasEditadas] = useState(new Set());
  const [dadosEditados, setDadosEditados] = useState({});
  const [modalBulkVisible, setModalBulkVisible] = useState(false);

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
  }, []);

  const carregarDados = useCallback(async () => {
    if (!abaAtiva) return;
    
    setLoading(true);
    try {
      const params = {
        page: pagination.current,
        size: pagination.pageSize,
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
  }, [abaAtiva, pagination.current, pagination.pageSize]);

  useEffect(() => {
    carregarAbas();
  }, [carregarAbas]);

  useEffect(() => {
    if (abaAtiva) {
      carregarDados();
    }
  }, [abaAtiva, carregarDados]);

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
    const key = record.__key || Math.random();
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

  const handleBuscaGlobal = (value) => {
    // Aplicar filtro de busca em todas as colunas
    if (value) {
      const dadosFiltrados = dados.filter((item) =>
        Object.values(item).some((val) =>
          String(val).toLowerCase().includes(value.toLowerCase())
        )
      );
      setDados(dadosFiltrados);
    } else {
      carregarDados();
    }
  };

  const colunasTabela = colunas.map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    width: 150,
    sorter: true,
    filterDropdown: ({ setSelectedKeys, selectedKeys, confirm }) => (
      <div style={{ padding: 8 }}>
        <Input
          placeholder={`Filtrar ${col}`}
          value={selectedKeys[0]}
          onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
          onPressEnter={confirm}
          style={{ marginBottom: 8, display: 'block' }}
        />
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
              confirm();
            }}
            size="small"
            style={{ width: 90 }}
          >
            Limpar
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered) => (
      <FilterOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
    ),
    onFilter: (value, record) =>
      String(record[col] || '').toLowerCase().includes(value.toLowerCase()),
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
            <Button
              icon={<ThunderboltOutlined />}
              onClick={() => setModalBulkVisible(true)}
              type="dashed"
            >
              Aplicar em Massa
            </Button>
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
                pagination={{
                  ...pagination,
                  showSizeChanger: true,
                  showTotal: (total) => `Total: ${total} linhas`,
                  pageSizeOptions: ['20', '50', '100'],
                  onChange: (page, pageSize) => {
                    setPagination({ ...pagination, current: page, pageSize });
                  },
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

