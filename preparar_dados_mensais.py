import pandas as pd
import os
import sys
import unicodedata


# --- FUNÇÕES AUXILIARES ---
def _parse_dates_smart(series):
    """
    Parse dates intelligently, detecting ISO format (YYYY-MM-DD) automatically.
    Falls back to day-first or month-first parsing for ambiguous formats.
    """
    raw = series.astype(str).str.strip().replace({"nan": ""})
    raw_clean = raw.str.replace("\u00a0", " ", regex=False).str.replace(
        "T", " ", regex=False
    )

    # Check if most values match ISO format pattern (YYYY-MM-DD)
    iso_pattern = r"^\d{4}-\d{2}-\d{2}"
    iso_count = raw_clean.str.match(iso_pattern, na=False).sum()

    # If >= 50% are ISO format, use yearfirst=True
    if iso_count >= max(1, int(0.5 * len(raw_clean))):
        return pd.to_datetime(raw_clean, yearfirst=True, errors="coerce")
    else:
        # Try both dayfirst and monthfirst, choose the one with fewer NaT
        parsed1 = pd.to_datetime(raw_clean, dayfirst=True, errors="coerce")
        parsed2 = pd.to_datetime(raw_clean, dayfirst=False, errors="coerce")
        return parsed1 if parsed1.isna().sum() <= parsed2.isna().sum() else parsed2


# --- CONFIGURAÇÕES ---
ARQUIVO_ANALISE_COMPLETA = "Analise_Comercial_Completa.csv"
ARQUIVO_SAIDA_FATURADOS = "Faturados.xlsx"

# Default column sets used to create empty files when inputs are missing
DEFAULT_WANTED_FATURADOS = [
    "Código Produto",
    "Descrição Produto",
    "Qtde Atendida",
    "Operação",
    "Processo",
    "Status Processo",
    "Dt Emissão",
    "Valor Realizado",
    "Consultor Interno",
    "Representante-pedido",
    "Gerente Comercial-Pedido",
    "Aplicação Mat./Serv.",
    "Cliente",
    "Nome Cliente",
    "Cidade",
    "UF",
    "Tipo de Mercadoria",
    "Subgrupo",
    "Grupo",
    "Negócio",
]

DEFAULT_CONVERSOES_COLS = [
    "Código Produto",
    "Descrição Produto",
    "Qtde Atendida",
    "Operação",
    "Processo",
    "Status Processo",
    "Data Aceite",
    "Valor Orçado",
    "Valor Realizado",
    "Consultor Interno",
    "Representante-pedido",
    "Gerente Comercial-Pedido",
    "Aplicação Mat./Serv.",
    "Cliente",
    "Nome Cliente",
    "Cidade",
    "UF",
    "Tipo de Mercadoria",
    "Subgrupo",
    "Grupo",
    "Negócio",
]

DEFAULT_YTD_WANTED = [
    "Código Produto",
    "Descrição Produto",
    "Processo",
    "Dt Emissão",
    "Valor Realizado",
    "Consultor Interno",
    "Representante-pedido",
    "Tipo de Mercadoria",
    "Subgrupo",
    "Grupo",
    "Negócio",
    "Fabricante",
]

# Auto-conversão: suportar .xlsx e .csv
# Se existir .xlsx e não existir .csv, converte automaticamente
if os.path.exists("Analise_Comercial_Completa.xlsx") and not os.path.exists(
    ARQUIVO_ANALISE_COMPLETA
):
    try:
        print("Detectado Analise_Comercial_Completa.xlsx - convertendo para .csv...")
        df_temp = pd.read_excel("Analise_Comercial_Completa.xlsx", dtype=str)
        df_temp.to_csv(ARQUIVO_ANALISE_COMPLETA, index=False, encoding="utf-8-sig")
        print(f"[OK] Conversao concluida: {ARQUIVO_ANALISE_COMPLETA} criado.")
    except Exception as e:
        print(f"AVISO: Falha ao converter .xlsx para .csv: {e}")
        print("Tentarei usar o arquivo .xlsx diretamente se possivel.")


def obter_mes_ano():
    """Solicita ao usuário o mês e o ano para apuração."""
    while True:
        try:
            ano = int(input("Digite o ano para apuração (ex: 2025): "))
            if 2000 < ano < 2100:
                break
            else:
                print("Ano inválido. Por favor, insira um ano realista.")
        except ValueError:
            print("Entrada inválida. Por favor, digite um número para o ano.")

    while True:
        try:
            mes = int(input(f"Digite o número do mês para apuração em {ano} (1-12): "))
            if 1 <= mes <= 12:
                break
            else:
                print("Mês inválido. Por favor, insira um número entre 1 e 12.")
        except ValueError:
            print("Entrada inválida. Por favor, digite um número para o mês.")

    print(f"Mês e ano selecionados: {mes}/{ano}")
    return mes, ano


# Normalization helper available module-wide
def _norm(s: str) -> str:
    try:
        s2 = str(s)
        s2 = unicodedata.normalize("NFKD", s2)
        s2 = s2.encode("ASCII", "ignore").decode()
        s2 = s2.strip().lower()
        s2 = " ".join(s2.split())
        return s2
    except Exception:
        return str(s).strip().lower()


def _detect_sep(path, encodings=("utf-8-sig", "utf-8", "latin1")):
    """Detect separator and encoding by reading first line of the file."""
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="replace") as fh:
                first = fh.readline()
                counts = {
                    ",": first.count(","),
                    ";": first.count(";"),
                    "\t": first.count("\t"),
                }
                sep = max(counts, key=lambda k: (counts[k], 1 if k == ";" else 0))
                if counts[sep] == 0:
                    sep = ","
                return sep, enc
        except Exception:
            continue
    return ",", encodings[0]


