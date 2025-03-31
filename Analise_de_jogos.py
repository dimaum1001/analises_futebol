import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import numpy as np
from scipy.stats import poisson

# Variável global para armazenar o DataFrame
df_global = None

def carregar_csv():
    arquivo = filedialog.askopenfilename(filetypes=[("Arquivos CSV", "*.csv")])
    if not arquivo:
        return
    # Carregar o CSV usando pandas
    df = pd.read_csv(arquivo)
    # Dicionário para renomear os cabeçalhos
    nomes_personalizados = {
        "Date": "Data",
        "HomeTeam": "Time Casa",
        "AwayTeam": "Time Visitante",
        "FTHG": "Gols Casa FT",
        "FTAG": "Gols Visitante FT",
        "FTR": "Resultado",
        "HTHG": "HT Gols Casa",
        "HTAG": "HT Gols Visitante",
        "HTR": "HT Resultado",
        "HS": "Chutes Casa",
        "AS": "Chutes Visitante",
        "HST": "Chutes no Gol Casa",
        "AST": "Chutes no Gol Visitante",
        "HF": "Faltas Casa",
        "AF": "Faltas Visitante",
        "HC": "Escanteios Casa",
        "AC": "Escanteios Visitante",        
        "PSH": "odds home win",
        "PSD": "odds draw",
        "PSA": "odds away win",
        "PH": "odds home win 2",
        "PD": "odds draw 2",
        "PA": "odds away win 2"
    }
    # Renomear colunas existentes
    df.rename(columns=nomes_personalizados, inplace=True)
    # Colunas necessárias para o funcionamento do aplicativo
    colunas_essenciais = {'Time Casa', 'Time Visitante', 'Gols Casa FT', 'Gols Visitante FT', 'odds home win', 'odds draw', 'odds away win'}
    # Verificar se as colunas essenciais estão presentes
    if not colunas_essenciais.issubset(df.columns):
        messagebox.showerror("Erro", "O arquivo CSV deve conter as colunas: Time Casa, Time Visitante, Gols Casa FT, Gols Visitante FT, odds home win, odds draw, odds away win.")
        return
    # Colunas para renomear (todas as colunas do dicionário)
    colunas_retencao = list(nomes_personalizados.values())
    # Verificar se as colunas adicionais existem e ajustar a lista de retenção
    colunas_adicionais = {'odds home win 2', 'odds draw 2', 'odds away win 2'}
    colunas_presentes = set(df.columns)
    colunas_retencao = [col for col in colunas_retencao if col in colunas_presentes]
    # Remover colunas não renomeadas
    df = df[colunas_retencao]
    # Calcular probabilidades ajustadas para remover o juice
    if 'odds home win 2' in df.columns:
        df['prob_home'] = 1 / df['odds home win 2']
    else:
        df['prob_home'] = 1 / df['odds home win']
    if 'odds draw 2' in df.columns:
        df['prob_draw'] = 1 / df['odds draw 2']
    else:
        df['prob_draw'] = 1 / df['odds draw']
    if 'odds away win 2' in df.columns:
        df['prob_away'] = 1 / df['odds away win 2']
    else:
        df['prob_away'] = 1 / df['odds away win']
    df['total_prob'] = df['prob_home'] + df['prob_draw'] + df['prob_away']
    df['adjusted_prob_home'] = (df['prob_home'] / df['total_prob']) * 100
    df['adjusted_prob_away'] = (df['prob_away'] / df['total_prob']) * 100
    # Limpar Treeview
    tree.delete(*tree.get_children())   
    # Inserir cabeçalhos na Treeview
    tree["columns"] = list(df.columns)
    tree["show"] = "headings"
    for coluna in df.columns:
        tree.heading(coluna, text=coluna)
        tree.column(coluna, width=120, 
                   anchor=tk.E if coluna.startswith('adjusted') or coluna.startswith('prob') else tk.W)
    # Inserir os dados na Treeview com formatação
    for _, row in df.iterrows():
        # Converter as últimas 6 colunas para duas casas decimais
        values = list(row)
        for i in range(-6, 0):  # Últimos 6 elementos
            if isinstance(values[i], (int, float)):
                values[i] = f"{values[i]:.2f}"
        tree.insert("", "end", values=values)
    # Salvar o dataframe globalmente
    global df_global
    df_global = df

