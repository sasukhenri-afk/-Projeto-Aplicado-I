"""Normaliza os quatro CSVs publicados pelo Metrô no Projeto Aplicado I."""
import argparse
import csv
from datetime import date
from pathlib import Path
import re

import pandas as pd


ARQUIVOS = {
    "mensal": "Entrada de Passageiros por Linha  - 2025_8.csv",
    "diaria": "Entrada de Passageiros por Estação - Diária - 2025_7.csv",
    "oferta": "Oferta - 2026_4.csv",
    "infraestrutura": "Infraestrutura - 2024_11.csv",
}
MESES = {
    nome.upper(): numero
    for numero, nome in enumerate("Jan Fev Mar Abr Mai Jun Jul Ago Set Out Nov Dez".split(), 1)
}
LINHAS = ["Linha 1-Azul", "Linha 2-Verde", "Linha 3-Vermelha", "Linha 15-Prata"]
PADRAO_LINHA = re.compile(r"LINHA\s+(\d+\s*-\s*[A-Z]+)", re.I)
PADRAO_MES = re.compile(r"([A-Z]{3})/(\d{4})", re.I)
NULOS = {"", "-", "–", "—"}


def ler_csv(caminho):
    conteudo = caminho.read_bytes()
    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = conteudo.decode("cp1252")
    return [[valor.strip() for valor in linha] for linha in csv.reader(
        texto.splitlines(), delimiter=";"
    )]


def numero_br(valor):
    if valor in NULOS:
        return None
    if not re.fullmatch(r"(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?", valor):
        raise ValueError(f"Valor numérico inesperado: {valor!r}")
    return float(valor.replace(".", "").replace(",", "."))


def nome_linha(titulo):
    trecho = PADRAO_LINHA.search(titulo)[1]
    return "Linha " + re.sub(r"\s+", "", trecho).title()


def preparar_mensal(linhas):
    registros = []
    for indice, linha in enumerate(linhas[:-1]):
        for coluna, titulo in enumerate(linha):
            if re.fullmatch(r"REDE(?:\s+\*)?", titulo, re.I):
                grupo = "Rede"
            elif PADRAO_LINHA.match(titulo):
                grupo = nome_linha(titulo)
            else:
                continue
            cabecalho = linhas[indice + 1][coluna:coluna + 6]
            if cabecalho != ["Mês", "Total", "MDU", "MSA", "MDO", "MAX"]:
                raise ValueError(f"Cabeçalho mensal inesperado em {titulo}: {cabecalho}")
            for linha_dados in linhas[indice + 2:]:
                mes = MESES.get(linha_dados[coluna].upper())
                if mes is None:
                    break
                total, mdu, msa, mdo, maximo = map(numero_br, linha_dados[coluna + 1:coluna + 6])
                registros.append((2025, mes, grupo, total, mdu, msa, mdo, maximo))
    return pd.DataFrame(registros, columns=[
        "ano", "mes", "linha", "entradas_mil", "mdu_mil", "msa_mil", "mdo_mil", "max_mil"
    ])


def preparar_diaria(linhas):
    estacoes, totais = [], []
    for indice, linha in enumerate(linhas[:-1]):
        for inicio, titulo in enumerate(linha):
            if not titulo.upper().startswith("ENTRADAS POR ESTAÇÃO"):
                continue
            grupo = nome_linha(titulo)
            mes_texto, ano = PADRAO_MES.search(titulo).groups()
            mes = MESES[mes_texto.upper()]
            cabecalho = linhas[indice + 1]
            fim = cabecalho.index("TOTAL", inicio + 1)
            codigos = cabecalho[inicio + 1:fim]
            if cabecalho[inicio] != "DIA" or len(set(codigos)) != len(codigos) or "" in codigos:
                raise ValueError(f"Cabeçalho diário inesperado em {titulo}")
            for linha_dados in linhas[indice + 2:]:
                dia = linha_dados[inicio]
                if not dia.isdecimal():
                    break
                data = date(int(ano), mes, int(dia))
                total = numero_br(linha_dados[fim])
                totais.append((data, grupo, total))
                for codigo, valor in zip(codigos, linha_dados[inicio + 1:fim]):
                    estacoes.append((data, grupo, codigo, numero_br(valor), valor))
    return (
        pd.DataFrame(estacoes, columns=["data", "linha", "estacao", "entradas_mil", "valor_fonte"]),
        pd.DataFrame(totais, columns=["data", "linha", "entradas_mil"]),
    )


