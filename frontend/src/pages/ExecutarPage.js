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
  Drawer,
  Input,
} from 'antd';
import {
  PlayCircleOutlined,
  DownloadOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import { execucaoAPI, resultadosAPI, healthAPI, debugAPI } from '../services/api';
import { execucaoAPI2 } from '../services/api';
import CrossSellingModal from '../components/CrossSellingModal';
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
  const [isCsModalVisible, setIsCsModalVisible] = useState(false);
  const [csCases, setCsCases] = useState([]);
  const navigate = useNavigate();
  const pollingRef = useRef(null);
  const lastParamsRef = useRef({ mes: null, ano: null });
  const elapsedTimeRef = useRef(0);
  const elapsedIntervalRef = useRef(null);
  const [debugVisible, setDebugVisible] = useState(false);
  const [backendLogs, setBackendLogs] = useState('');
  const [logLines, setLogLines] = useState(400);
  const debugIntervalRef = useRef(null);

  // Limpar polling e intervalos ao desmontar
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
      if (elapsedIntervalRef.current) {
        clearInterval(elapsedIntervalRef.current);
      }
    };
  }, []);

  const fetchBackendLogs = async (lines) => {
    try {
      console.log('[DEBUG] Buscando logs do backend...', { lines });
      const res = await debugAPI.getLogs(lines || logLines);
      setBackendLogs(typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2));
    } catch (e) {
      console.error('[DEBUG] Falha ao buscar logs do backend', e);
      setBackendLogs(`Falha ao obter logs: ${e.message}`);
    }
  };

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
    lastParamsRef.current = { mes, ano };

    console.log('[DEBUG] Iniciando handleCalcular', { mes, ano });

    setLoading(true);
    elapsedTimeRef.current = 0;
    setProgresso({
      percent: 0,
      etapa: 'Pré-scan de Cross-Selling... (0s)',
      mensagens: [],
      status: 'em_andamento',
    });

    // Iniciar contador de tempo decorrido
    if (elapsedIntervalRef.current) {
      clearInterval(elapsedIntervalRef.current);
    }
    elapsedIntervalRef.current = setInterval(() => {
      elapsedTimeRef.current += 1;
      const elapsed = elapsedTimeRef.current;
      setProgresso(prev => ({
        ...prev,
        etapa: `Pré-scan de Cross-Selling... (${elapsed}s)`,
      }));
    }, 1000);

    const startTime = Date.now();
    let timeoutId = null;

    try {
      // Verificar saúde do servidor antes de iniciar (opcional, mas útil para debug)
      try {
        console.log('[DEBUG] Verificando saúde do servidor...');
        const healthCheck = await Promise.race([
          healthAPI.check(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Health check timeout')), 5000))
        ]);
        console.log('[DEBUG] Servidor está acessível', healthCheck.data);
      } catch (healthError) {
        console.warn('[DEBUG] Health check falhou ou timeout', healthError);
        // Não bloquear, apenas logar
      }

      console.log('[DEBUG] Chamando executarPreScanCrossSelling...', { mes, ano });

      // Fallback manual de timeout (além do timeout do axios)
      const timeoutPromise = new Promise((_, reject) => {
        timeoutId = setTimeout(() => {
          console.error('[DEBUG] Timeout manual detectado após 30 segundos');
          reject(new Error('TIMEOUT_MANUAL: Requisição demorou mais de 30 segundos'));
        }, 30000); // 30 segundos
      });

      const requestPromise = execucaoAPI2.executarPreScanCrossSelling(mes, ano);

      const response = await Promise.race([requestPromise, timeoutPromise]);

      // Limpar timeouts e intervalos
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      if (elapsedIntervalRef.current) {
        clearInterval(elapsedIntervalRef.current);
        elapsedIntervalRef.current = null;
      }

      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

      console.log('[DEBUG] Pré-scan concluído', {
        elapsed: `${elapsed}s`,
        responseStatus: response.status,
        dataType: typeof response.data,
        dataLength: Array.isArray(response.data) ? response.data.length : 'N/A',
        data: response.data
      });

      const cases = response.data || [];
      console.log('[DEBUG] Casos processados', { count: cases.length, cases });

      if (!cases.length) {
        console.log('[DEBUG] Nenhum caso detectado, executando cálculo direto');
        // Sem casos -> executar direto
        runFinalExecution([]);
      } else {
        console.log('[DEBUG] Casos detectados, abrindo modal', { count: cases.length });
        setCsCases(cases);
        setIsCsModalVisible(true);
        setLoading(false);
        setProgresso(prev => ({ ...prev, status: 'idle' }));
      }
    } catch (error) {
      // Limpar timeouts e intervalos
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      if (elapsedIntervalRef.current) {
        clearInterval(elapsedIntervalRef.current);
        elapsedIntervalRef.current = null;
      }

      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      console.error('[DEBUG] Erro no pré-scan', {
        elapsed: `${elapsed}s`,
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack,
        errorResponse: error.response?.data,
        errorStatus: error.response?.status,
        errorCode: error.code,
      });

      let errorMsg = `Erro no pré-scan: ${error.message}`;
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout') || error.message.includes('TIMEOUT_MANUAL')) {
        errorMsg = 'Timeout: O pré-scan demorou mais de 30 segundos. O servidor pode estar processando ou travado. Tente novamente.';
      } else if (error.response?.status === 500) {
        errorMsg = `Erro no servidor: ${error.response.data?.detail || error.message}`;
      } else if (!error.response) {
        errorMsg = 'Erro de conexão: Verifique se o servidor está rodando e acessível.';
      }

      message.error(errorMsg);
      setLoading(false);
      setProgresso(prev => ({ ...prev, status: 'erro', etapa: `Erro: ${errorMsg}` }));
    }
  };

  const runFinalExecution = async (decisions) => {
    const { mes, ano } = lastParamsRef.current || {};
    if (!mes || !ano) {
      console.error('[DEBUG] runFinalExecution: parâmetros ausentes', { mes, ano });
      message.error('Parâmetros de mês e ano não informados.');
      return;
    }

    console.log('[DEBUG] Iniciando runFinalExecution', { mes, ano, decisionsCount: decisions?.length || 0, decisions });

    setLoading(true);
    setProgresso({
      percent: 0,
      etapa: 'Executando cálculo de comissões...',
      mensagens: [],
      status: 'em_andamento',
    });

    const startTime = Date.now();
    try {
      console.log('[DEBUG] Chamando executarCalculo...', { mes, ano, decisions });
      await execucaoAPI2.executarCalculo(mes, ano, decisions);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log('[DEBUG] Cálculo concluído com sucesso', { elapsed: `${elapsed}s` });

      setLoading(false);
      message.success('Cálculo concluído com sucesso!');
      navigate('/resultados');
    } catch (error) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      console.error('[DEBUG] Erro no cálculo', {
        elapsed: `${elapsed}s`,
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack,
        errorResponse: error.response?.data,
        errorStatus: error.response?.status,
        errorCode: error.code,
      });

      let errorMsg = `Erro ao executar cálculo: ${error.message}`;
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMsg = 'Timeout: O cálculo demorou mais de 10 minutos. Verifique o servidor.';
      } else if (error.response?.status === 500) {
        errorMsg = `Erro no servidor: ${error.response.data?.detail || error.message}`;
      } else if (!error.response) {
        errorMsg = 'Erro de conexão: Verifique se o servidor está rodando.';
      }

      message.error(errorMsg);
      setLoading(false);
      setProgresso(prev => ({ ...prev, status: 'erro', etapa: `Erro: ${errorMsg}` }));
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
                  <Button
                    size="small"
                    onClick={() => {
                      setDebugVisible(true);
                      fetchBackendLogs();
                      if (debugIntervalRef.current) {
                        clearInterval(debugIntervalRef.current);
                      }
                      debugIntervalRef.current = setInterval(() => fetchBackendLogs(), 3000);
                    }}
                  >
                    Ver Logs Backend
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
              action={
                <Button
                  size="small"
                  onClick={() => {
                    setDebugVisible(true);
                    fetchBackendLogs();
                    if (debugIntervalRef.current) {
                      clearInterval(debugIntervalRef.current);
                    }
                    debugIntervalRef.current = setInterval(() => fetchBackendLogs(), 3000);
                  }}
                >
                  Ver Logs Backend
                </Button>
              }
            />
          )}
        </Card>
      )}
      <Drawer
        title="Logs do Backend"
        placement="right"
        width={720}
        open={debugVisible}
        onClose={() => {
          setDebugVisible(false);
          if (debugIntervalRef.current) {
            clearInterval(debugIntervalRef.current);
            debugIntervalRef.current = null;
          }
        }}
        extra={
          <Space>
            <Input
              type="number"
              min={50}
              max={5000}
              value={logLines}
              onChange={(e) => setLogLines(Number(e.target.value) || 400)}
              style={{ width: 120 }}
              placeholder="Linhas"
            />
            <Button onClick={() => fetchBackendLogs()}>Atualizar</Button>
          </Space>
        }
      >
        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: 600, overflowY: 'auto', background: '#111', color: '#0f0', padding: 12 }}>
          {backendLogs || 'Sem logs disponíveis.'}
        </pre>
      </Drawer>
      <CrossSellingModal
        visible={isCsModalVisible}
        cases={csCases}
        onConfirm={(decisionsArray) => {
          setIsCsModalVisible(false);
          runFinalExecution(decisionsArray);
        }}
        onCancel={() => {
          setIsCsModalVisible(false);
        }}
      />
    </div>
  );
};

export default ExecutarPage;

