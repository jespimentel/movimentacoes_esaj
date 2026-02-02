import json
import os
from bs4 import BeautifulSoup, Comment

#--- FUNÇÕES DE EXTRAÇÃO DE DADOS ---

def extrair_dados_principais(soup):
    # 1) Número do processo (usando strip para limpar espaços e quebras de linha)
    numero = soup.find(id="numeroProcesso")
    
    # 2-5) Campos que possuem ID direto
    classe = soup.find(id="classeProcesso")
    assunto = soup.find(id="assuntoProcesso")
    foro = soup.find(id="foroProcesso")
    vara = soup.find(id="varaProcesso")
    
    # 6-7) Campos não presentes no trecho enviado (buscando por IDs prováveis)
    distribuicao = soup.find(id="dataHoraDistribuicaoProcesso") 
    controle = soup.find(id="numeroControleProcesso")

    return {
        "Número do Processo": numero.get_text(strip=True) if numero else "Não encontrado",
        "Classe": classe.get_text(strip=True) if classe else "Não encontrado",
        "Assunto": assunto.get_text(strip=True) if assunto else "Não encontrado",
        "Foro": foro.get_text(strip=True) if foro else "Não encontrado",
        "Vara": vara.get_text(strip=True) if vara else "Não encontrado",
        "Distribuição": distribuicao.get_text(strip=True).split()[0] if distribuicao else "não sei",
        "Controle": controle.get_text(strip=True) if controle else "não sei"
    }

def extrair_dados_delegacia(soup):
    # Localiza o corpo da tabela pelo ID
    tbody = soup.find('tbody', id='dadosDaDelegacia')
    
    if not tbody:
        return "não sei"

    # Busca apenas a primeira linha (tr) dentro do corpo
    primeira_linha = tbody.find('tr')
    
    if not primeira_linha:
        return "não sei"

    # Extrai os dados baseado nas classes específicas de cada célula (td)
    return {
        "Documento": primeira_linha.find('td', class_='documento-delegacia').get_text(strip=True),
        "Número": primeira_linha.find('td', class_='numero-delegacia').get_text(strip=True),
        "Distrito policial": primeira_linha.find('td', class_='distrito-delegacia').get_text(strip=True),
        "Município": primeira_linha.find('td', class_='municipio-delegacia').get_text(strip=True)
    }

def extrair_partes_processo(soup):
    # Localiza a tabela de partes pelo ID
    tabela = soup.find('table', id='tablePartesPrincipais')
    
    if not tabela:
        return {"partes": [], "reu_preso": False}

    partes_lista = []
    reu_preso_encontrado = False
    
    # Percorre todas as linhas da tabela
    linhas = tabela.find_all('tr')
    
    for linha in linhas:
        # 1) Extrai o Tipo de Participação (Ex: Autor, Réu, Vítima)
        col_tipo = linha.find('td', class_='label')
        tipo = col_tipo.get_text(strip=True) if col_tipo else "não sei"
        
        # 2) Extrai o Nome da Parte
        col_nome = linha.find('td', class_='nomeParteEAdvogado')
        if col_nome:
            # Pegamos o primeiro texto disponível (nome da parte), ignorando advogados
            textos = list(col_nome.stripped_strings)
            nome = textos[0] if textos else "não sei"
            
            # Removemos "(Histórico da parte)" se estiver no texto do nome
            nome = nome.replace("(Histórico da parte)", "").strip()
            
            # 3) Verifica se existe a marcação de Réu Preso nesta linha
            # Busca pela classe específica ou pelo texto
            if linha.find(class_='reuPreso') or "Réu Preso" in col_nome.get_text():
                reu_preso_encontrado = True
        else:
            nome = "não sei"

        partes_lista.append({
            "Tipo": tipo,
            "Nome": nome
        })
    
    return {
        "partes": partes_lista,
        "reu_preso": reu_preso_encontrado
    }

def extrair_lista_movimentos(soup):
    tbody = soup.find('tbody', id='tabelaTodasMovimentacoes')
    if not tbody:
        return []

    movimentacoes = []
    linhas = tbody.find_all('tr', class_='containerMovimentacao')
    
    for linha in linhas:
        # 1) Data
        col_data = linha.find('td', class_='dataMovimentacao')
        data = col_data.get_text(strip=True) if col_data else "N/C"
        
        # 2) Movimento (Lógica corrigida)
        col_desc = linha.find('td', class_='descricaoMovimentacao')
        if col_desc:
            # stripped_strings gera um iterador com todos os textos dentro da célula
            # O primeiro texto geralmente é o título do movimento
            textos = list(col_desc.stripped_strings)
            movimento_texto = textos[0] if textos else "N/C"
        else:
            movimento_texto = "N/C"

        movimentacoes.append({
            "Data": data,
            "Movimento": movimento_texto
        })
    
    return movimentacoes

