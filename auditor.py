"""Auditor de boletos em PDF.

Lê os PDFs da pasta 'boletos', extrai beneficiário, CNPJ, valor e vencimento,
aplica regras de vencimento e gera um relatório em Excel.

Uso: python auditor.py [pasta_dos_boletos] [dias_de_alerta]
"""
import re
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pdfplumber
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

DIAS_ALERTA_PADRAO = 5

PADROES = {
    "beneficiario": re.compile(r"Benefici[áa]rio:\s*(.+)"),
    "cnpj": re.compile(r"CNPJ:\s*([\d./-]+)"),
    "documento": re.compile(r"N[úu]mero do documento:\s*(\d+)"),
    "vencimento": re.compile(r"Vencimento:\s*(\d{2}/\d{2}/\d{4})"),
    "valor": re.compile(r"Valor do documento:\s*R\$\s*([\d.]+,\d{2})"),
}

CORES = {
    "VENCIDO": "F8CBAD",
    "VENCE EM BREVE": "FFE699",
    "EM DIA": "C6E0B4",
    "ERRO DE LEITURA": "D9D9D9",
}


def ler_texto(caminho: Path) -> str:
    with pdfplumber.open(caminho) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


def extrair_dados(texto: str) -> dict | None:
    """Retorna os campos do boleto ou None se algum campo estiver faltando."""
    dados = {}
    for campo, padrao in PADROES.items():
        achou = padrao.search(texto)
        if not achou:
            return None
        dados[campo] = achou.group(1).strip()
    dados["vencimento"] = datetime.strptime(dados["vencimento"], "%d/%m/%Y").date()
    dados["valor"] = float(dados["valor"].replace(".", "").replace(",", "."))
    return dados


def classificar(vencimento: date, hoje: date, dias_alerta: int) -> str:
    dias = (vencimento - hoje).days
    if dias < 0:
        return "VENCIDO"
    if dias <= dias_alerta:
        return "VENCE EM BREVE"
    return "EM DIA"


def auditar(pasta: Path, dias_alerta: int) -> pd.DataFrame:
    hoje = date.today()
    linhas = []
    for pdf in sorted(pasta.glob("*.pdf")):
        try:
            dados = extrair_dados(ler_texto(pdf))
        except Exception:  # PDF corrompido, protegido etc.
            dados = None
        if dados is None:
            linhas.append({"arquivo": pdf.name, "status": "ERRO DE LEITURA"})
            continue
        dias = (dados["vencimento"] - hoje).days
        linhas.append({
            "arquivo": pdf.name,
            "documento": dados["documento"],
            "beneficiario": dados["beneficiario"],
            "cnpj": dados["cnpj"],
            "vencimento": dados["vencimento"],
            "dias_para_vencer": dias,
            "valor": dados["valor"],
            "status": classificar(dados["vencimento"], hoje, dias_alerta),
        })
    return pd.DataFrame(linhas)


def marcar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    """Sinaliza boletos com mesmo CNPJ, valor e vencimento (possível duplicidade)."""
    ok = df["status"] != "ERRO DE LEITURA"
    chave = ["cnpj", "valor", "vencimento"]
    dup = df[ok].duplicated(subset=chave, keep=False)
    df["possivel_duplicidade"] = ""
    df.loc[dup[dup].index, "possivel_duplicidade"] = "SIM"
    return df


def salvar_excel(df: pd.DataFrame, destino: Path) -> None:
    resumo = (
        df.groupby("status")
        .agg(quantidade=("arquivo", "count"), valor_total=("valor", "sum"))
        .reset_index()
    )
    resumo["valor_total"] = resumo["valor_total"].fillna(0)

    with pd.ExcelWriter(destino, engine="openpyxl") as escritor:
        df.to_excel(escritor, sheet_name="Boletos", index=False)
        resumo.to_excel(escritor, sheet_name="Resumo", index=False)

    wb = load_workbook(destino)
    for nome in ("Boletos", "Resumo"):
        ws = wb[nome]
        ws.freeze_panes = "A2"
        for celula in ws[1]:
            celula.font = Font(bold=True, color="FFFFFF")
            celula.fill = PatternFill("solid", fgColor="1F4E78")
            celula.alignment = Alignment(horizontal="center")
        for coluna in ws.columns:
            largura = max(len(str(c.value)) if c.value is not None else 0 for c in coluna)
            ws.column_dimensions[get_column_letter(coluna[0].column)].width = largura + 3

    ws = wb["Boletos"]
    cab = [c.value for c in ws[1]]
    col_status = cab.index("status") + 1
    col_valor = cab.index("valor") + 1
    col_venc = cab.index("vencimento") + 1
    for linha in ws.iter_rows(min_row=2):
        cor = CORES.get(linha[col_status - 1].value)
        if cor:
            linha[col_status - 1].fill = PatternFill("solid", fgColor=cor)
        linha[col_valor - 1].number_format = 'R$ #,##0.00'
        linha[col_venc - 1].number_format = "DD/MM/YYYY"
    for linha in wb["Resumo"].iter_rows(min_row=2):
        linha[2].number_format = 'R$ #,##0.00'
    wb.save(destino)


def main() -> None:
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("boletos")
    dias_alerta = int(sys.argv[2]) if len(sys.argv) > 2 else DIAS_ALERTA_PADRAO
    if not pasta.is_dir():
        sys.exit(f"Pasta '{pasta}' não encontrada. Rode antes: python gerar_boletos.py")

    df = marcar_duplicados(auditar(pasta, dias_alerta))
    destino = Path(f"relatorio_boletos_{date.today():%Y%m%d}.xlsx")
    salvar_excel(df, destino)

    print(f"Relatório salvo em: {destino}")
    print(df["status"].value_counts().to_string())


if __name__ == "__main__":
    main()
