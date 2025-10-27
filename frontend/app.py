from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Commission Rules Viewer", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR.parent / "Regras_Comissoes.xlsx"
DELETE_COLUMN = "__delete_row__"


def load_excel_file(file_path: Path) -> Optional[pd.ExcelFile]:
    try:
        return pd.ExcelFile(file_path, engine="openpyxl")
    except FileNotFoundError:
        st.error(
            f"Excel file not found. Expected to find it at: {file_path.resolve()}"
        )
    except Exception as exc:
        st.error(f"Unable to open Excel file: {exc}")
    return None


def get_sheet_names(excel_file: pd.ExcelFile) -> Tuple[str, ...]:
    return tuple(excel_file.sheet_names)


def load_sheet_data(file_path: Path, sheet_name: str) -> Optional[pd.DataFrame]:
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
    except FileNotFoundError:
        st.error(
            f"Excel file not found. Expected to find it at: {file_path.resolve()}"
        )
    except ValueError as exc:
        st.error(f"Sheet '{sheet_name}' could not be loaded: {exc}")
    except Exception as exc:
        st.error(f"Unable to load data from sheet '{sheet_name}': {exc}")
    return None


def ensure_sheet_data(sheet_name: str, file_path: Path) -> Optional[pd.DataFrame]:
    sheet_key = "active_sheet"
    data_key = "sheet_data"

    if (
        st.session_state.get(sheet_key) != sheet_name
        or data_key not in st.session_state
    ):
        dataframe = load_sheet_data(file_path, sheet_name)
        if dataframe is None:
            return None

        st.session_state[sheet_key] = sheet_name
        st.session_state[data_key] = dataframe
        _clear_save_state()

    return st.session_state.get(data_key)


def generate_filter_widgets(
    df: pd.DataFrame,
) -> Dict[str, Dict[str, Any]]:
    filters: Dict[str, Dict[str, Any]] = {}
    st.sidebar.header("Filters")

    for column in df.columns:
        filter_config = _build_filter_for_column(column, df[column])
        if filter_config is not None:
            filters[column] = filter_config

    return filters


def _build_filter_for_column(
    column: str,
    series: pd.Series,
) -> Optional[Dict[str, Any]]:
    ui = st.sidebar
    non_null = series.dropna()

    if non_null.empty:
        return None

    label = f"{column}"

    if pd.api.types.is_numeric_dtype(non_null):
        min_val = non_null.min()
        max_val = non_null.max()

        if pd.isna(min_val) or pd.isna(max_val) or min_val == max_val:
            return None

        if pd.api.types.is_integer_dtype(non_null):
            min_val = int(min_val)
            max_val = int(max_val)
            selected = ui.slider(
                label,
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                step=1,
            )
        else:
            min_float = float(min_val)
            max_float = float(max_val)
            selected = ui.slider(
                label,
                min_value=min_float,
                max_value=max_float,
                value=(min_float, max_float),
            )
            min_val, max_val = min_float, max_float

        return {
            "type": "numeric_range",
            "value": selected,
            "full_value": (min_val, max_val),
        }

    unique_values = non_null.unique()

    if unique_values.size <= 20:
        options = sorted(unique_values.tolist(), key=lambda item: str(item))
        selected = ui.multiselect(label, options=options, default=options)
        return {"type": "categorical", "value": selected, "full_value": options}

    text_value = ui.text_input(label, value="")
    return {"type": "text", "value": text_value}


