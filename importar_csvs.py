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

# Ler CSV
stock_df = pd.read_csv("base_stock_inicial.csv")
inseminacoes_df = pd.read_csv("inseminacoes_iniciais.csv")

# Criar coluna em falta
stock_df["Quantidade Inicial"] = stock_df["Palhetas Produzidas"]

# Renomear colunas para o padrão do banco
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
    "Existência Atual": "existencia_atual"
}, inplace=True)

conn = get_connection()
cur = conn.cursor()

# Inserir STOCK
for _, row in stock_df.iterrows():
    cur.execute("""
        INSERT INTO stock (
            garanhao, data_embriovet, origem_externa,
            palhetas_produzidas, qualidade, concentracao,
            motilidade, local_armazenagem, certificado,
            dose, observacoes, quantidade_inicial, existencia_atual
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row["garanhao"],
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
        row["existencia_atual"],
    ))

# Inserir INSEMINAÇÕES
for _, row in inseminacoes_df.iterrows():
    cur.execute("""
        INSERT INTO inseminacoes (
            garanhao, data_inseminacao, egua, protocolo, palhetas_gastas
        ) VALUES (%s, %s, %s, %s, %s)
    """, (
        row["Garanhão"],
        row["Data Inseminação"],
        row["Égua"],
        row["Protocolo (Data/Origem)"],
        row["Palhetas Gastas"]
    ))

conn.commit()
cur.close()
conn.close()

print("✅ Dados importados com sucesso.")
