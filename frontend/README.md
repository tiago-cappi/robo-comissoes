# Commission Rules Frontend

This Streamlit application provides an interactive viewer and editor for the `Regras_Comissoes.xlsx` workbook.

## Installation

1. Create or activate the Python virtual environment used by the project.
2. Install the dependencies:

   ```bash
   pip install streamlit pandas openpyxl
   ```

## Usage

Run the Streamlit application from the project root directory:

```bash
streamlit run frontend/app.py
```

The viewer expects the `Regras_Comissoes.xlsx` file to be located in the project root (one level above the `frontend` folder). Use the editable table to adjust values, marque linhas na coluna **Excluir?** para removê-las ou clique em **Adicionar nova linha** (com filtros limpos) para inserir registros vazios. Finalize clicando em **Salvar Alterações no Regras_Comissoes.xlsx** e confirme para sobrescrever a aba selecionada.
