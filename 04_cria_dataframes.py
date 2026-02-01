#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Análise com Pandas
Mostra como carregar o JSON gerado e criar DataFrames para análise
"""

import pandas as pd
import json
from pathlib import Path
import glob


def carregar_dados():
    """Carrega o arquivo JSON mais recente gerado pelo extrator"""
    
    # Procurar arquivo JSON gerado (mais recente)
    arquivos = glob.glob('processos_extraidos_*.json')
    
    if not arquivos:
        print("Nenhum arquivo de processos encontrado!")
        print("Execute primeiro: python extrator_processos_esaj_v2.py")
        return None
    
    # Pegar o arquivo mais recente
    arquivo_mais_recente = max(arquivos, key=lambda x: Path(x).stat().st_mtime)
    print(f"Carregando: {arquivo_mais_recente}\n")
    
    with open(arquivo_mais_recente, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    return dados


def criar_dataframe_principal(dados):
    """Cria DataFrame principal com informações básicas dos processos"""
    
    print("="*80)
    print("1. DATAFRAME PRINCIPAL - Informações Básicas dos Processos")
    print("="*80)
    
    df = pd.DataFrame(dados)
    
    # Mostrar informações
    print(f"\nShape: {df.shape}")
    print(f"\nColunas disponíveis:")
    for col in df.columns:
        print(f"  • {col}")
    
    print(f"\n{df.head()}")
    
    return df


def criar_dataframe_partes(dados):
    """Cria DataFrame com todas as partes (normalizado)"""
    
    print("\n" + "="*80)
    print("2. DATAFRAME DE PARTES - Normalizado")
    print("="*80)
    
    partes_lista = []
    
    for processo in dados:
        numero_processo = processo['numero_processo']
        
        for parte in processo['partes']:
            partes_lista.append({
                'numero_processo': numero_processo,
                'tipo_parte': parte['tipo'],
                'nome_parte': parte['nome'],
                'advogados': ', '.join(parte['advogados']) if parte['advogados'] else None,
                'quantidade_advogados': len(parte['advogados'])
            })
    
    df_partes = pd.DataFrame(partes_lista)
    
    print(f"\nTotal de registros: {len(df_partes)}")
    print(f"\n{df_partes.head(10)}")
    
    # Estatísticas por tipo de parte
    print(f"\n--- Contagem por Tipo de Parte ---")
    print(df_partes['tipo_parte'].value_counts())
    
    return df_partes


def criar_dataframe_movimentacoes(dados):
    """Cria DataFrame com todas as movimentações (normalizado)"""
    
    print("\n" + "="*80)
    print("3. DATAFRAME DE MOVIMENTAÇÕES - Normalizado")
    print("="*80)
    
    movimentacoes_lista = []
    
    for processo in dados:
        numero_processo = processo['numero_processo']
        classe = processo['classe']
        vara = processo['vara']
        
        for mov in processo['movimentacoes']:
            movimentacoes_lista.append({
                'numero_processo': numero_processo,
                'classe': classe,
                'vara': vara,
                'data': mov['data'],
                'descricao': mov['descricao']
            })
    
    df_mov = pd.DataFrame(movimentacoes_lista)
    
    print(f"\nTotal de movimentações: {len(df_mov)}")
    print(f"\n{df_mov.head(10)}")
    
    # Tentar converter data
    try:
        df_mov['data_convertida'] = pd.to_datetime(df_mov['data'], format='%d/%m/%Y', errors='coerce')
        print(f"\n--- Movimentações por Mês ---")
        if df_mov['data_convertida'].notna().any():
            df_mov['ano_mes'] = df_mov['data_convertida'].dt.to_period('M')
            print(df_mov['ano_mes'].value_counts().sort_index())
    except Exception as e:
        print(f"Não foi possível converter datas: {e}")
    
    return df_mov


def criar_dataframe_delegacias(dados):
    """Cria DataFrame com dados das delegacias (normalizado)"""
    
    print("\n" + "="*80)
    print("4. DATAFRAME DE DELEGACIAS - Normalizado")
    print("="*80)
    
    delegacias_lista = []
    
    for processo in dados:
        numero_processo = processo['numero_processo']
        
        for deleg in processo['dados_delegacia']:
            delegacias_lista.append({
                'numero_processo': numero_processo,
                'delegacia': deleg['delegacia'],
                'boletim_ocorrencia': deleg['boletim_ocorrencia'],
                'data_instauracao': deleg['data_instauracao'],
                'data_ocorrencia': deleg['data_ocorrencia']
            })
    
    df_deleg = pd.DataFrame(delegacias_lista)
    
    print(f"\nTotal de registros: {len(df_deleg)}")
    print(f"\n{df_deleg.head()}")
    
    # Delegacias mais frequentes
    print(f"\n--- Delegacias Mais Frequentes ---")
    print(df_deleg['data_instauracao'].value_counts())
    
    return df_deleg


def analises_estatisticas(df):
    """Realiza análises estatísticas básicas"""
    
    print("\n" + "="*80)
    print("5. ANÁLISES ESTATÍSTICAS")
    print("="*80)
    
    # Distribuição por classe
    print("\n--- Distribuição por Classe ---")
    print(df['classe'].value_counts())
    
    # Distribuição por foro
    print("\n--- Distribuição por Foro ---")
    print(df['foro'].value_counts())
    
    # Distribuição por vara
    print("\n--- Distribuição por Vara ---")
    print(df['vara'].value_counts())
    
    # Processos com réu preso
    print("\n--- Situação de Prisão ---")
    presos = df['preso'].value_counts()
    print(presos)
    print(f"Percentual com réu preso: {(presos.get(True, 0) / len(df) * 100):.1f}%")
    
    # Estatísticas de movimentações
    df['qtd_movimentacoes'] = df['movimentacoes'].apply(len)
    print("\n--- Estatísticas de Movimentações ---")
    print(df['qtd_movimentacoes'].describe())
    
    # Processo com mais movimentações
    idx_max = df['qtd_movimentacoes'].idxmax()
    print(f"\nProcesso com mais movimentações:")
    print(f"  Número: {df.loc[idx_max, 'numero_processo']}")
    print(f"  Quantidade: {df.loc[idx_max, 'qtd_movimentacoes']}")


def exportar_para_excel(df, df_partes, df_mov, df_deleg):
    """Exporta todos os DataFrames para um arquivo Excel com múltiplas abas"""
    
    print("\n" + "="*80)
    print("6. EXPORTAÇÃO PARA EXCEL")
    print("="*80)
    
    try:
        arquivo_excel = 'processos_analise.xlsx'
        
        with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
            df.drop(columns=['movimentacoes', 'partes', 'dados_delegacia', 
                             'peticoes_diversas', 'audiencias', 'historico_classes'], 
                    errors='ignore').to_excel(writer, sheet_name='Processos', index=False)
            df_partes.to_excel(writer, sheet_name='Partes', index=False)
            df_mov.to_excel(writer, sheet_name='Movimentações', index=False)
            df_deleg.to_excel(writer, sheet_name='Delegacias', index=False)
        
        print(f"✓ Arquivo Excel criado: {arquivo_excel}")
        print(f"  Abas: Processos, Partes, Movimentações, Delegacias")
        
    except ImportError:
        print("⚠ Para exportar para Excel, instale: pip install openpyxl")
    except Exception as e:
        print(f"✗ Erro ao criar Excel: {e}")


def main():
    """Função principal"""
    
    # Carregar dados
    dados = carregar_dados()
    if not dados:
        return
    
    print(f"Total de processos carregados: {len(dados)}\n")
    
    # Criar DataFrames
    df = criar_dataframe_principal(dados)
    df_partes = criar_dataframe_partes(dados)
    df_mov = criar_dataframe_movimentacoes(dados)
    df_deleg = criar_dataframe_delegacias(dados)
    
    # Análises
    analises_estatisticas(df)
    
    # Exportar
    exportar_para_excel(df, df_partes, df_mov, df_deleg)
    
    print("\n" + "="*80)
    print("ANÁLISE CONCLUÍDA")
    print("="*80)
    
    # Retornar DataFrames para uso interativo
    return {
        'processos': df,
        'partes': df_partes,
        'movimentacoes': df_mov,
        'delegacias': df_deleg
    }


if __name__ == '__main__':
    dfs = main()
    
    # Se executado em ambiente interativo, os DataFrames ficam disponíveis
    if dfs:
        print("\nDataFrames disponíveis na variável 'dfs':")
        print("  • dfs['processos']")
        print("  • dfs['partes']")
        print("  • dfs['movimentacoes']")
        print("  • dfs['delegacias']")