def apply_filters(
    df: pd.DataFrame,
    filters: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    filtered_df = df.copy()

    for column, config in filters.items():
        filter_type = config.get("type")
        value = config.get("value")

        if filter_type == "numeric_range" and isinstance(value, tuple):
            min_selected, max_selected = value
            if pd.isna(min_selected) or pd.isna(max_selected):
                continue

            full_range = config.get("full_value")
            if (
                isinstance(full_range, tuple)
                and len(full_range) == 2
                and _ranges_equivalent(
                    min_selected, max_selected, full_range[0], full_range[1]
                )
            ):
                continue

            filtered_df = filtered_df[
                filtered_df[column].between(min_selected, max_selected)
            ]

        elif filter_type == "categorical" and isinstance(value, list):
            options = config.get("full_value", [])
            if not value or set(value) == set(options):
                continue
            filtered_df = filtered_df[filtered_df[column].isin(value)]

        elif filter_type == "text" and isinstance(value, str) and value:
            filtered_df = filtered_df[
                filtered_df[column]
                .astype(str)
                .str.contains(value, case=False, na=False)
            ]

    return filtered_df


def _ranges_equivalent(
    first_min: Any, first_max: Any, second_min: Any, second_max: Any
) -> bool:
    if any(pd.isna(val) for val in (first_min, first_max, second_min, second_max)):
        return False

    if all(
        isinstance(val, int)
        for val in (first_min, first_max, second_min, second_max)
    ):
        return first_min == second_min and first_max == second_max

    try:
        return (
            abs(float(first_min) - float(second_min)) <= 1e-9
            and abs(float(first_max) - float(second_max)) <= 1e-9
        )
    except (TypeError, ValueError):
        return False


def render_editable_table(
    filtered_df: pd.DataFrame,
    total_rows: int,
    sheet_name: str,
) -> Tuple[Optional[pd.DataFrame], Optional[pd.Series]]:
    if filtered_df.empty:
        st.warning("No rows match the current filters.")
        return None, None

    if total_rows != len(filtered_df):
        st.caption(f"Showing {len(filtered_df)} of {total_rows} rows.")
    else:
        st.caption(f"Showing {total_rows} rows.")

    editor_key = f"data_editor_{sheet_name}"
    editor_df = filtered_df.copy()
    if DELETE_COLUMN in editor_df.columns:
        raise ValueError(
            f"Column name conflict detected. Please rename column '{DELETE_COLUMN}'."
        )

    editor_df.insert(0, DELETE_COLUMN, False)
    edited_df = st.data_editor(
        editor_df,
        key=editor_key,
        num_rows="fixed",
        hide_index=False,
        use_container_width=True,
        column_config={
            DELETE_COLUMN: st.column_config.CheckboxColumn(
                "Excluir?", help="Marque para excluir a linha selecionada."
            )
        },
    )

    delete_mask = None
    if isinstance(edited_df, pd.DataFrame) and DELETE_COLUMN in edited_df.columns:
        delete_mask = edited_df[DELETE_COLUMN].astype(bool)
        edited_df = edited_df.drop(columns=[DELETE_COLUMN])

    return edited_df, delete_mask


def update_dataframe_with_edits(
    current_full_df: pd.DataFrame, edited_subset: Optional[pd.DataFrame]
) -> pd.DataFrame:
    if edited_subset is None:
        return current_full_df

    updated_df = current_full_df.copy()
    shared_columns = [col for col in edited_subset.columns if col in updated_df.columns]

    if not shared_columns:
        return updated_df

    updated_df.loc[edited_subset.index, shared_columns] = edited_subset[shared_columns]
    return updated_df


def save_sheet_changes(
    updated_sheet: pd.DataFrame, sheet_name: str, excel_path: Path
) -> Tuple[bool, str]:
    try:
        excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
    except FileNotFoundError:
        return False, f"Excel file not found. Expected: {excel_path.resolve()}"
    except Exception as exc:
        return False, f"Unable to open Excel file: {exc}"

    sheets_data: Dict[str, pd.DataFrame] = {}
    try:
        for name in excel_file.sheet_names:
            if name == sheet_name:
                sheets_data[name] = updated_sheet.copy()
            else:
                sheets_data[name] = excel_file.parse(name)
    finally:
        excel_file.close()

    try:
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            for name, dataframe in sheets_data.items():
                dataframe.to_excel(writer, sheet_name=name, index=False)
    except PermissionError:
        return (
            False,
            "Could not save changes. The Excel file may be open in another application.",
        )
    except Exception as exc:
        return False, f"Failed to save Excel file: {exc}"

    return True, "Alterações salvas com sucesso."


def _rerun_app() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
        return

    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
        return

    raise RuntimeError("Unable to rerun Streamlit app; no rerun method available.")


def render_save_controls(
    sheet_name: str, excel_path: Path, sheet_df: pd.DataFrame
) -> None:
    status = st.session_state.pop("save_status", None)
    if status:
        status_type, message = status
        if status_type == "success":
            st.success(message)
        elif status_type == "error":
            st.error(message)

    primary_label = "Salvar Alterações no Regras_Comissoes.xlsx"
    if st.button(primary_label, type="primary"):
        st.session_state["pending_save_confirmation"] = True

    if st.session_state.get("pending_save_confirmation"):
        st.warning(
            "Esta ação irá sobrescrever a aba selecionada em 'Regras_Comissoes.xlsx'. "
            "Confirme para prosseguir."
        )
        confirm_col, cancel_col = st.columns(2)

        with confirm_col:
            if st.button("Confirmar Salvar", key="confirm_save"):
                success, message = save_sheet_changes(sheet_df, sheet_name, excel_path)
                status_type = "success" if success else "error"
                st.session_state["save_status"] = (status_type, message)
                st.session_state["pending_save_confirmation"] = False
                _rerun_app()

        with cancel_col:
            if st.button("Cancelar", key="cancel_save"):
                st.session_state["pending_save_confirmation"] = False


def add_empty_row(dataframe: pd.DataFrame) -> pd.DataFrame:
    empty_row = {column: pd.NA for column in dataframe.columns}
    return pd.concat(
        [dataframe, pd.DataFrame([empty_row], columns=dataframe.columns)],
        ignore_index=True,
    )


def _clear_save_state() -> None:
    st.session_state.pop("pending_save_confirmation", None)
    st.session_state.pop("save_status", None)


def main() -> None:
    st.title("Commission Rules Viewer")
    st.write(
        "Select an Excel sheet to explore the commission rules, apply filters, "
        "and edit the data before saving your changes."
    )

    excel_file = load_excel_file(EXCEL_PATH)
    if excel_file is None:
        st.stop()

    sheet_names = get_sheet_names(excel_file)
    if not sheet_names:
        st.warning("No sheets found in the Excel file.")
        st.stop()

    selected_sheet = st.selectbox("Select a sheet", sheet_names)

    dataframe = ensure_sheet_data(selected_sheet, EXCEL_PATH)
    if dataframe is None:
        st.stop()

    total_rows = len(dataframe)
    st.subheader(f"Sheet: {selected_sheet}")

    filters = generate_filter_widgets(dataframe)
    filtered_dataframe = apply_filters(dataframe, filters)

    if st.button("Adicionar nova linha"):
        if len(filtered_dataframe) != len(dataframe):
            st.warning(
                "Limpe os filtros antes de adicionar uma nova linha, para que ela fique visível e possa ser editada."
            )
        else:
            dataframe = add_empty_row(dataframe)
            st.session_state["sheet_data"] = dataframe
            _clear_save_state()
            _rerun_app()

    edited_subset, delete_mask = render_editable_table(
        filtered_dataframe, total_rows, selected_sheet
    )

    if edited_subset is not None:
        updated_dataframe = update_dataframe_with_edits(dataframe, edited_subset)
        st.session_state["sheet_data"] = updated_dataframe
        dataframe = updated_dataframe

        if delete_mask is not None:
            delete_candidates = delete_mask[delete_mask].index
            delete_disabled = len(delete_candidates) == 0
            if st.button(
                "Excluir linhas selecionadas",
                disabled=delete_disabled,
                help="Selecione linhas na coluna 'Excluir?' para habilitar.",
            ):
                if delete_disabled:
                    st.warning("Nenhuma linha selecionada para exclusão.")
                else:
                    dataframe = dataframe.drop(index=delete_candidates)
                    st.session_state["sheet_data"] = dataframe
                    _clear_save_state()
                    _rerun_app()

    render_save_controls(selected_sheet, EXCEL_PATH, dataframe)


if __name__ == "__main__":
    main()
