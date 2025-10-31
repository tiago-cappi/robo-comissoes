import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  FileTextOutlined,
  UploadOutlined,
  PlayCircleOutlined,
  BarChartOutlined,
} from '@ant-design/icons';

const { Sider, Header } = Layout;

const MainLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/regras',
      icon: <FileTextOutlined />,
      label: 'Regras',
    },
    {
      key: '/uploads',
      icon: <UploadOutlined />,
      label: 'Uploads',
    },
    {
      key: '/executar',
      icon: <PlayCircleOutlined />,
      label: 'Executar Cálculo',
    },
    {
      key: '/resultados',
      icon: <BarChartOutlined />,
      label: 'Resultados',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        theme="light"
        width={250}
        style={{
          boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
        }}
      >
        <div style={{ padding: '16px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold' }}>
            Robô de Comissões
          </h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0, marginTop: '8px' }}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 'normal' }}>
            Sistema de Cálculo de Comissões
          </h1>
        </Header>
        {children}
      </Layout>
    </Layout>
  );
};

export default MainLayout;

