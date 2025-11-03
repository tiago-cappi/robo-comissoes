import React from 'react';
import { Typography, Tooltip } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

const { Title } = Typography;

function formatCurrencyBR(value) {
  const num = Number(value);
  if (isNaN(num)) return '-';
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

const EstadoModal = ({ rowData }) => {
  return (
    <div>
      <Title level={4}>Detalhe do Estado do Processo</Title>
      <p><b>Processo:</b> {rowData?.PROCESSO || rowData?.processo}</p>
      <hr />
      <ul>
        <li>
          <b>Status de Pagamento:</b> {rowData?.STATUS_PAGAMENTO}
          <Tooltip title="Status do pagamento do cliente (ex: 'Quitado'). Vem de Status_Pagamentos_Processos.xlsx.">
            <InfoCircleOutlined style={{ marginLeft: 8 }} />
          </Tooltip>
        </li>
        <li>
          <b>Status de Reconciliação:</b> {rowData?.STATUS_RECONCILIACAO}
          <Tooltip title="Status do acerto de comissão (ex: 'Pendente', 'Realizada'). Controlado pelo robô.">
            <InfoCircleOutlined style={{ marginLeft: 8 }} />
          </Tooltip>
        </li>
        <li>
          <b>Valor Total do Processo:</b> {formatCurrencyBR(rowData?.VALOR_TOTAL_PROCESSO)}
          <Tooltip title="Valor total faturado deste processo. Vem de Analise_Comercial_Completa.csv.">
            <InfoCircleOutlined style={{ marginLeft: 8 }} />
          </Tooltip>
        </li>
        <li>
          <b>Total Recebido (Acumulado):</b> {formatCurrencyBR(rowData?.TOTAL_PAGO_ACUMULADO)}
          <Tooltip title="Soma de todos os pagamentos de cliente para este processo, acumulado ao longo do tempo.">
            <InfoCircleOutlined style={{ marginLeft: 8 }} />
          </Tooltip>
        </li>
        <li>
          <b>Total Adiantado (Comissão):</b> {formatCurrencyBR(rowData?.TOTAL_ADIANTADO_COMISSAO)}
          <Tooltip title="Soma de todas as comissões pagas como adiantamento (com FC=1.0) para este processo, acumulado ao longo do tempo.">
            <InfoCircleOutlined style={{ marginLeft: 8 }} />
          </Tooltip>
        </li>
      </ul>
    </div>
  );
};

export default EstadoModal;


