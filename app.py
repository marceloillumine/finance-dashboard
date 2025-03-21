
import streamlit as st
import pandas as pd
import sqlite3
import os
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

# Função para análise dos dados (apenas um exemplo de cálculos de indicadores)
def calcular_indicadores(df):
    df['Liquidez Corrente'] = df['Ativo Circulante'] / df['Passivo Circulante']
    df['ROE'] = df['Lucro Líquido'] / df['Patrimônio Líquido']
    df['EBITDA'] = df['EBIT'] / df['Receita Líquida']
    return df

# Função para mostrar o dashboard com os indicadores financeiros
def dashboard(df):
    st.title("Dashboard de Indicadores Financeiros")
    indicadores = calcular_indicadores(df)
    st.write(indicadores)
    st.bar_chart(indicadores[['Liquidez Corrente', 'ROE', 'EBITDA']])

# Função principal do Streamlit
def main():
    st.title("Illumine - Análise de Indicadores Financeiros")
    # Exibir o versículo de Provérbios
    versiculo = versiculo_do_dia()
    st.subheader(f"Versículo do Dia: {versiculo}")
    
    # Layout de duas colunas para exibir o cadastro e a seleção da empresa
    col1, col2 = st.columns(2)

    with col1:
        # Mostrar empresas cadastradas
        st.subheader("Empresas Cadastradas")
        empresas = obter_empresas()
        empresas_names = [empresa[1] for empresa in empresas]
        empresa_selecionada = st.selectbox("Escolha uma empresa", empresas_names)
        
        if empresa_selecionada:
            empresa_id = empresas[empresas_names.index(empresa_selecionada)][0]
            uploaded_file = upload_arquivo(empresa_id)
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                dashboard(df)
    
    with col2:
        # Cadastro de nova empresa
        st.subheader("Cadastro de Nova Empresa")
        nome_cliente = st.text_input("Nome do Cliente")
        cnpj_cliente = st.text_input("CNPJ")
        email_cliente = st.text_input("E-mail")
        
        if st.button("Cadastrar"):
            if nome_cliente and cnpj_cliente and email_cliente:
                cadastro_empresa(nome_cliente, cnpj_cliente, email_cliente)
                st.success(f"Empresa {nome_cliente} cadastrada com sucesso!")
            else:
                st.error("Por favor, preencha todos os campos.")

# Rodar a aplicação
if __name__ == "__main__":
    setup_db()
    main()
