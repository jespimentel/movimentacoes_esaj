import pandas as pd

df = pd.read_excel('data.xlsx', engine='openpyxl')
df = df.dropna()

# Instaurações em 2025 e 2026
df_recentes = df[df['Instauração'] > '2025-01-01']

# IPs únicos
df_recentes_unicos = df_recentes.drop_duplicates(subset=['Nº Processo | SAJMP'])

lista_de_links = df_recentes_unicos['e-SAJ'].to_list()
print(f'Foram extraídos {len(lista_de_links)} links únicos.')

with open('links.txt', 'w') as f:
    for link in lista_de_links:
      f.writelines(link + '\n')

print("Links salvos em 'links.txt'.")