"""Calcula indicadores, verifica cobertura e gera três gráficos para a apresentação."""
import argparse
from pathlib import Path

import pandas as pd
from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib.colors import HexColor


TIPOS_DIA = ["Seg–sex", "Sábado", "Domingo"]
MESES = "Jan Fev Mar Abr Mai Jun Jul Ago Set Out Nov Dez".split()
CORES = ["#006A82", "#9B5500", "#6352A2"]
TEXTO = "#182838"
SECUNDARIO = "#41546A"
GRADE = "#DCE5EB"


def ler(pasta, nome, **opcoes):
    return pd.read_csv(pasta / f"{nome}.csv", encoding="utf-8-sig", **opcoes)


def agregar(tabela, grupos):
    return tabela.groupby(grupos, as_index=False).agg(
        dias_base=("entradas_mil", "size"),
        dias_com_valor=("entradas_mil", "count"),
        media_entradas_mil=("entradas_mil", "mean"),
        mediana_entradas_mil=("entradas_mil", "median"),
        p25_entradas_mil=("entradas_mil", lambda serie: serie.quantile(0.25)),
    )


def reconciliar(diaria, mensal):
    totais = diaria.groupby(["ano", "mes", "linha"], as_index=False).agg(
        soma_diaria_mil=("entradas_mil", lambda serie: serie.sum(min_count=1)),
        dias_com_valor=("entradas_mil", "count"),
    )
    escopo = mensal.loc[mensal.linha.ne("Rede"), ["ano", "mes", "linha", "entradas_mil"]]
    resultado = escopo.merge(totais, on=["ano", "mes", "linha"], how="outer", validate="one_to_one")
    resultado["diferenca_mil"] = resultado.soma_diaria_mil - resultado.entradas_mil
    # A origem arredonda o total mensal a 1 mil e os totais diários a 0,1 mil.
    tolerancia = 0.5 + 0.05 * resultado.dias_com_valor
    resultado["dentro_tolerancia"] = resultado.diferenca_mil.abs().le(tolerancia + 1e-9)
    if not resultado.dentro_tolerancia.all():
        print("Atenção: há diferenças além da tolerância. Consulte reconciliacao_mensal.csv.")
    return resultado


def rotulo(desenho, x, y, texto, tamanho=11, cor=TEXTO, ancora="start", negrito=False):
    desenho.add(String(x, y, texto, textAnchor=ancora, fontSize=tamanho,
                       fontName="Helvetica-Bold" if negrito else "Helvetica",
                       fillColor=HexColor(cor)))


def barra(desenho, x, y, largura, altura, cor):
    desenho.add(Rect(x, y, largura, altura, strokeColor=None, fillColor=HexColor(cor)))


def linha(desenho, x, y, x2, y2, cor=GRADE, espessura=1):
    desenho.add(Line(x, y, x2, y2, strokeColor=HexColor(cor), strokeWidth=espessura))


def quadro(titulo, subtitulo, rodape, altura):
    desenho = Drawing(920, altura)
    barra(desenho, 0, 0, 920, altura, "#FFFFFF")
    rotulo(desenho, 40, altura - 40, titulo, 24, negrito=True)
    rotulo(desenho, 40, altura - 64, subtitulo, 12, SECUNDARIO)
    rotulo(desenho, 40, 25, rodape, 10, SECUNDARIO)
    return desenho


