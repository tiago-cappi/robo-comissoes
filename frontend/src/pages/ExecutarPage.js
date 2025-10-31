import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Form,
  InputNumber,
  Button,
  Progress,
  Typography,
  Space,
  Alert,
  List,
  Divider,
  message,
} from 'antd';
import {
  PlayCircleOutlined,
  DownloadOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import { execucaoAPI, resultadosAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const ExecutarPage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [, setJobId] = useState(null);
  const [progresso, setProgresso] = useState({
    percent: 0,
    etapa: '',
    mensagens: [],
    status: 'idle',
  });
  const navigate = useNavigate();
  const pollingRef = useRef(null);

  // Limpar polling ao desmontar
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const iniciarPolling = (id) => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    pollingRef.current = setInterval(async () => {
      try {
        const response = await execucaoAPI.consultarProgresso(id);
        const data = response.data;
        setProgresso({
          percent: data.percent || 0,
          etapa: data.etapa || '',
          mensagens: data.mensagens || [],
          status: data.status || 'em_andamento',
        });

        // Se concluído, parar polling
        if (data.status === 'concluido' || data.status === 'erro') {
          clearInterval(pollingRef.current);
          setLoading(false);
        }
      } catch (error) {
        console.error('Erro ao consultar progresso:', error);
      }
    }, 1500); // Polling a cada 1.5 segundos
  };

  const handleCalcular = async (values) => {
    const { mes, ano } = values;
    
    setLoading(true);
    setProgresso({
      percent: 0,
      etapa: 'Iniciando cálculo...',
      mensagens: [],
      status: 'em_andamento',
    });

    try {
      const response = await execucaoAPI.iniciar(mes, ano);
      const newJobId = response.data.job_id;
      setJobId(newJobId);
      
      // Iniciar polling
      iniciarPolling(newJobId);
      
      message.success('Cálculo iniciado com sucesso!');
    } catch (error) {
      message.error(`Erro ao iniciar cálculo: ${error.message}`);
      setLoading(false);
    }
  };

  const handleBaixar = async () => {
    try {
      const response = await resultadosAPI.baixar();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Obter nome do arquivo do header ou usar padrão
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'Comissoes_Calculadas.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      message.error(`Erro ao baixar arquivo: ${error.message}`);
    }
  };

  const handleVerResultados = () => {
    navigate('/resultados');
  };

  const isConcluido = progresso.status === 'concluido';
  const isErro = progresso.status === 'erro';
  const isExecutando = progresso.status === 'em_andamento';

  return (
    <div>
      <Card>
        <Title level={2}>Executar Cálculo de Comissões</Title>
        <Text type="secondary">
          Selecione o mês e ano para apuração e execute o cálculo de comissões.
        </Text>
      </Card>

      <Card style={{ marginTop: 24 }}>
        <Form
          form={form}
          layout="inline"
          onFinish={handleCalcular}
          initialValues={{
            mes: new Date().getMonth() + 1,
            ano: new Date().getFullYear(),
          }}
        >
          <Form.Item
            label="Mês"
            name="mes"
            rules={[
              { required: true, message: 'Selecione o mês' },
              { type: 'number', min: 1, max: 12 },
            ]}
          >
            <InputNumber min={1} max={12} />
          </Form.Item>

          <Form.Item
            label="Ano"
            name="ano"
            rules={[
              { required: true, message: 'Selecione o ano' },
              { type: 'number', min: 2000, max: 2100 },
            ]}
          >
            <InputNumber min={2000} max={2100} />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              htmlType="submit"
              loading={loading}
              disabled={isExecutando}
              size="large"
            >
              Calcular Comissões
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {(isExecutando || isConcluido || isErro) && (
        <Card style={{ marginTop: 24 }}>
          <Title level={4}>Progresso da Execução</Title>
          
          <Progress
            percent={Math.round(progresso.percent)}
            status={isErro ? 'exception' : isConcluido ? 'success' : 'active'}
            strokeColor={isConcluido ? '#52c41a' : undefined}
          />

          <Divider />

          <Space direction="vertical" style={{ width: '100%' }}>
            <Text strong>Etapa Atual:</Text>
            <Text>{progresso.etapa || 'Aguardando...'}</Text>
          </Space>

          {progresso.mensagens.length > 0 && (
            <>
              <Divider />
              <Title level={5}>Logs:</Title>
              <List
                size="small"
                dataSource={progresso.mensagens}
                renderItem={(msg, idx) => (
                  <List.Item>
                    <Text code style={{ fontSize: 12 }}>
                      {msg}
                    </Text>
                  </List.Item>
                )}
                style={{ maxHeight: 300, overflowY: 'auto' }}
              />
            </>
          )}

          {isConcluido && (
            <Alert
              message="Cálculo concluído com sucesso!"
              type="success"
              showIcon
              style={{ marginTop: 16 }}
              action={
                <Space>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={handleBaixar}
                  >
                    Baixar Excel
                  </Button>
                  <Button
                    size="small"
                    type="primary"
                    icon={<ArrowRightOutlined />}
                    onClick={handleVerResultados}
                  >
                    Ver Resultados
                  </Button>
                </Space>
              }
            />
          )}

          {isErro && (
            <Alert
              message="Erro durante a execução"
              description="Verifique os logs para mais detalhes"
              type="error"
              showIcon
              style={{ marginTop: 16 }}
            />
          )}
        </Card>
      )}
    </div>
  );
};

export default ExecutarPage;

