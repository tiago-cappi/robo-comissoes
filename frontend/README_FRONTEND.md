# 🎯 Frontend - Robô de Comissões

Sistema web para gerenciamento e visualização de comissões de vendas.

## 📋 Índice

- [Instalação](#instalação)
- [Como Usar](#como-usar)
- [Funcionalidades](#funcionalidades)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Desenvolvimento](#desenvolvimento)

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- Arquivos do backend configurados na pasta raiz do projeto

### Passos de Instalação

1. **Navegue até a pasta do frontend:**
```bash
cd frontend
```

2. **Instale as dependências:**
```bash
pip install -r requirements_frontend.txt
```

3. **Execute a aplicação:**
```bash
streamlit run app_main.py
```

4. **Acesse no navegador:**
```
http://localhost:8501
```

## 📖 Como Usar

### 1️⃣ Editar Regras de Comissões
- Navegue até a página **"📋 Regras Comissões"**
- Selecione a aba que deseja editar
- Modifique, adicione ou exclua linhas
- Salve as alterações

### 2️⃣ Upload de Arquivos
- Acesse **"📤 Upload Arquivos"**
- Faça upload dos 3 arquivos principais:
  - Análise Comercial Completa
  - fin_conci_adcli_m3
  - fin_adcli_pg_m3
- Valide os dados carregados

### 3️⃣ Processar Comissões
- Vá para **"⚙️ Processar"**
- Selecione o mês e ano
- Execute o cálculo
- Acompanhe o progresso em tempo real

### 4️⃣ Visualizar Resultados
- Entre em **"📊 Resultados"**
- Explore as tabelas e gráficos
- Baixe os relatórios gerados

## ✨ Funcionalidades

### Gerenciamento de Regras
- ✅ Edição inline de todas as abas do arquivo Regras_Comissoes.xlsx
- ✅ Adição e remoção de linhas
- ✅ Validação automática de dados
- ✅ Backup automático antes de salvar

### Upload de Dados
- ✅ Upload múltiplo de arquivos
- ✅ Validação de formato e estrutura
- ✅ Preview dos dados carregados
- ✅ Histórico de uploads

### Processamento
- ✅ Execução dos scripts de backend
- ✅ Logs em tempo real
- ✅ Tratamento de erros amigável
- ✅ Relatório de execução

### Visualização
- ✅ Tabelas interativas com filtros
- ✅ Gráficos dinâmicos
- ✅ Dashboards de métricas
- ✅ Export de dados

## 📁 Estrutura do Projeto

```
frontend/
├── app_main.py                 # Aplicação principal
├── requirements_frontend.txt   # Dependências
├── .streamlit/
│   └── config.toml            # Configuração do Streamlit
├── pages/
│   ├── 1_📋_Regras_Comissoes.py
│   ├── 2_📤_Upload_Arquivos.py
│   ├── 3_⚙️_Processar.py
│   └── 4_📊_Resultados.py
├── components/
│   ├── table_editor.py        # Editor de tabelas
│   ├── file_uploader.py       # Upload de arquivos
│   └── charts.py              # Gráficos
├── utils/
│   ├── excel_handler.py       # Manipulação de Excel
│   ├── backend_runner.py      # Interface com backend
│   └── validators.py          # Validações
├── config/
│   └── settings.py            # Configurações
└── assets/
    └── styles.css             # Estilos customizados
```

## 🛠️ Desenvolvimento

### Tecnologias Utilizadas

- **Streamlit**: Framework web para Python
- **Pandas**: Manipulação de dados
- **Plotly**: Visualizações interativas
- **OpenPyXL**: Leitura/escrita de Excel

### Arquitetura

O frontend é **completamente isolado** do backend:
- Lê arquivos da pasta raiz do projeto
- Executa scripts do backend via subprocess
- Não modifica o código do backend

### Contribuindo

1. Mantenha o código organizado e documentado
2. Teste todas as funcionalidades antes de commitar
3. Siga as convenções de código Python (PEP 8)
4. Documente novas funcionalidades neste README

## 📝 Notas Importantes

- ⚠️ **Não modifique os arquivos do backend** - O frontend apenas os utiliza
- 💾 **Backups automáticos** - Criados antes de qualquer alteração em Regras
- 🔒 **Validações** - Dados são validados antes de serem salvos
- 📊 **Performance** - Uso de cache para melhor experiência

## 🆘 Suporte

Para dúvidas ou problemas:
1. Consulte a documentação inline da aplicação
2. Verifique os logs de erro
3. Revise este README

---

**Versão**: 1.0.0  
**Última atualização**: Outubro 2025