def gerar_faturados(df, mes, ano):
    """Gera o arquivo Faturados.xlsx filtrando por mês/ano e operações relevantes."""
    arquivo_saida = "Faturados.xlsx"
    print(f"\nIniciando a geração do arquivo '{arquivo_saida}'...")

    # localizar coluna de data (Dt Emissão) e parse robusto
    date_col = None
    for c in df.columns:
        if _norm(c) == _norm("Dt Emissão") or (
            "dt" in _norm(c) and "emiss" in _norm(c)
        ):
            date_col = c
            break
    if date_col is None:
        print(
            "ERRO: não foi possível localizar coluna de data 'Dt Emissão' para faturados. Gerando arquivo vazio com cabeçalho."
        )
        # criar arquivo vazio com cabeçalho esperado
        df_out = pd.DataFrame(columns=DEFAULT_WANTED_FATURADOS)
        try:
            df_out.to_excel(arquivo_saida, index=False)
            print(
                f"Sucesso! O arquivo '{arquivo_saida}' foi gerado com {len(df_out)} linhas (vazio)."
            )
            return True
        except Exception as e:
            print(f"ERRO: falha ao salvar '{arquivo_saida}': {e}")
            return False

    print(f"[DEBUG Faturados] Coluna de data detectada: '{date_col}'")
    print(
        f"[DEBUG Faturados] Amostra Dt Emissão (bruto): {df[date_col].astype(str).head(5).tolist()}"
    )
    df[date_col] = _parse_dates_smart(df[date_col])
    print(
        f"[DEBUG Faturados] Tipo após parse: {df[date_col].dtype}, válidas: {int(df[date_col].notna().sum())} de {len(df)}"
    )
    try:
        amostra = df[date_col].dropna().astype(str).head(5).tolist()
        print(f"[DEBUG Faturados] Amostra Dt Emissão (parse): {amostra}")
    except Exception:
        pass

    filtro = (df[date_col].dt.month == mes) & (df[date_col].dt.year == ano)
    df_filtrado = df[filtro].copy()
    print(
        f"[DEBUG Faturados] Encontradas {len(df_filtrado)} linhas para {mes:02d}/{ano} por Dt Emissão."
    )

    if df_filtrado.empty:
        print(
            "Nenhum dado encontrado para o período selecionado por Dt Emissão. Gerando 'Faturados.xlsx' vazio com cabeçalho."
        )
        df_out = pd.DataFrame(columns=DEFAULT_WANTED_FATURADOS)
        try:
            df_out.to_excel(arquivo_saida, index=False)
            print(
                f"Sucesso! O arquivo '{arquivo_saida}' foi gerado com {len(df_out)} linhas (vazio)."
            )
            return True
        except Exception as e:
            print(f"ERRO: falha ao salvar '{arquivo_saida}': {e}")
            return False

    # aplicar filtro por operações (tolerante)
    operacoes_validas = {
        "FLOC",
        "IMO2",
        "OR19",
        "P205",
        "PSEM",
        "PSER",
        "SERV",
        "PVEN",
        "PVMA",
    }
    op_col = None
    for c in df_filtrado.columns:
        if _norm(c) == "operacao" or _norm(c) == "operação":
            op_col = c
            break
    if op_col is not None:
        print(
            f"[DEBUG Faturados] Coluna 'Operação' detectada: '{op_col}'. Aplicando filtro de operações válidas."
        )
        before_ops = len(df_filtrado)
        df_filtrado["operacao_codigo"] = (
            df_filtrado[op_col]
            .astype(str)
            .str.strip()
            .str.split(" - ", n=1)
            .str[0]
            .str.split()
            .str[0]
            .str.upper()
        )
        try:
            unique_codes = sorted(
                df_filtrado["operacao_codigo"].dropna().unique().tolist()
            )
            print(f"[DEBUG Faturados] Códigos de operação detectados: {unique_codes}")
        except Exception:
            pass
        df_filtrado = df_filtrado[
            df_filtrado["operacao_codigo"].isin(operacoes_validas)
        ].copy()
        if "operacao_codigo" in df_filtrado.columns:
            df_filtrado = df_filtrado.drop(columns=["operacao_codigo"])
        after_ops = len(df_filtrado)
        print(
            f"[DEBUG Faturados] Filtragem por operação: {before_ops} -> {after_ops} linhas."
        )
    else:
        print(
            "AVISO: coluna 'Operação' não encontrada; gerando faturados sem filtro por operação."
        )

    # escolher colunas básicas para o arquivo de faturados (preserve as existentes)
    wanted = [
        "Código Produto",
        "Descrição Produto",
        "Qtde Atendida",
        "Operação",
        "Processo",
        "Status Processo",
        "Dt Emissão",
        "Valor Realizado",
        "Consultor Interno",
        "Representante-pedido",
        "Gerente Comercial-Pedido",
        "Aplicação Mat./Serv.",
        "Cliente",
        "Nome Cliente",
        "Cidade",
        "UF",
        "Tipo de Mercadoria",
        "Subgrupo",
        "Grupo",
        "Negócio",
    ]
    for want in wanted:
        if want not in df_filtrado.columns:
            # tentar encontrar por nome normalizado
            found = None
            for c in df_filtrado.columns:
                if _norm(c) == _norm(want):
                    found = c
                    break
            if found:
                df_filtrado = df_filtrado.rename(columns={found: want})
            else:
                df_filtrado[want] = pd.NA

    df_out = df_filtrado[wanted].copy()

    # Aplicar aliases de colaboradores nas colunas Consultor Interno e Representante-pedido
    try:
        if os.path.exists("Regras_Comissoes.xlsx"):
            import openpyxl

            aliases_df = pd.read_excel("Regras_Comissoes.xlsx", sheet_name="ALIASES")
            alias_map = (
                aliases_df[aliases_df["entidade"] == "colaborador"]
                .set_index("alias")["padrao"]
                .to_dict()
            )

            if "Consultor Interno" in df_out.columns:
                df_out["Consultor Interno"] = (
                    df_out["Consultor Interno"]
                    .astype(str)
                    .replace(alias_map)
                    .str.strip()
                )
            if "Representante-pedido" in df_out.columns:
                df_out["Representante-pedido"] = (
                    df_out["Representante-pedido"]
                    .astype(str)
                    .replace(alias_map)
                    .str.strip()
                )

            print("[DEBUG Faturados] Aliases aplicados com sucesso.")
    except Exception as e:
        print(f"AVISO: Falha ao aplicar aliases: {e}")

    try:
        df_out.to_excel(arquivo_saida, index=False)
        print(
            f"Sucesso! O arquivo '{arquivo_saida}' foi gerado com {len(df_out)} linhas."
        )
        return True
    except Exception as e:
        print(f"ERRO: falha ao salvar '{arquivo_saida}': {e}")
        return False


