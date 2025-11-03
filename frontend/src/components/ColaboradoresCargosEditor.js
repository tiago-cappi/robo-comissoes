import React, { useEffect, useMemo, useState } from 'react';
import { Card, Tabs, Table, Space, Button, Input, message, Modal } from 'antd';
import { ReloadOutlined, SaveOutlined, PlusOutlined, CopyOutlined, DeleteOutlined } from '@ant-design/icons';
import { regrasAPI } from '../services/api';

const sheetConfigs = {
  COLABORADORES: {
    key: 'COLABORADORES',
    idFields: ['id_colaborador'],
    display: 'Colaboradores',
  },
  CARGOS: {
    key: 'CARGOS',
    idFields: ['cargo'],
    display: 'Cargos',
  },
};

const EditorTabela = ({ sheetKey }) => {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const carregar = async () => {
    setLoading(true);
    try {
      const resp = await regrasAPI.lerAba(sheetKey, { allPages: true });
      const arr = resp.data?.data || [];
      setData(arr.map((row, idx) => ({ key: idx, __key: idx, ...row })));
      setColumns(resp.data?.columns || Object.keys(arr[0] || {}));
    } catch (e) {
      message.error(`Erro ao carregar ${sheetKey}: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sheetKey]);

  const setCell = (rowKey, col, value) => {
    setData((prev) => prev.map((r) => (r.key === rowKey ? { ...r, [col]: value } : r)));
  };

  const addRow = () => {
    const template = {};
    columns.forEach((c) => (template[c] = ''));
    const key = `new_${Date.now()}`;
    setData((prev) => [...prev, { key, __key: key, ...template }]);
  };

  const duplicateRow = (row) => {
    const key = `dup_${Date.now()}`;
    const { key: _k, __key: _r, ...rest } = row;
    setData((prev) => [...prev, { key, __key: key, ...rest }]);
  };

  const deleteRow = (row) => {
    Modal.confirm({
      title: 'Excluir linha',
      content: 'Confirma a exclusão desta linha?',
      onOk: () => setData((prev) => prev.filter((r) => r.key !== row.key)),
    });
  };

  const validateUnique = () => {
    const cfg = sheetConfigs[sheetKey];
    const idFields = cfg?.idFields || [];
    if (idFields.length === 0) return true;
    const seen = new Set();
    for (const row of data) {
      const keyVal = idFields.map((f) => String(row[f] || '').trim()).join('||');
      if (!keyVal || keyVal === '||') continue;
      if (seen.has(keyVal)) return false;
      seen.add(keyVal);
    }
    return true;
  };

  const salvar = async () => {
    if (!validateUnique()) {
      message.error('Violação de unicidade: verifique IDs/cargos duplicados.');
      return;
    }
    setSaving(true);
    try {
      const payload = data.map(({ key, __key, ...rest }) => rest);
      await regrasAPI.salvarAba(sheetKey, payload, true);
      message.success('Alterações salvas');
      await carregar();
    } catch (e) {
      message.error(e.message || 'Falha ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const tableCols = useMemo(() => (
    (columns || []).map((c) => ({
      title: c,
      dataIndex: c,
      key: c,
      width: 180,
      render: (val, row) => (
        <Input value={val} onChange={(e) => setCell(row.key, c, e.target.value)} />
      ),
    })).concat([
      {
        title: 'Ações',
        key: 'acoes',
        width: 120,
        fixed: 'right',
        render: (_, row) => (
          <Space>
            <Button icon={<CopyOutlined />} onClick={() => duplicateRow(row)} />
            <Button danger icon={<DeleteOutlined />} onClick={() => deleteRow(row)} />
          </Space>
        ),
      },
    ])
  ), [columns, data]);

  return (
    <Card
      title={sheetConfigs[sheetKey]?.display || sheetKey}
      extra={
        <Space>
          <Button icon={<PlusOutlined />} onClick={addRow}>Adicionar</Button>
          <Button icon={<ReloadOutlined />} onClick={carregar} loading={loading}>Recarregar</Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={salvar} loading={saving}>Salvar</Button>
        </Space>
      }
    >
      <Table
        columns={tableCols}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 'max-content' }}
        size="small"
      />
    </Card>
  );
};

const ColaboradoresCargosEditor = () => {
  return (
    <Card>
      <Tabs
        items={[
          { key: 'colabs', label: 'Colaboradores', children: <EditorTabela sheetKey="COLABORADORES" /> },
          { key: 'cargos', label: 'Cargos', children: <EditorTabela sheetKey="CARGOS" /> },
        ]}
      />
    </Card>
  );
};

export default ColaboradoresCargosEditor;


