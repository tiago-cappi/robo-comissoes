import React, { useEffect, useMemo, useState } from 'react';
import { Card, Tabs, Table, Space, Button, InputNumber, Input, Select, message } from 'antd';
import { ReloadOutlined, SaveOutlined } from '@ant-design/icons';
import { regrasAPI } from '../services/api';

const { Option } = Select;

const SHEETS = [
  { key: 'METAS_APLICACAO', label: 'Metas de Aplicação', ctx: ['linha', 'tipo_mercadoria'] },
  { key: 'METAS_INDIVIDUAIS', label: 'Metas Individuais', ctx: ['nome_colaborador'] },
  { key: 'META_RENTABILIDADE', label: 'Metas de Rentabilidade', ctx: ['linha', 'grupo', 'subgrupo', 'tipo_mercadoria'] },
  { key: 'METAS_FORNECEDORES', label: 'Metas de Fornecedores', ctx: ['linha', 'fornecedor', 'moeda'] },
];

const isNumericColumnName = (col) => {
  const name = String(col || '').toLowerCase();
  return name.startsWith('meta') || name.endsWith('_pct') || name.includes('valor') || name.includes('meta_') || name.includes('anual');
};

const GenericSheetEditor = ({ sheetName, contextCols }) => {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [filters, setFilters] = useState({});
  const [options, setOptions] = useState({});

  const loadOptions = async () => {
    const opts = {};
    for (const c of contextCols) {
      try {
        const resp = await regrasAPI.obterValoresUnicos(sheetName, c);
        opts[c] = resp.data?.valores || [];
      } catch (e) {
        opts[c] = [];
      }
    }
    setOptions(opts);
  };

  const carregar = async () => {
    setLoading(true);
    try {
      const resp = await regrasAPI.lerAba(sheetName, { allPages: true, filters: Object.keys(filters).length ? filters : undefined });
      const arr = resp.data?.data || [];
      setData(arr.map((row, idx) => ({ key: idx, __key: idx, ...row })));
      setColumns(resp.data?.columns || Object.keys(arr[0] || []));
    } catch (e) {
      message.error(`Erro ao carregar ${sheetName}: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOptions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sheetName]);

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sheetName, JSON.stringify(filters)]);

  const setCell = (rowKey, col, value) => {
    setData((prev) => prev.map((r) => (r.key === rowKey ? { ...r, [col]: value } : r)));
  };

  const antdColumns = useMemo(() => {
    return (columns || []).map((col) => ({
      title: col,
      dataIndex: col,
      key: col,
      width: 160,
      render: (val, row) => (
        isNumericColumnName(col) ? (
          <InputNumber
            min={0}
            step={0.1}
            value={val !== undefined && val !== '' ? Number(val) : 0}
            onChange={(v) => setCell(row.key, col, v)}
            style={{ width: '100%' }}
          />
        ) : (
          <Input value={val} onChange={(e) => setCell(row.key, col, e.target.value)} />
        )
      ),
    }));
  }, [columns]);

  const salvar = async () => {
    setSaving(true);
    try {
      const payload = data.map(({ key, __key, ...rest }) => rest);
      await regrasAPI.salvarAba(sheetName, payload, true);
      message.success('Alterações salvas');
      await carregar();
    } catch (e) {
      message.error(e.message || 'Falha ao salvar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card
      title={sheetName}
      extra={
        <Space>
          {contextCols.map((c) => (
            <Select
              key={c}
              placeholder={c}
              style={{ width: 200 }}
              allowClear
              value={filters[c]}
              onChange={(v) => setFilters((prev) => ({ ...prev, [c]: v }))}
              showSearch
              filterOption={(input, option) => String(option?.children || '').toLowerCase().includes((input || '').toLowerCase())}
            >
              {(options[c] || []).map((opt) => (
                <Option key={opt} value={opt}>{opt}</Option>
              ))}
            </Select>
          ))}
          <Button icon={<ReloadOutlined />} onClick={carregar} loading={loading}>Recarregar</Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={salvar} loading={saving}>Salvar</Button>
        </Space>
      }
    >
      <Table
        columns={antdColumns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 'max-content' }}
        size="small"
      />
    </Card>
  );
};

const MetasEditor = () => {
  const items = SHEETS.map((s) => ({
    key: s.key,
    label: s.label,
    children: <GenericSheetEditor sheetName={s.key} contextCols={s.ctx} />,
  }));

  return (
    <Card>
      <Tabs items={items} />
    </Card>
  );
};

export default MetasEditor;


