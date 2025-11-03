import React, { useEffect, useMemo, useState } from 'react';
import { Card, Table, InputNumber, Button, Space, message, Tag } from 'antd';
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';
import { regrasAPI } from '../services/api';

const COMPONENTES = [
  'faturamento_linha',
  'conversao_linha',
  'rentabilidade',
  'faturamento_individual',
  'conversao_individual',
  'retencao_clientes',
  'meta_fornecedor_1',
  'meta_fornecedor_2',
];

const PesosMetasEditor = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const carregar = async () => {
    setLoading(true);
    try {
      const resp = await regrasAPI.getPesosMetas();
      const arr = Array.isArray(resp.data) ? resp.data : [];
      // Garantir campos numéricos
      const norm = arr.map((row, idx) => ({
        key: idx,
        ...row,
      }));
      setData(norm);
    } catch (e) {
      message.error(`Erro ao carregar PESOS_METAS: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChangeValor = (rowIndex, field, value) => {
    setData((prev) => {
      const copy = [...prev];
      copy[rowIndex] = { ...copy[rowIndex], [field]: value };
      return copy;
    });
  };

  const columns = useMemo(() => {
    const cols = [];
    // Primeira coluna de identificação (tenta usar 'cargo' se existir, senão a primeira string)
    const idTitle = 'cargo';
    const hasCargo = data.some((r) => Object.prototype.hasOwnProperty.call(r, 'cargo'));
    cols.push({
      title: hasCargo ? 'Cargo' : 'Linha',
      dataIndex: hasCargo ? 'cargo' : Object.keys(data[0] || {}).find((k) => typeof (data[0] || {})[k] === 'string') || 'cargo',
      key: 'idcol',
      width: 200,
      fixed: 'left',
      render: (text) => text || '-',
    });

    COMPONENTES.forEach((field) => {
      cols.push({
        title: field,
        dataIndex: field,
        key: field,
        width: 150,
        render: (value, record, index) => (
          <InputNumber
            min={0}
            max={100}
            step={0.1}
            value={value !== undefined && value !== '' ? Number(value) : 0}
            onChange={(v) => handleChangeValor(index, field, v)}
            style={{ width: '100%' }}
          />
        ),
      });
    });

    cols.push({
      title: 'Soma',
      key: 'soma',
      width: 120,
      fixed: 'right',
      render: (_, record) => {
        const soma = COMPONENTES.reduce((acc, c) => acc + (Number(record[c]) || 0), 0);
        const ok = Math.abs(soma - 100) <= 0.1;
        return ok ? <Tag color="green">{soma.toFixed(1)}%</Tag> : <Tag color="red"><b>{soma.toFixed(1)}%</b></Tag>;
      },
    });

    return cols;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const salvar = async () => {
    setSaving(true);
    try {
      const payload = data.map(({ key, ...rest }) => rest);
      await regrasAPI.updatePesosMetas(payload);
      message.success('PESOS_METAS salvo com sucesso');
      await carregar();
    } catch (e) {
      message.error(e.message || 'Falha ao salvar PESOS_METAS');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card
      title="Pesos do Fator de Correção (FC)"
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={carregar} loading={loading}>Recarregar</Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={salvar} loading={saving}>Salvar Pesos</Button>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 'max-content' }}
        size="small"
      />
    </Card>
  );
};

export default PesosMetasEditor;


