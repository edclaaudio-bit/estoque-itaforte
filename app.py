import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="ITAFORTE | Inventory", layout="wide")

# --- 2. SISTEMA DE SEGURANÇA (OCULTO) ---
# O código abaixo busca a senha nos "Secrets" do Streamlit Cloud.
# No GitHub não aparecerá nada, apenas o nome da chave.
try:
    SENHA_CORRETA = st.secrets["APP_PASSWORD"]
except KeyError:
    st.error("ERRO: A senha não foi configurada nos Secrets do Streamlit Cloud.")
    st.stop()

def verificar_senha():
    """Gerencia o estado de login do usuário."""
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        _, col2, _ = st.columns([1, 1, 1])
        with col2:
            st.markdown("### 🔒 Acesso Restrito - ITAFORTE")
            senha_digitada = st.text_input("Digite a senha de acesso:", type="password")
            if st.button("Entrar"):
                if senha_digitada == SENHA_CORRETA:
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        return False
    return True

# --- 3. EXECUÇÃO DO APLICATIVO ---
if verificar_senha():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    conn = st.connection("gsheets", type=GSheetsConnection)

    def carregar_dados():
        return conn.read(ttl="0") 

    # Botão de Logout discreto na lateral
    if st.sidebar.button("Encerrar Sessão"):
        st.session_state["autenticado"] = False
        st.rerun()

    # --- CSS CUSTOMIZADO ---
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
            .mega-header { 
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
                padding: 30px; border-radius: 15px; margin-bottom: 25px; 
                border-left: 10px solid #3b82f6; color: white; 
            }
            .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; background-color: #3b82f6 !important; color: white !important; }
        </style>
        <div class="mega-header">
            <h1 style="margin:0; font-weight:800;">ITAFORTE - High Performance Materials</h1>
            <p style="margin:0; opacity:0.7;">Smart Inventory Cloud </p>
        </div>
    """, unsafe_allow_html=True)

    # --- 4. FLUXO DE DADOS ---
    try:
        df_mov = carregar_dados()
        df_mov = df_mov.dropna(how='all')
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
                    
                    if st.form_submit_button("REGISTRAR"):
                        if p and q > 0:
                            agora_br = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                            nova_linha = pd.DataFrame([{"Data": agora_br, "Produto": p, "Tipo": t, "Quantidade": q, "Motivo": obs}])
                            df_atualizado = pd.concat([df_mov, nova_linha], ignore_index=True)
                            conn.update(data=df_atualizado)
                            st.success("Dados enviados!")
                            st.rerun()

            with st.expander("⚙️ NOVO ITEM", expanded=False):
                novo = st.text_input("Nome do Produto").upper()
                if st.button("CADASTRAR"):
                    if novo and novo not in lista_prods:
                        agora_br = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                        nova_p = pd.DataFrame([{"Data": agora_br, "Produto": novo, "Tipo": "Cadastro", "Quantidade": 0, "Motivo": "Novo Item"}])
                        df_atualizado = pd.concat([df_mov, nova_p], ignore_index=True)
                        conn.update(data=df_atualizado)
                        st.success(f"{novo} adicionado!")
                        st.rerun()

        with col_dir:
            st.subheader("📈 Dashboard")
            prod_sel = st.selectbox("Análise por produto:", options=["Ver Todos"] + lista_prods)
            
            c1, c2, c3 = st.columns(3)
            if not df_mov.empty:
                if prod_sel != "Ver Todos":
                    df_p = df_mov[df_mov['Produto'] == prod_sel]
                    ent = df_p[df_p['Tipo'] == 'Entrada']['Quantidade'].sum()
                    sai = df_p[df_p['Tipo'] == 'Saída']['Quantidade'].sum()
                    c1.metric("Entradas", f"{ent:,.2f}")
                    c2.metric("Saídas", f"{sai:,.2f}")
                    c3.metric("Estoque", f"{ent-sai:,.2f}")
                else:
                    c1.metric("Total Entradas", f"{df_mov[df_mov['Tipo']=='Entrada']['Quantidade'].sum():,.2f}")
                    c2.metric("Total Saídas", f"{df_mov[df_mov['Tipo']=='Saída']['Quantidade'].sum():,.2f}")
                    c3.metric("Itens", len(lista_prods))

            st.divider()
            if not df_mov.empty:
                df_viz = df_mov.copy()
                if prod_sel != "Ver Todos":
                    df_viz = df_viz[df_viz['Produto'] == prod_sel]
                st.dataframe(df_viz.sort_index(ascending=False), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error("Erro na conexão com a planilha.")
