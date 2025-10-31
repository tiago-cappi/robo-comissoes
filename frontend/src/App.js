import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import MainLayout from './components/MainLayout';
import RegrasPage from './pages/RegrasPage';
import UploadsPage from './pages/UploadsPage';
import ExecutarPage from './pages/ExecutarPage';
import ResultadosPage from './pages/ResultadosPage';

import 'antd/dist/reset.css';
import './App.css';

const { Content } = Layout;

function App() {
  return (
    <Router>
      <MainLayout>
        <Content style={{ padding: '24px', minHeight: '100vh' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/regras" replace />} />
            <Route path="/regras" element={<RegrasPage />} />
            <Route path="/uploads" element={<UploadsPage />} />
            <Route path="/executar" element={<ExecutarPage />} />
            <Route path="/resultados" element={<ResultadosPage />} />
          </Routes>
        </Content>
      </MainLayout>
    </Router>
  );
}

export default App;

