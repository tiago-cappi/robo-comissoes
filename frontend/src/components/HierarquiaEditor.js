import React, { useEffect, useMemo, useState } from 'react';
import { Card, Table, Space, Button, Select, Input, Modal, message } from 'antd';
import { ReloadOutlined, SaveOutlined, PlusOutlined, CopyOutlined, DeleteOutlined } from '@ant-design/icons';
import { regrasAPI } from '../services/api';

const { Option } = Select;

const CONTEXT_COLS = ['linha', 'grupo', 'subgrupo', 'tipo_mercadoria'];

const HierarquiaEditor = () => {
    const [data, setData] = useState([]);
    const [columns, setColumns] = useState([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [filters, setFilters] = useState({});
  const [options, setOptions] = useState({});

    const loadOptions = async () => {
        const opts = {};
        for (const c of CONTEXT_COLS) {
            try {
                const resp = await regrasAPI.obterValoresUnicos('HIERARQUIA', c);
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
            const resp = await regrasAPI.lerAba('HIERARQUIA', { allPages: true, filters: Object.keys(filters).length ? filters : undefined });
            const arr = resp.data?.data || [];
            setData(arr.map((row, idx) => ({ key: idx, __key: idx, ...row })));
            setColumns(resp.data?.columns || Object.keys(arr[0] || {}));
        } catch (e) {
            message.error(`Erro ao carregar HIERARQUIA: ${e.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadOptions(); }, []);
    useEffect(() => { carregar(); /* eslint-disable-next-line */ }, [JSON.stringify(filters)]);

  const dynOptions = useMemo(() => {
    const byCol = {};
    CONTEXT_COLS.forEach((c) => {
      byCol[c] = Array.from(new Set((data || []).map((r) => r[c]).filter((v) => v !== undefined && v !== null && String(v).trim() !== ''))).sort();
    });
    return byCol;
  }, [data]);

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

    const validateUniqueTuple = () => {
        const seen = new Set();
        for (const row of data) {
            const tuple = CONTEXT_COLS.map((c) => String(row[c] || '').trim()).join('||');
            if (!tuple) continue;
            if (seen.has(tuple)) return false;
            seen.add(tuple);
        }
        return true;
    };

    const validateRequired = () => {
        // exigir pelo menos linha e tipo_mercadoria
        for (const row of data) {
            const linha = String(row['linha'] || '').trim();
            const tipo = String(row['tipo_mercadoria'] || '').trim();
            if (!linha || !tipo) return false;
        }
        return true;
    };

    const salvar = async () => {
        if (!validateRequired()) {
            message.error('Preencha ao menos linha e tipo_mercadoria em todas as linhas.');
            return;
        }
        if (!validateUniqueTuple()) {
            message.error('Existe duplicidade em (linha, grupo, subgrupo, tipo_mercadoria).');
            return;
        }
        setSaving(true);
        try {
            const payload = data.map(({ key, __key, ...rest }) => rest);
            await regrasAPI.salvarAba('HIERARQUIA', payload, true);
            message.success('HIERARQUIA salva com sucesso');
            await carregar();
        } catch (e) {
            message.error(e.message || 'Falha ao salvar HIERARQUIA');
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
                width: 140,
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
            title="Hierarquia de Produtos (HIERARQUIA)"
            extra={
                <Space>
          {CONTEXT_COLS.map((c) => (
                        <Select
                            key={c}
                            placeholder={c}
                            style={{ width: 180 }}
                            allowClear
                            value={filters[c]}
                            onChange={(v) => setFilters((prev) => ({ ...prev, [c]: v }))}
                            showSearch
                            filterOption={(input, option) => String(option?.children || '').toLowerCase().includes((input || '').toLowerCase())}
                        >
              {(dynOptions[c] && dynOptions[c].length ? dynOptions[c] : (options[c] || [])).map((opt) => (
                                <Option key={opt} value={opt}>{opt}</Option>
                            ))}
                        </Select>
                    ))}
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

export default HierarquiaEditor;


