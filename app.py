from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st
from supabase import create_client, Client

st.set_page_config(
    page_title="AgendUp - Sistema de Agendamentos",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Credenciais Supabase
SUPABASE_URL = "https://aphyrkigrszverlsainz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFwaHlya2lncnN6dmVybHNhaW56Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxODMxODYsImV4cCI6MjEwMzc1OTE4Nn0.rsYGRDdyuoMpH-aFLAgG2NF5GJtOltEIu4ANLhaDa60"

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# Estado de Sessão
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None
if "auth_role" not in st.session_state:
    st.session_state["auth_role"] = None
if "company_id" not in st.session_state:
    st.session_state["company_id"] = None
if "company_name" not in st.session_state:
    st.session_state["company_name"] = None

if "empresa_logins" not in st.session_state:
    st.session_state["empresa_logins"] = {}

def get_table_data(table_name: str) -> list[dict[str, Any]]:
    try:
        res = supabase.table(table_name).select("*").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao ler {table_name} no Supabase: {e}")
        return []

def safe_insert_establishment(nome: str, segmento: str, telefone: str) -> dict[str, Any] | None:
    payload = {"nome": nome, "segmento": segmento, "telefone": telefone}
    try:
        res = supabase.table("estabelecimentos").insert(payload).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        st.error(f"Erro ao salvar estabelecimento no Supabase: {e}")
    return None

def safe_insert_agendamento(payload: dict[str, Any]) -> bool:
    try:
        supabase.table("agendamentos").insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar agendamento no Supabase: {e}")
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

# Barra Lateral
st.sidebar.title("⚡ AgendUp")

if not st.session_state["auth_user"]:
    nav = st.sidebar.radio("Navegação", ["🙋‍♂️ Cliente (Agendamentos)", "🔒 Acesso Restrito (Login)"])
else:
    nav = "🔒 Acesso Restrito (Login)"

# -----------------------------------------------------------------------------
# 1. VISÃO DO CLIENTE (AGENDAMENTO ONLINE)
# -----------------------------------------------------------------------------
if nav == "🙋‍♂️ Cliente (Agendamentos)":
    st.title("📅 Agendamento Online")
    st.write("Preencha as informações para realizar seu agendamento.")

    empresas = get_table_data("estabelecimentos")

    if not empresas:
        st.warning("Nenhum estabelecimento cadastrado no banco de dados até o momento.")
        st.stop()

    empresa_dict = {f"{e.get('nome')} ({e.get('segmento', 'Geral')})": e for e in empresas}
    empresa_selecionada_nome = st.selectbox("Selecione o Estabelecimento*", list(empresa_dict.keys()))
    empresa_atual = empresa_dict[empresa_selecionada_nome]

    st.divider()

    with st.form("form_agendamento_cliente", clear_on_submit=True):
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
            "Selecione como deseja pagar:",
            ["PIX", "Dinheiro", "Maquineta (Cartão no Local)"],
            horizontal=True
        )

        st.info(f"Empresa Selecionada: **{empresa_atual.get('nome')}**")
        btn_agendar = st.form_submit_button("Confirmar Agendamento", type="primary", use_container_width=True)

        if btn_agendar:
            if not c_nome or not c_tel:
                st.error("Por favor, preencha nome e telefone para contato.")
            else:
                payload = {
                    "cliente_nome": c_nome,
                    "telefone": c_tel,
                    "data_hora": f"{c_data}T{c_hora}",
                    "estabelecimento_id": empresa_atual.get("id"),
                    "forma_pagamento": c_pagamento,
                    "status": "Pendente (PIX)" if c_pagamento == "PIX" else "Aguardando"
                }
                if safe_insert_agendamento(payload):
                    st.success("🎉 Agendamento registrado com sucesso no Supabase!")
                    st.rerun()