def gerar_conversoes(df, mes, ano):
    """Gera o arquivo Conversões.xlsx filtrando por 'Data Aceite' (quando existir) e por mês/ano."""
    arquivo_saida = "Conversões.xlsx"
    print(f"\nIniciando a geração do arquivo '{arquivo_saida}'...")

    # localizar coluna 'Data Aceite' ou alternativa
    data_aceite_col = None
    for c in df.columns:
        if _norm(c) == _norm("Data Aceite") or (
            "aceite" in _norm(c) and "data" in _norm(c)
        ):
            data_aceite_col = c
            break
    if data_aceite_col is None:
        # tentar por colunas comuns
        for alt in ["Data Aceite", "Dt Aceite", "Dt Entrada"]:
            for c in df.columns:
                if _norm(c) == _norm(alt):
                    data_aceite_col = c
                    break
            if data_aceite_col:
                break

    if data_aceite_col is None:
        print(
            "AVISO: coluna 'Data Aceite' não encontrada; gerando 'Conversões.xlsx' vazio com cabeçalho."
        )
        # gerar arquivo vazio com colunas base
        arquivo_saida = "Conversões.xlsx"
        base_cols = [
            "Código Produto",
            "Descrição Produto",
            "Qtde Atendida",
            "Operação",
            "Processo",
            "Status Processo",
            "Data Aceite",
            "Valor Orçado",
            "Valor Realizado",
            "Consultor Interno",
            "Representante-pedido",
            "Gerente Comercial-Pedido",
            "Aplicação Mat./Serv.",
            "Cliente",
            "Nome Cliente",
            "Cidade",
            "UF",
            "Tipo de Mercadoria",
            "Subgrupo",
            "Grupo",
            "Negócio",
        ]
        df_final = pd.DataFrame(columns=base_cols)
        try:
            df_final.to_excel(arquivo_saida, index=False)
            print(
                f"Sucesso! O arquivo '{arquivo_saida}' foi gerado com {len(df_final)} linhas (vazio)."
            )
            return True
        except Exception as e:
            print(f"ERRO: falha ao salvar '{arquivo_saida}': {e}")
            return False

    df[data_aceite_col] = _parse_dates_smart(df[data_aceite_col])

    n_invalid = df[data_aceite_col].isna().sum()
    if n_invalid > 0:
        print(
            f"AVISO: {n_invalid} linhas com 'Data Aceite' inválida; essas linhas serão ignoradas."
        )

    filtro = (df[data_aceite_col].dt.month == mes) & (
        df[data_aceite_col].dt.year == ano
    )
    df_filtrado = df[filtro].copy()
    print(
        f"Encontradas {len(df_filtrado)} linhas para o período de {mes}/{ano} (Data Aceite)."
    )

    if df_filtrado.empty:
        print(
            "Nenhum dado convertido encontrado para o período selecionado. Gerando 'Conversões.xlsx' vazio com cabeçalho."
        )
        arquivo_saida = "Conversões.xlsx"
        base_cols = [
            "Código Produto",
            "Descrição Produto",
            "Qtde Atendida",
            "Operação",
            "Processo",
            "Status Processo",
            "Data Aceite",
            "Valor Orçado",
            "Valor Realizado",
            "Consultor Interno",
            "Representante-pedido",
            "Gerente Comercial-Pedido",
            "Aplicação Mat./Serv.",
            "Cliente",
            "Nome Cliente",
            "Cidade",
            "UF",
            "Tipo de Mercadoria",
            "Subgrupo",
            "Grupo",
            "Negócio",
        ]
        df_final = pd.DataFrame(columns=base_cols)
        try:
            df_final.to_excel(arquivo_saida, index=False)
            print(
                f"Sucesso! O arquivo '{arquivo_saida}' foi gerado com {len(df_final)} linhas (vazio)."
            )
            return True
        except Exception as e:
            print(f"ERRO: falha ao salvar '{arquivo_saida}': {e}")
            return False

    # aplicar filtro de operações semelhante ao faturados
    operacoes_validas = {
        "FLOC",
        "IMO2",
        "OR19",
        "P205",
        "PSEM",
        "PSER",
        "SERV",
        "PVEN",
        "PVMA",
    }
    op_col = None
    for c in df_filtrado.columns:
        if _norm(c) == "operacao" or _norm(c) == "operação":
            op_col = c
            break
    if op_col is not None:
        before_ops = len(df_filtrado)
        df_filtrado["operacao_codigo"] = (
            df_filtrado[op_col]
            .astype(str)
            .str.strip()
            .str.split(" - ", n=1)
            .str[0]
            .str.split()
            .str[0]
            .str.upper()
        )
        df_filtrado = df_filtrado[
            df_filtrado["operacao_codigo"].isin(operacoes_validas)
        ].copy()
        if "operacao_codigo" in df_filtrado.columns:
            df_filtrado = df_filtrado.drop(columns=["operacao_codigo"])
        after_ops = len(df_filtrado)
        print(
            f"Filtragem por operação aplicada: {before_ops} -> {after_ops} linhas (apenas operações válidas mantidas)."
        )
    else:
        print("AVISO: coluna 'Operação' não encontrada; pulando filtro por operação.")

    # escolher colunas para conversões (similar ao faturados mas com Data Aceite)
    base_cols = [
        "Código Produto",
        "Descrição Produto",
        "Qtde Atendida",
        "Operação",
        "Processo",
        "Status Processo",
        "Data Aceite",
        "Valor Orçado",
        "Valor Realizado",
        "Consultor Interno",
        "Representante-pedido",
        "Gerente Comercial-Pedido",
        "Aplicação Mat./Serv.",
        "Cliente",
        "Nome Cliente",
        "Cidade",
        "UF",
        "Tipo de Mercadoria",
        "Subgrupo",
        "Grupo",
        "Negócio",
    ]

    # ajustar nomes presentes
    desired = base_cols
    available = []
    for want in desired:
        if want in df_filtrado.columns:
            available.append(want)
            continue
        # try normalized search
        found = None
        for c in df_filtrado.columns:
            if _norm(c) == _norm(want):
                found = c
                break
        if found:
            df_filtrado = df_filtrado.rename(columns={found: want})
            available.append(want)

    if not available:
        print(
            "AVISO: nenhuma das colunas desejadas foi encontrada para montar 'Conversões'."
        )
        return False

    df_final = df_filtrado[available].copy()

    # Aplicar aliases de colaboradores nas colunas Consultor Interno e Representante-pedido
    try:
        if os.path.exists("Regras_Comissoes.xlsx"):
            import openpyxl

            aliases_df = pd.read_excel("Regras_Comissoes.xlsx", sheet_name="ALIASES")
            alias_map = (
                aliases_df[aliases_df["entidade"] == "colaborador"]
                .set_index("alias")["padrao"]
                .to_dict()
            )

            if "Consultor Interno" in df_final.columns:
                df_final["Consultor Interno"] = (
                    df_final["Consultor Interno"]
                    .astype(str)
                    .replace(alias_map)
                    .str.strip()
                )
            if "Representante-pedido" in df_final.columns:
                df_final["Representante-pedido"] = (
                    df_final["Representante-pedido"]
                    .astype(str)
                    .replace(alias_map)
                    .str.strip()
                )

            print("[DEBUG Conversões] Aliases aplicados com sucesso.")
    except Exception as e:
        print(f"AVISO: Falha ao aplicar aliases em Conversões: {e}")

    try:
        df_final.to_excel(arquivo_saida, index=False)
        print(
            f"Sucesso! O arquivo '{arquivo_saida}' foi gerado com {len(df_final)} linhas."
        )
        return True
    except Exception as e:
        print(f"ERRO: falha ao salvar '{arquivo_saida}': {e}")
        return False


