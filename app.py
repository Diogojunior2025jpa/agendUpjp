from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st
from supabase import create_client, Client

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AgendUp - Sistema de Agendamentos",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Credenciais do Supabase
SUPABASE_URL = "https://aphyrkigrszverlsainz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFwaHlya2lncnN6dmVybHNhaW56Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxODMxODYsImV4cCI6MjEwMzc1OTE4Nn0.rsYGRDdyuoMpH-aFLAgG2NF5GJtOltEIu4ANLhaDa60"

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# Controle de Sessão
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None
if "auth_role" not in st.session_state:
    st.session_state["auth_role"] = None
if "company_id" not in st.session_state:
    st.session_state["company_id"] = None
if "company_name" not in st.session_state:
    st.session_state["company_name"] = None

# Mapeamento dinâmico de logins criados no painel Super Admin
if "empresa_logins" not in st.session_state:
    st.session_state["empresa_logins"] = {}

# -----------------------------------------------------------------------------
# FUNÇÕES DE BANCO DE DADOS (SUPABASE DIRETO)
# -----------------------------------------------------------------------------
def fetch_table(table_name: str) -> list[dict[str, Any]]:
    try:
        res = supabase.table(table_name).select("*").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao consultar {table_name}: {e}")
        return []

def insert_estabelecimento(nome: str, categoria: str, chave_pix: str = "", tipo_chave_pix: str = "") -> dict[str, Any] | None:
    payload = {
        "nome": nome,
        "categoria": categoria,
        "chave_pix": chave_pix,
        "tipo_chave_pix": tipo_chave_pix
    }
    try:
        res = supabase.table("estabelecimentos").insert(payload).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        st.error(f"Erro ao salvar estabelecimento no Supabase: {e}")
    return None

def insert_agendamento(payload: dict[str, Any]) -> bool:
    try:
        supabase.table("agendamentos").insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao registrar agendamento no Supabase: {e}")
        return False

