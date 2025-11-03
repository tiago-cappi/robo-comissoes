import React from 'react';
import { Typography, Divider } from 'antd';

const { Title, Text } = Typography;

function formatCurrencyBR(value) {
  const num = Number(value);
  if (isNaN(num)) return '-';
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

const ResumoColaboradorModal = ({ rowData }) => {
  return (
    <div>
      <Title level={4}>Composição da Comissão</Title>
      <p><b>Colaborador:</b> {rowData?.nome_colaborador}</p>
      <p><b>Cargo:</b> {rowData?.cargo}</p>
      <Divider />

      <div style={{ textAlign: 'center', margin: '20px 0' }}>
        <span style={{ fontSize: '1.2em' }}>Comissão Total:</span>
        <h2 style={{ margin: 0, color: '#1890ff' }}>
          {formatCurrencyBR(rowData?.comissao_total)}
        </h2>
      </div>

      <p>
        Sua comissão total é a soma de todos os seus ganhos (itens de faturamento, adiantamentos de recebimento e saldos de reconciliação) calculados pelo robô.
      </p>
      <p>Para ver a origem detalhada de cada valor, navegue até as abas correspondentes e filtre pelo seu nome:</p>

      <ul>
        <li><b>Itens de Faturamento:</b> Aba 'COMISSOES_CALCULADAS'</li>
        <li><b>Adiantamentos de Recebimento:</b> Aba 'COMISSOES_RECEBIMENTO'</li>
        <li><b>Saldos de Reconciliação:</b> Aba 'RECONCILIACAO'</li>
      </ul>
    </div>
  );
};

export default ResumoColaboradorModal;


