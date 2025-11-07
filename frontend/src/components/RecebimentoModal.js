import React from 'react';
import { Typography, Divider } from 'antd';

const { Title, Text } = Typography;

function formatCurrencyBR(value) {
  const num = Number(value);
  if (isNaN(num)) return '-';
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatPercent(value) {
  const num = Number(value);
  if (isNaN(num)) return '-';
  return `${(num * 100).toFixed(2)}%`;
}

const RecebimentoModal = ({ rowData }) => {
  return (
    <div>
      <Title level={4}>Detalhe do Adiantamento por Recebimento</Title>
      <p><b>Colaborador:</b> {rowData?.nome_colaborador} ({rowData?.cargo})</p>
      <p><b>Processo:</b> {rowData?.processo}</p>
      {rowData?.DATA_RECEBIMENTO && <p><b>Data Recebimento:</b> {rowData.DATA_RECEBIMENTO}</p>}
      <Divider />

      <Title level={5}>Passo 1: Cálculo</Title>
      <ul>
        <li><b>A. Valor Recebido (Base):</b> {formatCurrencyBR(rowData?.valor_recebido_total)}</li>
        {rowData?.tcmp_aplicado !== undefined ? (
          <>
            <li><b>B. TCMP (Taxa Ponderada):</b> {formatPercent(Number(rowData?.tcmp_aplicado || 0))}</li>
            <li><b>C. FCMP (Fator Ponderado):</b> {formatPercent(Number(rowData?.fator_correcao_fc || 0))}</li>
          </>
        ) : (
          <>
            <li><b>B. Taxa de Rateio (da Regra):</b> {formatPercent(Number(rowData?.taxa_rateio_aplicada || 0))}</li>
            <li><b>C. Sua Fatia do Cargo (PE):</b> {formatPercent(Number(rowData?.percentual_elegibilidade_pe || 0))}</li>
          </>
        )}
      </ul>
      {rowData?.tcmp_aplicado !== undefined ? (
        <>
          <p><b>Fórmula (Parcela):</b> (A) × (TCMP) × (FCMP)</p>
          <p><b>Cálculo:</b> {formatCurrencyBR(rowData?.valor_recebido_total)} × {formatPercent(Number(rowData?.tcmp_aplicado || 0))} × {formatPercent(Number(rowData?.fator_correcao_fc || 0))}</p>
        </>
      ) : (
        <>
          <p><b>Fórmula (Adiantamento):</b> (A) × (B) × (C)</p>
          <p><b>Cálculo:</b> {formatCurrencyBR(rowData?.valor_recebido_total)} × {formatPercent(Number(rowData?.taxa_rateio_aplicada || 0))} × {formatPercent(Number(rowData?.percentual_elegibilidade_pe || 0))}</p>
        </>
      )}
      <h4 style={{ marginTop: 10 }}>
        Adiantamento Calculado = {formatCurrencyBR(rowData?.comissao_total)}
      </h4>
      <Divider />

      <Title level={5}>Passo 2: Explicação</Title>
      <div style={{ padding: '10px', background: '#f0f8ff', border: '1px solid #cce5ff', borderRadius: '4px' }}>
        {rowData?.tcmp_aplicado !== undefined ? (
          <>
            <p><b>ⓘ Este é um pagamento de parcela pós-faturamento.</b></p>
            <p>As métricas calculadas no mês do faturamento foram aplicadas: <b>TCMP</b> e <b>FCMP</b>.</p>
          </>
        ) : (
          <>
            <p><b>ⓘ Este é um pagamento de adiantamento.</b></p>
            <p>O Fator de Correção (FC) baseado em metas não é aplicado neste momento (FC = 1.0).</p>
            <p>O ajuste ocorrerá na 'Reconciliação' (aba RECONCILIACAO), com base no FCMP calculado no mês do faturamento.</p>
          </>
        )}
      </div>
    </div>
  );
};

export default RecebimentoModal;


