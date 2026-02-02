import os
import json
import glob
import re
from bs4 import BeautifulSoup

def limpar_texto(texto):
    """Remove espaços em branco excessivos e quebras de linha."""
    if texto:
        return re.sub(r'\s+', ' ', texto).strip()
    return ""

def extrair_valor_por_label(soup, lista_labels):
    """
    Busca um valor associado a um label (ex: 'Classe:', 'Foro:').
    """
    for label in lista_labels:
        tag_label = soup.find(string=re.compile(label, re.IGNORECASE))
        if tag_label:
            pai = tag_label.parent
            
            # Caso 1: O valor está no próximo irmão (comum em spans/divs lado a lado)
            proximo = pai.find_next_sibling()
            if proximo:
                return limpar_texto(proximo.get_text())
            
            # Caso 2: O valor está dentro do texto do próprio pai (ex: "Label: Valor")
            texto_pai = limpar_texto(pai.get_text())
            if ":" in texto_pai:
                partes = texto_pai.split(":", 1)
                if len(partes) > 1:
                    return partes[1].strip()
            
            # Caso 3: Estrutura de tabela (Label num TD, valor no próximo TD)
            td_pai = tag_label.find_parent('td')
            if td_pai:
                td_prox = td_pai.find_next_sibling('td')
                if td_prox:
                    return limpar_texto(td_prox.get_text())
                    
    return None

def extrair_tabela_chave_valor(soup, texto_titulo):
    """Extrai listas de dados de seções baseadas em tabelas."""
    dados = []
    titulo = soup.find(string=re.compile(texto_titulo, re.IGNORECASE))
    if titulo:
        container = titulo.find_parent('table')
        if not container:
            container = titulo.find_next('table')
        
        if container:
            linhas = container.find_all('tr')
            for tr in linhas:
                cols = tr.find_all(['td', 'th'])
                if len(cols) >= 2:
                    chave = limpar_texto(cols[0].get_text())
                    valor = limpar_texto(cols[1].get_text())
                    if chave and valor:
                        dados.append(f"{chave}: {valor}")
    return dados

def extrair_partes(soup):
    """Extrai as partes do processo."""
    partes = []
    tabela = soup.find('table', id=re.compile(r'tablePartesPrincipais|tableTodasPartes', re.I))
    
    if tabela:
        for tr in tabela.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= 2:
                tipo = limpar_texto(tds[0].get_text())
                conteudo_nomes = tds[1].get_text(" | ", strip=True)
                partes.append(f"{tipo}: {conteudo_nomes}")
    return partes

def extrair_movimentacoes(soup):
    """Extrai o histórico de movimentações."""
    movs = []
    tabela = soup.find('table', id=re.compile(r'tabelaTodasMovimentacoes|tabelaUltimasMovimentacoes', re.I))
        
    if tabela:
        for tr in tabela.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= 3:
                data = limpar_texto(tds[0].get_text())
                # No e-SAJ, a descrição costuma estar na última coluna ou na penúltima
                descricao = limpar_texto(tds[-1].get_text()) 
                if data and (len(data) == 10 and data[2] == '/'): # Validação simples de data
                    movs.append(f"{data} - {descricao}")
    return movs

def processar_arquivo(caminho_arquivo):
    nome_arquivo = os.path.basename(caminho_arquivo)
    print(f"Lendo: {nome_arquivo}...")
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Erro ao abrir arquivo {nome_arquivo}: {e}")
        return None

    soup = BeautifulSoup(html_content, 'html.parser')
    dados = {}
    
    # --- Extração de Campos ---
    
    # Nº do Processo
    elem_proc = soup.find(id='numeroProcesso')
    dados['n_processo'] = limpar_texto(elem_proc.get_text()) if elem_proc else extrair_valor_por_label(soup, ['Processo:'])

    # Classe / Foro / Vara / Distribuição / Controle / Área
    dados['classe'] = extrair_valor_por_label(soup, ['Classe:'])
    dados['foro'] = extrair_valor_por_label(soup, ['Foro:'])
    dados['vara'] = extrair_valor_por_label(soup, ['Vara:'])
    dados['distribuicao'] = extrair_valor_por_label(soup, ['Distribuição:', 'Data da Distribuição'])
    dados['controle'] = extrair_valor_por_label(soup, ['Controle:'])
    dados['area'] = extrair_valor_por_label(soup, ['Área:'])
    
    # --- Booleanos ---
    texto_total = soup.get_text()
    dados['reu_preso'] = any(x in texto_total for x in ["Situação: Preso", "Réu Preso"])
    
    link_2inst = soup.find('a', href=re.compile(r'sgcr|segundo', re.I))
    dados['consultar_2_instancia'] = bool(link_2inst)

    # --- Listas ---
    dados['dados_delegacia'] = extrair_tabela_chave_valor(soup, "Dados da Delegacia")
    dados['partes_processo'] = extrair_partes(soup)
    dados['movimentacoes'] = extrair_movimentacoes(soup)
    dados['peticoes_diversas'] = extrair_tabela_chave_valor(soup, "Petições diversas")
    dados['audiencias'] = extrair_tabela_chave_valor(soup, "Audiências")
    dados['historico_classes'] = extrair_tabela_chave_valor(soup, "Histórico de classes")
    
    return dados

def main():
    # Define o diretório onde estão os arquivos salvos pelo PyAutoGUI
    diretorio_extratos = os.path.join('.', 'extratos')
    arquivos_html = glob.glob(os.path.join(diretorio_extratos, '*.html'))
    
    if not arquivos_html:
        print(f"Nenhum arquivo encontrado em {diretorio_extratos}")
        return

    lista_processos = []
    for arquivo in arquivos_html:
        res = processar_arquivo(arquivo)
        if res:
            lista_processos.append(res)
            
    # Salva o resultado consolidado
    with open('dados_processos.json', 'w', encoding='utf-8') as f:
        json.dump(lista_processos, f, ensure_ascii=False, indent=4)
        
    print(f"\nFinalizado! {len(lista_processos)} processos extraídos para 'dados_processos.json'.")

if __name__ == "__main__":
    main()