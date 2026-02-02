import streamlit as st
import pandas as pd
import psycopg2

# 🔐 Conexão com PostgreSQL

def get_connection():
    return psycopg2.connect(
        dbname="embriovet",
        user="postgres",
        password="123",
        host="localhost",
        port="5432"
    )

# 📥 Carregamento de dados

def carregar_donos():
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM dono", conn)
    return df

def atualizar_dono_stock(estoque_id, novo_dono_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE estoque_dono SET dono_id = %s WHERE id = %s
    """, (novo_dono_id, estoque_id))
    conn.commit()
    cur.close()
    conn.close()


def carregar_estoque():
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM estoque_dono", conn)
    return df




def carregar_inseminacoes():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM inseminacoes", conn)
    conn.close()
    return df

# 💾 Inserção de novo stock

def inserir_stock(dados):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO estoque_dono (
            garanhao, dono_id, data_embriovet, origem_externa,
            palhetas_produzidas, qualidade, concentracao, motilidade,
            local_armazenagem, certificado, dose, observacoes,
            quantidade_inicial, existencia_atual
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        dados["Garanhão"], dados["Dono"], dados["Data"], dados["Origem"],
        dados["Palhetas"], dados["Qualidade"], dados["Concentração"], dados["Motilidade"],
        dados["Local"], dados["Certificado"], dados["Dose"], dados["Observações"],
        dados["Palhetas"], dados["Palhetas"]
    ))
    conn.commit()
    cur.close()
    conn.close()

# 💾 Inserção de inseminação

def registrar_inseminacao(registro):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO inseminacoes (garanhao, dono_id, data_inseminacao, egua, protocolo, palhetas_gastas)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        registro["garanhao"], registro["dono_id"], registro["data"],
        registro["egua"], registro["protocolo"], registro["palhetas"]
    ))

    cur.execute("""
        UPDATE estoque_dono SET existencia_atual = existencia_atual - %s
        WHERE id = %s
    """, (
        registro["palhetas"], registro["estoque_id"]
    ))
    conn.commit()
    cur.close()
    conn.close()

# 🖼️ Interface
st.set_page_config(page_title="Gestor Sémen - MultiDonos", layout="wide")
st.title("🐴 Gestor de Sémen com Múltiplos Donos")

aba = st.sidebar.radio("Menu", ["📦 Ver Estoque", "➕ Adicionar Stock", "📝 Registrar Inseminação", "📈 Relatórios"])

donos = carregar_donos()
estoque = carregar_estoque()
insem = carregar_inseminacoes()

if aba == "📦 Ver Estoque":
    st.header("📦 Estoque Atual por Garanhão e Dono")
    if not estoque.empty:
        filtro = st.selectbox("Filtrar por Garanhão:", estoque["garanhao"].unique())
        estoque_filtrado = estoque[estoque["garanhao"] == filtro]

        donos_dict = dict(zip(donos["id"], donos["nome"]))

        for idx, row in estoque_filtrado.iterrows():
            existencia = 0 if pd.isna(row['existencia_atual']) else int(row['existencia_atual'])
            with st.expander(f"📦 {row['origem_externa'] or row['data_embriovet']} — {existencia} palhetas"):

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Local:** {row['local_armazenagem']}")
                    st.markdown(f"**Certificado:** {row['certificado']}")
                    st.markdown(f"**Qualidade:** {row['qualidade']}%")
                with col2:
                    dono_atual = row['dono_id']
                    novo_dono = st.selectbox(
                        "Dono do Sémen",
                        options=donos["id"],
                        format_func=lambda x: donos_dict[x],
                        index=list(donos["id"]).index(dono_atual) if dono_atual in donos["id"].values else 0,
                        key=f"select_{row['id']}"
                    )
                    if st.button("💾 Atualizar Dono", key=f"btn_update_{row['id']}"):
                        atualizar_dono_stock(row["id"], novo_dono)
                        st.success("Dono atualizado com sucesso!")
                        st.experimental_rerun()
    else:
        st.info("Nenhum stock cadastrado.")


elif aba == "➕ Adicionar Stock":
    st.header("➕ Inserir novo stock com Dono")
    with st.form("novo_stock"):
        garanhao = st.text_input("Garanhão")
        dono_nome = st.selectbox("Dono do Sémen", donos["nome"])
        dono_id = donos[donos["nome"] == dono_nome]["id"].values[0]

        data = st.text_input("Data de Produção")
        origem = st.text_input("Origem Externa / Referência")
        palhetas = st.number_input("Palhetas Produzidas", min_value=0)
        qualidade = st.number_input("Qualidade (%)", min_value=0, max_value=100)
        concentracao = st.number_input("Concentração (milhões/mL)", min_value=0)
        motilidade = st.number_input("Motilidade (%)", min_value=0, max_value=100)
        local = st.text_input("Local Armazenagem")
        certificado = st.selectbox("Certificado?", ["Sim", "Não"])
        dose = st.text_input("Dose")
        observacoes = st.text_area("Observações")
        submitted = st.form_submit_button("Salvar")

        if submitted and garanhao:
            inserir_stock({
                "Garanhão": garanhao,
                "Dono": dono_id,
                "Data": data,
                "Origem": origem,
                "Palhetas": palhetas,
                "Qualidade": qualidade,
                "Concentração": concentracao,
                "Motilidade": motilidade,
                "Local": local,
                "Certificado": certificado,
                "Dose": dose,
                "Observações": observacoes
            })
            st.success("Stock adicionado!")

elif aba == "📝 Registrar Inseminação":
    st.header("📝 Registrar uso de Sémen")
    if not estoque.empty:
        garanhao = st.selectbox("Garanhão", estoque["garanhao"].unique())
        estoques_filtrados = estoque[estoque["garanhao"] == garanhao]
        estoque_id = st.selectbox("Lote (por dono/protocolo)", estoques_filtrados.index)
        dono_nome = donos[donos["id"] == estoques_filtrados.loc[estoque_id, "dono_id"]]["nome"].values[0]

        st.markdown(f"Dono: **{dono_nome}**")
        data = st.date_input("Data de Inseminação")
        egua = st.text_input("Égua")
        protocolo = estoques_filtrados.loc[estoque_id, "data_embriovet"] or estoques_filtrados.loc[estoque_id, "origem_externa"]
        max_palhetas = int(estoques_filtrados.loc[estoque_id, "existencia_atual"])
        palhetas = st.number_input("Palhetas utilizadas", min_value=0, max_value=max_palhetas)

        if st.button("Registrar") and egua and palhetas > 0:
            registrar_inseminacao({
                "garanhao": garanhao,
                "dono_id": estoques_filtrados.loc[estoque_id, "dono_id"],
                "data": data,
                "egua": egua,
                "protocolo": protocolo,
                "palhetas": palhetas,
                "estoque_id": estoques_filtrados.loc[estoque_id, "id"]
            })
            st.success("Inseminação registrada!")
    else:
        st.warning("Nenhum stock disponível.")

elif aba == "📈 Relatórios":
    st.header("📈 Relatório de Inseminações")
    if not insem.empty:
        resultado = insem.merge(donos, left_on="dono_id", right_on="id")
        st.dataframe(resultado[["garanhao", "nome", "data_inseminacao", "egua", "protocolo", "palhetas_gastas"]], use_container_width=True)
    else:
        st.info("Nenhuma inseminação ainda.")