def run_preparador(mes: int, ano: int) -> bool:
    """Entry point para execução não-interativa: lê o arquivo mestre, normaliza e chama os geradores.

    Retorna True em sucesso (mesmo que algum gerador emita avisos), False em erro crítico.
    """
    print(f"--- Preparador: gerando arquivos para {mes}/{ano} ---")

    # Auto-conversão: se existir .xlsx e não existir .csv, converte automaticamente
    if not os.path.exists(ARQUIVO_ANALISE_COMPLETA):
        xlsx_path = "Analise_Comercial_Completa.xlsx"
        if os.path.exists(xlsx_path):
            try:
                print(f"Detectado {xlsx_path} - convertendo para .csv...")
                df_temp = pd.read_excel(xlsx_path, dtype=str)
                df_temp.to_csv(
                    ARQUIVO_ANALISE_COMPLETA, index=False, encoding="utf-8-sig"
                )
                print(f"[OK] Conversao concluida: {ARQUIVO_ANALISE_COMPLETA} criado.")
            except Exception as e:
                print(f"AVISO: Falha ao converter .xlsx para .csv: {e}")
                print("Tentarei usar o arquivo .xlsx diretamente se possivel.")
        else:
            print(
                f"\nERRO CRÍTICO: O arquivo '{ARQUIVO_ANALISE_COMPLETA}' não foi encontrado e '{xlsx_path}' também não existe."
            )
            return False

    if not os.path.exists(ARQUIVO_ANALISE_COMPLETA):
        print(
            f"\nERRO CRÍTICO: O arquivo '{ARQUIVO_ANALISE_COMPLETA}' não foi encontrado após tentativa de conversão."
        )
        return False

    print(
        f"\nLendo o arquivo '{ARQUIVO_ANALISE_COMPLETA}'... (Isso pode levar alguns instantes)"
    )
    df_analise = None
    encodings_to_try = ["utf-8-sig", "utf-8", "latin1"]
    last_exc = None

    def _detect_sep(path, encodings=("utf-8-sig", "utf-8", "latin1")):
        for enc in encodings:
            try:
                with open(path, "r", encoding=enc, errors="replace") as fh:
                    first = fh.readline()
                    counts = {
                        ",": first.count(","),
                        ";": first.count(";"),
                        "\t": first.count("\t"),
                    }
                    sep = max(counts, key=lambda k: (counts[k], 1 if k == ";" else 0))
                    if counts[sep] == 0:
                        sep = ","
                    return sep, enc
            except Exception:
                continue
        return ",", encodings[0]

    sep_detected, used_enc_for_sep = _detect_sep(
        ARQUIVO_ANALISE_COMPLETA, encodings_to_try
    )
    for enc in encodings_to_try:
        try:
            df_analise = pd.read_csv(
                ARQUIVO_ANALISE_COMPLETA,
                sep=sep_detected,
                engine="python",
                on_bad_lines="warn",
                dtype=str,
                encoding=enc,
            )
            df_analise.columns = [c.strip() for c in df_analise.columns]
            print(
                f"Arquivo lido com sucesso com encoding={enc} and sep='{sep_detected}'."
            )
            break
        except Exception as e:
            last_exc = e
            print(f"Aviso: falha ao ler com encoding={enc}: {e}")
            df_analise = None

    if df_analise is None:
        print(
            f"\nERRO CRÍTICO: Falha ao ler o arquivo '{ARQUIVO_ANALISE_COMPLETA}' com encodings tentados. Último erro: {last_exc}"
        )
        return False

    # Tentar normalização de colunas e consolidar
    df_analise.columns = [c.strip() for c in df_analise.columns]

    # Consolidar colunas duplicadas por normalização
    def _consolidate_duplicates_local(df_local):
        cols = list(df_local.columns)
        norm_map = {}
        for c in cols:
            key = _norm(c)
            norm_map.setdefault(key, []).append(c)
        for key, group in norm_map.items():
            if len(group) <= 1:
                continue
            first = group[0]
            s = df_local[group].bfill(axis=1).iloc[:, 0]
            df_local.drop(columns=group, inplace=True)
            df_local[first] = s
        return df_local

    df_analise = _consolidate_duplicates_local(df_analise)

    # Garantir colunas esperadas (não estritas; geradores lidarão com faltantes)
    # Chamar geradores
    try:
        gerar_faturados(df_analise, mes, ano)
    except Exception as e:
        print(f"AVISO: falha ao gerar 'Faturados.xlsx': {e}")
    try:
        gerar_conversoes(df_analise, mes, ano)
    except Exception as e:
        print(f"AVISO: falha ao gerar 'Conversões.xlsx': {e}")
    try:
        gerar_faturados_ytd(df_analise, mes, ano)
    except Exception as e:
        print(f"AVISO: falha ao gerar 'Faturados_YTD.xlsx': {e}")
    try:
        gerar_retencao_clientes(df_analise, mes, ano)
    except Exception as e:
        print(f"AVISO: falha ao gerar 'Retencao_Clientes.xlsx': {e}")

    return True


