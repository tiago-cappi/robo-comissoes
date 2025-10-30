"""
Helpers para criação de formulários.
Funções auxiliares para validação e criação de campos de formulário.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import re


def validate_required_fields(data: Dict[str, Any], required: List[str]) -> Tuple[bool, List[str]]:
    """
    Valida se os campos obrigatórios estão preenchidos.

    Args:
        data: Dicionário com os dados
        required: Lista de campos obrigatórios

    Returns:
        (is_valid, missing_fields)
    """
    missing = []
    
    for field in required:
        value = data.get(field)
        
        # Verificar se está vazio
        if value is None or value == "" or (isinstance(value, str) and value.strip() == ""):
            missing.append(field)
    
    return len(missing) == 0, missing


def validate_email(email: str) -> bool:
    """
    Valida formato de email.

    Args:
        email: Email para validar

    Returns:
        True se válido
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_cpf(cpf: str) -> bool:
    """
    Valida formato de CPF (simplificado).

    Args:
        cpf: CPF para validar

    Returns:
        True se válido
    """
    # Remover caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verificar tamanho
    return len(cpf) == 11


def validate_phone(phone: str) -> bool:
    """
    Valida formato de telefone.

    Args:
        phone: Telefone para validar

    Returns:
        True se válido
    """
    # Remover caracteres não numéricos
    phone = re.sub(r'[^0-9]', '', phone)
    
    # Verificar tamanho (10 ou 11 dígitos)
    return len(phone) in [10, 11]


def validate_unique_value(
    df: pd.DataFrame,
    column: str,
    value: Any,
    exclude_index: Optional[int] = None
) -> bool:
    """
    Valida se um valor é único em uma coluna.

    Args:
        df: DataFrame
        column: Nome da coluna
        value: Valor para verificar
        exclude_index: Índice a excluir da verificação (para edição)

    Returns:
        True se único
    """
    if df.empty or column not in df.columns:
        return True
    
    # Filtrar DataFrame
    df_check = df if exclude_index is None else df.drop(exclude_index)
    
    # Verificar se valor existe
    return value not in df_check[column].values


