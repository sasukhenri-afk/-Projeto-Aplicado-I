"""Caracterização das tabelas tratadas e outliers pelo critério de 1,5 IQR."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def resumo_serie(serie):
    s = serie.dropna()
    q1, q3 = s.quantile([.25, .75]) if len(s) else (np.nan, np.nan)
    iqr = q3 - q1
    inferior, superior = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return {
        'observacoes': len(serie), 'validas': len(s), 'ausentes': int(serie.isna().sum()),
        'minimo': s.min(), 'maximo': s.max(), 'media': s.mean(), 'mediana': s.median(),
        'variancia_amostral': s.var(ddof=1), 'desvio_padrao_amostral': s.std(ddof=1),
        'q1': q1, 'q3': q3, 'iqr': iqr, 'limite_inferior': inferior,
        'limite_superior': superior,
        'outliers_iqr': int(((s < inferior) | (s > superior)).sum()),
    }


def descrever(tabela, grupos, variaveis, nome):
    resumos, atipicos = [], []
    for chave, parte in tabela.groupby(grupos, dropna=False, sort=True):
        if not isinstance(chave, tuple): chave = (chave,)
        identidade = dict(zip(grupos, chave))
        for variavel in variaveis:
            resumo = resumo_serie(parte[variavel])
            resumos.append({'tabela': nome, **identidade, 'variavel': variavel, **resumo})
            mascara = parte[variavel].lt(resumo['limite_inferior']) | parte[variavel].gt(resumo['limite_superior'])
            for _, linha in parte.loc[mascara].iterrows():
                atipicos.append({'tabela': nome, **identidade, 'variavel': variavel,
                                 'data': linha.get('data', ''), 'mes': linha.get('mes', ''),
                                 'valor': linha[variavel], 'limite_inferior': resumo['limite_inferior'],
                                 'limite_superior': resumo['limite_superior']})
    return pd.DataFrame(resumos), pd.DataFrame(atipicos)


def gerar(dados, saida):
    dados, saida = Path(dados), Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    mensal = pd.read_csv(dados/'demanda_mensal.csv')
    diaria = pd.read_csv(dados/'demanda_diaria_linha.csv', parse_dates=['data'])
    estacoes = pd.read_csv(dados/'demanda_diaria_estacao.csv', parse_dates=['data'],
                          keep_default_na=False, na_values={'entradas_mil':['']})
    oferta = pd.read_csv(dados/'oferta_mensal.csv')
    infra = pd.read_csv(dados/'infraestrutura.csv', keep_default_na=False)
    diaria['tipo_dia'] = diaria.data.dt.dayofweek.map(dict(enumerate(['Seg–sex']*5+['Sábado','Domingo'])))
    fontes = [
        ('demanda_mensal', mensal, ['ano','mes','linha'], ['linha'],
         ['entradas_mil','mdu_mil','msa_mil','mdo_mil','max_mil']),
        ('demanda_diaria_linha', diaria, ['data','linha'], ['linha'], ['entradas_mil']),
        ('demanda_diaria_estacao', estacoes, ['data','linha','estacao'], ['linha','estacao'], ['entradas_mil']),
        ('oferta_mensal', oferta, ['ano','mes','linha','metrica'], ['linha','metrica'], ['valor']),
    ]
    qualidade, ausentes, resumos, atipicos = [], [], [], []
    for nome, tabela, chaves, grupos, variaveis in fontes:
        qualidade.append({'tabela': nome, 'linhas': len(tabela), 'colunas': len(tabela.columns),
                          'chaves_duplicadas': int(tabela.duplicated(chaves).sum())})
        for coluna in tabela:
            ausentes.append({'tabela':nome,'variavel':coluna,'tipo_python':str(tabela[coluna].dtype),
                             'ausentes':int(tabela[coluna].isna().sum())})
        resumo, pontos = descrever(tabela, grupos, variaveis, nome)
        resumo.to_csv(saida/f'estatisticas_{nome}.csv',index=False,encoding='utf-8-sig')
        resumos.append(resumo)
        if not pontos.empty: atipicos.append(pontos)
    # Compara valores atípicos também dentro de cada tipo de dia para reduzir
    # a mistura entre a movimentação de segunda a sexta e os fins de semana.
    perfil_stats, perfil_atipicos = descrever(diaria, ['linha','tipo_dia'], ['entradas_mil'], 'demanda_por_tipo_dia')
    perfil_stats.to_csv(saida/'estatisticas_por_tipo_dia.csv',index=False,encoding='utf-8-sig')
    if not perfil_atipicos.empty: atipicos.append(perfil_atipicos)
    pd.DataFrame(qualidade).to_csv(saida/'qualidade_tabelas.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(ausentes).to_csv(saida/'ausentes_por_variavel.csv',index=False,encoding='utf-8-sig')
    pontos = pd.concat(atipicos, ignore_index=True) if atipicos else pd.DataFrame(columns=['tabela','variavel','valor'])
    pontos.to_csv(saida/'outliers_iqr.csv',index=False,encoding='utf-8-sig')
    # A infraestrutura inclui métricas de unidades diferentes e uma frota
    # compartilhada. Preserva-se seu conteúdo; não se calcula média entre métricas.
    infra.to_csv(saida/'infraestrutura_contexto.csv',index=False,encoding='utf-8-sig')
    linhas = sorted(diaria.linha.unique(), key=lambda x:int(x.split()[1].split('-')[0]))
    fig, axes = plt.subplots(2,2,figsize=(12,8))
    for ax, linha in zip(axes.flat,linhas):
        ax.hist(diaria.loc[diaria.linha.eq(linha),'entradas_mil'].dropna(),bins=20,edgecolor='white')
        ax.set(title=linha,xlabel='Entradas diárias (mil)',ylabel='Quantidade de dias')
    fig.suptitle('Distribuição da demanda diária em 2025');fig.tight_layout()
    fig.savefig(saida/'04_histogramas_demanda.png',dpi=160);plt.close(fig)
    fig, axes = plt.subplots(2,2,figsize=(12,8))
    tipos = ['Seg–sex','Sábado','Domingo']
    for ax, linha in zip(axes.flat,linhas):
        parte=diaria.loc[diaria.linha.eq(linha)]
        ax.boxplot([parte.loc[parte.tipo_dia.eq(t),'entradas_mil'].dropna() for t in tipos],tick_labels=tipos)
        ax.set(title=linha,ylabel='Entradas diárias (mil)')
    fig.suptitle('Demanda por tipo de dia em 2025 — seg–sex inclui feriados');fig.tight_layout()
    fig.savefig(saida/'05_boxplots_tipo_dia.png',dpi=160);plt.close(fig)
    print('Estatísticas, ausentes, outliers e gráficos de distribuição gerados.')
    return pd.DataFrame(qualidade)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dados',type=Path,default=Path('dados_tratados'))
    parser.add_argument('--saida',type=Path,default=Path('resultados'))
    args=parser.parse_args(argv)
    gerar(args.dados,args.saida)

if __name__=='__main__':main()
