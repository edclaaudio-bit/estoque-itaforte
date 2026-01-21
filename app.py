import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="ITAFORTE | Smart Inventory", layout="wide")

# 2. CONEXÃO COM GOOGLE SHEETS
# O link que você forneceu: https://docs.google.com/spreadsheets/d/1LQPeIhv2OoM_k0fPQEf03gi3TRqZUeGPR1fyx3qUL3I/edit?usp=sharing
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    # Lê os dados da planilha especificada nas configurações
    return conn.read(ttl="0") 

# --- CSS PROFISSIONAL ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
        .stExpander details summary p { font-size: 1.1rem !important; font-weight: 700 !important; margin: 0 !important; }
        .stExpander details summary svg { display: none !important; }
        :root { --cor-texto: #0f172a; }
        @media (prefers-color-scheme: dark) { :root { --cor-texto: #ffffff; } }
        .stExpander details summary p { color: var(--cor-texto) !important; }
        .mega-header { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 30px; border-radius: 15px; margin-bottom: 25px; border-left: 10px solid #3b82f6; color: white; }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; background-color: #3b82f6 !important; color: white !important; }
    </style>
    <div class="mega-header">
        <h1 style="margin:0; font-weight:800;">ITAFORTE</h1>
        <p style="margin:0; opacity:0.7;">Smart Inventory Cloud 2026</p>
    </div>
""", unsafe_allow_html=True)

# 3. INTERFACE E LÓGICA
try:
    df_mov = carregar_dados()
    # Remove linhas vazias se houver
    df_mov = df_mov.dropna(how='all')
    
    # Lista de produtos únicos baseada no que já foi cadastrado
    lista_prods = sorted(df_mov['Produto'].unique().tolist()) if not df_mov.empty else []

    col_esq, col_dir = st.columns([1, 2.3], gap="large")

    with col_esq:
        st.subheader("📥 Gestão")
        
        with st.expander("🚀 LANÇAMENTO", expanded=True):
            with st.form("form_lanche", clear_on_submit=True):
                p = st.selectbox("Produto", options=[""] + lista_prods)
                t = st.selectbox("Operação", ["Entrada", "Saída"])
                q = st.number_input("Quantidade", min_value=0.0, step=0.01)
                obs = st.text_input("Observação")
                
                if st.form_submit_button("REGISTRAR NA NUVEM"):
                    if p and q > 0:
                        nova_linha = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Produto": p, "Tipo": t, "Quantidade": q, "Motivo": obs}])
                        df_atualizado = pd.concat([df_mov, nova_linha], ignore_index=True)
                        conn.update(data=df_atualizado)
                        st.success("Salvo no Google Sheets!")
                        st.rerun()

        with st.expander("⚙️ NOVO ITEM", expanded=False):
            novo = st.text_input("Nome do Produto").upper()
            if st.button("CADASTRAR"):
                if novo and novo not in lista_prods:
                    nova_p = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Produto": novo, "Tipo": "Cadastro", "Quantidade": 0, "Motivo": "Novo Item"}])
                    df_atualizado = pd.concat([df_mov, nova_p], ignore_index=True)
                    conn.update(data=df_atualizado)
                    st.success(f"Produto {novo} cadastrado!")
                    st.rerun()

    with col_dir:
        st.subheader("🕒 Fluxo em Tempo Real")
        if not df_mov.empty:
            st.dataframe(df_mov.sort_index(ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Aguardando o primeiro lançamento...")

except Exception as e:
    st.error("Erro ao conectar com a planilha. Verifique as configurações de Secrets.")
    st.write(e)