def limpar():
    tree.delete(*tree.get_children())

def abrir_estatisticas():
    if df_global is None:
        messagebox.showwarning("Erro", "Carregue um arquivo CSV primeiro.")
        return
    estatisticas_window = tk.Toplevel(root)
    estatisticas_window.title("Melhores Estatísticas dos Times em Casa")
    melhores_times = df_global.groupby('Time Casa').agg(
        Vitórias=('Resultado', lambda x: (x == 'H').sum()),
        Gols=('Gols Casa FT', 'sum')
    ).reset_index()
    melhores_times = melhores_times.sort_values(by=['Vitórias', 'Gols'], ascending=False)
    tree_estatisticas = ttk.Treeview(estatisticas_window)
    tree_estatisticas.pack(expand=True, fill="both")
    tree_estatisticas["columns"] = ['Time', 'Vitórias', 'Gols']
    tree_estatisticas["show"] = "headings"
    tree_estatisticas.heading('Time', text="Time")
    tree_estatisticas.heading('Vitórias', text="Vitórias")
    tree_estatisticas.heading('Gols', text="Gols")
    for _, row in melhores_times.iterrows():
        tree_estatisticas.insert("", "end", values=(row['Time Casa'], row['Vitórias'], row['Gols']))

def abrir_odds_home_win():
    if df_global is None:
        messagebox.showwarning("Erro", "Carregue um arquivo CSV primeiro.")
        return
    odds_window = tk.Toplevel(root)
    odds_window.title("Times ordenados por probabilidade home win (%)")
    # Calcular a média das probabilidades ajustadas por time
    odds_media = df_global.groupby('Time Casa').agg(
        Media_Prob=('adjusted_prob_home', 'mean')
    ).reset_index()
    odds_media = odds_media.sort_values(by='Media_Prob', ascending=False)
    tree_odds = ttk.Treeview(odds_window)
    tree_odds.pack(expand=True, fill="both")
    tree_odds["columns"] = ['Time', 'Probabilidade (%)']
    tree_odds["show"] = "headings"
    tree_odds.heading('Time', text="Time")
    tree_odds.heading('Probabilidade (%)', text="Probabilidade de Vitória (%)")
    for _, row in odds_media.iterrows():
        formatted_prob = f"{row['Media_Prob']:.2f}%"
        tree_odds.insert("", "end", values=(row['Time Casa'], formatted_prob))

def abrir_odds_away_win():
    if df_global is None:
        messagebox.showwarning("Erro", "Carregue um arquivo CSV primeiro.")
        return
    odds_window = tk.Toplevel(root)
    odds_window.title("Times ordenados por probabilidade away win (%)")
    # Calcular a média das probabilidades ajustadas por time visitante
    odds_media = df_global.groupby('Time Visitante').agg(
        Media_Prob=('adjusted_prob_away', 'mean')
    ).reset_index()
    odds_media = odds_media.sort_values(by='Media_Prob', ascending=False)
    tree_odds = ttk.Treeview(odds_window)
    tree_odds.pack(expand=True, fill="both")
    tree_odds["columns"] = ['Time', 'Probabilidade (%)']
    tree_odds["show"] = "headings"
    tree_odds.heading('Time', text="Time")
    tree_odds.heading('Probabilidade (%)', text="Probabilidade de Vitória (%)")
    for _, row in odds_media.iterrows():
        formatted_prob = f"{row['Media_Prob']:.2f}%"
        tree_odds.insert("", "end", values=(row['Time Visitante'], formatted_prob))

