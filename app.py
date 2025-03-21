
import pandas as pd
import streamlit as st
import sqlite3
import random
import pdfplumber
from datetime import datetime

# Função para gerar o versículo aleatório de Provérbios
def versiculo_do_dia():
    versiculos = [
        "O início da sabedoria é o temor do Senhor; bom entendimento têm todos os que praticam os seus mandamentos. O seu louvor subsiste para sempre. (Salmos 111:10)",
        "Filho meu, não te esqueças dos meus ensinos, e o teu coração guarde os meus mandamentos. (Provérbios 3:1)",
        "Confia no Senhor de todo o teu coração e não te estribes no teu próprio entendimento. (Provérbios 3:5)"
    ]
    return random.choice(versiculos)

# Função para conectar ao banco de dados SQLite
def connect_to_db():
    conn = sqlite3.connect("empresas.db")
    return conn

# Função para criar a tabela de empresas e de arquivos no banco de dados
def setup_db():
    conn = connect_to_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS empresas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT,
                    cnpj TEXT,
                    email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS arquivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER,
                    arquivo_nome TEXT,
                    arquivo_blob BLOB,
                    FOREIGN KEY(empresa_id) REFERENCES empresas(id))''')
    conn.commit()
    conn.close()

# Função para cadastrar uma nova empresa
def cadastro_empresa(nome, cnpj, email):
    conn = connect_to_db()
    c = conn.cursor()
    c.execute("INSERT INTO empresas (nome, cnpj, email) VALUES (?, ?, ?)", (nome, cnpj, email))
    conn.commit()
    conn.close()

# Função para pegar todas as empresas cadastradas
def obter_empresas():
    conn = connect_to_db()
    c = conn.cursor()
    c.execute("SELECT id, nome FROM empresas")
    empresas = c.fetchall()
    conn.close()
    return empresas

# Função para upload de arquivos (PDF ou Excel)
def upload_arquivo(empresa_id):
    uploaded_file = st.file_uploader(f"Escolha um arquivo para a empresa {empresa_id}", type=['xlsx', 'pdf'])
    if uploaded_file is not None:
        # Salvar o arquivo no banco de dados
        conn = connect_to_db()
        c = conn.cursor()
        file_data = uploaded_file.read()
        c.execute("INSERT INTO arquivos (empresa_id, arquivo_nome, arquivo_blob) VALUES (?, ?, ?)",
                  (empresa_id, uploaded_file.name, file_data))
        conn.commit()
        conn.close()
        return uploaded_file
    return None

# Função para leitura de dados do arquivo Excel
def leitura_dados(uploaded_file):
    if uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        try:
            df = pd.read_excel(uploaded_file, sheet_name=None)  # Carregar todas as planilhas
            sheet_names = df.keys()
            st.write("Planilhas encontradas: ", sheet_names)
            df = df[next(iter(sheet_names))]  # Pega a primeira planilha
            st.write(f"Primeiras linhas do arquivo:")
            st.write(df.head())
            st.write(f"Colunas disponíveis: {df.columns.tolist()}")
            st.write(f"Número de linhas: {df.shape[0]}, Número de colunas: {df.shape[1]}")

            # Limpeza dos dados
            df_cleaned = df[['Descrição', '2019', '2020', '2021', '2022', '2023', '2024']]
            df_cleaned.columns = ['Descrição', '2019', '2020', '2021', '2022', '2023', '2024']
            return df_cleaned
        except Exception as e:
            st.error(f"Erro ao ler o arquivo Excel: {e}")
            return None
    elif uploaded_file.type == "application/pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
        st.text(text)
        return None
    else:
        st.error("Tipo de arquivo não suportado.")
        return None

# Função principal do Streamlit
def main():
    st.set_page_config(page_title="Illumine - Análise Financeira", page_icon=":chart_with_upwards_trend:", layout="wide")
    
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("<h1 style='text-align: center; font-size: 35px;'>Illumine</h1>", unsafe_allow_html=True)
        versiculo = versiculo_do_dia()
        st.markdown(f"<h3 style='text-align: center; font-size: 14px; color: #555;'>"{versiculo}"</h3>", unsafe_allow_html=True)
    
    with col2:
        st.subheader("Empresas Cadastradas")
        empresas = obter_empresas()
        empresas_names = [empresa[1] for empresa in empresas]
        empresa_selecionada = st.selectbox("Escolha uma empresa", empresas_names)
        
        if empresa_selecionada:
            empresa_id = empresas[empresas_names.index(empresa_selecionada)][0]
            uploaded_file = upload_arquivo(empresa_id)
            if uploaded_file:
                df_cleaned = leitura_dados(uploaded_file)
                if df_cleaned is not None:
                    st.write(df_cleaned)
                    
# Rodar a aplicação
if __name__ == "__main__":
    setup_db()
    main()
    st.markdown(f"<h3 style='text-align: center; font-size: 14px; color: #555;'>\"{versiculo}\"</h3>", unsafe_allow_html=True)
