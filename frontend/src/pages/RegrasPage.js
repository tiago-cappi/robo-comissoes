import React from 'react';
import { Card, Tabs } from 'antd';
import PesosMetasEditor from '../components/PesosMetasEditor';
import ConfigComissaoEditor from '../components/ConfigComissaoEditor';
import MetasEditor from '../components/MetasEditor';
import ColaboradoresCargosEditor from '../components/ColaboradoresCargosEditor';
import HierarquiaEditor from '../components/HierarquiaEditor';

const RegrasPage = () => {
  const items = [
    { key: 'pesos', label: 'Pesos do FC', children: <PesosMetasEditor /> },
    { key: 'hierarquia', label: 'Hierarquia de Produtos', children: <HierarquiaEditor /> },
    { key: 'config', label: 'Taxas e Fatias de Comissão', children: <ConfigComissaoEditor /> },
    { key: 'metas', label: 'Gerenciar Metas', children: <MetasEditor /> },
    { key: 'colabs', label: 'Colaboradores e Cargos', children: <ColaboradoresCargosEditor /> },
  ];

  return (
    <Card title="Gerenciamento de Regras de Negócio">
      <Tabs items={items} />
      </Card>
  );
};

export default RegrasPage;

