"""Gera boletos FICTÍCIOS em PDF para testar o auditor.

Todos os dados (empresas, CNPJs, valores) são inventados.
Uso: python gerar_boletos.py [quantidade]
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

PASTA_SAIDA = Path("boletos")

FORNECEDORES = [
    "Papelaria Exemplo Ltda",
    "Limpeza Modelo ME",
    "Tech Suprimentos Fictícios S.A.",
    "Gráfica Demonstração Ltda",
    "Manutenção Teste EIRELI",
    "Distribuidora Amostra Ltda",
    "Serviços Ficção Ltda",
]


def cnpj_ficticio(rng: random.Random) -> str:
    n = [rng.randint(0, 9) for _ in range(8)]
    base = "".join(map(str, n))
    return f"{base[:2]}.{base[2:5]}.{base[5:8]}/0001-{rng.randint(10, 99)}"


def formatar_valor(valor: float) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_boleto(caminho: Path, numero: int, fornecedor: str, cnpj: str,
                 valor: float, vencimento: date, emissao: date) -> None:
    c = canvas.Canvas(str(caminho), pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 790, "BOLETO DE COBRANÇA (FICTÍCIO)")
    c.setFont("Helvetica", 11)
    linhas = [
        f"Beneficiário: {fornecedor}",
        f"CNPJ: {cnpj}",
        f"Número do documento: {numero:05d}",
        f"Data de emissão: {emissao:%d/%m/%Y}",
        f"Vencimento: {vencimento:%d/%m/%Y}",
        f"Valor do documento: R$ {formatar_valor(valor)}",
    ]
    y = 750
    for linha in linhas:
        c.drawString(50, y, linha)
        y -= 24
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 60, "Documento gerado apenas para fins de demonstração.")
    c.save()


def main() -> None:
    quantidade = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    rng = random.Random(42)  # semente fixa: resultado reproduzível
    PASTA_SAIDA.mkdir(exist_ok=True)
    hoje = date.today()

    primeiro = None
    for i in range(1, quantidade + 1):
        fornecedor = rng.choice(FORNECEDORES)
        valor = round(rng.uniform(120, 9500), 2)
        # mistura de vencidos, a vencer em breve e em dia
        vencimento = hoje + timedelta(days=rng.randint(-10, 30))
        emissao = vencimento - timedelta(days=rng.randint(5, 30))
        cnpj = cnpj_ficticio(rng)
        nome = f"boleto_{i:03d}.pdf"
        gerar_boleto(PASTA_SAIDA / nome, i, fornecedor, cnpj, valor, vencimento, emissao)
        if primeiro is None:
            primeiro = (fornecedor, cnpj, valor, vencimento, emissao)

    # cópia do primeiro boleto com outro número: testa a detecção de duplicidade
    gerar_boleto(PASTA_SAIDA / "boleto_duplicado.pdf", quantidade + 1, *primeiro)

    # boleto propositalmente ilegível para testar o tratamento de erros
    c = canvas.Canvas(str(PASTA_SAIDA / "boleto_invalido.pdf"), pagesize=A4)
    c.drawString(50, 750, "Documento sem os campos esperados.")
    c.save()

    print(f"{quantidade} boletos fictícios + 1 inválido gerados em '{PASTA_SAIDA}/'")


if __name__ == "__main__":
    main()
