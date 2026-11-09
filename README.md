# Planejamento de Manutenções no Metrô de São Paulo

Projeto Aplicado I — Banco de Dados — Universidade Presbiteriana Mackenzie.

Integrantes: Júlia Gonzaga Heringer, Pedro Henrique Dornelas Pereira, Raphael Miranda da Silva e Danielle Carotta.

O projeto caracteriza demanda de passageiros, oferta de trens e contexto de infraestrutura. A comparação de fins de semana apoia a investigação de períodos de menor movimentação. Os dados não determinam horários de manutenção nem comprovam efeitos de intervenções.

## Análise oficial

Abra **notebooks/Analise_Metro.ipynb**. O notebook acompanha os módulos de `scripts/` e deve ser mantido junto das demais pastas. A cópia entregue contém as saídas da execução de verificação.

O notebook e os scripts originais foram preservados em `historico/` para consulta. Não use esses arquivos como versão oficial.

## Instalação local

Python 3.10 ou superior; recomendado Python 3.12.

```bash
python -m pip install -r requirements.txt
python executar_analise.py
```

O comando pode ser chamado de outra pasta pelo caminho absoluto: a raiz é identificada pela localização do próprio arquivo. Para uma cópia alternativa dos dados, use `--raiz CAMINHO_DO_PROJETO`.

## Executar as etapas separadamente

A partir da raiz do projeto:

```bash
python scripts/preparar_dados.py --dados dados --saida dados_tratados
python scripts/storytelling_eda.py --dados dados_tratados --saida resultados
python scripts/analise_fins_de_semana.py --dados dados_tratados --saida resultados
python scripts/estatisticas_eda.py --dados dados_tratados --saida resultados
```

Cada arquivo tem um único ponto de entrada. As análises recebem tabelas tratadas, não os CSVs originais. Nenhum CSV de origem é alterado. Os resultados são recalculados e substituídos ao executar novamente.

## Google Colab

Envie `notebooks/Analise_Metro.ipynb` ao Colab. Execute as células em ordem. Quando solicitado, envie o ZIP completo deste projeto corrigido. O notebook descompacta os dados e os módulos e encontra sua raiz. Se faltar alguma dependência, instale as de `requirements.txt` e reinicie a sessão. O teste automatizado desta entrega foi local; a interface de upload do Colab não foi exercitada.

## Estrutura

- `dados/`: quatro CSVs originais do Metrô, preservados.
- `dados_tratados/`: cinco tabelas normalizadas, geradas automaticamente.
- `scripts/`: preparação, storytelling, fins de semana e estatísticas.
- `notebooks/Analise_Metro.ipynb`: análise oficial com explicações e resultados.
- `resultados/`: tabelas, gráficos SVG e gráficos de distribuição PNG.
- `documentos/`: PDFs recebidos, preservados; precisam incorporar as análises atualizadas.
- `historico/`: versões anteriores que não integram o fluxo oficial.
- `VALIDACAO.md`: verificações realizadas e limites.

## Fontes e metadados

Os arquivos de origem foram recebidos na pasta `dados/` do repositório. A atribuição é ao Metrô de São Paulo, conforme os cabeçalhos e notas dos CSVs. Os endereços específicos de download e a data de coleta devem ser adicionados pelo grupo após conferência; não foram inventados links.

| Fonte | Período | Escopo |
|---|---|---|
| Entrada de Passageiros por Linha  - 2025_8.csv | 2025 | 12 meses, quatro linhas e agregado Rede |
| Entrada de Passageiros por Estação - Diária - 2025_7.csv | 2025 | Registros por data, linha e estação |
| Oferta - 2026_4.csv | 2026 | 12 meses previstos; sete meses com valores nas duas métricas |
| Infraestrutura - 2024_11.csv | 2024 | Características por linha e rede |

Datas são datas de calendário; linha e estação são categorias. As colunas `entradas_mil`, `mdu_mil`, `msa_mil`, `mdo_mil` e `max_mil` estão em milhares de entradas. MDU é média dos dias úteis; MSA, média dos sábados; MDO, média dos domingos; MAX, máxima diária. Entradas incluem transferências conforme as notas da origem e não correspondem necessariamente a pessoas únicas.

Na oferta, `valor` depende de `metrica`: intervalo mínimo em segundos ou velocidade comercial em km/h. Na infraestrutura, `valor_fonte` preserva unidades e anotações originais; a frota compartilhada não é repartida entre linhas.

## Critérios estatísticos

As medidas incluem contagens, ausentes, mínimo, máximo, média, mediana, quartis, variância e desvio padrão amostrais (`ddof=1`). A variância tem unidade ao quadrado. O critério de outliers é 1,5 IQR, calculado por variável e grupo; na demanda diária há também um recorte por tipo de dia. Os pontos são sinalizados, sem exclusão automática. Uma mesma observação pode aparecer em dois recortes de investigação.

Segunda a sexta inclui feriados. A comparação de sábados e domingos usa pares completos do mesmo fim de semana, com um segundo resumo apenas das datas comuns às quatro linhas. Ausentes não são substituídos por zero.

Os totais diários são reconciliados com os mensais, considerando tolerância de `0,5 + 0,05 × dias com valor`, em milhares de entradas. A média do intervalo mínimo mensal não equivale ao intervalo médio real observado entre todos os trens.

## Pendências do documento

Atualizar o relatório e o storytelling com as tabelas de `resultados/`, a análise de distribuição, os outliers e a comparação dos fins de semana. Os PDFs anteriores não foram modificados nesta revisão dos códigos. A geração desses resultados não garante, por si só, o atendimento do critério de análise exploratória inserida no documento.
