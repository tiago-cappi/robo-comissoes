import os
import sys
import glob
import time
import traceback
import logging
from pathlib import Path


def setup_logging(root: Path) -> logging.Logger:
    log = logging.getLogger("run_commissions_test")
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = logging.FileHandler(root / "test_run.log", encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.INFO)
    log.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(logging.INFO)
    log.addHandler(sh)

    return log


def ensure_sys_path(root: Path):
    root_str = str(root.resolve())
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def check_base_files(root: Path, log: logging.Logger) -> bool:
    required = [
        root / "Analise_Comercial_Completa.xlsx",
        root / "fin_adcli_pg_m3.xls",
        root / "fin_conci_adcli_m3.xls",
        root / "Análise Financeira.xlsx",
    ]
    ok = True
    for f in required:
        if not f.exists():
            log.error(f"Arquivo base ausente: {f}")
            ok = False
        else:
            log.info(f"OK arquivo base: {f.name} ({f.stat().st_size} bytes)")
    return ok


def run_preparador(mes: int, ano: int, log: logging.Logger):
    log.info(f"[1/4] Executando preparador de dados para {mes}/{ano}...")
    import preparar_dados_mensais

    started = time.time()
    ok = preparar_dados_mensais.run_preparador(mes, ano)
    elapsed = time.time() - started
    if not ok:
        raise RuntimeError("preparar_dados_mensais.run_preparador retornou False")
    log.info(f"Preparador concluído em {elapsed:.1f}s")


def detect_cross_selling(calc, log: logging.Logger):
    log.info("[2/4] Carregando e pré-processando dados...")
    calc._carregar_dados()
    calc._preprocessar_dados()
    log.info("[3/4] Rodando detecção de cross-selling...")
    calc._detectar_cross_selling()
    casos = getattr(calc, "casos_cross_selling_detectados", []) or []
    log.info(f"Casos de cross-selling detectados: {len(casos)}")
    for i, c in enumerate(casos[:10]):
        log.info(f"  {i+1:02d}) processo={c.get('processo')} consultor={c.get('consultor')} linha={c.get('linha')} taxa={c.get('taxa')}")
    return casos


def run_execucao(calc, log: logging.Logger, decisoes=None):
    log.info("[4/4] Executando cálculo de comissões...")
    started = time.time()
    calc.executar(decisoes_cross_selling=decisoes or [])
    elapsed = time.time() - started
    log.info(f"Cálculo concluído em {elapsed:.1f}s")


def last_output(root: Path) -> Path | None:
    files = sorted(root.glob("Comissoes_Calculadas_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Rodar cálculo de comissões com logs completos")
    parser.add_argument("--mes", type=int, default=None)
    parser.add_argument("--ano", type=int, default=None)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    log = setup_logging(root)
    ensure_sys_path(root)

    # Mes/Ano padrão: mês atual
    from datetime import datetime
    today = datetime.today()
    mes = args.mes or today.month
    ano = args.ano or today.year
    log.info(f"Root: {root}")
    log.info(f"Executando para {mes}/{ano}")

    try:
        if not check_base_files(root, log):
            raise RuntimeError("Arquivos base ausentes. Faça upload/copie os 4 arquivos necessários.")

        run_preparador(mes, ano, log)

        # Ajustar caminhos de arquivos conforme CLI main do módulo
        # IMPORTANTE: definir antes de importar CalculoComissao para que _carregar_dados use esses valores
        import calculo_comissoes as cc
        cc.ARQUIVO_FATURADOS = "Faturados.xlsx"
        cc.ARQUIVO_CONVERSOES = "Conversões.xlsx"
        cc.ARQUIVO_FATURADOS_YTD = "Faturados_YTD.xlsx"
        mm = str(mes).zfill(2)
        import glob as _glob
        encontrados = _glob.glob(str(root / f"rentabilidades/*{mm}*{ano}*agrupada*.xlsx"))
        if encontrados:
            cc.ARQUIVO_RENTABILIDADE = encontrados[0]
            log.info(f"Usando arquivo de rentabilidade: {cc.ARQUIVO_RENTABILIDADE}")
        else:
            padrao = root / f"rentabilidades/rentabilidade_{mm}_{ano}_agrupada.xlsx"
            if padrao.exists():
                cc.ARQUIVO_RENTABILIDADE = str(padrao)
                log.info(f"Usando arquivo de rentabilidade: {cc.ARQUIVO_RENTABILIDADE}")
            else:
                # Criar DataFrame vazio se não houver arquivo de rentabilidade
                log.warning(
                    f"Arquivo de rentabilidade não encontrado para {mm}/{ano}. Usando DataFrame vazio."
                )
                cc.ARQUIVO_RENTABILIDADE = None

        from calculo_comissoes import CalculoComissao
        calc = CalculoComissao()
        casos = detect_cross_selling(calc, log)

        # Preparar decisões: usar Opção A (padrão) para todos os casos detectados
        decisoes = []
        if casos:
            log.info(f"Preparando {len(casos)} decisões com Opção A (padrão)...")
            for caso in casos:
                decisoes.append({
                    "processo": str(caso.get("processo")),
                    "decision": "A"
                })

        # Executar com decisões (se houver casos, usa Opção A; senão, vazio -> usa default A)
        run_execucao(calc, log=log, decisoes=decisoes if decisoes else None)

        out = last_output(root)
        if out:
            log.info(f"Arquivo de saída gerado: {out.name}")
        else:
            log.warning("Nenhum arquivo de saída encontrado após a execução.")

        log.info("Execução finalizada com sucesso.")
        return 0
    except Exception as e:
        log.error(f"ERRO FATAL: {e}")
        log.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())


