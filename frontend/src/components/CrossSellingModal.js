import React, { useEffect, useState } from 'react';
import { Modal, Card, Radio, Button } from 'antd';

const CrossSellingModal = ({ visible, cases, onConfirm, onCancel }) => {
  const [decisions, setDecisions] = useState({});

  useEffect(() => {
    const initialDecisions = {};
    (cases || []).forEach((c) => {
      initialDecisions[c.processo] = 'A';
    });
    setDecisions(initialDecisions);
  }, [cases]);

  const handleConfirm = () => {
    const decisionsArray = Object.keys(decisions).map((proc) => ({
      processo: proc,
      decision: decisions[proc],
    }));
    if (onConfirm) onConfirm(decisionsArray);
  };

  return (
    <Modal
      title="⚠️ Ação Necessária: Casos de Cross-Selling Detectados"
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Cancelar
        </Button>,
        <Button key="ok" type="primary" onClick={handleConfirm}>
          Confirmar Decisões e Executar Cálculo
        </Button>,
      ]}
      width={720}
    >
      {(cases || []).map((caseItem) => (
        <Card
          key={caseItem.processo}
          title={`Processo: ${caseItem.processo}`}
          style={{ marginBottom: 16 }}
        >
          <p>
            <strong>Consultor Externo:</strong> {caseItem.consultor}
          </p>
          <p>
            <strong>Linha da Venda:</strong> {caseItem.linha}
          </p>
          <p>
            <strong>Taxa de Cross-Selling:</strong> {caseItem.taxa}%
          </p>

          <Radio.Group
            value={decisions[caseItem.processo] || 'A'}
            onChange={(e) =>
              setDecisions({ ...decisions, [caseItem.processo]: e.target.value })
            }
          >
            <Radio value="A" style={{ display: 'block' }}>
              <strong>Opção A: SUBTRAIR da Taxa de Rateio (Padrão)</strong>
              <div style={{ marginLeft: 24, color: '#555' }}>
                A taxa de {caseItem.taxa}% é paga ao consultor. A taxa de rateio da equipe é REDUZIDA. O consultor NÃO participa do rateio restante.
              </div>
            </Radio>
            <Radio value="B" style={{ display: 'block', marginTop: 10 }}>
              <strong>Opção B: PAGAR SEPARADAMENTE</strong>
              <div style={{ marginLeft: 24, color: '#555' }}>
                A taxa de {caseItem.taxa}% é paga ao consultor. A taxa de rateio da equipe fica INTACTA. O consultor NÃO participa do rateio.
              </div>
            </Radio>
          </Radio.Group>
        </Card>
      ))}
    </Modal>
  );
};

export default CrossSellingModal;