def decimal_br(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")


def grafico_mensal(mensal, pasta):
    rede = mensal.loc[mensal.linha.eq("Rede")].sort_values("mes")
    desenho = quadro(
        "O mês de maior volume mudou quando olhamos por dia",
        "Total mensal e total dividido pelos dias de calendário | Rede publicada | 2025",
        "Fonte: Metrô de São Paulo, entradas mensais de 2025. Rede conforme o CSV.",
        385,
    )
    paineis = [
        (64, "Entradas no mês (milhões)", rede.entradas_mil / 1000, [0, 20, 40, 60], 66),
        (502, "Entradas por dia (milhões)", rede.entradas_mil_por_dia_calendario / 1000,
         [0, 0.5, 1, 1.5, 2], 2.15),
    ]
    for x, titulo, valores, marcas, limite in paineis:
        rotulo(desenho, x, 285, titulo, 13, negrito=True)
        for valor in marcas:
            y = 75 + 182 * valor / limite
            linha(desenho, x, y, x + 360, y)
            rotulo(desenho, x - 8, y - 3, f"{valor:g}".replace(".", ","), 9, SECUNDARIO, "end")
        pico = valores.idxmax()
        for (indice, mes), valor in zip(rede.mes.items(), valores):
            px = x + 5 + (mes - 1) * 30
            altura = 182 * valor / limite
            cor = CORES[0] if indice == pico else "#C5D7DF"
            barra(desenho, px, 75, 20, altura, cor)
            rotulo(desenho, px + 10, 56, MESES[mes - 1], 9, SECUNDARIO, "middle")
            if indice == pico:
                rotulo(desenho, px + 10, 82 + altura, decimal_br(valor, 3), 10,
                       CORES[0], "middle", negrito=True)
    renderSVG.drawToFile(desenho, str(pasta / "01_volume_e_ritmo.svg"))


def grafico_dia(perfil, pasta):
    desenho = quadro(
        "Domingo teve a menor média diária nas quatro linhas",
        "Entradas médias por dia (mil) | Totais diários publicados | 2025",
        "Fonte: Metrô de São Paulo. Seg–sex inclui feriados. Prata: 49 domingos com valor de 52.",
        435,
    )
    for i, (tipo, cor) in enumerate(zip(TIPOS_DIA, CORES)):
        x = 83 + 136 * i
        barra(desenho, x, 330, 12, 12, cor)
        rotulo(desenho, x + 19, 330, tipo, 11)
    for valor in range(0, 901, 200):
        y = 79 + 230 * valor / 900
        linha(desenho, 78, y, 873, y)
        rotulo(desenho, 69, y - 3, str(valor), 10, SECUNDARIO, "end")
    nomes = sorted(perfil.linha.unique(), key=lambda nome: int(nome.split()[1].split("-")[0]))
    for i, nome in enumerate(nomes):
        x = 119 + 194 * i
        serie = perfil.loc[perfil.linha.eq(nome)].set_index("tipo_dia")
        for j, (tipo, cor) in enumerate(zip(TIPOS_DIA, CORES)):
            valor = serie.at[tipo, "media_entradas_mil"]
            altura = 230 * valor / 900
            px = x + 45 * j
            barra(desenho, px, 79, 34, altura, cor)
            rotulo(desenho, px + 17, 84 + altura, decimal_br(valor), 10, cor, "middle")
        rotulo(desenho, x + 62, 59, nome, 11, TEXTO, "middle", negrito=True)
    renderSVG.drawToFile(desenho, str(pasta / "02_demanda_tipo_de_dia.svg"))


def grafico_estacoes(ranking, pasta):
    azul = ranking.loc[ranking.linha.eq("Linha 1-Azul")].head(5)
    desenho = quadro(
        "Luz liderou as entradas diárias da Linha 1–Azul",
        "Cinco maiores médias por estação (mil entradas/dia) | 2025",
        "Fonte: Metrô de São Paulo. Média sobre dias com valor. TUC tem 364 dias, as demais têm 365.",
        415,
    )
    nomes = {"LUZ": "Luz", "SCZ": "Santa Cruz", "JAB": "Jabaquara",
             "TUC": "Tucuruvi", "BTO": "São Bento"}
    for i, registro in enumerate(azul.itertuples(index=False)):
        y = 290 - i * 48
        valor = registro.media_entradas_mil
        rotulo(desenho, 42, y + 8, nomes.get(registro.estacao, registro.estacao), 13)
        largura = 625 * valor / 110
        cor = CORES[0] if i < 3 else "#829BA6"
        barra(desenho, 145, y, largura, 27, cor)
        rotulo(desenho, 157 + largura, y + 8, decimal_br(valor), 12, SECUNDARIO, negrito=True)
    renderSVG.drawToFile(desenho, str(pasta / "03_concentracao_linha_azul.svg"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, default=Path("dados_tratados"))
    parser.add_argument("--saida", type=Path, default=Path("resultados"))
    args = parser.parse_args(argv)

    mensal = ler(args.dados, "demanda_mensal")
    periodo = pd.to_datetime(mensal[["ano", "mes"]].rename(columns={"ano": "year", "mes": "month"})
                             .assign(day=1))
    mensal["dias_calendario"] = periodo.dt.days_in_month
    mensal["entradas_mil_por_dia_calendario"] = mensal.entradas_mil / mensal.dias_calendario
    diaria = ler(args.dados, "demanda_diaria_linha", parse_dates=["data"])
    estacoes = ler(args.dados, "demanda_diaria_estacao", parse_dates=["data"], keep_default_na=False,
                   na_values={"entradas_mil": [""]})
    oferta = ler(args.dados, "oferta_mensal")
    diaria["ano"] = diaria.data.dt.year
    diaria["mes"] = diaria.data.dt.month
    diaria["tipo_dia"] = diaria.data.dt.dayofweek.map(dict(enumerate(
        ["Seg–sex"] * 5 + ["Sábado", "Domingo"]
    )))
    perfil = agregar(diaria, ["linha", "tipo_dia"])
    ranking = agregar(estacoes, ["linha", "estacao"]).sort_values(
        ["linha", "media_entradas_mil", "estacao"], ascending=[True, False, True]
    )
    ranking["cobertura_pct"] = 100 * ranking.dias_com_valor / ranking.dias_base
    comparaveis = estacoes.merge(
        diaria[["data", "linha", "entradas_mil"]],
        on=["data", "linha"], how="left", suffixes=("_estacao", "_linha"), validate="many_to_one"
    ).dropna(subset=["entradas_mil_estacao", "entradas_mil_linha"])
    volumes = comparaveis.groupby(["linha", "estacao"], as_index=False).agg(
        total_estacao_mil=("entradas_mil_estacao", "sum"),
        total_linha_nos_mesmos_dias_mil=("entradas_mil_linha", "sum"),
    )
    ranking = ranking.merge(volumes, on=["linha", "estacao"], how="left", validate="one_to_one")
    ranking["participacao_entradas_pct"] = (
        100 * ranking.total_estacao_mil / ranking.total_linha_nos_mesmos_dias_mil
    )

    oferta_resumo = oferta.groupby(["ano", "linha", "metrica"], as_index=False).agg(
        meses_base=("valor", "size"),
        meses_com_valor=("valor", "count"),
        media_valor=("valor", "mean"),
        minimo_valor=("valor", "min"),
        maximo_valor=("valor", "max"),
    )
    conciliacao = reconciliar(diaria, mensal)
    saidas = {
        "demanda_mensal": mensal,
        "perfil_tipo_dia": perfil,
        "perfil_mes_tipo_dia": agregar(diaria, ["ano", "mes", "linha", "tipo_dia"]),
        "ranking_estacoes": ranking,
        "oferta_resumo": oferta_resumo,
        "reconciliacao_mensal": conciliacao,
        "sem_valor_linha_dia": diaria.loc[diaria.entradas_mil.isna(), ["data", "linha"]],
        "sem_valor_estacao_dia": estacoes.loc[estacoes.entradas_mil.isna(),
                                              ["data", "linha", "estacao", "valor_fonte"]],
    }
    args.saida.mkdir(parents=True, exist_ok=True)
    for nome, tabela in saidas.items():
        tabela.to_csv(args.saida / f"{nome}.csv", index=False, encoding="utf-8-sig", float_format="%.4f")

    grafico_mensal(mensal, args.saida)
    grafico_dia(perfil, args.saida)
    grafico_estacoes(ranking, args.saida)
    print(f"{len(saidas)} tabelas e 3 gráficos em {args.saida}")
    print(f"Reconciliação mensal: {conciliacao.dentro_tolerancia.sum()}/{len(conciliacao)} comparações "
          "dentro da tolerância de arredondamento")


if __name__ == "__main__":
    main()
