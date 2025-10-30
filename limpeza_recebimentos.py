import pandas as pd
import re
import os
import sys
import unicodedata

# --- CONFIGURAÇÕES ---
# Nome do arquivo bruto gerado pelo ERP
ARQUIVO_BRUTO_RECEBIMENTOS = "fin_conci_adcli_m3.xls"

# Nome do arquivo de saída, limpo e estruturado
ARQUIVO_SAIDA_LIMPO = "Recebimentos_do_Mes.xlsx"
# ---------------------


def _normalize_colname(s):
    if not isinstance(s, str):
        return ""
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s


def extrair_processo(texto_documento):
    """Extrai a primeira sequência de dígitos encontrada no texto."""
    if isinstance(texto_documento, str):
        texto_base = texto_documento.split("/")[0]
        match = re.search(r"\d+", texto_base)
        if match:
            return match.group(0)
    return None


def _to_float(v):
    try:
        if pd.isna(v):
            return None
        # Remover símbolos e ajustar decimal (ex: '1.234,56' -> '1234.56')
        s = str(v)
        # remover espaços invisíveis
        s = s.replace("\xa0", " ").strip()
        # transformar separadores: remover milhares e padronizar decimal
        # primeiro, se houver mais de um ',', assume formato pt-br e remove pontos
        if s.count(",") >= 1 and s.count(".") >= 1 and s.find(".") < s.find(","):
            # exemplo: '1.234,56'
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            s = s.replace(",", ".")
        # remover qualquer caracter que não seja dígito, sinal ou ponto
        s = re.sub(r"[^0-9\-\.]", "", s)
        if s == "" or s == "." or s == "-":
            return None
        return float(s)
    except Exception:
        return None


