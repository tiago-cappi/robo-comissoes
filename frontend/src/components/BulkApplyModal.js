import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Steps,
  Select,
  Input,
  Button,
  Table,
  Space,
  message,
} from 'antd';
import { regrasAPI } from '../services/api';

const { Step } = Steps;
const { Option } = Select;

const BulkApplyModal = ({ visible, onCancel, onConfirm, abaNome, dados = [], colunas = [] }) => {
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [previewData, setPreviewData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!visible) {
      form.resetFields();
      setCurrentStep(0);
      setPreviewData([]);
    }
  }, [visible, form]);

  const handlePreview = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const request = {
        escopo: values.escopo || {},
        campos: values.campos || {},
        modo: values.modo,
        previewOnly: true,
      };

      const response = await regrasAPI.aplicarMassa(abaNome, request);
      const { preview, total_afetadas } = response.data;

      setPreviewData(preview || []);
      message.success(`Preview: ${total_afetadas} linhas serão afetadas`);
      setCurrentStep(3);
    } catch (error) {
      message.error(`Erro ao gerar preview: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const request = {
        escopo: values.escopo || {},
        campos: values.campos || {},
        modo: values.modo,
        previewOnly: false,
      };

      await regrasAPI.aplicarMassa(abaNome, request);
      message.success('Alterações aplicadas com sucesso!');
      onConfirm();
    } catch (error) {
      message.error(`Erro ao aplicar: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Obter valores únicos para filtros
  const getUniqueValues = (coluna) => {
    if (!dados || !coluna) return [];
    const values = new Set();
    dados.forEach((item) => {
      if (item[coluna]) values.add(item[coluna]);
    });
    return Array.from(values).sort();
  };

  // Colunas de escopo comuns
  const colunasEscopo = ['linha', 'grupo', 'subgrupo', 'tipo_mercadoria'].filter(
    (col) => colunas.includes(col)
  );

  // Colunas editáveis (excluindo colunas de escopo)
  const colunasEditaveis = colunas.filter(
    (col) => !colunasEscopo.includes(col) && col !== 'id_colaborador'
  );

  return (
    <Modal
      title="Aplicar Alterações em Massa"
      visible={visible}
      onCancel={onCancel}
      width={800}
      footer={null}
    >
      <Form form={form} layout="vertical">
        <Steps current={currentStep} style={{ marginBottom: 24 }}>
          <Step title="Escopo" description="Definir filtros" />
          <Step title="Campos" description="Valores a definir" />
          <Step title="Modo" description="Criar ou atualizar" />
          <Step title="Preview" description="Visualizar alterações" />
        </Steps>

        {currentStep === 0 && (
          <Form.Item label="Filtros de Escopo">
            <Space direction="vertical" style={{ width: '100%' }}>
              {colunasEscopo.map((col) => (
                <Form.Item key={col} label={col} name={['escopo', col]}>
                  <Select
                    mode="multiple"
                    placeholder={`Selecione ${col}`}
                    showSearch
                    allowClear
                  >
                    {getUniqueValues(col).map((val) => (
                      <Option key={val} value={val}>
                        {val}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              ))}
            </Space>
          </Form.Item>
        )}

        {currentStep === 1 && (
          <Form.Item label="Campos a Definir">
            <Space direction="vertical" style={{ width: '100%' }}>
              {colunasEditaveis.map((col) => (
                <Form.Item key={col} label={col} name={['campos', col]}>
                  <Input placeholder={`Valor para ${col}`} />
                </Form.Item>
              ))}
            </Space>
          </Form.Item>
        )}

        {currentStep === 2 && (
          <Form.Item
            label="Modo de Aplicação"
            name="modo"
            rules={[{ required: true, message: 'Selecione o modo' }]}
          >
            <Select>
              <Option value="criar">Criar novas linhas</Option>
              <Option value="atualizar">Atualizar linhas existentes</Option>
            </Select>
          </Form.Item>
        )}

        {currentStep === 3 && (
          <div>
            <Table
              dataSource={previewData}
              columns={colunas.slice(0, 10).map((col) => ({
                title: col,
                dataIndex: col,
                key: col,
              }))}
              pagination={{ pageSize: 5 }}
              size="small"
            />
            <p style={{ marginTop: 16, color: '#666' }}>
              Total de linhas afetadas: {previewData.length}
            </p>
          </div>
        )}

        <Space style={{ marginTop: 24, float: 'right' }}>
          {currentStep > 0 && (
            <Button onClick={() => setCurrentStep(currentStep - 1)}>Anterior</Button>
          )}
          {currentStep < 3 && (
            <Button type="primary" onClick={() => setCurrentStep(currentStep + 1)}>
              Próximo
            </Button>
          )}
          {currentStep === 2 && (
            <Button type="primary" onClick={handlePreview} loading={loading}>
              Gerar Preview
            </Button>
          )}
          {currentStep === 3 && (
            <Button type="primary" onClick={handleConfirm} loading={loading}>
              Confirmar e Aplicar
            </Button>
          )}
        </Space>
      </Form>
    </Modal>
  );
};

export default BulkApplyModal;

