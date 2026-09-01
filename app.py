from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st
from supabase import create_client, Client

# Configuração Visual da Aplicação
st.set_page_config(
    page_title="AgendUp - Gestão SaaS",
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

# Funções de Leitura e Escrita Supabase
def get_table_data(table_name: str) -> list[dict[str, Any]]:
    try:
        res = supabase.table(table_name).select("*").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao buscar {table_name}: {e}")
        return []

def insert_table_data(table_name: str, payload: dict[str, Any]) -> bool:
    try:
        supabase.table(table_name).insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar em {table_name}: {e}")
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

# Lateral
st.sidebar.title("⚡ AgendUp")

if not st.session_state["auth_user"]:
    nav = st.sidebar.radio("Navegação", ["🙋‍♂️ Cliente (Agendamentos)", "🔒 Acesso Restrito (Login)"])
else:
    nav = "🔒 Acesso Restrito (Login)"

# -----------------------------------------------------------------------------
# 1. TELA DO CLIENTE FINAL (ÁREA PÚBLICA DE AGENDAMENTO)
# -----------------------------------------------------------------------------
if nav == "🙋‍♂️ Cliente (Agendamentos)":
    st.title("📅 Agendamento Online")
    st.write("Escolha o estabelecimento, o serviço e a forma de pagamento.")

    empresas = get_table_data("estabelecimentos")
    if not empresas:
        st.warning("Nenhum estabelecimento cadastrado no sistema no momento.")
        st.stop()

    empresa_dict = {f"{e.get('nome')} ({e.get('segmento', 'Geral')})": e for e in empresas}
    empresa_selecionada_nome = st.selectbox("Selecione onde deseja agendar*", list(empresa_dict.keys()))
    empresa_atual = empresa_dict[empresa_selecionada_nome]

    st.divider()

    with st.form("form_cliente_publico", clear_on_submit=True):
        st.subheader("1. Seus Dados")
        c1, c2 = st.columns(2)
        with c1:
            c_nome = st.text_input("Seu Nome Completo*")
        with c2:
            c_tel = st.text_input("Seu WhatsApp / Telefone*")

        st.subheader("2. Atendimento")
        c3, c4 = st.columns(2)
        with c3:
            c_data = st.date_input("Data do Agendamento")
        with c4:
            c_hora = st.time_input("Horário")

        st.subheader("3. Pagamento")
        c_pagamento = st.radio(
            "Forma de Pagamento:",
            ["PIX", "Dinheiro", "Maquineta (Cartão no Local)"],
            horizontal=True
        )

        st.caption(f"Unidade selecionada: **{empresa_atual.get('nome')}**")
        btn_agendar = st.form_submit_button("Confirmar Agendamento", type="primary", use_container_width=True)

        if btn_agendar:
            if not c_nome or not c_tel:
                st.error("Preencha nome e telefone para contato.")
            else:
                payload = {
                    "cliente_nome": c_nome,
                    "telefone": c_tel,
                    "data_hora": f"{c_data}T{c_hora}",
                    "estabelecimento_id": empresa_atual.get("id"),
                    "forma_pagamento": c_pagamento,
                    "status": "Pendente (PIX)" if c_pagamento == "PIX" else "Aguardando"
                }
                if insert_table_data("agendamentos", payload):
                    st.success("🎉 Agendamento realizado com sucesso!")
                    if c_pagamento == "PIX":
                        st.info("Efetue o pagamento PIX para a empresa confirmar sua vaga.")

# -----------------------------------------------------------------------------
# 2. ÁREA ADMINISTRATIVA (AUTENTICAÇÃO E PAINÉIS)
# -----------------------------------------------------------------------------
else:
    # SE NÃO ESTÁ AUTENTICADO -> TELA DE LOGIN
    if not st.session_state["auth_user"]:
        st.title("🔒 Login Administrativo")
        
        with st.form("form_login_sistema"):
            email_input = st.text_input("E-mail de Acesso").strip()
            senha_input = st.text_input("Senha", type="password").strip()
            sub_login = st.form_submit_button("Acessar Painel", type="primary", use_container_width=True)

            if sub_login:
                # 1. Validação do Super Admin
                if email_input == "adm@gmail.com" and senha_input == "15022019Jpa":
                    st.session_state["auth_user"] = email_input
                    st.session_state["auth_role"] = "SUPER_ADMIN"
                    st.session_state["company_id"] = None
                    st.session_state["company_name"] = "Plataforma AgendUp"
                    st.success("Acesso liberado: Super Admin")
                    st.rerun()

                # 2. Validação dos Clientes Empresa (Cadastrados pelo Super Admin)
                else:
                    empresas = get_table_data("estabelecimentos")
                    empresa_encontrada = None
                    for emp in empresas:
                        if emp.get("email") == email_input and emp.get("senha") == senha_input:
                            empresa_encontrada = emp
                            break

                    if empresa_encontrada:
                        st.session_state["auth_user"] = email_input
                        st.session_state["auth_role"] = "ADMIN_EMPRESA"
                        st.session_state["company_id"] = empresa_encontrada.get("id")
                        st.session_state["company_name"] = empresa_encontrada.get("nome")
                        st.success(f"Bem-vindo, {empresa_encontrada.get('nome')}!")
                        st.rerun()
                    else:
                        st.error("Credenciais incorretas. Verifique seu e-mail e senha.")

    # SE JÁ ESTÁ AUTENTICADO -> EXIBE O PAINEL CORRESPONDENTE
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
        # PAINEL 1: SUPER ADMIN (GESTÃO COMPLETA DE CLIENTES EMPRESA)
        # =====================================================================
        if role == "SUPER_ADMIN":
            st.title("👑 Painel do Super Admin")
            st.write("Gerencie seus Clientes Empresa, crie novos acessos e monitore o SaaS.")

            empresas = get_table_data("estabelecimentos")
            agendamentos = get_table_data("agendamentos")

            m1, m2 = st.columns(2)
            m1.metric("Empresas Cadastradas", len(empresas))
            m2.metric("Total de Agendamentos no Sistema", len(agendamentos))

            st.divider()

            st.subheader("➕ Cadastrar Novo Cliente Empresa")
            st.write("Cadastre o estabelecimento e crie os dados de login para o dono da empresa.")

            with st.form("form_cadastrar_empresa_saas", clear_on_submit=True):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    emp_nome = st.text_input("Nome da Empresa / Estabelecimento*")
                    emp_segmento = st.selectbox("Segmento", ["Barbearia", "Clínica Odontológica", "Salão de Beleza", "Estúdio de Tatuagem", "Consultório", "Outro"])
                    emp_telefone = st.text_input("Telefone / WhatsApp")
                with col_e2:
                    emp_email = st.text_input("E-mail de Login do Cliente Empresa*")
                    emp_senha = st.text_input("Senha de Acesso do Cliente Empresa*", type="password")

                btn_salvar_empresa = st.form_submit_button(" Cadastrar Empresa e Gerar Acesso", type="primary")

                if btn_salvar_empresa:
                    if not emp_nome or not emp_email or not emp_senha:
                        st.error("Preencha Nome, E-mail e Senha para criar o acesso da empresa.")
                    else:
                        payload_empresa = {
                            "nome": emp_nome,
                            "segmento": emp_segmento,
                            "telefone": emp_telefone,
                            "email": emp_email,
                            "senha": emp_senha
                        }
                        if insert_table_data("estabelecimentos", payload_empresa):
                            st.success(f"Empresa '{emp_nome}' cadastrada! O cliente já pode logar com o e-mail: {emp_email}")
                            st.rerun()

            st.divider()

            st.subheader("📋 Lista de Empresas e Acessos Cadastrados")
            if empresas:
                st.dataframe(empresas, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma empresa cadastrada no Supabase ainda.")

        # =====================================================================
        # PAINEL 2: ADMIN DA EMPRESA (CLIENTE EMPRESA)
        # =====================================================================
        elif role == "ADMIN_EMPRESA":
            company_id = st.session_state["company_id"]
            company_name = st.session_state["company_name"]

            st.title(f"🏢 Painel Gestor - {company_name}")
            st.write("Acompanhe os agendamentos dos seus clientes e confirme pagamentos.")

            todos_agendamentos = get_table_data("agendamentos")
            
            # Filtra agendamentos apenas desta empresa
            meus_agendamentos = [a for a in todos_agendamentos if str(a.get("estabelecimento_id")) == str(company_id)]

            if not meus_agendamentos:
                st.info("Sua empresa ainda não possui agendamentos registrados.")
            else:
                for item in meus_agendamentos:
                    item_id = item.get("id")
                    status = item.get("status", "Aguardando")
                    
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 1], vertical_alignment="center")
                        with c1:
                            st.markdown(f"### {item.get('cliente_nome')}")
                            st.caption(f"📱 Contato: {item.get('telefone')} | 📅 Data: {format_date(item.get('data_hora'))}")
                        with c2:
                            st.write(f"**Pagamento:** {item.get('forma_pagamento')}")
                            st.write(f"**Status:** `{status}`")
                        with c3:
                            if "Pendente" in str(status) or "Aguardando" in str(status):
                                if st.button("Confirmar", key=f"btn_pay_{item_id}", type="primary"):
                                    try:
                                        supabase.table("agendamentos").update({"status": "Confirmado"}).eq("id", item_id).execute()
                                        st.success("Confirmado!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Erro: {err}")