def abrir_probabilidades_geral():
    if df_global is None:
        messagebox.showwarning("Erro", "Carregue um arquivo CSV primeiro.")
        return
    geral_window = tk.Toplevel(root)
    geral_window.title("Probabilidades Gerais")
    # Calcular médias para mandante e visitante
    home_probs = df_global.groupby('Time Casa').agg(
        Media_Mandante=('adjusted_prob_home', 'mean')
    ).reset_index()
    home_probs.rename(columns={'Time Casa': 'Time'}, inplace=True)
    away_probs = df_global.groupby('Time Visitante').agg(
        Media_Visitante=('adjusted_prob_away', 'mean')
    ).reset_index()
    away_probs.rename(columns={'Time Visitante': 'Time'}, inplace=True)
    # Juntar as probabilidades
    merged = pd.merge(home_probs, away_probs, on='Time', how='outer')
    merged.fillna(0, inplace=True)  # Substituir NaN por 0
    # Calcular a média geral
    merged['Media_Geral'] = (merged['Media_Mandante'] + merged['Media_Visitante']) / 2
    # Ordenar pelo maior valor de Média Geral
    merged = merged.sort_values(
        by=['Media_Geral', 'Media_Mandante', 'Media_Visitante'],
        ascending=[False, False, False]
    )
    # Criar Treeview com a nova coluna
    tree_geral = ttk.Treeview(geral_window, 
                             columns=['Time', 'Mandante', 'Visitante', 'Geral'])
    tree_geral.pack(expand=True, fill="both")
    # Definir cabeçalhos
    tree_geral.heading('Time', text="Time")
    tree_geral.heading('Mandante', text="Prob. Mandante (%)")
    tree_geral.heading('Visitante', text="Prob. Visitante (%)")
    tree_geral.heading('Geral', text="Média Geral (%)")
    # Inserir dados formatados
    for _, row in merged.iterrows():
        tree_geral.insert("", "end", 
                         values=(
                             row['Time'], 
                             f"{row['Media_Mandante']:.2f}%",
                             f"{row['Media_Visitante']:.2f}%",
                             f"{row['Media_Geral']:.2f}%"
                         ))

def abrir_chutes_ao_gol():
    if df_global is None:
        messagebox.showwarning("Erro", "Carregue um arquivo CSV primeiro.")
        return
    chutes_window = tk.Toplevel(root)
    chutes_window.title("Melhores Times por Chutes ao Gol")
    # Calcular médias de chutes ao gol para mandante e visitante
    home_chutes = df_global.groupby('Time Casa').agg(
        Media_Casa=('Chutes no Gol Casa', 'mean')
    ).reset_index()
    home_chutes.rename(columns={'Time Casa': 'Time'}, inplace=True)
    away_chutes = df_global.groupby('Time Visitante').agg(
        Media_Visitante=('Chutes no Gol Visitante', 'mean')
    ).reset_index()
    away_chutes.rename(columns={'Time Visitante': 'Time'}, inplace=True)
    # Juntar as médias de chutes ao gol
    merged = pd.merge(home_chutes, away_chutes, on='Time', how='outer')
    merged.fillna(0, inplace=True)  # Substituir NaN por 0
    # Calcular a média geral de chutes ao gol
    merged['Media_Geral'] = (merged['Media_Casa'] + merged['Media_Visitante']) / 2
    # Ordenar pelo maior valor de Média Geral de chutes ao gol
    merged = merged.sort_values(
        by=['Media_Geral', 'Media_Casa', 'Media_Visitante'],
        ascending=[False, False, False]
    )
    # Criar Treeview com as colunas relevantes
    tree_chutes = ttk.Treeview(chutes_window, 
                              columns=['Time', 'Casa', 'Visitante', 'Geral'])
    tree_chutes.pack(expand=True, fill="both")
    # Definir cabeçalhos
    tree_chutes.heading('Time', text="Time")
    tree_chutes.heading('Casa', text="Média de Chutes ao Gol (Casa)")
    tree_chutes.heading('Visitante', text="Média de Chutes ao Gol (Visitante)")
    tree_chutes.heading('Geral', text="Média Geral de Chutes ao Gol")
    # Inserir dados formatados
    for _, row in merged.iterrows():
        tree_chutes.insert("", "end", 
                          values=(
                              row['Time'], 
                              f"{row['Media_Casa']:.2f}",
                              f"{row['Media_Visitante']:.2f}",
                              f"{row['Media_Geral']:.2f}"
                          ))