def prepare_dataframes_for_month(mes: int, ano: int):
    """Returna uma tupla de DataFrames (faturados_df, conversoes_df, faturados_ytd_df, retencao_df)
    para o mês/ano solicitado sem gravar arquivos em disco. Usa a mesma lógica interna
    dos geradores, mas retorna DataFrames temporários.
    """
    if not os.path.exists(ARQUIVO_ANALISE_COMPLETA):
        raise FileNotFoundError(ARQUIVO_ANALISE_COMPLETA)

    # Ler arquivo como em run_preparador
    sep_detected, used_enc_for_sep = _detect_sep(
        ARQUIVO_ANALISE_COMPLETA, ["utf-8-sig", "utf-8", "latin1"]
    )
    df_analise = None
    for enc in ["utf-8-sig", "utf-8", "latin1"]:
        try:
            df_analise = pd.read_csv(
                ARQUIVO_ANALISE_COMPLETA,
                sep=sep_detected,
                engine="python",
                on_bad_lines="warn",
                dtype=str,
                encoding=enc,
            )
            df_analise.columns = [c.strip() for c in df_analise.columns]
            break
        except Exception:
            df_analise = None
    if df_analise is None:
        raise RuntimeError("Falha ao ler Analise_Comercial_Completa")

    # Consolidar colunas duplicadas
    def _consolidate_duplicates_local(df_local):
        cols = list(df_local.columns)
        norm_map = {}
        for c in cols:
            key = _norm(c)
            norm_map.setdefault(key, []).append(c)
        for key, group in norm_map.items():
            if len(group) <= 1:
                continue
            first = group[0]
            s = df_local[group].bfill(axis=1).iloc[:, 0]
            df_local.drop(columns=group, inplace=True)
            df_local[first] = s
        return df_local

    df_analise = _consolidate_duplicates_local(df_analise)

    # build DataFrames using existing generators but without writing to disk
    # For Faturados
    try:
        # reuse logic from gerar_faturados but return df
        # locate date col
        date_col = None
        for c in df_analise.columns:
            if _norm(c) == _norm("Dt Emissão") or (
                "dt" in _norm(c) and "emiss" in _norm(c)
            ):
                date_col = c
                break
        faturados_df = pd.DataFrame()
        if date_col is not None:
            df_analise[date_col] = _parse_dates_smart(df_analise[date_col])
            filtro = (df_analise[date_col].dt.month == mes) & (
                df_analise[date_col].dt.year == ano
            )
            faturados_df = df_analise[filtro].copy()
        # attempt to normalize column names similar to gerar_faturados
        wanted = [
            "Código Produto",
            "Descrição Produto",
            "Qtde Atendida",
            "Operação",
            "Processo",
            "Status Processo",
            "Dt Emissão",
            "Valor Realizado",
            "Consultor Interno",
            "Representante-pedido",
            "Gerente Comercial-Pedido",
            "Aplicação Mat./Serv.",
            "Cliente",
            "Nome Cliente",
            "Cidade",
            "UF",
            "Tipo de Mercadoria",
            "Subgrupo",
            "Grupo",
            "Negócio",
        ]
        for want in wanted:
            if want not in faturados_df.columns:
                found = None
                for c in faturados_df.columns:
                    if _norm(c) == _norm(want):
                        found = c
                        break
                if found:
                    faturados_df = faturados_df.rename(columns={found: want})
                else:
                    faturados_df[want] = pd.NA
        faturados_df = (
            faturados_df[wanted].copy()
            if not faturados_df.empty
            else pd.DataFrame(columns=wanted)
        )

        # Aplicar aliases de colaboradores nas colunas Consultor Interno e Representante-pedido
        try:
            if os.path.exists("Regras_Comissoes.xlsx") and not faturados_df.empty:
                import openpyxl

                aliases_df = pd.read_excel(
                    "Regras_Comissoes.xlsx", sheet_name="ALIASES"
                )
                alias_map = (
                    aliases_df[aliases_df["entidade"] == "colaborador"]
                    .set_index("alias")["padrao"]
                    .to_dict()
                )

                if "Consultor Interno" in faturados_df.columns:
                    faturados_df["Consultor Interno"] = (
                        faturados_df["Consultor Interno"]
                        .astype(str)
                        .replace(alias_map)
                        .str.strip()
                    )
                if "Representante-pedido" in faturados_df.columns:
                    faturados_df["Representante-pedido"] = (
                        faturados_df["Representante-pedido"]
                        .astype(str)
                        .replace(alias_map)
                        .str.strip()
                    )
        except Exception:
            pass
    except Exception:
        faturados_df = pd.DataFrame()

    # Conversoes
    try:
        # find a 'Data Aceite' column
        data_aceite_col = None
        for c in df_analise.columns:
            if _norm(c) == _norm("Data Aceite") or (
                "aceite" in _norm(c) and "data" in _norm(c)
            ):
                data_aceite_col = c
                break
        conversoes_df = pd.DataFrame()
        if data_aceite_col is not None:
            df_analise[data_aceite_col] = _parse_dates_smart(
                df_analise[data_aceite_col]
            )
            filtro = (df_analise[data_aceite_col].dt.month == mes) & (
                df_analise[data_aceite_col].dt.year == ano
            )
            conversoes_df = df_analise[filtro].copy()
        base_cols = [
            "Código Produto",
            "Descrição Produto",
            "Qtde Atendida",
            "Operação",
            "Processo",
            "Status Processo",
            "Data Aceite",
            "Valor Orçado",
            "Valor Realizado",
            "Consultor Interno",
            "Representante-pedido",
            "Gerente Comercial-Pedido",
            "Aplicação Mat./Serv.",
            "Cliente",
            "Nome Cliente",
            "Cidade",
            "UF",
            "Tipo de Mercadoria",
            "Subgrupo",
            "Grupo",
            "Negócio",
        ]
        available = []
        for want in base_cols:
            if want in conversoes_df.columns:
                available.append(want)
                continue
            found = None
            for c in conversoes_df.columns:
                if _norm(c) == _norm(want):
                    found = c
                    break
            if found:
                conversoes_df = conversoes_df.rename(columns={found: want})
                available.append(want)
        conversoes_df = (
            conversoes_df[available].copy()
            if available
            else pd.DataFrame(columns=base_cols)
        )

        # Aplicar aliases de colaboradores nas colunas Consultor Interno e Representante-pedido
        try:
            if os.path.exists("Regras_Comissoes.xlsx") and not conversoes_df.empty:
                import openpyxl

                aliases_df = pd.read_excel(
                    "Regras_Comissoes.xlsx", sheet_name="ALIASES"
                )
                alias_map = (
                    aliases_df[aliases_df["entidade"] == "colaborador"]
                    .set_index("alias")["padrao"]
                    .to_dict()
                )

                if "Consultor Interno" in conversoes_df.columns:
                    conversoes_df["Consultor Interno"] = (
                        conversoes_df["Consultor Interno"]
                        .astype(str)
                        .replace(alias_map)
                        .str.strip()
                    )
                if "Representante-pedido" in conversoes_df.columns:
                    conversoes_df["Representante-pedido"] = (
                        conversoes_df["Representante-pedido"]
                        .astype(str)
                        .replace(alias_map)
                        .str.strip()
                    )
        except Exception:
            pass
    except Exception:
        conversoes_df = pd.DataFrame()

    # Faturados_YTD
    try:
        # reuse gerar_faturados_ytd logic to create df
        date_col = None
        for c in df_analise.columns:
            if _norm(c) == _norm("Dt Emissão") or (
                "dt" in _norm(c) and "emiss" in _norm(c)
            ):
                date_col = c
                break
        faturados_ytd_df = pd.DataFrame()
        if date_col is not None:
            df_analise[date_col] = _parse_dates_smart(df_analise[date_col])
            from datetime import datetime
            import calendar

            start = datetime(ano, 1, 1)
            last_day = calendar.monthrange(ano, mes)[1]
            end = datetime(ano, mes, last_day, 23, 59, 59)
            mask_date = (
                (df_analise[date_col].notna())
                & (df_analise[date_col] >= start)
                & (df_analise[date_col] <= end)
            )
            df_ytd = df_analise[mask_date].copy()
            # filter status
            status_col = None
            for c in df_ytd.columns:
                if _norm(c) == _norm("Status Processo"):
                    status_col = c
                    break
            if status_col is not None:
                df_ytd = df_ytd[
                    df_ytd[status_col].astype(str).str.strip().str.upper() == "FATURADO"
                ]
            wanted = [
                "Código Produto",
                "Descrição Produto",
                "Processo",
                "Dt Emissão",
                "Valor Realizado",
                "Consultor Interno",
                "Representante-pedido",
                "Tipo de Mercadoria",
                "Subgrupo",
                "Grupo",
                "Negócio",
                "Fabricante",
            ]
            for want in wanted:
                if want not in df_ytd.columns:
                    found = None
                    for c in df_ytd.columns:
                        if _norm(c) == _norm(want):
                            found = c
                            break
                    if found:
                        df_ytd = df_ytd.rename(columns={found: want})
                    else:
                        df_ytd[want] = pd.NA
            faturados_ytd_df = df_ytd[wanted].copy()
        else:
            faturados_ytd_df = pd.DataFrame()
    except Exception:
        faturados_ytd_df = pd.DataFrame()

    # Retencao_Clientes - calcular usando a mesma lógica de gerar_retencao_clientes
    try:
        retencao_df = _calcular_retencao_para_mes(df_analise, mes, ano)
    except Exception:
        retencao_df = pd.DataFrame(
            columns=["linha", "clientes_mes_anterior", "clientes_mes_atual"]
        )

    return faturados_df, conversoes_df, faturados_ytd_df, retencao_df


