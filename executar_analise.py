"""Execute todo o projeto com python executar_analise.py."""
import argparse
from pathlib import Path
from scripts import preparar_dados, storytelling_eda, analise_fins_de_semana, estatisticas_eda


def executar(raiz=None):
    raiz=Path(raiz or Path(__file__).resolve().parent).resolve()
    dados=raiz/'dados'; tratados=raiz/'dados_tratados'; saida=raiz/'resultados'
    preparar_dados.main(['--dados',str(dados),'--saida',str(tratados)])
    storytelling_eda.main(['--dados',str(tratados),'--saida',str(saida)])
    analise_fins_de_semana.main(['--dados',str(tratados),'--saida',str(saida)])
    estatisticas_eda.gerar(tratados,saida)
    return tratados,saida


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent)
    executar(parser.parse_args().raiz)
