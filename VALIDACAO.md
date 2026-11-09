# Validação da revisão dos códigos

## Execução verificada

- `python executar_analise.py` concluiu tratamento, storytelling, fins de semana e estatísticas sem erro.
- As dez células de código de `notebooks/Analise_Metro.ipynb` foram executadas em ordem em uma sessão IPython local nova, com captura de tabelas, mensagens e imagens. O arquivo foi validado contra o formato de notebook.
- O kernel Jupyter externo não iniciou neste ambiente por restrição de sockets. A validação das células foi feita no mesmo processo IPython; não se afirma teste da interface do Jupyter ou do upload do Colab.
- Os quatro CSVs de origem foram comparados byte a byte com os recebidos e permanecem intactos.
- Os scripts passaram pela compilação sintática.

## Conferências dos resultados

- 60 registros mensais: quatro linhas e Rede, com 12 meses em cada grupo, sem duplicidade de chave.
- 24.090 registros por estação e dia; 1.460 totais por linha e dia.
- 96 registros de oferta, incluindo meses previstos sem valor, e 55 de infraestrutura contextual.
- 48 de 48 reconciliações entre totais diários e mensais dentro da tolerância de arredondamento.
- Médias mensais em milhares: Azul 19.936,9167 e Verde 12.867,0833.
- Três totais diários ausentes na Linha Prata; 37 valores de entradas ausentes por estação no conjunto tratado.
- Fins de semana: 52 pares completos em Azul, Verde e Vermelha; 49 na Prata; 49 datas completas comuns às quatro linhas.
- Todos os pares completos analisados apresentam domingo abaixo do sábado. Isso não comprova viabilidade técnica de manutenção.
- A relação entre variância e desvio padrão foi conferida. Cada alerta de outlier está fora do respectivo limite IQR; nenhum registro foi excluído.
- Histogramas e boxplots foram inspecionados visualmente.

## Limites e pendências

Os scripts são dependências do notebook e acompanham o ZIP. O fluxo local foi testado com os dados recebidos. Não houve publicação no GitHub nem exame do histórico de commits. Os PDFs de documentos foram preservados e precisam ser atualizados pelo grupo com os resultados gerados.