def gerar_faturados_ytd(df, mes, ano):
    """Gera Faturados_YTD.xlsx usando os filtros SQL fornecidos pelo usuário e selecionando somente colunas necessárias."""
    arquivo_saida = "Faturados_YTD.xlsx"
    print(
        f"\nIniciando a geração do arquivo '{arquivo_saida}' (YTD com filtros SQL)..."
    )

    # Determine date column (Dt Emissão)
    date_col = None
    for c in df.columns:
        if _norm(c) == _norm("Dt Emissão") or (
            "dt" in _norm(c) and "emiss" in _norm(c)
        ):
            date_col = c
            break
    if date_col is None:
        print(
            "ERRO: não foi possível encontrar coluna 'Dt Emissão' para gerar Faturados_YTD. Gerando arquivo vazio com cabeçalho."
        )
        df_final = pd.DataFrame(columns=DEFAULT_YTD_WANTED)
        try:
            df_final.to_excel(arquivo_saida, index=False)
            print(
                f"Sucesso! O arquivo '{arquivo_saida}' foi gerado com {len(df_final)} linhas (vazio)."
            )
            return True
        except Exception as e:
            print(f"ERRO: falha ao salvar '{arquivo_saida}': {e}")
            return False

    # Parse dates robustly
    df[date_col] = _parse_dates_smart(df[date_col])

    # Compute YTD window: from Jan 1 of year to last day of selected month/year
    from datetime import datetime
    import calendar

    start = datetime(ano, 1, 1)
    last_day = calendar.monthrange(ano, mes)[1]
    end = datetime(ano, mes, last_day, 23, 59, 59)

    mask_date = (df[date_col].notna()) & (df[date_col] >= start) & (df[date_col] <= end)
    df_ytd = df[mask_date].copy()

    # Filter Status Processo == 'FATURADO'
    status_col = None
    for c in df_ytd.columns:
        if _norm(c) == _norm("Status Processo"):
            status_col = c
            break
    if status_col is None:
        print(
            "AVISO: coluna 'Status Processo' não encontrada; nenhum filtro de status será aplicado."
        )
    else:
        df_ytd = df_ytd[
            df_ytd[status_col].astype(str).str.strip().str.upper() == "FATURADO"
        ]

    # Filter operations: allowed full phrases from SQL (also allow fallback by short code)
    allowed_full = set(
        [
            _norm("IMO2 - VENDA IMOBILIZADO"),
            _norm("OR19 - VENDA A ORDEM POR CONTA DE TERCEIRO"),
            _norm("P205 - SIMPLES FATURAMENTO"),
            _norm("PVEN - PEDIDO DE VENDA"),
            _norm("PVMA - PEDIDO DE VENDA MANUTENÇÃO"),
        ]
    )
    allowed_codes = {"IMO2", "OR19", "P205", "PVEN", "PVMA"}
    # find operation column
    op_col = None
    for c in df_ytd.columns:
        if _norm(c) == "operacao" or _norm(c) == "operação":
            op_col = c
            break
    if op_col is not None:

        def op_allowed(val):
            s = str(val)
            n = _norm(s)
            # exact normalized phrase match
            if n in allowed_full:
                return True
            # check prefix code
            code = (
                s.strip().split(" - ")[0].split()[0].upper() if s.strip() != "" else ""
            )
            if code in allowed_codes:
                return True
            # last resort: check if any allowed code appears in the normalized string
            for ac in allowed_codes:
                if ac.lower() in n:
                    return True
            return False

        mask_ops = df_ytd[op_col].apply(op_allowed)
        df_ytd = df_ytd[mask_ops].copy()
    else:
        print("AVISO: coluna 'Operação' não encontrada; pulando filtro por operação.")

    # Only keep the exact columns specified by the SQL in the requested order
    wanted = [
        "Código Produto",
        "Descrição Produto",
        "Processo",
        "Dt Emissão",
        "Valor Realizado",
        "Consultor Interno",
        "Representante-pedido",
        "Tipo de Mercadoria",
        "Subgrupo",
        "Grupo",
        "Negócio",
        "Fabricante",
    ]

    # Ensure columns exist (try to locate and rename if needed)
    for want in wanted:
        if want not in df_ytd.columns:
            # try to find a column with matching normalized name
            found = None
            for c in df_ytd.columns:
                if _norm(c) == _norm(want):
                    found = c
                    break
            if found:
                df_ytd = df_ytd.rename(columns={found: want})
            else:
                df_ytd[want] = pd.NA

    df_final = df_ytd[wanted].copy()
    try:
        # garantir que um arquivo seja sempre gerado mesmo se df_final estiver vazio
        df_final.to_excel(arquivo_saida, index=False)
        print(
            f"Sucesso! O arquivo '{arquivo_saida}' foi gerado com {len(df_final)} linhas."
        )
        return True
    except Exception as e:
        print(f"ERRO: falha ao salvar '{arquivo_saida}': {e}")
        return False


def _calcular_retencao_para_mes(df, mes, ano):
    """Calcula dados de retenção de clientes por linha (negócio) para um mês específico.

    Retorna um DataFrame com colunas: linha, clientes_mes_anterior, clientes_mes_atual
    Usa a mesma lógica de gerar_retencao_clientes mas sem salvar em arquivo.
    """
    from datetime import datetime
    import calendar

    # operations allowed
    allowed_ops = set(
        [
            _norm("PSEM - PEDIDO DE VENDA/REV. MANUT. E SERVIÇO"),
            _norm("PSER - PEDIDO SERVIÇO"),
            _norm("PVMA - PEDIDO DE VENDA MANUTENÇÃO"),
            _norm("FLOC - FATURA DE LOCAÇÃO EQUIPAMENTOS"),
            _norm("IMO2 - VENDA IMOBILIZADO"),
            _norm("OR19 - VENDA A ORDEM POR CONTA DE TERCEIRO"),
            _norm("P205 - SIMPLES FATURAMENTO"),
            _norm("PVEN - PEDIDO DE VENDA"),
        ]
    )

    # find date column
    date_col = None
    for c in df.columns:
        if _norm(c) == _norm("Dt Emissão") or (
            "dt" in _norm(c) and "emiss" in _norm(c)
        ):
            date_col = c
            break
    if date_col is None:
        return pd.DataFrame(
            columns=["linha", "clientes_mes_anterior", "clientes_mes_atual"]
        )

    # Parse dates
    df = df.copy()
    df[date_col] = _parse_dates_smart(df[date_col])

    # Find columns
    op_col = None
    status_col = None
    negocio_col = None
    cliente_col = None
    for c in df.columns:
        nc = _norm(c)
        if nc == "operacao":
            op_col = c
        if nc == _norm("Status Processo"):
            status_col = c
        if nc == _norm("Negócio") or nc == "negocio":
            negocio_col = c
        if nc == _norm("Cliente"):
            cliente_col = c

    if negocio_col is None or cliente_col is None:
        return pd.DataFrame(
            columns=["linha", "clientes_mes_anterior", "clientes_mes_atual"]
        )

    # Compute windows
    if mes == 1:
        prev_month = 12
        prev_year = ano - 1
    else:
        prev_month = mes - 1
        prev_year = ano

    def window_end(year, month):
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day, 23, 59, 59)

    def window_start_for_end(year, month):
        ym_end_index = year * 12 + (month - 1)
        ym_start_index = ym_end_index - 23
        s_year = ym_start_index // 12
        s_month = (ym_start_index % 12) + 1
        return datetime(s_year, s_month, 1)

    end_prev = window_end(prev_year, prev_month)
    start_prev = window_start_for_end(prev_year, prev_month)
    end_curr = window_end(ano, mes)
    start_curr = window_start_for_end(ano, mes)

    cutoff = start_prev
    df_base = df[df[date_col].notna() & (df[date_col] >= cutoff)].copy()

    # Apply filters
    if status_col:
        df_base = df_base[
            df_base[status_col].astype(str).str.strip().str.upper() == "FATURADO"
        ]

    if op_col:
        df_base["_op_norm"] = df_base[op_col].astype(str).apply(_norm)
        df_base = df_base[
            df_base["_op_norm"].apply(
                lambda x: any(x in a or a.startswith(x) for a in allowed_ops if x)
            )
        ].copy()
        df_base.drop(columns=["_op_norm"], inplace=True)

    # Compute distinct clients per negocio
    mask_prev = (df_base[date_col] >= start_prev) & (df_base[date_col] <= end_prev)
    mask_curr = (df_base[date_col] >= start_curr) & (df_base[date_col] <= end_curr)

    prev = df_base[mask_prev].groupby(negocio_col)[cliente_col].nunique()
    curr = df_base[mask_curr].groupby(negocio_col)[cliente_col].nunique()

    negocios = sorted(set(prev.index.tolist()) | set(curr.index.tolist()))
    rows = []
    for n in negocios:
        rows.append(
            {
                "linha": n,
                "clientes_mes_anterior": int(prev.get(n, 0)),
                "clientes_mes_atual": int(curr.get(n, 0)),
            }
        )

    if rows:
        return pd.DataFrame(rows).sort_values("linha")
    else:
        return pd.DataFrame(
            columns=["linha", "clientes_mes_anterior", "clientes_mes_atual"]
        )


