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
            # Exibindo as planilhas para ajudar na identificação
            sheet_names = df.keys()
            st.write("Planilhas encontradas: ", sheet_names)
            
            # Suponhamos que a planilha relevante seja a primeira, vamos pegá-la
            df = df[next(iter(sheet_names))]  # Pega a primeira planilha

            # Limpando e organizando os dados
            df_cleaned = df.iloc[1:, [0, 1, 2, 3, 4, 5, 6, 7]]  # Seleciona as colunas de dados financeiros
            df_cleaned.columns = ['Descrição', '2019', '2020', '2021', '2022', '2023', '2024', '2025']
            
            # Verificando as colunas
            st.write(df_cleaned.head())
            return df_cleaned
        except Exception as e:
            st.error(f"Erro ao ler o arquivo Excel: {e}")
            return None
    elif uploaded_file.type == "application/pdf":
        # Extração de dados de PDF
        with pdfplumber.open(uploaded_file) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
        st.text(text)  # Exibindo o conteúdo extraído do PDF
        return None
    else:
        st.error("Tipo de arquivo não suportado.")
        return None

# Função para calcular todos os indicadores financeiros
def calcular_indicadores(df_cleaned):
    # Identificar as linhas relevantes, como 'ATIVO CIRCULANTE', 'PASSIVO CIRCULANTE', etc.
    ativo_circulante = df_cleaned[df_cleaned['Descrição'] == 'ATIVO CIRCULANTE'].iloc[0, 1:]
    passivo_circulante = df_cleaned[df_cleaned['Descrição'] == 'PASSIVO CIRCULANTE'].iloc[0, 1:]
    
    # Convertendo os valores para números
    ativo_circulante = ativo_circulante.astype(float)
    passivo_circulante = passivo_circulante.astype(float)

    # Calcular a Liquidez Corrente
    liquidez_corrente = ativo_circulante / passivo_circulante

    # Outros cálculos de indicadores financeiros (fictícios para exemplo)
    roe = df_cleaned[df_cleaned['Descrição'] == 'LUCRO LÍQUIDO'].iloc[0, 1:] / df_cleaned[df_cleaned['Descrição'] == 'PATRIMÔNIO LÍQUIDO'].iloc[0, 1:]
    ebitda = df_cleaned[df_cleaned['Descrição'] == 'EBITDA'].iloc[0, 1:] / df_cleaned[df_cleaned['Descrição'] == 'RECEITA LÍQUIDA'].iloc[0, 1:]
    
    # Criar um DataFrame para exibir os resultados
    indicadores = pd.DataFrame({
        'Ano': ['2019', '2020', '2021', '2022', '2023', '2024', '2025'],
        'Ativo Circulante': ativo_circulante,
        'Passivo Circulante': passivo_circulante,
        'Liquidez Corrente': liquidez_corrente,
        'ROE': roe,
        'EBITDA': ebitda
    })
    
    # Exibindo os resultados
    st.write(indicadores)
    return indicadores

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
                df_cleaned = leitura_dados(uploaded_file)
                if df_cleaned is not None:
                    indicadores = calcular_indicadores(df_cleaned)
    
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
