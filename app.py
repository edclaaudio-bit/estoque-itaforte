import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="ITAFORTE | Smart Inventory", layout="wide")

# 2. CSS PROFISSIONAL E LIMPO (CORREÇÃO DE BUGS)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        
        /* LIMPEZA DE BUGS: Remove apenas o que atrapalha, sem esconder o texto real */
        .stExpander details summary p { 
            font-size: 1.1rem !important; 
            font-weight: 700 !important;
            margin: 0 !important;
        }
        .stExpander details summary svg { display: none !important; } /* Remove a seta que as vezes encavala */

        /* Ajuste de cores para os títulos das barras (Expander) */
        :root { --cor-texto: #0f172a; }
        @media (prefers-color-scheme: dark) { :root { --cor-texto: #ffffff; } }
        
        .stExpander details summary p {
            color: var(--cor-texto) !important;
        }

        /* Estilo do Header Principal */
        .mega-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 25px;
            border-left: 10px solid #3b82f6;
            color: white;
        }
        
        /* Botões */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            font-weight: 600;
            background-color: #3b82f6 !important;
            color: white !important;
        }
    </style>
    
    <div class="mega-header">
        <h1 style="margin:0; font-weight:800;">ITAFORTE</h1>
        <p style="margin:0; opacity:0.7;">Gestão Inteligente de Estoque</p>
    </div>
""", unsafe_allow_html=True)

# 3. LÓGICA DE DADOS
DATA_FILE = "dados_estoque.csv"
PRODS_FILE = "lista_produtos.txt"

def carregar_dados():
    if os.path.exists(DATA_FILE): return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Data", "Produto", "Tipo", "Quantidade", "Motivo"])

def carregar_produtos():
    if os.path.exists(PRODS_FILE):
        with open(PRODS_FILE, "r") as f:
            return sorted(list(set([l.strip() for l in f.readlines() if l.strip()])))
    return []

df_mov = carregar_dados()
lista_prods = carregar_produtos()

# 4. ESTRUTURA
col_esq, col_dir = st.columns([1, 2.3], gap="large")

with col_esq:
    st.subheader("📥 Gestão")
    
    # BARRA 1: LANÇAMENTO (Texto agora via Python para evitar erro de CSS)
    with st.expander("🚀 LANÇAMENTO", expanded=True):
        with st.form("form_lanche", clear_on_submit=True):
            p = st.selectbox("Produto", options=[""] + lista_prods)
            t = st.selectbox("Operação", ["Entrada", "Saída"])
            q = st.number_input("Quantidade", min_value=0.0)
            obs = st.text_input("Observação")
            if st.form_submit_button("REGISTRAR"):
                if p and q > 0:
                    nova = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Produto": p, "Tipo": t, "Quantidade": q, "Motivo": obs}])
                    pd.concat([df_mov, nova], ignore_index=True).to_csv(DATA_FILE, index=False)
                    st.rerun()

    # BARRA 2: CADASTRO
    with st.expander("⚙️ CADASTRO", expanded=False):
        novo = st.text_input("Novo Produto").upper()
        if st.button("ADICIONAR"):
            if novo and novo not in lista_prods:
                with open(PRODS_FILE, "a") as f: f.write(novo + "\n")
                st.rerun()

    # BARRA 3: APAGAR
    with st.expander("🗑️ APAGAR / CORRIGIR", expanded=False):
        if not df_mov.empty:
            df_rev = df_mov.copy().iloc[::-1]
            opcoes = [f"{i} | {r['Data']} - {r['Produto']}" for i, r in df_rev.iterrows()]
            escolha = st.selectbox("Selecionar lançamento", options=opcoes)
            idx_apagar = int(escolha.split(" | ")[0])
            if st.button("EXCLUIR DEFINITIVAMENTE"):
                df_mov.drop(idx_apagar).to_csv(DATA_FILE, index=False)
                st.rerun()

with col_dir:
    st.subheader("🕒 Fluxo de Estoque")
    
    # Métricas simples no topo da tabela
    m1, m2 = st.columns(2)
    m1.metric("REGISTROS", len(df_mov))
    m2.metric("PRODUTOS", len(lista_prods))
    
    # Tabela de Visualização
    st.dataframe(df_mov.sort_index(ascending=False), use_container_width=True, hide_index=True)
    
    # Exportar
    csv = df_mov.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Relatório CSV", csv, "estoque_itaforte.csv", "text/csv")