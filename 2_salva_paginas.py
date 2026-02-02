import pyautogui
import time
import pyperclip
import os
from datetime import datetime

def ler_links_do_arquivo(caminho_arquivo):
    """Lê links de um arquivo .txt, um por linha."""
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return []
    
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        links = [linha.strip() for linha in f.readlines() if linha.strip()]
    return links

def salvar_html_automatizado(arquivo_entrada):
    links = ler_links_do_arquivo(arquivo_entrada)
    
    if not links:
        print("Nenhum link para processar.")
        return

    print(f"Total de links encontrados: {len(links)}")
    print("Mude para o navegador agora! A automação começa em 5 segundos...")
    time.sleep(5)

    for i, link in enumerate(links):
        try:
            # 1. Abre nova aba e acessa o link do processo
            pyautogui.hotkey('ctrl', 't')
            time.sleep(0.5)
            pyperclip.copy(link)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            
            # Espera carregar a página (Aumente se a conexão for lenta ou usar Token)
            # Como você usa token, talvez precise de mais tempo para a autenticação automática
            time.sleep(5) 

            # 2. Comando Salvar Direto (Ctrl + S)
            # Isso salva a página real, não o "view-source"
            pyautogui.hotkey('ctrl', 's')
            time.sleep(2) # Espera a janela de diálogo do Windows abrir

            # 3. Gera nome único para o arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"processo_{i+1}_{timestamp}"
            pyperclip.copy(nome_arquivo)
            
            # 4. Preenche o nome e garante o tipo "Somente HTML"
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            
            # Simula um TAB para ir ao campo "Tipo" e garantir "Página Web, Somente HTML"
            # Geralmente é a primeira ou segunda opção após o nome
            pyautogui.press('tab')
            time.sleep(0.3)
            pyautogui.press('up') # Sobe para a próxima opção da lista
            time.sleep(0.3)
            pyautogui.press('up') # Sobe para a próxima opção da lista (HTML único)
            time.sleep(0.3)
            
            # Confirma o salvamento
            pyautogui.press('enter')
            
            # 5. Fecha a aba do processo e aguarda o próximo
            # Espera um pouco mais para garantir que o Windows iniciou a gravação do arquivo
            time.sleep(2) 
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(1)

            print(f"[{i+1}/{len(links)}] Salvo com sucesso: {nome_arquivo}")

        except Exception as e:
            print(f"Erro ao processar o link {link}: {e}")

if __name__ == "__main__":
    # Certifique-se de que o arquivo 'links.txt' está na mesma pasta
    salvar_html_automatizado("links.txt")