def extrair_peticoes(soup):
    # 1) Encontra o comentário que marca o início da seção
    comentario = soup.find(string=lambda text: isinstance(text, Comment) and "Tabela de petições diversas" in text)
    
    if not comentario:
        return []

    # 2) Encontra a próxima tabela após esse comentário
    tabela = comentario.find_next('table')
    
    if not tabela:
        return []

    peticoes = []
    # 3) Busca o corpo da tabela e percorre as linhas
    tbody = tabela.find('tbody')
    if not tbody:
        return []

    linhas = tbody.find_all('tr')
    for linha in linhas:
        colunas = linha.find_all('td')
        
        # Garante que a linha possui as colunas de Data e Tipo
        if len(colunas) >= 2:
            # Extrai o texto ignorando tags como <br> e espaços vazios
            data = colunas[0].get_text(strip=True)
            tipo = colunas[1].get_text(strip=True)

            # Filtra linhas vazias de formatação
            if data or tipo:
                peticoes.append({
                    "Data": data if data else "não sei",
                    "Tipo": tipo if tipo else "não sei"
                })
    
    return peticoes

def extrair_audiencias(soup):
    # 1) Localiza a âncora que serve como marcador
    ancora = soup.find('a', attrs={'name': 'audienciasPlaceHolder'})
    
    if not ancora:
        return []

    # 2) Encontra a próxima tabela após essa âncora
    tabela = ancora.find_next('table')
    
    if not tabela:
        return []

    audiencias = []
    
    # 3) Percorre as linhas do corpo da tabela
    # Note que o seu HTML tem o tbody mas as linhas de cabeçalho estão dentro dele
    linhas = tabela.find_all('tr')
    
    for linha in linhas:
        colunas = linha.find_all('td')
        
        # Ignora linhas que não possuem as 4 colunas de dados (Data, Audiência, Situação, Qt)
        if len(colunas) >= 2:
            data = colunas[0].get_text(strip=True)
            tipo_audiencia = colunas[1].get_text(strip=True)
            
            # Se não encontrar conteúdo de data, tratamos como solicitado
            if not data:
                data = ""

            # Só adicionamos se ao menos o campo de audiência tiver texto 
            # (para evitar a linha de formatação vazia)
            if data or tipo_audiencia:
                audiencias.append({
                    "Data": data,
                    "Audiência": tipo_audiencia if tipo_audiencia else ""
                })
    
    return audiencias

#--- PROCESSAMENTO DOS ARQUIVOS ---
if __name__ == "__main__":
    diretorio = 'extratos'  # Diretório contendo os arquivos HTML
    arquivos_para_processar = [f for f in os.listdir(diretorio) if f.endswith('.html')]
    arquivo_saida = os.path.join('resultados', 'resultado_extracao.json')

    # Lista que armazenará todos os processos
    todos_os_processos = []

    print(f"Iniciando processamento de {len(arquivos_para_processar)} arquivos...")

    for nome_arquivo in arquivos_para_processar:
        caminho_completo = os.path.join(diretorio, nome_arquivo)
        
        try:
            with open(caminho_completo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            soup = BeautifulSoup(conteudo, 'html.parser')
            
            # Execução das extrações
            dados_principais = extrair_dados_principais(soup)
            dados_delegacia = extrair_dados_delegacia(soup)
            partes = extrair_partes_processo(soup)
            movimentos = extrair_lista_movimentos(soup)
            peticoes = extrair_peticoes(soup)
            audiencias = extrair_audiencias(soup)

            # Estrutura um dicionário único para este arquivo (uma linha do futuro DataFrame)
            processo_dict = {
                "arquivo_origem": nome_arquivo,
                **dados_principais,  # Desempacota as chaves (Número, Classe, Assunto, etc)
                "dados_delegacia": dados_delegacia,
                "partes": partes['partes'],
                "reu_preso": partes['reu_preso'],
                "movimentacoes": movimentos,
                "peticoes": peticoes,
                "audiencias": audiencias
            }

            todos_os_processos.append(processo_dict)
            print(f"Processado: {nome_arquivo}")

        except Exception as e:
            print(f"Erro ao processar o arquivo {nome_arquivo}: {e}")

    # Salva a lista completa em formato JSON
    try:
        with open(arquivo_saida, 'w', encoding='utf-8') as json_file:
            json.dump(todos_os_processos, json_file, ensure_ascii=False, indent=4)
        
        print(f"\nSucesso! {len(todos_os_processos)} processos salvos em: {arquivo_saida}")
    except Exception as e:
        print(f"Erro ao salvar arquivo JSON: {e}")

    print("Processamento total concluído.")