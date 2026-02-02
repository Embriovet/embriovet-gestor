import pandas as pd
import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="embriovet",
        user="postgres",
        password="123",
        host="localhost",
        port="5432"
    )

def obter_id_proprietario(nome_proprietario, conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM dono WHERE nome = %s", (nome_proprietario,))
    result = cur.fetchone()

    if result:
        return result[0]
    else:
        cur.execute(
            "INSERT INTO dono (nome) VALUES (%s) RETURNING id",
            (nome_proprietario,)
        )
        novo_id = cur.fetchone()[0]
        conn.commit()
        return novo_id


# 📄 Ler o CSV
stock_df = pd.read_csv("base_stock_inicial.csv")

# ✅ Verificar se existe a coluna "Proprietário"
if "Proprietário" not in stock_df.columns:
    raise Exception(
        "⚠️ O CSV deve ter uma coluna chamada 'Proprietário'"
    )

# ➕ Criar coluna em falta
stock_df["Quantidade Inicial"] = stock_df["Palhetas Produzidas"]

# 🔁 Normalizar nomes das colunas
stock_df.rename(columns={
    "Garanhão": "garanhao",
    "Data de Produção (Embriovet)": "data_embriovet",
    "Origem Externa / Referência": "origem_externa",
    "Palhetas Produzidas": "palhetas_produzidas",
    "Qualidade (%)": "qualidade",
    "Concentração (milhões/mL)": "concentracao",
    "Motilidade (%)": "motilidade",
    "Local Armazenagem": "local_armazenagem",
    "Certificado": "certificado",
    "Dose inseminante (DI)": "dose",
    "Observações": "observacoes",
    "Quantidade Inicial": "quantidade_inicial",
    "Existência Atual": "existencia_atual",
    "Proprietário": "proprietario_nome"
}, inplace=True)

# 🔄 Tratar dados inválidos
stock_df.replace("Não exportar", pd.NA, inplace=True)
stock_df.replace("NaN", pd.NA, inplace=True)

# 🔁 Converter colunas numéricas corretamente
colunas_numericas = [
    "palhetas_produzidas", "qualidade", "concentracao", "motilidade",
    "quantidade_inicial", "existencia_atual"
]
for coluna in colunas_numericas:
    stock_df[coluna] = pd.to_numeric(
        stock_df[coluna], errors='coerce'
    )


# 💾 Inserir na base de dados
conn = get_connection()
cur = conn.cursor()

for _, row in stock_df.iterrows():
    proprietario_nome = row["proprietario_nome"]

    proprietario_id = None
    if pd.notna(proprietario_nome) and proprietario_nome.strip() != "":
        proprietario_id = obter_id_proprietario(
            proprietario_nome.strip(), conn
        )

    cur.execute("""
        INSERT INTO estoque_dono (
            garanhao, dono_id, data_embriovet, origem_externa,
            palhetas_produzidas, qualidade, concentracao,
            motilidade, local_armazenagem, certificado,
            dose, observacoes, quantidade_inicial, existencia_atual
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row["garanhao"],
        proprietario_id,
        row["data_embriovet"],
        row["origem_externa"],
        row["palhetas_produzidas"],
        row["qualidade"],
        row["concentracao"],
        row["motilidade"],
        row["local_armazenagem"],
        row["certificado"],
        row["dose"],
        row["observacoes"],
        row["quantidade_inicial"],
        row["existencia_atual"]
    ))

conn.commit()
cur.close()
conn.close()

print("✅ Base de dados restaurada com sucesso (com PROPRIETÁRIO).")
