# Ajustes realizados

1. Separação do tratamento em `scripts/preparar_dados.py` e remoção da duplicação desse programa nos dois scripts de análise.
2. Cada script passou a ter um único `main(argv=None)`, com entrada e saída explícitas.
3. Inclusão de `executar_analise.py` para executar todas as etapas, com caminhos relativos à raiz do projeto.
4. Criação de `notebooks/Analise_Metro.ipynb`, sem estado oculto, inclusão manual de janeiro ou variável `azul` com dois significados. O notebook utiliza os módulos fornecidos e exibe os resultados.
5. Estatísticas das tabelas tratadas, contagens de ausentes, verificação de duplicidade, variância e desvio padrão amostrais, quartis e investigação de outliers.
6. Inclusão de histogramas e boxplots por tipo de dia, preservando todos os registros.
7. README atualizado com execução local, uso no Colab, metadados, critérios estatísticos e limites de interpretação.
8. Arquivos antigos preservados em `historico/`; PDFs e CSVs de origem não foram reescritos.

Para atualizar o repositório, copie o conteúdo da pasta do ZIP mantendo essa estrutura. Remova ou mova as versões antigas que estavam em `graficos/` e `notebooks/`, conforme a organização de `historico/`; um simples upload dos novos arquivos não remove automaticamente os antigos no GitHub.
