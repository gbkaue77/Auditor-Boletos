# Auditor de Boletos em PDF

Robô em Python que lê boletos em PDF, extrai os dados, aplica regras de vencimento e gera um **relatório em Excel** pronto para uso.

> Projeto de portfólio. Todos os boletos, empresas e CNPJs usados nos testes são **fictícios**.

## O problema

Conferir boletos manualmente (vencimento, valor, duplicidade) é lento e sujeito a erro. Este projeto automatiza essa rotina em segundos.

## O que ele faz

- Lê todos os PDFs de uma pasta
- Extrai beneficiário, CNPJ, número do documento, vencimento e valor
- Classifica cada boleto: `VENCIDO`, `VENCE EM BREVE` ou `EM DIA`
- Detecta **possíveis duplicidades** (mesmo CNPJ, valor e vencimento)
- Trata arquivos ilegíveis sem quebrar (`ERRO DE LEITURA`)
- Gera um Excel com duas abas: **Boletos** (colorida por status) e **Resumo** (quantidade e valor total por status)

## Como usar

```bash
pip install -r requirements.txt

python gerar_boletos.py        # cria boletos fictícios na pasta boletos/
python auditor.py              # gera relatorio_boletos_AAAAMMDD.xlsx
```

Opções do auditor:

```bash
python auditor.py minha_pasta 7   # outra pasta e alerta de 7 dias
```

## Tecnologias

Python, pdfplumber, pandas, openpyxl, reportlab

## Estrutura

```
auditor.py          # leitura dos PDFs, regras e relatório Excel
gerar_boletos.py    # gerador de boletos fictícios para teste
requirements.txt
```

## Próximos passos

- Ler também a linha digitável / código de barras
- Enviar o relatório por e-mail automaticamente
- Interface simples para escolher a pasta

## Autor

Gabriel Kauê
