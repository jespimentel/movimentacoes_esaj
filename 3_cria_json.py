#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrator de Dados Processuais do e-SAJ/TJSP
Desenvolvido para extrair informações estruturadas de arquivos HTML do sistema e-SAJ
Versão modificada: processa pasta ./extratos e gera JSON único
"""

import json
import re
import html
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime


class ExtratorProcessoESAJ:
    """Classe para extrair dados de processos do e-SAJ/TJSP"""
    
    def __init__(self, caminho_html: str):
        """
        Inicializa o extrator com o caminho do arquivo HTML
        
        Args:
            caminho_html: Caminho para o arquivo HTML do processo
        """
        self.caminho = caminho_html
        self.html_original = None
        self.soup = None
        self._carregar_html()
    
    def _carregar_html(self):
        """Carrega e processa o arquivo HTML"""
        try:
            with open(self.caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Parsear o HTML encapsulado pelo navegador
            soup_wrapper = BeautifulSoup(conteudo, 'html.parser')
            
            # Extrair o HTML original das células line-content
            line_contents = soup_wrapper.find_all('td', class_='line-content')
            
            if line_contents:
                # Reconstruir o HTML original usando get_text() para obter as entidades HTML
                html_parts = [td.get_text() for td in line_contents]
                html_texto = '\n'.join(html_parts)
                # Decodificar entidades HTML
                self.html_original = html.unescape(html_texto)
            else:
                # Se não houver encapsulamento, usar o conteúdo direto
                self.html_original = conteudo
            
            # Parsear o HTML original
            self.soup = BeautifulSoup(self.html_original, 'html.parser')
            
        except Exception as e:
            raise Exception(f"Erro ao carregar HTML: {str(e)}")
    
    def _extrair_texto_por_id(self, element_id: str) -> Optional[str]:
        """Extrai texto de um elemento pelo ID"""
        elemento = self.soup.find(id=element_id)
        if elemento:
            texto = elemento.get_text(strip=True)
            return texto if texto else None
        return None
    
    def _extrair_texto_por_span_title(self, span_id: str) -> Optional[str]:
        """Extrai texto do atributo title de um span"""
        elemento = self.soup.find('span', id=span_id)
        if elemento and elemento.get('title'):
            return elemento.get('title').strip()
        return None
    
    def extrair_numero_processo(self) -> Optional[str]:
        """Extrai o número do processo"""
        numero = self._extrair_texto_por_id('numeroProcesso')
        if not numero:
            # Tentar extrair da URL ou outros locais
            match = re.search(r'(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})', self.html_original)
            if match:
                return match.group(1)
        return numero
    
    def extrair_classe(self) -> Optional[str]:
        """Extrai a classe processual"""
        return self._extrair_texto_por_span_title('classeProcesso')
    
    def extrair_foro(self) -> Optional[str]:
        """Extrai o foro"""
        return self._extrair_texto_por_span_title('foroProcesso')
    
    def extrair_vara(self) -> Optional[str]:
        """Extrai a vara"""
        return self._extrair_texto_por_span_title('varaProcesso')
    
    def extrair_distribuicao(self) -> Optional[str]:
        """Extrai a data de distribuição"""
        return self._extrair_texto_por_id('dataHoraDistribuicaoProcesso')
    
    def extrair_controle(self) -> Optional[str]:
        """Extrai o número de controle"""
        return self._extrair_texto_por_id('numeroControleProcesso')
    
    def extrair_area(self) -> Optional[str]:
        """Extrai a área do processo"""
        return self._extrair_texto_por_id('areaProcesso')
    
    def extrair_dados_delegacia(self) -> List[Dict[str, str]]:
        """Extrai os dados da delegacia"""
        delegacias = []
        
        # Procurar pela tabela de delegacias
        tbody_delegacia = self.soup.find('tbody', id='dadosDaDelegacia')
        
        if tbody_delegacia:
            linhas = tbody_delegacia.find_all('tr')
            
            for linha in linhas:
                colunas = linha.find_all('td')
                if len(colunas) >= 4:
                    delegacia = {
                        'delegacia': colunas[0].get_text(strip=True),
                        'boletim_ocorrencia': colunas[1].get_text(strip=True),
                        'data_instauracao': colunas[2].get_text(strip=True),
                        'data_ocorrencia': colunas[3].get_text(strip=True)
                    }
                    delegacias.append(delegacia)
        
        return delegacias
    
    def extrair_partes(self) -> List[Dict[str, str]]:
        """Extrai as partes do processo"""
        partes = []
        
        # Procurar pela tabela de partes
        tabela_partes = self.soup.find('table', id='tablePartesPrincipais')
        
        if tabela_partes:
            # Buscar todas as linhas da tabela
            linhas = tabela_partes.find_all('tr')
            
            for linha in linhas:
                # Buscar células com tipo de parte e nome
                colunas = linha.find_all('td')
                
                if len(colunas) >= 2:
                    # A primeira coluna geralmente tem o tipo da parte
                    tipo_td = colunas[0]
                    nome_td = colunas[1]
                    
                    # Verificar se tem a classe esperada
                    if nome_td.get('class') and 'nomeParteEAdvogado' in nome_td.get('class'):
                        tipo = tipo_td.get_text(strip=True).replace(':', '').strip()
                        
                        if not tipo:
                            continue
                        
                        # Extrair nome da parte (pode estar em link ou texto)
                        nome_link = nome_td.find('a')
                        if nome_link:
                            nome_parte = nome_link.get_text(strip=True)
                        else:
                            # Se não houver link, pegar o primeiro item do texto
                            texto_completo = nome_td.get_text(strip=True)
                            # Dividir por quebras de linha
                            linhas_texto = [l for l in texto_completo.split('\n') if l.strip()]
                            nome_parte = linhas_texto[0] if linhas_texto else texto_completo
                        
                        # Remover informações extras do nome (como "Histórico da parte")
                        nome_parte = re.sub(r'\s*\(.*?\)\s*$', '', nome_parte).strip()
                        
                        # Extrair advogados
                        advogados = []
                        
                        # Método 1: Procurar span com "Adv" e pegar o próximo texto
                        span_adv = nome_td.find('span', class_='mensagemExibindo')
                        if span_adv:
                            texto_span = span_adv.get_text(strip=True)
                            # Verificar se é relacionado a advogado
                            if re.search(r'adv', texto_span, re.IGNORECASE):
                                # Pegar o próximo conteúdo após o span
                                next_sibling = span_adv.next_sibling
                                while next_sibling:
                                    if isinstance(next_sibling, str):
                                        texto = next_sibling.strip()
                                        if texto and not texto.startswith('('):
                                            advogados.append(texto)
                                            break
                                    elif hasattr(next_sibling, 'name') and next_sibling.name:
                                        texto = next_sibling.get_text(strip=True)
                                        if texto and not texto.startswith('('):
                                            advogados.append(texto)
                                            break
                                    next_sibling = next_sibling.next_sibling
                        
                        # Método 2: Se não encontrou, buscar por padrão no texto completo
                        if not advogados:
                            texto_td = nome_td.get_text(strip=True)
                            match_adv = re.search(r'Adv(?:ogad[oa])?s?\.?\s*[:-]\s*(.+?)(?:\n|$)', texto_td, re.IGNORECASE)
                            if match_adv:
                                advogado_texto = match_adv.group(1).strip()
                                if advogado_texto:
                                    advogados = [advogado_texto]
                        
                        # Criar registro da parte
                        if tipo and nome_parte:
                            parte = {
                                'tipo': tipo,
                                'nome': nome_parte,
                                'advogados': advogados if advogados else []
                            }
                            partes.append(parte)
        
        return partes
    
    def verificar_preso(self) -> bool:
        """Verifica se há réu preso"""
        # Procurar por indicações de prisão
        texto_completo = self.html_original.lower()
        
        # Padrões que indicam prisão
        padroes_prisao = [
            r'preso',
            r'prisão',
            r'custodiado',
            r'encarcerado',
            r'detido'
        ]
        
        for padrao in padroes_prisao:
            if re.search(padrao, texto_completo):
                # Verificar contexto para evitar falsos positivos
                # (ex: "não está preso", "ex-preso")
                contexto = re.findall(r'.{0,50}' + padrao + r'.{0,50}', texto_completo)
                for ctx in contexto:
                    if not re.search(r'(não|sem|ex-)', ctx):
                        return True
        
        return False
    
    def extrair_movimentacoes(self) -> List[Dict[str, str]]:
        """Extrai as movimentações processuais"""
        movimentacoes = []
        
        # Procurar pela tabela de movimentações
        tabela_mov = self.soup.find('tbody', id='tabelaTodasMovimentacoes')
        
        if tabela_mov:
            linhas = tabela_mov.find_all('tr', class_=['fundoClaro', 'fundoEscuro', 'containerMovimentacao'])
            
            for linha in linhas:
                colunas = linha.find_all('td')
                
                if len(colunas) >= 3:
                    # A primeira coluna tem a data
                    data = colunas[0].get_text(strip=True)
                    # A terceira coluna (índice 2) tem a descrição
                    descricao = colunas[2].get_text(separator=' ', strip=True)
                    
                    if descricao:  # Só adicionar se houver descrição
                        movimentacao = {
                            'data': data,
                            'descricao': descricao
                        }
                        movimentacoes.append(movimentacao)
        
        return movimentacoes
    
    def extrair_peticoes_diversas(self) -> List[Dict[str, str]]:
        """Extrai as petições diversas"""
        peticoes = []
        
        # Procurar pela tabela de petições
        tabela_pet = self.soup.find('table', id='tabelaTodasPeticoesDiversas')
        
        if tabela_pet:
            tbody = tabela_pet.find('tbody')
            if tbody:
                linhas = tbody.find_all('tr', class_='fundoClaro')
                
                for linha in linhas:
                    colunas = linha.find_all('td')
                    if len(colunas) >= 3:
                        peticao = {
                            'data': colunas[0].get_text(strip=True),
                            'tipo': colunas[1].get_text(strip=True),
                            'descricao': colunas[2].get_text(strip=True)
                        }
                        peticoes.append(peticao)
        
        return peticoes
    
    def extrair_audiencias(self) -> List[Dict[str, str]]:
        """Extrai as audiências"""
        audiencias = []
        
        # Procurar pela tabela de audiências
        tabela_aud = self.soup.find('table', id='tabelaTodasAudiencias')
        
        if tabela_aud:
            tbody = tabela_aud.find('tbody')
            if tbody:
                linhas = tbody.find_all('tr', class_='fundoClaro')
                
                for linha in linhas:
                    colunas = linha.find_all('td')
                    if len(colunas) >= 3:
                        audiencia = {
                            'data': colunas[0].get_text(strip=True),
                            'tipo': colunas[1].get_text(strip=True),
                            'situacao': colunas[2].get_text(strip=True)
                        }
                        audiencias.append(audiencia)
        
        return audiencias
    
    def extrair_historico_classes(self) -> List[Dict[str, str]]:
        """Extrai o histórico de classes"""
        historico = []
        
        # Procurar pela tabela de histórico de classes
        tabela_hist = self.soup.find('table', id='tabelaHistoricoDeClasses')
        
        if tabela_hist:
            tbody = tabela_hist.find('tbody')
            if tbody:
                linhas = tbody.find_all('tr', class_='fundoClaro')
                
                for linha in linhas:
                    colunas = linha.find_all('td')
                    if len(colunas) >= 2:
                        classe_historico = {
                            'data': colunas[0].get_text(strip=True),
                            'classe': colunas[1].get_text(strip=True)
                        }
                        historico.append(classe_historico)
        
        return historico
    
    def extrair_todas_informacoes(self) -> Dict:
        """Extrai todas as informações do processo"""
        dados = {
            'numero_processo': self.extrair_numero_processo(),
            'classe': self.extrair_classe(),
            'foro': self.extrair_foro(),
            'vara': self.extrair_vara(),
            'distribuicao': self.extrair_distribuicao(),
            'controle': self.extrair_controle(),
            'area': self.extrair_area(),
            'dados_delegacia': self.extrair_dados_delegacia(),
            'partes': self.extrair_partes(),
            'preso': self.verificar_preso(),
            'movimentacoes': self.extrair_movimentacoes(),
            'peticoes_diversas': self.extrair_peticoes_diversas(),
            'audiencias': self.extrair_audiencias(),
            'historico_classes': self.extrair_historico_classes()
        }
        
        return dados


def processar_pasta_extratos():
    """
    Processa todos os arquivos HTML da pasta ./extratos e gera um único JSON
    """
    # Definir caminhos
    pasta_extratos = Path('./extratos')
    
    # Verificar se a pasta existe
    if not pasta_extratos.exists():
        print(f"ERRO: A pasta '{pasta_extratos}' não existe!")
        print(f"Crie a pasta e coloque os arquivos HTML nela.")
        return
    
    # Buscar todos os arquivos HTML
    arquivos_html = list(pasta_extratos.glob('*.html'))
    
    if not arquivos_html:
        print(f"AVISO: Nenhum arquivo HTML encontrado em '{pasta_extratos}'")
        return
    
    print("="*80)
    print(f"EXTRATOR DE PROCESSOS e-SAJ/TJSP")
    print("="*80)
    print(f"\nPasta de origem: {pasta_extratos.absolute()}")
    print(f"Arquivos encontrados: {len(arquivos_html)}")
    print()
    
    # Lista para armazenar todos os processos
    todos_processos = []
    processos_com_erro = []
    
    # Processar cada arquivo
    for i, arquivo in enumerate(arquivos_html, 1):
        try:
            print(f"[{i}/{len(arquivos_html)}] Processando: {arquivo.name}...", end=' ')
            
            extrator = ExtratorProcessoESAJ(str(arquivo))
            dados = extrator.extrair_todas_informacoes()
            
            # Adicionar informação do arquivo fonte
            dados['arquivo_fonte'] = arquivo.name
            
            todos_processos.append(dados)
            print("✓ OK")
            
        except Exception as e:
            print(f"✗ ERRO")
            processos_com_erro.append({
                'arquivo': arquivo.name,
                'erro': str(e)
            })
            print(f"    Detalhes: {str(e)}")
    
    # Gerar nome do arquivo de saída com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivo_saida = f'processos_extraidos_{timestamp}.json'
    
    # Salvar o JSON único
    if todos_processos:
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(todos_processos, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*80)
        print("PROCESSAMENTO CONCLUÍDO")
        print("="*80)
        print(f"\n✓ Processos extraídos com sucesso: {len(todos_processos)}")
        print(f"✓ Arquivo gerado: {arquivo_saida}")
        print(f"✓ Tamanho do arquivo: {Path(arquivo_saida).stat().st_size / 1024:.2f} KB")
        
        # Estatísticas resumidas
        print(f"\n--- Resumo dos dados extraídos ---")
        total_movimentacoes = sum(len(p['movimentacoes']) for p in todos_processos)
        total_partes = sum(len(p['partes']) for p in todos_processos)
        presos = sum(1 for p in todos_processos if p['preso'])
        
        print(f"• Total de movimentações: {total_movimentacoes}")
        print(f"• Total de partes: {total_partes}")
        print(f"• Processos com réu preso: {presos}")
        
        if processos_com_erro:
            print(f"\n⚠ Arquivos com erro: {len(processos_com_erro)}")
            for erro_info in processos_com_erro:
                print(f"  - {erro_info['arquivo']}: {erro_info['erro']}")
        
        print(f"\n--- Próximos passos ---")
        print(f"Para criar um DataFrame com pandas:")
        print(f"  import pandas as pd")
        print(f"  import json")
        print(f"  ")
        print(f"  with open('{arquivo_saida}', 'r', encoding='utf-8') as f:")
        print(f"      dados = json.load(f)")
        print(f"  ")
        print(f"  df = pd.DataFrame(dados)")
        print(f"  print(df.info())")
        
    else:
        print("\nNenhum processo foi extraído com sucesso.")


def main():
    """Função principal"""
    processar_pasta_extratos()


if __name__ == '__main__':
    main()