# -----------------------------------------------------------------------------
# 2. ÁREA ADMINISTRATIVA
# -----------------------------------------------------------------------------
else:
    if not st.session_state["auth_user"]:
        st.title("🔒 Login Administrativo")
        
        with st.form("form_login_sistema"):
            email_input = st.text_input("E-mail de Acesso").strip()
            senha_input = st.text_input("Senha", type="password").strip()
            sub_login = st.form_submit_button("Acessar Painel", type="primary", use_container_width=True)

            if sub_login:
                if email_input == "adm@gmail.com" and senha_input == "15022019Jpa":
                    st.session_state["auth_user"] = email_input
                    st.session_state["auth_role"] = "SUPER_ADMIN"
                    st.session_state["company_id"] = None
                    st.session_state["company_name"] = "Plataforma AgendUp"
                    st.success("Acesso liberado: Super Admin")
                    st.rerun()

                elif email_input in st.session_state["empresa_logins"]:
                    acc_info = st.session_state["empresa_logins"][email_input]
                    if acc_info["senha"] == senha_input:
                        st.session_state["auth_user"] = email_input
                        st.session_state["auth_role"] = "ADMIN_EMPRESA"
                        st.session_state["company_id"] = acc_info["empresa_id"]
                        st.session_state["company_name"] = acc_info["empresa_nome"]
                        st.success(f"Bem-vindo, {acc_info['empresa_nome']}!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("E-mail ou senha não encontrados.")

    else:
        role = st.session_state["auth_role"]
        user_email = st.session_state["auth_user"]

        st.sidebar.divider()
        st.sidebar.markdown(f"**Conectado:** `{user_email}`")
        st.sidebar.markdown(f"**Perfil:** `{role}`")
        if st.sidebar.button("🚪 Sair"):
            st.session_state["auth_user"] = None
            st.session_state["auth_role"] = None
            st.session_state["company_id"] = None
            st.session_state["company_name"] = None
            st.rerun()

        # PAINEL SUPER ADMIN
        if role == "SUPER_ADMIN":
            st.title("👑 Painel do Super Admin")
            st.write("Cadastre estabelecimentos e gerencie os acessos do sistema SaaS.")

            empresas = get_table_data("estabelecimentos")
            agendamentos = get_table_data("agendamentos")

            m1, m2 = st.columns(2)
            m1.metric("Empresas Cadastradas", len(empresas))
            m2.metric("Total de Agendamentos", len(agendamentos))

            st.divider()

            st.subheader("➕ Cadastrar Novo Cliente Empresa")
            with st.form("form_cadastrar_empresa_saas", clear_on_submit=True):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    emp_nome = st.text_input("Nome da Empresa / Estabelecimento*")
                    emp_segmento = st.selectbox("Segmento", ["Clínica Odontológica", "Barbearia", "Salão de Beleza", "Estúdio de Tatuagem", "Consultório", "Outro"])
                    emp_telefone = st.text_input("Telefone / WhatsApp")
                with col_e2:
                    emp_email = st.text_input("E-mail de Login do Cliente Empresa*")
                    emp_senha = st.text_input("Senha de Acesso do Cliente Empresa*", type="password")

                btn_salvar_empresa = st.form_submit_button("Cadastrar Empresa e Gerar Acesso", type="primary")

                if btn_salvar_empresa:
                    if not emp_nome or not emp_email or not emp_senha:
                        st.error("Preencha Nome, E-mail e Senha.")
                    else:
                        created_emp = safe_insert_establishment(emp_nome, emp_segmento, emp_telefone)
                        if created_emp:
                            emp_id = created_emp.get("id")
                            st.session_state["empresa_logins"][emp_email] = {
                                "senha": emp_senha,
                                "empresa_id": emp_id,
                                "empresa_nome": emp_nome
                            }
                            st.success(f"Empresa '{emp_nome}' salva no Supabase (ID: {emp_id})!")
                            st.info(f"Login Gerado: **{emp_email}** | Senha: **{emp_senha}**")
                            st.rerun()

            st.divider()
            st.subheader("📋 Lista de Empresas Cadastradas")
            if empresas:
                st.dataframe(empresas, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma empresa encontrada no banco de dados.")

        # PAINEL ADMIN EMPRESA
        elif role == "ADMIN_EMPRESA":
            company_id = st.session_state["company_id"]
            company_name = st.session_state["company_name"]

            st.title(f"🏢 Painel Gestor - {company_name}")
            st.write("Acompanhe e gerencie os agendamentos do seu estabelecimento.")

            todos_agendamentos = get_table_data("agendamentos")
            
            # Filtra agendamentos pertencentes ao ID desta empresa
            meus_agendamentos = [
                a for a in todos_agendamentos 
                if str(a.get("estabelecimento_id")) == str(company_id)
            ]

            if not meus_agendamentos:
                st.info("Nenhum agendamento recebido até o momento para o seu estabelecimento.")
            else:
                for item in meus_agendamentos:
                    item_id = item.get("id")
                    status = item.get("status", "Aguardando")
                    
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 2], vertical_alignment="center")
                        with c1:
                            st.markdown(f"### {item.get('cliente_nome', 'Cliente')}")
                            st.caption(f"📱 Contato: {item.get('telefone', 'Não informado')} | 📅 Data: {format_date(item.get('data_hora'))}")
                        with c2:
                            st.write(f"**Pagamento:** {item.get('forma_pagamento', 'N/I')}")
                            st.write(f"**Status:** `{status}`")
                        with c3:
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("Confirmar", key=f"btn_confirm_{item_id}", type="primary"):
                                    try:
                                        supabase.table("agendamentos").update({"status": "Confirmado"}).eq("id", item_id).execute()
                                        st.success("Confirmado!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro: {e}")
                            with col_btn2:
                                if st.button("Cancelar", key=f"btn_cancel_{item_id}"):
                                    try:
                                        supabase.table("agendamentos").update({"status": "Cancelado/Recusado"}).eq("id", item_id).execute()
                                        st.warning("Cancelado!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro: {e}")