def validate_numeric_range(
    value: float,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Valida se um valor numérico está dentro de um intervalo.

    Args:
        value: Valor para validar
        min_val: Valor mínimo (opcional)
        max_val: Valor máximo (opcional)

    Returns:
        (is_valid, error_message)
    """
    if min_val is not None and value < min_val:
        return False, f"Valor deve ser maior ou igual a {min_val}"
    
    if max_val is not None and value > max_val:
        return False, f"Valor deve ser menor ou igual a {max_val}"
    
    return True, ""


def render_required_label(label: str) -> str:
    """
    Adiciona asterisco (*) para campos obrigatórios.

    Args:
        label: Label do campo

    Returns:
        Label com asterisco
    """
    return f"{label} *"


def render_validation_errors(errors: List[str]):
    """
    Renderiza erros de validação.

    Args:
        errors: Lista de erros
    """
    if not errors:
        return
    
    st.error(f"❌ {len(errors)} erro(s) encontrado(s):")
    
    for error in errors:
        st.write(f"- {error}")


def render_success_message(message: str, duration: int = 2):
    """
    Renderiza mensagem de sucesso temporária.

    Args:
        message: Mensagem
        duration: Duração em segundos
    """
    placeholder = st.empty()
    
    with placeholder.container():
        st.success(message)
    
    import time
    time.sleep(duration)
    
    placeholder.empty()


def create_form_section(title: str, icon: str = "📝"):
    """
    Cria uma seção de formulário com título.

    Args:
        title: Título da seção
        icon: Ícone da seção
    """
    st.markdown(f"### {icon} {title}")
    st.markdown("---")


def create_field_help_text(field_name: str, examples: List[str] = None) -> str:
    """
    Cria texto de ajuda para um campo.

    Args:
        field_name: Nome do campo
        examples: Lista de exemplos (opcional)

    Returns:
        Texto de ajuda
    """
    help_text = f"Preencha o campo {field_name}"
    
    if examples:
        help_text += f"\n\nExemplos: {', '.join(examples)}"
    
    return help_text


def confirm_action(action: str, description: str) -> bool:
    """
    Pede confirmação para uma ação.

    Args:
        action: Nome da ação
        description: Descrição da ação

    Returns:
        True se confirmado
    """
    st.warning(f"⚠️ **{action}**\n\n{description}")
    
    col1, col2 = st.columns(2)
    
    confirmed = False
    
    with col1:
        if st.button("✅ Confirmar", type="primary", use_container_width=True):
            confirmed = True
    
    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            confirmed = False
    
    return confirmed


class FormValidator:
    """Classe para validação de formulários."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def add_error(self, message: str):
        """Adiciona um erro."""
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Adiciona um aviso."""
        self.warnings.append(message)
    
    def is_valid(self) -> bool:
        """Verifica se não há erros."""
        return len(self.errors) == 0
    
    def has_warnings(self) -> bool:
        """Verifica se há avisos."""
        return len(self.warnings) > 0
    
    def render_results(self):
        """Renderiza resultados da validação."""
        if self.errors:
            st.error(f"❌ {len(self.errors)} erro(s):")
            for error in self.errors:
                st.write(f"- {error}")
        
        if self.warnings:
            st.warning(f"⚠️ {len(self.warnings)} aviso(s):")
            for warning in self.warnings:
                st.write(f"- {warning}")
        
        if not self.errors and not self.warnings:
            st.success("✅ Validação passou sem problemas!")
    
    def reset(self):
        """Reseta erros e avisos."""
        self.errors = []
        self.warnings = []


def create_dynamic_form(
    fields: Dict[str, Dict],
    form_key: str,
    submit_label: str = "Enviar"
) -> Optional[Dict[str, Any]]:
    """
    Cria um formulário dinâmico baseado em especificação.

    Args:
        fields: Dicionário com especificação dos campos
        form_key: Chave única do formulário
        submit_label: Label do botão de submit

    Returns:
        Dicionário com valores ou None se não submetido

    Exemplo:
        fields = {
            "nome": {
                "type": "text",
                "label": "Nome",
                "required": True,
                "placeholder": "Digite o nome"
            },
            "idade": {
                "type": "number",
                "label": "Idade",
                "min_value": 0,
                "max_value": 120
            }
        }
    """
    with st.form(form_key, clear_on_submit=True):
        values = {}
        
        for field_name, field_spec in fields.items():
            field_type = field_spec.get("type", "text")
            label = field_spec.get("label", field_name)
            required = field_spec.get("required", False)
            
            if required:
                label = render_required_label(label)
            
            # Renderizar campo baseado no tipo
            if field_type == "text":
                values[field_name] = st.text_input(
                    label,
                    placeholder=field_spec.get("placeholder", ""),
                    help=field_spec.get("help", "")
                )
            
            elif field_type == "number":
                values[field_name] = st.number_input(
                    label,
                    min_value=field_spec.get("min_value", None),
                    max_value=field_spec.get("max_value", None),
                    step=field_spec.get("step", 1),
                    help=field_spec.get("help", "")
                )
            
            elif field_type == "select":
                values[field_name] = st.selectbox(
                    label,
                    options=field_spec.get("options", []),
                    help=field_spec.get("help", "")
                )
            
            elif field_type == "multiselect":
                values[field_name] = st.multiselect(
                    label,
                    options=field_spec.get("options", []),
                    help=field_spec.get("help", "")
                )
            
            elif field_type == "checkbox":
                values[field_name] = st.checkbox(
                    label,
                    value=field_spec.get("default", False),
                    help=field_spec.get("help", "")
                )
            
            elif field_type == "date":
                values[field_name] = st.date_input(
                    label,
                    help=field_spec.get("help", "")
                )
            
            elif field_type == "textarea":
                values[field_name] = st.text_area(
                    label,
                    placeholder=field_spec.get("placeholder", ""),
                    help=field_spec.get("help", "")
                )
        
        # Botão de submit
        submitted = st.form_submit_button(submit_label, type="primary")
        
        if submitted:
            # Validar campos obrigatórios
            validator = FormValidator()
            
            for field_name, field_spec in fields.items():
                if field_spec.get("required", False):
                    value = values[field_name]
                    
                    if value is None or value == "" or (isinstance(value, str) and value.strip() == ""):
                        validator.add_error(f"Campo '{field_spec.get('label', field_name)}' é obrigatório")
            
            if validator.is_valid():
                return values
            else:
                validator.render_results()
                return None
    
    return None



