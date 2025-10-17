import pandas as pd
import os
import re

INPUT_DIR = "rentabilidades"
INPUT_FILE = "rentabilidade_realizada_07_2025.xls"
OUTPUT_FILE = "rentabilidade_07_2025_limpa.xlsx"

# Regex to find product codes like CEE301089-301209, CEE301091A, QED39534, CEE201852
PROD_CODE_RE = re.compile(r"\b[A-Z]{2,4}\d{3,6}[A-Z]?(?:-\d{3,6})?\b")
# Regex to extract numbers with thousands and decimal comma
NUM_RE = re.compile(r"[-+]?\d{1,3}(?:[\.\d{3}])*[,\.]\d+")
# Simpler numeric token regex
NUM_TOKEN_RE = re.compile(r"[-+]?\d[\d\.,]*\d")

IGNORED_PREFIXES = ["grupo", "total grupo", "total", "----"]


def extract_code_from_line_start(line: str) -> str | None:
    """Tenta extrair o código do produto somente a partir do início da linha.
    A estratégia: pegar o token antes do separador ' - ' (se houver) ou o primeiro token
    e validar que seja um código: contém pelo menos um dígito, só caracteres A-Z 0-9 - /,
    e não termina em '-'. Retorna o código em maiúsculas ou None.
    """
    if not line or not isinstance(line, str):
        return None
    # token antes de ' - '
    first = line.split(' - ', 1)[0].strip()
    if not first:
        return None
    first_token = first.split()[0].strip().rstrip(':').upper()
    # normalizar/remover caracteres estranhos
    token = re.sub(r"[^A-Z0-9\-/]", "", first_token)
    # deve conter ao menos um digito e não terminar com '-'
    if not re.search(r"\d", token):
        return None
    # deve conter ao menos uma letra (evita tokens numéricos como '14' que são contagens)
    if not re.search(r"[A-Z]", token):
        return None
    if token.endswith('-') or len(token) < 2:
        return None
    # limites razoáveis de tamanho
    if len(token) > 40:
        return None
    return token


def normalize_number(token: str) -> float | None:
    """Converte token numérico com formato brasileiro para float.
    Ex.: '9.299,89' -> 9299.89 ; '28,55' -> 28.55
    Retorna None se não for possível converter.
    """
    if not token or not isinstance(token, str):
        return None
    s = token.strip()
    # remover espaços
    s = s.replace('\xa0', '')
    # remover pontos que são separadores de milhares
    # mas cuidado com formatos como '1.234.567,89'
    # Estratégia: se houver vírgula, considerar vírgula como decimal separator
    if ',' in s and s.count(',') >= 1:
        s2 = s.replace('.', '')
        s2 = s2.replace(',', '.')
    else:
        # pode ser já com ponto decimal
        s2 = s.replace(',', '.')
        s2 = s2.replace(' ', '')
    try:
        return float(s2)
    except Exception:
        # tentar remover qualquer caractere não numérico restante
        s3 = re.sub(r"[^0-9\.-]", "", s2)
        try:
            return float(s3)
        except Exception:
            return None


def extract_from_lines(lines):
    results = []
    skipped = []
    seen = set()

    n = len(lines)
    i = 0
    while i < n:
        line = lines[i].strip()
        low = line.lower()
        # Ignorar linhas vazias e de grupo/total
        if not line or any(low.startswith(p) for p in IGNORED_PREFIXES):
            i += 1
            continue

        # tentar extrair código no início da linha (mais confiável)
        code = extract_code_from_line_start(line)
        if not code:
            # fallback: procurar em qualquer lugar na linha
            prod_match = PROD_CODE_RE.search(line)
            if prod_match:
                code = prod_match.group(0)
        if code:
            if code in seen:
                i += 1
                continue
            # Não extrair números da mesma linha do código (muitos códigos têm '-12345' que vira número)
            rent = None
            # Caso não encontrado, procurar nas próximas até 4 linhas
            if rent is None:
                look_ahead = 4
                for j in range(1, look_ahead + 1):
                    if i + j >= n:
                        break
                    cand_line = lines[i + j].strip()
                    if not cand_line:
                        continue
                    if any(cand_line.lower().startswith(p) for p in IGNORED_PREFIXES):
                        continue
                    nums2 = NUM_TOKEN_RE.findall(cand_line)
                    if nums2:
                        # escolher último número
                        # procurar do último para o primeiro um token plausível que não venha do código
                        for cand in reversed(nums2):
                            # evitar tokens que sejam apenas os dígitos presentes no código
                            code_digits = re.findall(r"\d+", code)
                            cand_digits = re.sub(r"[^0-9]", "", cand)
                            if any(cand_digits == cd for cd in code_digits):
                                # este token provavelmente é parte do código (ex: '-301209'), pular
                                continue
                            rent = normalize_number(cand)
                            if rent is None:
                                continue
                            if rent > 1000:
                                # valor monetário grande, pular
                                rent = None
                                continue
                            # aceitamos este token
                            break
                    # se encontramos rent dentro deste bloco, interromper o lookahead externo
                    if rent is not None:
                        break
                # end for

            if rent is None:
                skipped.append((i, code, line))
            else:
                results.append((code, rent, i))
                seen.add(code)
            i += 1
            continue

        # se não encontrou código, pular
        i += 1
    return results, skipped


def main():
    input_path = os.path.join(INPUT_DIR, INPUT_FILE)
    if not os.path.exists(input_path):
        print(f"Erro: arquivo de entrada não encontrado: {input_path}")
        return

    # Ler todo o arquivo como strings, sem header
    df = pd.read_excel(input_path, header=None, dtype=str)
    # juntar colunas em uma linha única
    df = df.fillna('').astype(str)
    lines = df.apply(lambda r: ' '.join([c.strip() for c in r if c and c.strip()]), axis=1)

    # Normalizar espaços múltiplos (inclui quebras de linha)
    lines = lines.str.replace(r"\s+", ' ', regex=True)

    # Extrair produtos e rentabilidades
    results, skipped = extract_from_lines(lines.tolist())

    # Montar DataFrame de saída
    df_out = pd.DataFrame([{'CodigoProduto': r[0], 'Rentabilidade': r[1]} for r in results])

    # Salvar em Excel na pasta rentabilidades
    output_path = os.path.join(INPUT_DIR, OUTPUT_FILE)
    df_out.to_excel(output_path, index=False)

    # Resumo
    print(f"Extraídos {len(df_out)} produtos com rentabilidade.")
    if len(df_out) > 0:
        print("Amostra (primeiras 20 linhas):")
        print(df_out.head(20).to_string(index=False))

    # Verificar se os exemplos do usuário estão presentes
    exemplos = ["CEE301089-301209","CEE301090-301209","CEE301091A","CEE201852","QED39534"]
    faltantes = [e for e in exemplos if e not in df_out['CodigoProduto'].values]
    if not faltantes:
        print("Todos os exemplos fornecidos foram encontrados e extraídos.")
    else:
        print(f"Exemplos faltantes: {faltantes}")

    # Se houver entradas puladas, salvar um CSV para auditoria (top 200)
    if skipped:
        skipped_path = os.path.join(INPUT_DIR, 'rentabilidade_skipped_sample.csv')
        pd.DataFrame(skipped[:200], columns=['linha_index','codigo_detectado','texto']).to_csv(skipped_path, index=False)
        print(f"Foram detectadas {len(skipped)} linhas com código sem rentabilidade plausível; uma amostra foi salva em {skipped_path}")


if __name__ == '__main__':
    main()