def limpar_dados_recebimento():
    print(
        f"Iniciando a limpeza do arquivo de recebimentos: {ARQUIVO_BRUTO_RECEBIMENTOS}"
    )

    if not os.path.exists(ARQUIVO_BRUTO_RECEBIMENTOS):
        print(
            f"ERRO: O arquivo de entrada '{ARQUIVO_BRUTO_RECEBIMENTOS}' não foi encontrado."
        )
        sys.exit(1)

    try:
        df_bruto = pd.read_excel(ARQUIVO_BRUTO_RECEBIMENTOS, header=0)
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo Excel: {e}")
        sys.exit(1)

    if df_bruto.empty:
        print("AVISO: arquivo lido, mas sem linhas.")
        df_empty = pd.DataFrame(
            columns=["PROCESSO", "DATA_RECEBIMENTO", "VALOR_RECEBIDO", "ID_CLIENTE"]
        )
        df_empty.to_excel(ARQUIVO_SAIDA_LIMPO, index=False, engine="openpyxl")
        print(f"Arquivo vazio salvo: '{ARQUIVO_SAIDA_LIMPO}'")
        sys.exit(0)

    # Normalizar nomes de colunas para facilitar heurísticas de detecção
    orig_cols = list(df_bruto.columns)
    norm_map = {c: _normalize_colname(str(c)) for c in orig_cols}
    df_bruto.rename(columns=norm_map, inplace=True)

    cols = list(df_bruto.columns)

    # Detectar colunas candidatas
    date_col = None
    amount_col = None
    client_col = None
    process_col = None

    for c in cols:
        if date_col is None and any(k in c for k in ("data", "dt", "receb", "entrada")):
            date_col = c
        if amount_col is None and any(
            k in c for k in ("valor", "vl", "recebido", "aberto", "original")
        ):
            amount_col = c
        if client_col is None and any(
            k in c for k in ("cliente", "id", "cod", "entrada")
        ):
            client_col = c
        if process_col is None and any(
            k in c
            for k in ("filial", "documento", "processo", "contrato", "nota", "doc")
        ):
            process_col = c

    # Refinar seleção das colunas com base no conteúdo real
    try:
        # Priorizar coluna de valor que represente baixa/pagamento/recebimento
        pref_amount = [
            c for c in cols if any(k in c for k in ("baix", "pago", "receb"))
        ]
        for c in pref_amount:
            s = pd.to_numeric(df_bruto[c], errors="coerce")
            if s.notna().sum() > 0 and float(s.fillna(0).abs().sum()) > 0:
                amount_col = c
                break

        # Se a coluna escolhida por preferência parecer data (ex.: interpretada como timestamp), desconsiderar
        if amount_col is not None:
            try:
                s_test = pd.to_datetime(df_bruto[amount_col], errors="coerce")
                if s_test.dropna().shape[0] > 0:
                    # muitas datas em anos plausíveis? então não é valor
                    share = (
                        (s_test.dropna().dt.year >= 2000)
                        & (s_test.dropna().dt.year <= 2100)
                    ).mean()
                    if share > 0.5:
                        amount_col = None
            except Exception:
                pass

        # Se ainda não tem uma coluna de valor adequada, escolher a coluna mais numérica (maior soma absoluta)
        def _numeric_score(col):
            s = pd.to_numeric(df_bruto[col], errors="coerce")
            return float(s.fillna(0).abs().sum())

        def _looks_like_date(col):
            s = pd.to_datetime(df_bruto[col], errors="coerce")
            s = s.dropna()
            if s.empty:
                return False
            share = ((s.dt.year >= 2000) & (s.dt.year <= 2100)).mean()
            return share > 0.5

        if (
            amount_col is None
            or pd.to_numeric(df_bruto[amount_col], errors="coerce").notna().sum() == 0
        ):
            numeric_candidates = [
                c for c in cols if _numeric_score(c) > 0 and not _looks_like_date(c)
            ]

            # Priorizar colunas com palavras-chave de valor (vl, valor, aberto, baixado)
            # ao invés de apenas ordenar por score numérico (que pode pegar colunas de ID/processo)
            def _is_value_keyword(col):
                value_keywords = ["vl_", "valor", "aberto", "baixado", "receb", "pago"]
                return any(kw in col for kw in value_keywords)

            def _priority_key(col):
                # Prioridade: (1) tem palavra-chave de valor, (2) score numérico alto
                has_keyword = _is_value_keyword(col)
                score = _numeric_score(col)
                # Retorna tupla: colunas com keyword vêm primeiro (0 < 1), depois por score
                return (0 if has_keyword else 1, -score)

            numeric_candidates.sort(key=_priority_key)
            if numeric_candidates:
                amount_col = numeric_candidates[0]

        # Validar/ajustar coluna de data: escolher a que mais se comporta como data
        cand_date = [
            c
            for c in cols
            if any(
                k in c
                for k in (
                    "entrada",
                    "baixa",
                    "pag",
                    "data",
                    "dt",
                    "ven",
                    "venc",
                    "original",
                )
            )
        ]

        def _date_score(col):
            s = pd.to_datetime(df_bruto[col], errors="coerce")
            s = s.dropna()
            if s.empty:
                return 0
            # considerar datas plausíveis (anos 2000..2100)
            return int(((s.dt.year >= 2000) & (s.dt.year <= 2100)).sum())

        # prioridade: entrada/baixa/pagamento > vencimento > demais
        def _priority(col):
            name = col
            if any(k in name for k in ("entrada", "baixa", "pag")):
                return 0
            if "ven" in name or "venc" in name:
                return 1
            return 2

        # Caso especial observado: coluna 'vl_original' pode conter a data misturada ao texto
        if "vl_original" in cols:
            import re as _re

            tmp = (
                df_bruto["vl_original"]
                .astype(str)
                .str.extract(
                    r"((?:\d{4}-\d{2}-\d{2})|(?:\d{2}/\d{2}/\d{4}))", expand=False
                )
            )
            if tmp.notna().sum() > 0:
                df_bruto["vl_original"] = tmp
                date_col = "vl_original"

        if cand_date and (date_col is None or date_col not in cand_date):
            scored = [(c, _date_score(c)) for c in cand_date]
            # escolher por maior score; em empate, menor prioridade
            scored.sort(key=lambda t: (-t[1], _priority(t[0])))
            if scored[0][1] > 0:
                date_col = scored[0][0]

        # Preferir coluna de processo que efetivamente contenha números identificadores
        cand_proc = []
        # ordem de preferência: filial -> processo -> contrato/nota -> documento/doc
        for key in ("filial", "processo", "contrato", "nota", "documento", "doc"):
            cand_proc.extend([c for c in cols if key in c])
        for c in cand_proc:
            vals = df_bruto[c].astype(str).fillna("")
            # score por presença de números com 4+ dígitos em algumas linhas
            has_digits = (
                vals.head(50)
                .apply(lambda x: True if re.search(r"\d{4,}", x) else False)
                .sum()
            )
            if has_digits > 0:
                process_col = c
                break
    except Exception:
        pass

    # Melhor fallback: inspecionar conteúdo para detectar possível coluna de processo
    if process_col is None:
        for c in cols:
            sample = df_bruto[c].astype(str).dropna().head(20).tolist()
            for val in sample:
                if re.search(r"\d{4,}", str(val)):
                    process_col = c
                    break
            if process_col:
                break

    print(
        f"Colunas detectadas -> date: {date_col}, amount: {amount_col}, client: {client_col}, process: {process_col}"
    )

    dados_limpos = []
    processo_bloco_atual = None

    for index, row in df_bruto.iterrows():
        # Se houver uma linha textual de total do cliente em qualquer coluna, resetar bloco
        if any(
            isinstance(x, str) and str(x).strip().lower().startswith("total do cliente")
            for x in row.values
        ):
            processo_bloco_atual = None
            continue

        # Extrair valores com base nas colunas detectadas
        try:
            data_val = (
                row[date_col]
                if (date_col is not None and date_col in row.index)
                else None
            )
        except Exception:
            data_val = None

        try:
            valor_val = (
                row[amount_col]
                if (amount_col is not None and amount_col in row.index)
                else None
            )
        except Exception:
            valor_val = None

        try:
            id_cliente_val = (
                row[client_col]
                if (client_col is not None and client_col in row.index)
                else None
            )
        except Exception:
            id_cliente_val = None

        # Normalizar e validar
        valor = _to_float(valor_val)
        # Tentar parsear data
        try:
            if pd.notna(data_val):
                data_receb = pd.to_datetime(data_val, errors="coerce")
            else:
                data_receb = pd.NaT
        except Exception:
            data_receb = pd.NaT

        # Se não existir processo no mesmo registro, manter processo_bloco_atual
        proc_this = None
        if process_col and process_col in row and pd.notna(row[process_col]):
            proc_this = extrair_processo(str(row[process_col]))

        if proc_this:
            processo_bloco_atual = proc_this

        # Validar campos essenciais
        if valor is None or pd.isna(data_receb) or processo_bloco_atual is None:
            continue

        id_cliente_str = None
        try:
            if pd.notna(id_cliente_val):
                id_cliente_str = str(int(float(id_cliente_val))).zfill(6)
        except Exception:
            try:
                id_cliente_str = str(id_cliente_val).strip()
            except Exception:
                id_cliente_str = ""

        dados_limpos.append(
            {
                "PROCESSO": str(processo_bloco_atual),
                "DATA_RECEBIMENTO": data_receb,
                "VALOR_RECEBIDO": float(valor),
                "ID_CLIENTE": id_cliente_str,
            }
        )

    if not dados_limpos:
        print(
            "\nAVISO: Nenhuma linha de recebimento válida foi encontrada no arquivo de entrada."
        )
        df_empty = pd.DataFrame(
            columns=["PROCESSO", "DATA_RECEBIMENTO", "VALOR_RECEBIDO", "ID_CLIENTE"]
        )
        df_empty.to_excel(ARQUIVO_SAIDA_LIMPO, index=False, engine="openpyxl")
        print(f"Arquivo vazio salvo: '{ARQUIVO_SAIDA_LIMPO}'")
        sys.exit(0)

    df_limpo = pd.DataFrame(dados_limpos)

    # Filtrar por mês/ano se passado como argumentos CLI (ordem: mes ano)
    try:
        if len(sys.argv) >= 3:
            arg_mes = int(sys.argv[1])
            arg_ano = int(sys.argv[2])
            before = len(df_limpo)
            df_limpo = df_limpo[
                (df_limpo["DATA_RECEBIMENTO"].dt.month == arg_mes)
                & (df_limpo["DATA_RECEBIMENTO"].dt.year == arg_ano)
            ].copy()
            print(
                f"Filtrado por mês/ano: {arg_mes}/{arg_ano} -> {len(df_limpo)} registros mantidos (antes {before})"
            )
    except Exception as e:
        print(
            f"AVISO: falha ao interpretar args mês/ano: {e}. Gerando arquivo sem filtro."
        )

    try:
        df_limpo.to_excel(ARQUIVO_SAIDA_LIMPO, index=False, engine="openpyxl")
        print(
            f"\nSucesso! Arquivo limpo e estruturado foi salvo como: '{ARQUIVO_SAIDA_LIMPO}'"
        )
        print(f"Total de {len(df_limpo)} registros de pagamento processados.")
        sys.exit(0)
    except Exception as e:
        print(f"Ocorreu um erro ao salvar o arquivo Excel de saída: {e}")
        sys.exit(1)


if __name__ == "__main__":
    limpar_dados_recebimento()
