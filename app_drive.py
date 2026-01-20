# Código corrigido do app_drive.py para funcionar no Streamlit Cloud com secrets
folder_id = "1bwU96yqfhAhVW7i0GP_USVddd-KIh39d"

updated_code = f"""
import streamlit as st
import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
import json
from streamlit.runtime.secrets import secrets

@st.cache_resource
def authenticate_drive():
    # Criar arquivo temporário com conteúdo do client_secrets.json vindo dos Secrets
    with open("client_secrets.json", "w") as f:
        f.write(secrets["client_secrets.json"])

    gauth = GoogleAuth()
    gauth.LoadClientConfigFile("client_secrets.json")
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive

drive = authenticate_drive()

FOLDER_ID = "{folder_id}"

def get_file_by_title(title):
    file_list = drive.ListFile({{
        'q': f"title='{{title}}' and '{{FOLDER_ID}}' in parents and trashed=false"
    }}).GetList()
    return file_list[0] if file_list else None

def download_csv(file_title, local_name):
    file = get_file_by_title(file_title)
    if file:
        file.GetContentFile(local_name)
        return pd.read_csv(local_name)
    else:
        st.error(f"Arquivo '{{file_title}}' não encontrado na pasta do Google Drive.")
        return pd.DataFrame()

def upload_csv(local_name, file_title):
    file = get_file_by_title(file_title)
    if file:
        file.SetContentFile(local_name)
        file.Upload()
    else:
        file = drive.CreateFile({{'title': file_title, 'parents': [{{'id': FOLDER_ID}}]}})
        file.SetContentFile(local_name)
        file.Upload()

stock_filename = "base_stock_inicial.csv"
insem_filename = "inseminacoes_iniciais.csv"

stock_df = download_csv(stock_filename, "stock_temp.csv")
inseminacoes_df = download_csv(insem_filename, "insem_temp.csv")

st.set_page_config(page_title="Gestor de Sémen - Embriovet", layout="wide")
st.title("📊 Gestor de Sémen - Embriovet (Google Drive)")

menu = st.sidebar.radio("Navegar", ["📦 Consultar Stock", "📝 Registrar Inseminação", "📈 Relatórios"])

if menu == "📦 Consultar Stock":
    st.header("📦 Stock Disponível por Garanhão")
    garanhao = st.selectbox("Selecione o Garanhão", sorted(stock_df["Garanhão"].dropna().unique()))
    qualidade_min = st.slider("Filtrar por qualidade mínima (%)", 0, 100, 0)

    df_filtrado = stock_df[
        (stock_df["Garanhão"] == garanhao) &
        (stock_df["Qualidade (%)"].fillna(0) >= qualidade_min) &
        (stock_df["Existência Atual"] > 0)
    ]
    st.dataframe(df_filtrado, use_container_width=True)

elif menu == "📝 Registrar Inseminação":
    st.header("📝 Registro de Inseminação")

    garanhao = st.selectbox("Garanhão", sorted(stock_df["Garanhão"].dropna().unique()))
    protocolos = stock_df[(stock_df["Garanhão"] == garanhao) & (stock_df["Existência Atual"] > 0)]

    if not protocolos.empty:
        data = st.date_input("Data da Inseminação")
        egua = st.text_input("Nome da Égua")

        st.markdown("### Selecionar protocolo e palhetas gastas")
        new_records = []
        for idx, row in protocolos.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{{row['Data de Produção (Embriovet)'] or row['Origem Externa / Referência']}} - Existência: {{row['Existência Atual']}}")
            with col2:
                qtd = st.number_input(f"Gastas ({{idx}})", min_value=0, max_value=int(row['Existência Atual']), step=1, key=f"qtd_{{idx}}")
                if qtd > 0:
                    new_records.append({{
                        "Garanhão": garanhao,
                        "Data Inseminação": data,
                        "Égua": egua,
                        "Protocolo (Data/Origem)": row["Data de Produção (Embriovet)"] or row["Origem Externa / Referência"],
                        "Palhetas Gastas": qtd
                    }})
                    stock_df.at[idx, "Existência Atual"] -= qtd

        if st.button("💾 Registrar Inseminação") and egua and new_records:
            new_df = pd.DataFrame(new_records)
            inseminacoes_df = pd.concat([inseminacoes_df, new_df], ignore_index=True)
            inseminacoes_df.to_csv("insem_temp.csv", index=False)
            stock_df.to_csv("stock_temp.csv", index=False)
            upload_csv("insem_temp.csv", insem_filename)
            upload_csv("stock_temp.csv", stock_filename)
            st.success("Inseminação registrada e dados atualizados com sucesso!")
    else:
        st.warning("Nenhum protocolo com stock disponível para este garanhão.")

elif menu == "📈 Relatórios":
    st.header("📈 Relatório de Inseminações")
    st.dataframe(inseminacoes_df.sort_values(by="Data Inseminação", ascending=False), use_container_width=True)
"""

updated_code