def gerar_retencao_clientes(df, mes, ano):
    """Gera Retencao_Clientes.xlsx usando a lógica ajustada do SQL.

    Usa o mês/ano fornecido pelo usuário e o mês anterior a ele para construir
    duas janelas de 24 meses:
      - janela anterior: [mês_anterior - 24 meses + 1 dia .. mês_anterior end]
      - janela atual: [mês_selecionado - 24 meses + 1 dia .. mês_selecionado end]

    Conta DISTINCT Cliente por 'Negócio' em cada janela, aplicando filtros de
    Status Processo = 'FATURADO' e Operação está na lista autorizada.
    """
    arquivo_saida = "Retencao_Clientes.xlsx"
    print(f"\nIniciando a geração do arquivo '{arquivo_saida}' (retenção por linha)...")

    # operations allowed (use full phrases as in SQL)
    allowed_ops = set(
        [
            _norm("PSEM - PEDIDO DE VENDA/REV. MANUT. E SERVIÇO"),
            _norm("PSER - PEDIDO SERVIÇO"),
            _norm("PVMA - PEDIDO DE VENDA MANUTENÇÃO"),
            _norm("FLOC - FATURA DE LOCAÇÃO EQUIPAMENTOS"),
            _norm("IMO2 - VENDA IMOBILIZADO"),
            _norm("OR19 - VENDA A ORDEM POR CONTA DE TERCEIRO"),
            _norm("P205 - SIMPLES FATURAMENTO"),
            _norm("PVEN - PEDIDO DE VENDA"),
        ]
    )

    # find date column and ensure parsed (Dt Emissão)
    date_col = None
    for c in df.columns:
        if _norm(c) == _norm("Dt Emissão") or (
            "dt" in _norm(c) and "emiss" in _norm(c)
        ):
            date_col = c
            break
    if date_col is None:
        print("ERRO: coluna 'Dt Emissão' não encontrada para retenção.")
        return False
    df[date_col] = _parse_dates_smart(df[date_col])

    # find operation column and status column and negocio and cliente
    op_col = None
    status_col = None
    negocio_col = None
    cliente_col = None
    for c in df.columns:
        nc = _norm(c)
        if nc == "operacao" or nc == "operacao":
            op_col = c
        if nc == _norm("Status Processo"):
            status_col = c
        if nc == _norm("Negócio") or nc == "negocio":
            negocio_col = c
        if nc == _norm("Cliente"):
            cliente_col = c

    if negocio_col is None or cliente_col is None:
        print(
            "ERRO: colunas necessárias 'Negócio' ou 'Cliente' não encontradas. Gerando arquivo vazio com cabeçalho."
        )
        arquivo_saida = "Retencao_Clientes.xlsx"
        df_out = pd.DataFrame(
            columns=["linha", "clientes_mes_anterior", "clientes_mes_atual"]
        )
        try:
            df_out.to_excel(arquivo_saida, index=False)
            print(
                f"Sucesso! O arquivo '{arquivo_saida}' foi gerado com {len(df_out)} linhas (vazio)."
            )
            return True
        except Exception as e:
            print(f"ERRO: falha ao salvar '{arquivo_saida}': {e}")
            return False

    # Build the two windows based on user-selected month/year and previous month
    from datetime import datetime
    import calendar

    # compute month_prev (month and year)
    if mes == 1:
        prev_month = 12
        prev_year = ano - 1
    else:
        prev_month = mes - 1
        prev_year = ano

    # windows: for each window we want the 24-month period ending at end of target month
    def window_end(year, month):
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day, 23, 59, 59)

    def window_start_for_end(year, month):
        # start is 24 months before the month (inclusive first day)
        start_year = year - 2 if month >= 1 else year - 2
        start_month = month
        # for a 24-month trailing window ending at (year,month), the start is month+1 two years before?
        # Simpler: compute year-month index
        ym_end_index = year * 12 + (month - 1)
        ym_start_index = ym_end_index - 23  # inclusive of 24 months
        s_year = ym_start_index // 12
        s_month = (ym_start_index % 12) + 1
        return datetime(s_year, s_month, 1)

    end_prev = window_end(prev_year, prev_month)
    start_prev = window_start_for_end(prev_year, prev_month)

    end_curr = window_end(ano, mes)
    start_curr = window_start_for_end(ano, mes)

    print(f"Janela anterior: {start_prev.date()} -> {end_prev.date()}")
    print(f"Janela atual:     {start_curr.date()} -> {end_curr.date()}")

    # Apply base filters: only rows with Dt Emissão within the last 25 months (optimization in SQL)
    cutoff = start_prev  # since start_prev is 24 months before prev_end inclusive; SQL used 25 months but we follow the windows logic
    df_base = df[df[date_col].notna() & (df[date_col] >= cutoff)].copy()

    # Apply Status Processo == 'FATURADO' and operation in allowed_ops
    if status_col:
        df_base = df_base[
            df_base[status_col].astype(str).str.strip().str.upper() == "FATURADO"
        ]
    else:
        print(
            "AVISO: Status Processo não encontrado; assumindo todas as linhas possíveis."
        )

    if op_col:
        # normalize op text and check membership
        # Valores no arquivo podem ser siglas curtas (ex: "PVEN") enquanto allowed_ops contém
        # descrições completas (ex: "pven - pedido de venda"). Verificar se o valor está contido
        # em alguma operação permitida OU se alguma operação permitida começa com o valor
        df_base["_op_norm"] = df_base[op_col].astype(str).apply(_norm)
        df_base = df_base[
            df_base["_op_norm"].apply(
                lambda x: any(x in a or a.startswith(x) for a in allowed_ops if x)
            )
        ].copy()
        df_base.drop(columns=["_op_norm"], inplace=True)
    else:
        print("AVISO: coluna Operação não encontrada; pulando filtro por operação.")

    # For each negocio, compute distinct clients in previous and current windows
    # prepare masks
    mask_prev = (df_base[date_col] >= start_prev) & (df_base[date_col] <= end_prev)
    mask_curr = (df_base[date_col] >= start_curr) & (df_base[date_col] <= end_curr)

    prev = df_base[mask_prev].groupby(negocio_col)[cliente_col].nunique()
    curr = df_base[mask_curr].groupby(negocio_col)[cliente_col].nunique()

    # combine into DataFrame
    negocios = sorted(set(prev.index.tolist()) | set(curr.index.tolist()))
    rows = []
    for n in negocios:
        rows.append(
            {
                "linha": n,
                "clientes_mes_anterior": int(prev.get(n, 0)),
                "clientes_mes_atual": int(curr.get(n, 0)),
            }
        )

    # Criar DataFrame garantindo que sempre tenha as colunas corretas
    if rows:
        df_out = pd.DataFrame(rows).sort_values("linha")
    else:
        # Se não houver dados, criar DataFrame vazio com colunas corretas
        df_out = pd.DataFrame(
            columns=["linha", "clientes_mes_anterior", "clientes_mes_atual"]
        )

    try:
        # garantir que sempre geramos o arquivo mesmo que vazio
        df_out.to_excel(arquivo_saida, index=False)
        print(
            f"Sucesso! O arquivo '{arquivo_saida}' foi gerado com {len(df_out)} linhas."
        )
        return True
    except Exception as e:
        print(f"ERRO: falha ao salvar '{arquivo_saida}': {e}")
        return False


