import React from 'react';
import { Typography, Divider } from 'antd';

const { Title } = Typography;

function formatCurrencyBR(value) {
  const num = Number(value);
  if (isNaN(num)) return '-';
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

const ReconProcessoModal = ({ rowData }) => {
  const saldo = Number(rowData?.SALDO_FINAL_RECONCILIACAO || 0);
  return (
    <div>
      <Title level={4}>Balanço da Reconciliação do Processo</Title>
      <p><b>Processo:</b> {rowData?.PROCESSO || rowData?.processo}</p>
      <Divider />

      <Title level={5}>Cálculo do Saldo Final</Title>
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0' }}>
        <span>A. Comissão Correta Total (c/ FC Histórico):</span>
        <strong style={{ fontSize: '1.1em' }}>{formatCurrencyBR(rowData?.COMISSAO_CORRETA_TOTAL)}</strong>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #ccc' }}>
        <span>B. Total de Adiantamentos já Pagos (sem FC):</span>
        <strong style={{ fontSize: '1.1em', color: '#ff4d4f' }}>- {formatCurrencyBR(rowData?.TOTAL_ADIANTAMENTOS_PAGOS)}</strong>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '20px 0' }}>
        <span style={{ fontSize: '1.2em' }}><b>Saldo Final (A - B):</b></span>
        <h3 style={{ margin: 0 }}>{formatCurrencyBR(rowData?.SALDO_FINAL_RECONCILIACAO)}</h3>
      </div>
      <Divider />

      <Title level={5}>Resultado</Title>
      {saldo > 0 && <p style={{ color: 'green' }}>Um saldo positivo de {formatCurrencyBR(saldo)} será PAGO para quitar este processo.</p>}
      {saldo < 0 && <p style={{ color: 'red' }}>Um saldo negativo de {formatCurrencyBR(Math.abs(saldo))} será DESCONTADO para quitar este processo.</p>}
      {saldo === 0 && <p>O valor adiantado estava correto. Nenhum ajuste é necessário.</p>}
    </div>
  );
};

export default ReconProcessoModal;


