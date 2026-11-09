"""Compara sábados e domingos do mesmo fim de semana usando os totais diários."""

import argparse
from pathlib import Path

import pandas as pd


def parear(tabela, chaves, domingos):
    fim_de_semana = tabela.loc[
        tabela.data.dt.dayofweek.ge(5)
    ].copy()

    fim_de_semana["tipo_dia"] = (
        fim_de_semana.data.dt.dayofweek.map({
            5: "sabado",
            6: "domingo"
        })
    )

    fim_de_semana["data_domingo"] = (
        fim_de_semana.data
        + pd.to_timedelta(
            6 - fim_de_semana.data.dt.dayofweek,
            unit="D"
        )
    )

    combinacoes = tabela[chaves].drop_duplicates().merge(
        pd.DataFrame({"data_domingo": domingos}),
        how="cross"
    )

    indice = [*chaves, "data_domingo"]

    pares = fim_de_semana.pivot(
        index=indice,
        columns="tipo_dia",
        values="entradas_mil"
    )

    pares = pares.reindex(
        index=pd.MultiIndex.from_frame(
            combinacoes[indice]
        ),
        columns=["sabado", "domingo"]
    ).reset_index()

    pares = pares.rename(columns={
        "sabado": "sabado_mil",
        "domingo": "domingo_mil"
    })

    pares.columns.name = None

    pares["data_sabado"] = (
        pares.data_domingo - pd.Timedelta(days=1)
    )

    pares["mes_domingo"] = (
        pares.data_domingo.dt.strftime("%Y-%m")
    )

    pares["par_valido"] = (
        pares[["sabado_mil", "domingo_mil"]]
        .notna()
        .all(axis=1)
    )

    pares["diferenca_mil"] = (
        pares.domingo_mil - pares.sabado_mil
    )

    pares["domingo_menor"] = (
        pares.diferenca_mil.lt(0)
        .astype("boolean")
        .where(pares.par_valido)
    )

    return pares.sort_values(indice)


def resumir(pares, chaves):
    cobertura = pares.groupby(
        chaves,
        as_index=False
    ).agg(
        pares_previstos=("par_valido", "size"),
        pares_validos=("par_valido", "sum"),
    )

    perfil = (
        pares.loc[pares.par_valido]
        .groupby(chaves, as_index=False)
        .agg(
            sabado_media_mil=("sabado_mil", "mean"),
            domingo_media_mil=("domingo_mil", "mean"),
            domingo_menor_qtd=("domingo_menor", "sum"),
            diferenca_mediana_mil=("diferenca_mil", "median"),
        )
    )

    resultado = cobertura.merge(
        perfil,
        on=chaves,
        how="left",
        validate="one_to_one"
    )

    resultado["domingo_menor_qtd"] = (
        resultado.domingo_menor_qtd
        .fillna(0)
        .astype(int)
    )

    resultado["domingo_menor_pct"] = (
        100 * resultado.domingo_menor_qtd
        / resultado.pares_validos.where(
            resultado.pares_validos.gt(0)
        )
    )

    resultado["domingo_vs_sabado_pct"] = (
        100 * (
            resultado.domingo_media_mil
            / resultado.sabado_media_mil.where(
                resultado.sabado_media_mil.gt(0)
            ) - 1
        )
    )

    return resultado


def ler(pasta, nome, chaves):
    tabela = pd.read_csv(
        pasta / f"{nome}.csv",
        encoding="utf-8-sig",
        parse_dates=["data"]
    )

    if (
        tabela.empty
        or tabela[chaves].isna().any().any()
        or tabela.duplicated(chaves).any()
    ):
        raise ValueError(
            f"{nome}: tabela vazia ou chaves incompletas ou duplicadas"
        )

    return tabela


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--dados",
        type=Path,
        default=Path("dados_tratados")
    )

    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("resultados")
    )

    args = parser.parse_args(argv)

    linhas = ler(
        args.dados,
        "demanda_diaria_linha",
        ["data", "linha"]
    )

    estacoes = ler(
        args.dados,
        "demanda_diaria_estacao",
        ["data", "linha", "estacao"]
    )

    domingos = pd.date_range(
        "2025-01-01",
        "2025-12-31",
        freq="W-SUN"
    )

    pares_linha = parear(
        linhas,
        ["linha"],
        domingos
    )

    pares_estacao = parear(
        estacoes,
        ["linha", "estacao"],
        domingos
    )

    todos_validos = (
        pares_linha.groupby("data_domingo")
        .par_valido.all()
    )

    datas_comuns = todos_validos.index[
        todos_validos
    ]

    mesmas_datas = pares_linha.loc[
        pares_linha.data_domingo.isin(datas_comuns)
    ]

    perfil_linha = pd.concat([
        resumir(
            pares_linha,
            ["linha"]
        ).assign(
            escopo="pares_disponiveis_por_linha"
        ),

        resumir(
            mesmas_datas,
            ["linha"]
        ).assign(
            escopo="mesmas_datas_em_todas_as_linhas"
        ),
    ], ignore_index=True)

    saidas = {
        "pares_por_linha": pares_linha,

        "resumo_por_linha": perfil_linha,

        "resumo_por_linha_mes": resumir(
            pares_linha,
            ["linha", "mes_domingo"]
        ),

        "resumo_por_estacao": resumir(
            pares_estacao,
            ["linha", "estacao"]
        ),
    }

    args.saida.mkdir(
        parents=True,
        exist_ok=True
    )

    for nome, tabela in saidas.items():
        tabela.to_csv(
            args.saida / f"{nome}.csv",
            index=False,
            encoding="utf-8-sig",
            float_format="%.4f"
        )

    print(
        f"{len(domingos)} fins de semana no calendário de 2025."
    )

    print(
        f"{len(datas_comuns)} pares completos em comum entre as linhas."
    )

    print(
        f"{len(saidas)} tabelas em {args.saida}."
    )


if __name__ == "__main__":
    main()
