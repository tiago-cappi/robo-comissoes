import React, { useEffect, useMemo, useState } from 'react';
import { Card, Table, Space, Button, Select, Modal, Tabs, Form, InputNumber, message, Typography } from 'antd';
import { FilterOutlined, EditOutlined, PlusOutlined, SearchOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { regrasAPI } from '../services/api';

const { Option } = Select;
const { Title, Text } = Typography;

const FIELDS_CTX = ['linha', 'grupo', 'subgrupo', 'tipo_mercadoria', 'cargo'];

const FiltersPanel = ({ options, filters, setFilters, onSearch }) => (
  <Space wrap style={{ marginBottom: 12 }}>
    {FIELDS_CTX.map((f) => (
      <Select
        key={f}
        placeholder={f}
        style={{ width: 200 }}
        allowClear
        value={filters[f]}
        onChange={(v) => setFilters((prev) => ({ ...prev, [f]: v }))}
        showSearch
        filterOption={(input, option) => String(option?.children || '').toLowerCase().includes((input || '').toLowerCase())}
      >
        {(options[f] || []).map((opt) => (
          <Option key={opt} value={opt}>{opt}</Option>
        ))}
      </Select>
    ))}
    <Button type="primary" icon={<SearchOutlined />} onClick={onSearch}>Buscar Regras</Button>
  </Space>
);

const ConfigComissaoEditor = () => {
  const [options, setOptions] = useState({});
  const [dynOptionsPanel, setDynOptionsPanel] = useState({});
  const [filters, setFilters] = useState({});
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  const [wizardOpen, setWizardOpen] = useState(false);
  const [activeBatchTab, setActiveBatchTab] = useState('taxa');
  const [formTaxa] = Form.useForm();
  const [formFatias] = Form.useForm();
  const [formValidar] = Form.useForm();
  const [dryRunTaxaCount, setDryRunTaxaCount] = useState(null);
  const [dryRunFatias, setDryRunFatias] = useState(null); // { total, porCargo: [{cargo, linhas}] }
  const [validarOpen, setValidarOpen] = useState(false);
  const [validarResult, setValidarResult] = useState(null);

  useEffect(() => {
    const carregarOptions = async () => {
      try {
        const resp = await regrasAPI.getRuleContextOptions();
        const base = resp.data || {};
        setOptions(base);
        setDynOptionsPanel(base);
      } catch (e) {
        message.error(`Erro ao carregar opções: ${e.message}`);
      }
    };
    carregarOptions();
  }, []);

  const updateDynPanelFromFilters = async (partialFilters) => {
    try {
      const ctxKeys = ['linha', 'tipo_mercadoria', 'grupo', 'subgrupo'];
      const resp = await regrasAPI.getConfigComissao(partialFilters || {});
      const arr = Array.isArray(resp.data) ? resp.data : [];
      const byCol = {};
      ctxKeys.forEach((k) => {
        byCol[k] = Array.from(new Set(arr.map((r) => r[k]).filter((v) => v !== undefined && v !== null && String(v).trim() !== ''))).sort();
      });
      byCol['cargo'] = options['cargo'] || [];
      setDynOptionsPanel(byCol);
    } catch (e) {
      setDynOptionsPanel(options);
    }
  };

  useEffect(() => {
    const partial = ['linha', 'tipo_mercadoria', 'grupo', 'subgrupo'].reduce((acc, k) => (filters[k] ? { ...acc, [k]: filters[k] } : acc), {});
    if (Object.keys(partial).length > 0) {
      updateDynPanelFromFilters(partial);
    } else {
      setDynOptionsPanel(options);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.linha, filters.tipo_mercadoria, filters.grupo, filters.subgrupo]);

  const buscar = async () => {
    setLoading(true);
    try {
      const resp = await regrasAPI.getConfigComissao(filters);
      const arr = Array.isArray(resp.data) ? resp.data : [];
      setData(arr.map((row, idx) => ({ key: idx, ...row })));
    } catch (e) {
      message.error(`Erro ao buscar regras: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const updateInline = async (row, field, value) => {
    try {
      const payload = { ...FIELDS_CTX.reduce((acc, k) => ({ ...acc, [k]: row[k] }), {}), [field]: value };
      await regrasAPI.updateConfigComissaoInLine(payload);
      message.success('Regra atualizada');
      setData((prev) => prev.map((r) => (r.key === row.key ? { ...r, [field]: value } : r)));
    } catch (e) {
      message.error(e.message || 'Falha ao atualizar');
    }
  };

  const columns = useMemo(() => {
    const base = FIELDS_CTX.map((f) => ({ title: f, dataIndex: f, key: f, width: 160, fixed: f === 'linha' ? 'left' : undefined }));
    base.push({
      title: 'taxa_rateio_maximo_pct',
      dataIndex: 'taxa_rateio_maximo_pct',
      key: 'taxa_rateio_maximo_pct',
      width: 180,
      render: (val, row) => (
        <InputNumber
          min={0}
          max={100}
          step={0.1}
          value={val !== undefined && val !== '' ? Number(val) : 0}
          onChange={(v) => updateInline(row, 'taxa_rateio_maximo_pct', v)}
          style={{ width: '100%' }}
        />
      ),
    });
    base.push({
      title: 'fatia_cargo_pct',
      dataIndex: 'fatia_cargo_pct',
      key: 'fatia_cargo_pct',
      width: 160,
      render: (val, row) => (
        <InputNumber
          min={0}
          max={100}
          step={0.1}
          value={val !== undefined && val !== '' ? Number(val) : 0}
          onChange={(v) => updateInline(row, 'fatia_cargo_pct', v)}
          style={{ width: '100%' }}
        />
      ),
    });
    return base;
  }, []);

  const abrirWizard = () => {
    setWizardOpen(true);
    setActiveBatchTab('taxa');
    formTaxa.resetFields();
    formFatias.resetFields();
    setDryRunTaxaCount(null);
    setDryRunFatias(null);
  };

  const doDryRunTaxa = async () => {
    try {
      const values = await formTaxa.validateFields();
      const batch = {
        escopo: values.escopo || {},
        acao: { taxa_rateio_maximo_pct: { valor: values.valor } },
      };
      const resp = await regrasAPI.dryRunConfigComissao(batch);
      setDryRunTaxaCount(resp.data?.linhas_afetadas || 0);
    } catch (e) {
      message.error(e.message || 'Erro no preview de Taxa');
    }
  };

  const applyTaxa = async () => {
    try {
      const values = await formTaxa.validateFields();
      const batch = {
        escopo: values.escopo || {},
        acao: { taxa_rateio_maximo_pct: { valor: values.valor } },
      };
      await regrasAPI.applyBatchConfigComissao(batch);
      message.success('Taxa de rateio aplicada');
      setWizardOpen(false);
      buscar();
    } catch (e) {
      message.error(e.message || 'Falha ao aplicar Taxa');
    }
  };

  const doDryRunFatias = async () => {
    try {
      const values = await formFatias.validateFields();
      const escopo = values.escopo || {};
      const fatias = values.fatias || {};
      // calcular soma considerando todos os cargos (vazios = 0)
      const todosCargos = options['cargo'] || [];
      const soma = todosCargos.reduce((acc, cargo) => {
        const valor = fatias[cargo];
        if (valor === undefined || valor === null || valor === '' || (typeof valor === 'string' && valor.trim() === '')) {
          return acc;
        }
        const numVal = Number(valor);
        if (isNaN(numVal)) {
          return acc;
        }
        return acc + numVal;
      }, 0);
      if (Number(soma.toFixed(2)) !== 100.00) {
        message.error('A soma das fatias por cargo deve ser exatamente 100.00%');
        return;
      }
      // obter contagem apenas dos cargos com valor definido
      const cargosComValor = todosCargos.filter((c) => {
        const valor = fatias[c];
        return valor !== undefined && valor !== null && valor !== '' && !(typeof valor === 'string' && valor.trim() === '');
      });
      const porCargo = [];
      for (const cargo of cargosComValor) {
        const resp = await regrasAPI.getConfigComissao({ ...escopo, cargo });
        const arr = Array.isArray(resp.data) ? resp.data : [];
        porCargo.push({ cargo, linhas: arr.length });
      }
      const total = porCargo.reduce((acc, x) => acc + x.linhas, 0);
      setDryRunFatias({ total, porCargo });
    } catch (e) {
      message.error(e.message || 'Erro no preview de Fatias');
    }
  };

  const applyFatias = async () => {
    try {
      const values = await formFatias.validateFields();
      const escopo = values.escopo || {};
      const fatias = values.fatias || {};
      // calcular soma considerando todos os cargos (vazios = 0)
      const todosCargos = options['cargo'] || [];
      const soma = todosCargos.reduce((acc, cargo) => {
        const valor = fatias[cargo];
        if (valor === undefined || valor === null || valor === '' || (typeof valor === 'string' && valor.trim() === '')) {
          return acc;
        }
        const numVal = Number(valor);
        if (isNaN(numVal)) {
          return acc;
        }
        return acc + numVal;
      }, 0);
      if (Number(soma.toFixed(2)) !== 100.00) {
        message.error('A soma das fatias por cargo deve ser exatamente 100.00%');
        return;
      }
      // aplicar apenas nos cargos com valor definido
      const cargosComValor = todosCargos.filter((c) => {
        const valor = fatias[c];
        return valor !== undefined && valor !== null && valor !== '' && !(typeof valor === 'string' && valor.trim() === '');
      });
      for (const cargo of cargosComValor) {
        const valor = fatias[cargo];
        await regrasAPI.updateConfigComissaoInLine({ ...escopo, cargo, fatia_cargo_pct: valor });
      }
      message.success('Fatias aplicadas');
      setWizardOpen(false);
      buscar();
    } catch (e) {
      message.error(e.message || 'Falha ao aplicar Fatias');
    }
  };

  const abrirValidar = () => {
    setValidarOpen(true);
    setValidarResult(null);
    formValidar.resetFields();
  };

  const executarValidar = async () => {
    try {
      const values = await formValidar.validateFields();
      const contexto = values?.contexto || {};
      const resp = await regrasAPI.validateConfigComissaoPE(contexto);
      setValidarResult(resp.data);
    } catch (e) {
      message.error(e.message || 'Falha na validação');
    }
  };

  return (
    <Card
      title="Taxas e Fatias de Comissão (CONFIG_COMISSAO)"
      extra={
        <Space>
          <Button icon={<FilterOutlined />} onClick={buscar}>Buscar Regras</Button>
          <Button type="dashed" icon={<PlusOutlined />} onClick={abrirWizard}>Aplicar Alteração em Lote</Button>
          <Button icon={<CheckCircleOutlined />} onClick={abrirValidar}>Validar Soma das Fatias (PE)</Button>
        </Space>
      }
    >
      <FiltersPanel options={Object.keys(dynOptionsPanel).length ? dynOptionsPanel : options} filters={filters} setFilters={setFilters} onSearch={buscar} />
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 'max-content' }}
        size="small"
      />

      <Modal
        title="Aplicar Alteração em Lote"
        open={wizardOpen}
        onCancel={() => setWizardOpen(false)}
        footer={null}
        width={820}
        destroyOnHidden
      >
        <Tabs activeKey={activeBatchTab} onChange={setActiveBatchTab}
          items={[
            {
              key: 'taxa',
              label: 'Taxa de Rateio Máximo',
              children: (
                <Form form={formTaxa} layout="vertical" onValuesChange={(_, all) => updateDynPanelFromFilters((all && all.escopo) || {})}>
                  <Form.Item label="Escopo" name={["escopo"]}>
                    <Space wrap>
                      {['linha', 'tipo_mercadoria', 'grupo', 'subgrupo'].map((f) => (
                        <Form.Item key={f} label={f} name={["escopo", f]}>
                          <Select style={{ width: 200 }} allowClear>
                            {((dynOptionsPanel[f] || options[f] || [])).map((opt) => (
                              <Option key={opt} value={opt}>{opt}</Option>
                            ))}
                          </Select>
                        </Form.Item>
                      ))}
                    </Space>
                  </Form.Item>
                  <Form.Item label="Valor (%)" name={["valor"]} rules={[{ required: true, message: 'Informe o valor' }]}>
                    <InputNumber min={0} max={100} step={0.1} />
                  </Form.Item>
                  <Space style={{ float: 'right' }}>
                    <Button onClick={doDryRunTaxa}>Pré-visualizar</Button>
                    <Button type="primary" onClick={applyTaxa} disabled={dryRunTaxaCount === 0}>Aplicar</Button>
                  </Space>
                  {dryRunTaxaCount !== null && (
                    <div style={{ marginTop: 12 }}>
                      <Text>Linhas afetadas: </Text><b>{dryRunTaxaCount}</b>
                    </div>
                  )}
                </Form>
              )
            },
            {
              key: 'fatias',
              label: 'Fatia por Cargo (PE)',
              children: (
                <Form form={formFatias} layout="vertical" onValuesChange={(_, all) => {
                  updateDynPanelFromFilters((all && all.escopo) || {});
                }}>
                  <Form.Item label="Escopo" name={["escopo"]}>
                    <Space wrap>
                      {['linha', 'tipo_mercadoria', 'grupo', 'subgrupo'].map((f) => (
                        <Form.Item key={f} label={f} name={["escopo", f]}>
                          <Select style={{ width: 200 }} allowClear>
                            {((dynOptionsPanel[f] || options[f] || [])).map((opt) => (
                              <Option key={opt} value={opt}>{opt}</Option>
                            ))}
                          </Select>
                        </Form.Item>
                      ))}
                    </Space>
                  </Form.Item>
                  {/* O 'name' foi removido deste Form.Item wrapper para corrigir o problema de atualização */}
                  <Form.Item label="Fatias por Cargo">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {(options['cargo'] || []).map((c) => (
                        <Space key={c}>
                          <span style={{ width: 160 }}>{c}</span>
                          <Form.Item name={["fatias", c]} noStyle>
                            <InputNumber min={0} max={100} step={0.1} />
                          </Form.Item>
                          <span>%</span>
                        </Space>
                      ))}
                    </Space>
                  </Form.Item>
                  <Space style={{ float: 'right' }}>
                    <Button onClick={doDryRunFatias}>Pré-visualizar</Button>
                    {/* Botão Aplicar reage a mudanças nas fatias */}
                    <Form.Item dependencies={['fatias']} noStyle>
                      {({ getFieldValue }) => {
                        const fatias = getFieldValue('fatias') || {};
                        const todosCargos = options['cargo'] || [];
                        const soma = todosCargos.reduce((acc, cargo) => {
                          const valor = fatias[cargo];
                          if (valor === undefined || valor === null || valor === '' || (typeof valor === 'string' && valor.trim() === '')) return acc;
                          const numVal = Number(valor);
                          return isNaN(numVal) ? acc : acc + numVal;
                        }, 0);
                        const disabled = Number(soma.toFixed(2)) !== 100.00;
                        // eslint-disable-next-line no-console
                        console.debug('[PE][Fatias] Botão Aplicar. Soma:', soma, 'Desabilitado:', disabled, 'Valores:', fatias);
                        return <Button type="primary" onClick={applyFatias} disabled={disabled}>Aplicar</Button>;
                      }}
                    </Form.Item>
                  </Space>

                  {/* Exibição da soma reage a mudanças nas fatias */}
                  <Form.Item dependencies={['fatias']} noStyle>
                    {({ getFieldValue }) => {
                      const fatias = getFieldValue('fatias') || {};
                      const todosCargos = options['cargo'] || [];
                      const soma = todosCargos.reduce((acc, cargo) => {
                        const valor = fatias[cargo];
                        if (valor === undefined || valor === null || valor === '' || (typeof valor === 'string' && valor.trim() === '')) return acc;
                        const numVal = Number(valor);
                        return isNaN(numVal) ? acc : acc + numVal;
                      }, 0);
                      // eslint-disable-next-line no-console
                      console.debug('[PE][Fatias] Display Soma. Soma:', soma, 'Valores:', fatias);
                      return (
                        <div style={{ marginTop: 12 }}>
                          <Text>Soma das fatias: </Text>
                          <b style={{ color: Number(soma.toFixed(2)) === 100.00 ? 'green' : 'red' }}>{soma.toFixed(2)}%</b>
                        </div>
                      );
                    }}
                  </Form.Item>

                  {dryRunFatias && (
                    <div style={{ marginTop: 12 }}>
                      <Text>Linhas afetadas (total): </Text><b>{dryRunFatias.total}</b>
                      <ul>
                        {dryRunFatias.porCargo.map((x) => (
                          <li key={x.cargo}>{x.cargo}: {x.linhas}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </Form>
              )
            },
          ]}
        />
      </Modal>

      <Modal
        title="Validar Soma das Fatias (PE)"
        open={validarOpen}
        onCancel={() => setValidarOpen(false)}
        onOk={executarValidar}
      >
        <Form form={formValidar} layout="vertical">
          <Form.Item label="Contexto" name={["contexto"]}>
            <Space wrap>
              {['linha', 'grupo', 'subgrupo', 'tipo_mercadoria'].map((f) => (
                <Form.Item key={f} label={f} name={["contexto", f]}>
                  <Select style={{ width: 200 }} allowClear>
                    {(options[f] || []).map((opt) => (
                      <Option key={opt} value={opt}>{opt}</Option>
                    ))}
                  </Select>
                </Form.Item>
              ))}
            </Space>
          </Form.Item>
        </Form>
        {validarResult && (
          <div style={{ marginTop: 12 }}>
            <p>{validarResult.message}</p>
          </div>
        )}
      </Modal>
    </Card>
  );
};

export default ConfigComissaoEditor;


