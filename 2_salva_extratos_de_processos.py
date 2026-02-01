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
        # Lê as linhas, remove espaços em branco e ignora linhas vazias
        links = [linha.strip() for linha in f.readlines() if linha.strip()]
    return links

def salvar_source_code_automatizado(arquivo_entrada):
    links = ler_links_do_arquivo(arquivo_entrada)
    
    if not links:
        print("Nenhum link para processar.")
        return

    print(f"Total de links encontrados: {len(links)}")
    print("Mude para o navegador agora! A automação começa em 5 segundos...")
    time.sleep(5)

    for i, link in enumerate(links):
        try:
            # 1. Abre nova aba e acessa o link
            pyautogui.hotkey('ctrl', 't')
            time.sleep(0.5)
            pyperclip.copy(link)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            
            # Espera carregar a página original (ajuste se o site for pesado)
            time.sleep(4) 

            # 2. Abre o código fonte (View Source)
            pyautogui.hotkey('ctrl', 'u')
            time.sleep(2) 

            # 3. Comando Salvar
            pyautogui.hotkey('ctrl', 's')
            time.sleep(1.5)

            # 4. Gera nome único (Data_Hora_Indice)
            # O índice 'i' garante ordem, o timestamp garante que não sobrescreva downloads antigos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"pag_{i+1}_{timestamp}"
            pyperclip.copy(nome_arquivo)
            
            # Cola o nome e confirma
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            
            # 5. Fecha as abas (a do código fonte e a do site original)
            time.sleep(1.5) # Espera o download iniciar
            pyautogui.hotkey('ctrl', 'w') # Fecha aba do código fonte
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'w') # Fecha aba do site

            print(f"[{i+1}/{len(links)}] Sucesso: {link}")

        except Exception as e:
            print(f"Erro ao processar o link {link}: {e}")

if __name__ == "__main__":
    salvar_source_code_automatizado("links.txt")