def main():
    """Função principal do script."""
    print("--- Preparador de Dados Mensais para Cálculo de Comissões ---")

    # 1. Obter mês e ano do usuário
    mes, ano = obter_mes_ano()

    # 2. Ler o arquivo de análise completa
    if not os.path.exists(ARQUIVO_ANALISE_COMPLETA):
        print(
            f"\nERRO CRÍTICO: O arquivo '{ARQUIVO_ANALISE_COMPLETA}' não foi encontrado."
        )
        sys.exit(1)  # Termina o script se o arquivo principal não existe

    print(
        f"\nLendo o arquivo '{ARQUIVO_ANALISE_COMPLETA}'... (Isso pode levar alguns instantes)"
    )
    df_analise = None
    encodings_to_try = ["utf-8-sig", "utf-8", "latin1"]
    last_exc = None

    # detect delimiter by sniffing the first line
    def _detect_sep(path, encodings=("utf-8-sig", "utf-8", "latin1")):
        for enc in encodings:
            try:
                with open(path, "r", encoding=enc, errors="replace") as fh:
                    first = fh.readline()
                    # count common delimiters
                    counts = {
                        ",": first.count(","),
                        ";": first.count(";"),
                        "\t": first.count("\t"),
                    }
                    # pick the delimiter with highest count (prefer ; over , if equal and ; present)
                    sep = max(counts, key=lambda k: (counts[k], 1 if k == ";" else 0))
                    if counts[sep] == 0:
                        # fallback to comma
                        sep = ","
                    return sep, enc
            except Exception:
                continue
        return ",", encodings[0]

    sep_detected, used_enc_for_sep = _detect_sep(
        ARQUIVO_ANALISE_COMPLETA, encodings_to_try
    )
    for enc in encodings_to_try:
        try:
            df_analise = pd.read_csv(
                ARQUIVO_ANALISE_COMPLETA,
                sep=sep_detected,
                engine="python",
                on_bad_lines="warn",
                dtype=str,
                encoding=enc,
            )
            # strip column names
            df_analise.columns = [c.strip() for c in df_analise.columns]
            print(
                f"Arquivo lido com sucesso com encoding={enc} and sep='{sep_detected}'."
            )
            break
        except Exception as e:
            last_exc = e
            print(f"Aviso: falha ao ler com encoding={enc}: {e}")
            df_analise = None

    if df_analise is None:
        print(
            f"\nERRO CRÍTICO: Falha ao ler o arquivo '{ARQUIVO_ANALISE_COMPLETA}' com encodings tentados. Último erro: {last_exc}"
        )
        sys.exit(1)

    # Normalizar/renomear colunas para os nomes canônicos esperados pelo gerador
    import unicodedata

    def _norm(s: str) -> str:
        try:
            s2 = str(s)
            s2 = unicodedata.normalize("NFKD", s2)
            s2 = s2.encode("ASCII", "ignore").decode()
            s2 = s2.strip().lower()
            s2 = " ".join(s2.split())
            return s2
        except Exception:
            return str(s).strip().lower()

    canonical_cols = [
        "Código Produto",
        "Descrição Produto",
        "Qtde Atendida",
        "Operação",
        "Processo",
        "Status Processo",
        "Dt Emissão",
        "Valor Realizado",
        "Consultor Interno",
        "Representante-pedido",
        "Gerente Comercial-Pedido",
        "Aplicação Mat./Serv.",
        "Cliente",
        "Nome Cliente",
        "Cidade",
        "UF",
        "Tipo de Mercadoria",
        "Subgrupo",
        "Grupo",
        "Negócio",
    ]

    # construir mapeamento: procurar correspondência por tokens (mais tolerante)
    mapping = {}
    existing = list(df_analise.columns)
    norm_existing = {col: _norm(col) for col in existing}
    norm_canon = {can: _norm(can) for can in canonical_cols}

    # We'll map each canonical name to the best existing column (one-to-one)
    used_existing = set()
    for can, nc in norm_canon.items():
        tokens = [t for t in nc.split() if len(t) > 2]
        best_col = None
        best_score = -1
        for col, ne in norm_existing.items():
            if col in used_existing:
                continue
            score = 0
            # exact match highest
            if ne == nc:
                score = 100
            # all tokens present
            elif all(tok in ne for tok in tokens):
                score = 50 + sum(ne.count(tok) for tok in tokens)
            else:
                # partial token matches
                score = sum(5 for tok in tokens if tok in ne)

            # prefer shorter distance (less extra words)
            if score > best_score:
                best_score = score
                best_col = col

        if best_col and best_score > 0:
            mapping[best_col] = can
            used_existing.add(best_col)

    # aplicar mapeamento (um-para-um)
    if mapping:
        df_analise = df_analise.rename(columns=mapping)
    df_analise.columns = [c.strip() for c in df_analise.columns]

    # Consolidar colunas que tornaram-se duplicadas após rename (ex: Nome Cliente, Nome Cliente.1...)
    def _consolidate_duplicates(df):
        cols = list(df.columns)
        norm_map = {}
        for c in cols:
            key = _norm(c)
            norm_map.setdefault(key, []).append(c)

        for key, group in norm_map.items():
            if len(group) <= 1:
                continue
            # coalescer valores: prefer left-most non-null
            first = group[0]
            # create a Series by bfill across the group
            s = df[group].bfill(axis=1).iloc[:, 0]
            df.drop(columns=group, inplace=True)
            df[first] = s
        return df

    df_analise = _consolidate_duplicates(df_analise)

    # Garantir que todas as colunas canônicas estão presentes (criar em branco quando ausentes)
    for can in canonical_cols:
        if can not in df_analise.columns:
            df_analise[can] = pd.NA

    # --- DETECÇÃO ROBUSTA DA COLUNA DE DATA ---
    # preferir colunas que contenham 'dt' e 'emiss'/'emissao', mas aceitar alternativas
    date_candidates = [c for c in df_analise.columns]
    date_col = None
    for c in date_candidates:
        nc = _norm(c)
        if (
            ("dt" in nc and ("emiss" in nc or "emissao" in nc))
            or "data" in nc
            and "emiss" in nc
        ):
            date_col = c
            break

    # se não encontrou, tentar algumas outras colunas candidatas comuns
    if date_col is None:
        for alt in [
            "Data Aceite",
            "Dt Entrada",
            "Dt Encerramento",
            "Dt Emissao",
            "Dt Emissao",
        ]:
            for c in df_analise.columns:
                if _norm(c) == _norm(alt):
                    date_col = c
                    break
            if date_col:
                break

    if date_col is None:
        print(
            f"ERRO: Não foi possível localizar coluna de data 'Dt Emissão' no arquivo '{ARQUIVO_ANALISE_COMPLETA}'. Colunas encontradas: {list(df_analise.columns)}"
        )
        sys.exit(1)

    # Tentar parse em várias heurísticas e escolher a coluna/parse com menos nulos
    df_analise[date_col] = _parse_dates_smart(df_analise[date_col])
    n_invalid = df_analise[date_col].isna().sum()
    if n_invalid > 0:
        print(
            f"AVISO: {n_invalid} linhas com data inválida na coluna detectada '{date_col}' após tentativas de parse."
        )

    # 3. Gerar o arquivo de faturados
    gerar_faturados(df_analise, mes, ano)
    # 4. Gerar o arquivo de conversões (filtrando por Data Aceite)
    try:
        gerar_conversoes(df_analise, mes, ano)
    except Exception as e:
        print(f"AVISO: falha ao gerar 'Conversões.xlsx': {e}")
    # 5. Gerar o Faturados_YTD (do começo do ano até o mês/ano informado)
    try:
        gerar_faturados_ytd(df_analise, mes, ano)
    except Exception as e:
        print(f"AVISO: falha ao gerar 'Faturados_YTD.xlsx': {e}")
    # 6. Gerar Retencao_Clientes.xlsx
    try:
        gerar_retencao_clientes(df_analise, mes, ano)
    except Exception as e:
        print(f"AVISO: falha ao gerar 'Retencao_Clientes.xlsx': {e}")


if __name__ == "__main__":
    main()