def preparar_oferta(linhas):
    secoes = {
        "Intervalo mínimo entre trens (segundos)": "intervalo_minimo_segundos",
        "Velocidade comercial (Km/h)": "velocidade_comercial_kmh",
    }
    registros = []
    for indice, linha in enumerate(linhas[:-1]):
        metrica = secoes.get(linha[0])
        if metrica is None:
            continue
        cabecalho = linhas[indice + 1]
        if cabecalho != ["Mês", *LINHAS]:
            raise ValueError(f"Cabeçalho de oferta inesperado: {cabecalho}")
        for linha_dados in linhas[indice + 2:]:
            mes = MESES.get(linha_dados[0].upper())
            if mes is None:
                break
            for grupo, valor in zip(cabecalho[1:], linha_dados[1:]):
                registros.append((2026, mes, grupo, metrica, numero_br(valor)))
    return pd.DataFrame(registros, columns=["ano", "mes", "linha", "metrica", "valor"])


def preparar_infraestrutura(linhas):
    colunas = ["linha", "caracteristica", "valor_fonte"]
    inicio = next(i for i, linha in enumerate(linhas) if linha[0] == "Características")
    grupos = linhas[inicio][1:]
    if grupos != [*LINHAS, "Rede"]:
        raise ValueError(f"Cabeçalho de infraestrutura inesperado: {grupos}")
    registros = []
    for linha in linhas[inicio + 1:]:
        if not linha[0] or linha[0].startswith(("¹", "²", "³", "Fonte:")):
            break
        for grupo, valor in zip(grupos, linha[1:]):
            registros.append((grupo, linha[0], valor))
    resultado = pd.DataFrame(registros, columns=colunas)
    resultado.insert(0, "ano", 2024)
    return resultado


def validar_chaves(tabela, chaves, nome):
    if tabela.empty or tabela[chaves].isna().any().any():
        raise ValueError(f"{nome}: tabela vazia ou chave ausente")
    duplicadas = tabela.loc[tabela.duplicated(chaves, keep=False), chaves]
    if not duplicadas.empty:
        raise ValueError(f"{nome}: chaves duplicadas\n{duplicadas.head().to_string(index=False)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, required=True, help="Pasta dados/ do repositório")
    parser.add_argument("--saida", type=Path, default=Path("dados_tratados"))
    args = parser.parse_args()

    entradas = {chave: ler_csv(args.dados / arquivo) for chave, arquivo in ARQUIVOS.items()}
    estacoes, linhas_diarias = preparar_diaria(entradas["diaria"])
    tabelas = {
        "demanda_mensal": (preparar_mensal(entradas["mensal"]), ["ano", "mes", "linha"]),
        "demanda_diaria_estacao": (estacoes, ["data", "linha", "estacao"]),
        "demanda_diaria_linha": (linhas_diarias, ["data", "linha"]),
        "oferta_mensal": (preparar_oferta(entradas["oferta"]), ["ano", "mes", "linha", "metrica"]),
        "infraestrutura": (preparar_infraestrutura(entradas["infraestrutura"]),
                           ["ano", "linha", "caracteristica"]),
    }
    for nome, (tabela, chaves) in tabelas.items():
        validar_chaves(tabela, chaves, nome)

    args.saida.mkdir(parents=True, exist_ok=True)
    for nome, (tabela, chaves) in tabelas.items():
        tabela.sort_values(chaves).to_csv(args.saida / f"{nome}.csv", index=False, encoding="utf-8-sig")
        print(f"{nome}: {len(tabela):,} registros")


if __name__ == "__main__":
    main()