def calcular_medias_gols():
    if df_global is None:
        messagebox.showwarning("Erro", "Carregue um arquivo CSV primeiro.")
        return
    # Calcular médias de gols para mandante e visitante
    home_gols = df_global.groupby('Time Casa').agg(
        Media_Gols_Casa=('Gols Casa FT', 'mean')
    ).reset_index()
    home_gols.rename(columns={'Time Casa': 'Time'}, inplace=True)
    away_gols = df_global.groupby('Time Visitante').agg(
        Media_Gols_Visitante=('Gols Visitante FT', 'mean')
    ).reset_index()
    away_gols.rename(columns={'Time Visitante': 'Time'}, inplace=True)
    # Juntar as médias de gols
    merged = pd.merge(home_gols, away_gols, on='Time', how='outer')
    merged.fillna(0, inplace=True)
    # Calcular a média geral de gols
    merged['Media_Gols_Geral'] = (merged['Media_Gols_Casa'] + merged['Media_Gols_Visitante']) / 2
    # Ordenar pelo maior valor de Média Geral de gols
    merged = merged.sort_values(
        by=['Media_Gols_Geral', 'Media_Gols_Casa', 'Media_Gols_Visitante'],
        ascending=[False, False, False]
    )
    return merged

def abrir_modelo_estatistico():
    if df_global is None:
        messagebox.showwarning("Erro", "Carregue um arquivo CSV primeiro.")
        return
    # Verificar se as colunas necessárias estão presentes
    colunas_essenciais = {'Time Casa', 'Time Visitante', 'Gols Casa FT', 'Gols Visitante FT', 'odds home win', 'odds draw', 'odds away win'}
    if not colunas_essenciais.issubset(df_global.columns):
        messagebox.showerror("Erro", "O arquivo CSV deve conter as colunas: Time Casa, Time Visitante, Gols Casa FT, Gols Visitante FT, odds home win, odds draw, odds away win.")
        return
    # Calcular médias de gols
    medias_gols = calcular_medias_gols()
    # Lista de times disponíveis
    times_disponiveis = medias_gols['Time'].tolist()
    # Janela para seleção de times
    modelo_window = tk.Toplevel(root)
    modelo_window.title("Modelo Estatístico de Comparação")
    # Frames para organizar os Comboboxes
    frame_times = []
    num_combobox = 20
    for i in range(num_combobox):
        frame = tk.Frame(modelo_window)
        frame.grid(row=i // 2, column=i % 2, padx=10, pady=5, sticky="w")
        lbl_time = tk.Label(frame, text=f"Time {i+1}:")
        lbl_time.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        cb_time = ttk.Combobox(frame, values=times_disponiveis, width=30)
        cb_time.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        frame_times.append((lbl_time, cb_time))
    # Botão para comparar os times
    btn_comparar = tk.Button(modelo_window, text="Comparar Times", command=lambda: comparar_times(frame_times, modelo_window))
    btn_comparar.grid(row=(num_combobox // 2) + 1, column=0, columnspan=2, padx=10, pady=10, sticky="we")

def comparar_times(frame_times, modelo_window):
    times_selecionados = [cb.get() for _, cb in frame_times]
    times_selecionados = [time for time in times_selecionados if time]  # Remover seleções vazias
    if len(times_selecionados) % 2 != 0:
        messagebox.showwarning("Erro", "Selecione um número par de times (2, 4, 6, ..., 20).")
        return
    if len(set(times_selecionados)) != len(times_selecionados):
        messagebox.showwarning("Erro", "Os times selecionados devem ser diferentes.")
        return
    # Calcular médias de gols
    medias_gols = calcular_medias_gols()
    # Janela para exibir os resultados
    resultados_window = tk.Toplevel(modelo_window)
    resultados_window.title("Resultados da Comparação")
    # Criar Treeview para exibir as probabilidades
    tree_resultados = ttk.Treeview(resultados_window, 
                                  columns=['Jogo', 'Time Mandante', 'Time Visitante', 'Prob. Mandante (%)', 'Prob. Empate (%)', 'Prob. Visitante (%)'])
    tree_resultados.pack(expand=True, fill="both")
    tree_resultados.heading('Jogo', text="Jogo")
    tree_resultados.heading('Time Mandante', text="Time Mandante")
    tree_resultados.heading('Time Visitante', text="Time Visitante")
    tree_resultados.heading('Prob. Mandante (%)', text="Prob. Mandante (%)")
    tree_resultados.heading('Prob. Empate (%)', text="Prob. Empate (%)")
    tree_resultados.heading('Prob. Visitante (%)', text="Prob. Visitante (%)")
    # Inserir dados formatados
    for i, (time1, time2) in enumerate(zip(times_selecionados[::2], times_selecionados[1::2])):
        if time1 and time2:
            media_gols_time1 = medias_gols.loc[medias_gols['Time'] == time1, 'Media_Gols_Casa'].values[0]
            media_gols_time2 = medias_gols.loc[medias_gols['Time'] == time2, 'Media_Gols_Visitante'].values[0]
            # Cálculo das probabilidades usando Poisson
            lambda_home = media_gols_time1
            lambda_away = media_gols_time2
            max_goals = 10  # Considerar até 10 gols
            home_goals = np.arange(max_goals + 1)
            away_goals = np.arange(max_goals + 1)
            # Matriz de probabilidades
            probs = np.outer(poisson.pmf(home_goals, lambda_home), poisson.pmf(away_goals, lambda_away))
            # Calcular probabilidades de resultado
            prob_home_win = np.sum(np.tril(probs, k=-1))
            prob_draw = np.sum(np.diag(probs))
            prob_away_win = np.sum(np.triu(probs, k=1))
            # Inserir dados na Treeview
            tree_resultados.insert("", "end", 
                                 values=(
                                     f"Jogo {i+1}",
                                     time1,
                                     time2,
                                     f"{prob_home_win * 100:.2f}%",
                                     f"{prob_draw * 100:.2f}%",
                                     f"{prob_away_win * 100:.2f}%"
                                 ))

# Criar a janela principal
root = tk.Tk()
root.title("Visualizador de CSV")
root.state("zoomed")

# Frame para os botões
frame_botoes = tk.Frame(root)
frame_botoes.pack(fill="x", pady=5)
btn_carregar = tk.Button(frame_botoes, text="Carregar CSV", command=carregar_csv)
btn_carregar.pack(side="left", padx=10, pady=5)
btn_limpar = tk.Button(frame_botoes, text="Limpar Dados", command=limpar)
btn_limpar.pack(side="left", padx=10, pady=5)
btn_estatisticas = tk.Button(frame_botoes, text="Melhores Estatísticas", command=abrir_estatisticas)
btn_estatisticas.pack(side="left", padx=10, pady=5)
btn_odds_home = tk.Button(frame_botoes, text="Probabilidades Home Win", command=abrir_odds_home_win)
btn_odds_home.pack(side="left", padx=10, pady=5)
btn_odds_away = tk.Button(frame_botoes, text="Probabilidades Away Win", command=abrir_odds_away_win)
btn_odds_away.pack(side="left", padx=10, pady=5)
btn_odds_geral = tk.Button(frame_botoes, text="Probabilidades Gerais", command=abrir_probabilidades_geral)
btn_odds_geral.pack(side="left", padx=10, pady=5)
btn_chutes_ao_gol = tk.Button(frame_botoes, text="Melhores Times por Chutes ao Gol", command=abrir_chutes_ao_gol)
btn_chutes_ao_gol.pack(side="left", padx=10, pady=5)
btn_modelo_estatistico = tk.Button(frame_botoes, text="Modelo Estatístico", command=abrir_modelo_estatistico)
btn_modelo_estatistico.pack(side="left", padx=10, pady=5)

# Frame para a Treeview
frame_tabela = tk.Frame(root)
frame_tabela.pack(expand=True, fill="both")
scroll_y = tk.Scrollbar(frame_tabela, orient="vertical")
scroll_x = tk.Scrollbar(frame_tabela, orient="horizontal")
tree = ttk.Treeview(frame_tabela, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
scroll_y.config(command=tree.yview)
scroll_x.config(command=tree.xview)
scroll_y.pack(side="right", fill="y")
scroll_x.pack(side="bottom", fill="x")
tree.pack(expand=True, fill="both")

df_global = None
root.mainloop()