def update_status_agendamento(agendamento_id: Any, novo_status: str) -> bool:
    try:
        supabase.table("agendamentos").update({"status": novo_status}).eq("id", agendamento_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar status no Supabase: {e}")
        return False

def format_date(value: Any) -> str:
    if not value:
        return "—"
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y às %H:%M")
        except ValueError:
            return value
    return str(value)

# -----------------------------------------------------------------------------
# BARRA LATERAL - NAVEGAÇÃO
# -----------------------------------------------------------------------------
st.sidebar.title("⚡ AgendUp")

if not st.session_state["auth_user"]:
    nav = st.sidebar.radio("Navegação", ["🙋‍♂️ Cliente (Agendamentos)", "🔒 Acesso Restrito (Login)"])
else:
    nav = "🔒 Acesso Restrito (Login)"

# -----------------------------------------------------------------------------
# 1. TELA DE AGENDAMENTO (VISÃO CLIENTE PÚBLICO)
# -----------------------------------------------------------------------------
if nav == "🙋‍♂️ Cliente (Agendamentos)":
    st.title("📅 Agendamento Online")
    st.write("Escolha o estabelecimento, preencha os dados e confirme o atendimento.")

    estabelecimentos = fetch_table("estabelecimentos")

    if not estabelecimentos:
        st.warning("Nenhum estabelecimento cadastrado no banco de dados até o momento.")
        st.stop()

    # Mapeia nomes do dropdown para os registros reais do banco
    emp_map = {f"{e.get('nome')} ({e.get('categoria', 'Geral')})": e for e in estabelecimentos}
    emp_selecionada_label = st.selectbox("Selecione o Estabelecimento*", list(emp_map.keys()))
    empresa_atual = emp_map[emp_selecionada_label]

    st.divider()

    with st.form("form_cliente_agendamento", clear_on_submit=True):
        st.subheader("1. Seus Dados")
        c1, c2 = st.columns(2)
        with c1:
            c_nome = st.text_input("Seu Nome Completo*")
        with c2:
            c_tel = st.text_input("Seu WhatsApp / Telefone*")

        st.subheader("2. Data e Horário")
        c3, c4 = st.columns(2)
        with c3:
            c_data = st.date_input("Data do Atendimento")
        with c4:
            c_hora = st.time_input("Horário")

        st.subheader("3. Forma de Pagamento")
        c_pagamento = st.radio(
            "Selecione a forma de pagamento:",
            ["PIX", "Dinheiro", "Maquineta (Cartão no Local)"],
            horizontal=True
        )

        st.info(f"Unidade selecionada: **{empresa_atual.get('nome')}**")
        btn_confirmar = st.form_submit_button("Confirmar Agendamento", type="primary", use_container_width=True)

        if btn_confirmar:
            if not c_nome or not c_tel:
                st.error("Por favor, preencha seu nome e telefone.")
            else:
                payload = {
                    "cliente_nome": c_nome,
                    "telefone": c_tel,
                    "data_hora": f"{c_data}T{c_hora}",
                    "estabelecimento_id": empresa_atual.get("id"),
                    "forma_pagamento": c_pagamento,
                    "status": "Aguardando Confirmação"
                }
                if insert_agendamento(payload):
                    st.success("🎉 Agendamento registrado com sucesso no Supabase!")
                    st.rerun()

# -----------------------------------------------------------------------------
# 2. ÁREA DE AUTENTICAÇÃO E PAINÉIS
# -----------------------------------------------------------------------------
else:
    # SE NÃO ESTÁ CONECTADO -> LOGIN
    if not st.session_state["auth_user"]:
        st.title("🔒 Login Administrativo")
        
        with st.form("form_login_sistema"):
            email_input = st.text_input("E-mail de Acesso").strip()
            senha_input = st.text_input("Senha", type="password").strip()
            sub_login = st.form_submit_button("Acessar Painel", type="primary", use_container_width=True)

            if sub_login:
                # Login do Super Admin
                if email_input == "adm@gmail.com" and senha_input == "15022019Jpa":
                    st.session_state["auth_user"] = email_input
                    st.session_state["auth_role"] = "SUPER_ADMIN"
                    st.session_state["company_id"] = None
                    st.session_state["company_name"] = "Plataforma AgendUp"
                    st.success("Acesso liberado: Super Admin")
                    st.rerun()

                # Login dos Clientes Empresa
                elif email_input in st.session_state["empresa_logins"]:
                    acc = st.session_state["empresa_logins"][email_input]
                    if acc["senha"] == senha_input:
                        st.session_state["auth_user"] = email_input
                        st.session_state["auth_role"] = "ADMIN_EMPRESA"
                        st.session_state["company_id"] = acc["empresa_id"]
                        st.session_state["company_name"] = acc["empresa_nome"]
                        st.success(f"Bem-vindo, {acc['empresa_nome']}!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("E-mail ou senha não encontrados.")

    # SE ESTÁ CONECTADO
    else:
        role = st.session_state["auth_role"]
        user_email = st.session_state["auth_user"]

        st.sidebar.divider()
        st.sidebar.markdown(f"**Conectado:** `{user_email}`")
        st.sidebar.markdown(f"**Perfil:** `{role}`")
        if st.sidebar.button("🚪 Sair do Sistema"):
            st.session_state["auth_user"] = None
            st.session_state["auth_role"] = None
            st.session_state["company_id"] = None
            st.session_state["company_name"] = None
            st.rerun()

        # =====================================================================
        # PAINEL 1: SUPER ADMIN
        # =====================================================================
        if role == "SUPER_ADMIN":
            st.title("👑 Painel Super Admin")
            st.write("Gerencie os estabelecimentos cadastrados e crie credenciais para os donos.")

            estabelecimentos = fetch_table("estabelecimentos")
            agendamentos = fetch_table("agendamentos")

            m1, m2 = st.columns(2)
            m1.metric("Empresas no Supabase", len(estabelecimentos))
            m2.metric("Agendamentos Globais", len(agendamentos))

            st.divider()

            st.subheader("➕ Cadastrar Novo Cliente Empresa")
            with st.form("form_cadastrar_empresa_saas", clear_on_submit=True):
                col_1, col_2 = st.columns(2)
                with col_1:
                    emp_nome = st.text_input("Nome da Empresa / Estabelecimento*")
                    emp_categoria = st.selectbox("Categoria*", ["odontologia", "barbearia", "salao_beleza", "consultorio", "outros"])
                    emp_chave_pix = st.text_input("Chave PIX (Opcional)")
                    emp_tipo_pix = st.selectbox("Tipo da Chave PIX", ["telefone", "cnpj", "cpf", "email", "aleatoria"])
                with col_2:
                    emp_email = st.text_input("E-mail de Login da Empresa*")
                    emp_senha = st.text_input("Senha de Acesso da Empresa*", type="password")

                btn_salvar = st.form_submit_button("Cadastrar e Gerar Acesso", type="primary")

                if btn_salvar:
                    if not emp_nome or not emp_email or not emp_senha:
                        st.error("Preencha Nome, E-mail e Senha.")
                    else:
                        novo_est = insert_estabelecimento(
                            nome=emp_nome,
                            categoria=emp_categoria,
                            chave_pix=emp_chave_pix,
                            tipo_chave_pix=emp_tipo_pix
                        )
                        if novo_est:
                            emp_id = novo_est.get("id")
                            # Vincula no dicionário de logins
                            st.session_state["empresa_logins"][emp_email] = {
                                "senha": emp_senha,
                                "empresa_id": emp_id,
                                "empresa_nome": emp_nome
                            }
                            st.success(f"Empresa '{emp_nome}' salva no Supabase (ID: {emp_id})!")
                            st.info(f"Credenciais Criadas -> E-mail: **{emp_email}** | Senha: **{emp_senha}**")
                            st.rerun()

            st.divider()
            st.subheader("📋 Lista de Estabelecimentos Salvos no Supabase")
            if estabelecimentos:
                st.dataframe(estabelecimentos, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum estabelecimento encontrado no Supabase.")

        # =====================================================================
        # PAINEL 2: GESTOR DA EMPRESA
        # =====================================================================
        elif role == "ADMIN_EMPRESA":
            company_id = st.session_state["company_id"]
            company_name = st.session_state["company_name"]

            st.title(f"🏢 Painel Gestor - {company_name}")
            st.write("Acompanhe e altere os agendamentos recebidos em tempo real.")

            todos_agendamentos = fetch_table("agendamentos")
            
            # Filtra os agendamentos pertencentes ao ID do estabelecimento logado
            meus_agendamentos = [
                a for a in todos_agendamentos 
                if str(a.get("estabelecimento_id")) == str(company_id)
            ]

            if not meus_agendamentos:
                st.info("Nenhum agendamento recebido até o momento para esta empresa.")
            else:
                for item in meus_agendamentos:
                    item_id = item.get("id")
                    status_atual = item.get("status", "Aguardando Confirmação")
                    
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 2, 2], vertical_alignment="center")
                        with col1:
                            st.markdown(f"### {item.get('cliente_nome', 'Cliente')}")
                            st.caption(f"📱 Telefone: {item.get('telefone', 'N/I')} | 📅 Data: {format_date(item.get('data_hora'))}")
                        with col2:
                            st.write(f"**Pagamento:** {item.get('forma_pagamento', 'N/I')}")
                            st.write(f"**Status:** `{status_atual}`")
                        with col3:
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("Confirmar", key=f"conf_{item_id}", type="primary"):
                                    if update_status_agendamento(item_id, "Confirmado"):
                                        st.success("Confirmado!")
                                        st.rerun()
                            with b2:
                                if st.button("Cancelar/Recusar", key=f"canc_{item_id}"):
                                    if update_status_agendamento(item_id, "Cancelado / Recusado"):
                                        st.warning("Cancelado!")
                                        st.rerun()
