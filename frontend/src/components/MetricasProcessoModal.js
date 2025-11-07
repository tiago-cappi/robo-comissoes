import React from 'react';
import { Typography, Table, Divider } from 'antd';

const { Title, Text } = Typography;

function formatPercent(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return '-';
  return `${(num * 100).toFixed(2)}%`;
}

const MetricasProcessoModal = ({ rowData }) => {
  const processo = rowData?.processo || rowData?.PROCESSO;
  const mesAno = rowData?.MES_ANO_FATURAMENTO || rowData?.mes_ano_faturamento;

  const colaboradores = Array.isArray(rowData?.__colaboradores_metricas)
    ? rowData.__colaboradores_metricas
    : [];

  return (
    <div>
      <Title level={4}>Métricas do Processo</Title>
      <p><b>Processo:</b> {processo}</p>
      {mesAno && <p><b>Mês/Ano do Faturamento:</b> {mesAno}</p>}
      <Divider />

      <Title level={5}>TCMP e FCMP por Colaborador</Title>
      <Table
        columns={[
          { title: 'Colaborador', dataIndex: 'nome_colaborador', key: 'nome_colaborador', width: 260 },
          { title: 'TCMP', dataIndex: 'tcmp', key: 'tcmp', width: 120, render: (v) => formatPercent(v) },
          { title: 'FCMP', dataIndex: 'fcmp', key: 'fcmp', width: 120, render: (v) => formatPercent(v) },
          { title: 'Fonte', dataIndex: 'fonte', key: 'fonte', width: 160 },
        ]}
        dataSource={colaboradores.map((c, idx) => ({
          key: c.key || idx,
          nome_colaborador: c.nome_colaborador,
          tcmp: c.tcmp,
          fcmp: c.fcmp,
          fonte: c.fonte || 'ESTADO',
        }))}
        pagination={false}
        rowKey="key"
        size="small"
        scroll={{ x: 'max-content' }}
      />

      <Divider />
      <div style={{ padding: '10px', background: '#f0f8ff', border: '1px solid #cce5ff', borderRadius: 4 }}>
        <Text>
          <b>TCMP</b> (Taxa de Comissão Média Ponderada) é a média ponderada pelo valor dos itens das taxas por item.
          <br />
          <b>FCMP</b> (Fator de Correção Médio Ponderado) é a média ponderada pelo valor dos itens dos FCs por item.
          <br />
          Essas métricas são calculadas no mês do faturamento e persistidas para uso em parcelas futuras.
        </Text>
      </div>
    </div>
  );
};

export default MetricasProcessoModal;


