from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st
from supabase import create_client, Client

st.set_page_config(
    page_title="AgendUp - Gestão de Agendamentos",
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

def fetch_table(table_name: str) -> list[dict[str, Any]]:
    try:
        res = supabase.table(table_name).select("*").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao carregar {table_name}: {e}")
        return []

def insert_estabelecimento(nome: str, categoria: str, chave_pix_raw: str, tipo_chave_pix: str) -> dict[str, Any] | None:
    # Trata 'chave_pix' para o tipo bigint do Supabase (converte para inteiro se preenchido, ou manda None/NULL se vazio)
    pix_clean = ''.join(filter(str.isdigit, chave_pix_raw)) if chave_pix_raw else ""
    chave_pix_val = int(pix_clean) if pix_clean else None

    payload = {
        "nome": nome,
        "categoria": categoria,
        "tipo_chave_pix": tipo_chave_pix
    }
    if chave_pix_val is not None:
        payload["chave_pix"] = chave_pix_val

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
        st.error(f"Erro ao registrar agendamento: {e}")
        return False

def update_status_agendamento(agendamento_id: Any, novo_status: str) -> bool:
    try:
        supabase.table("agendamentos").update({"status": novo_status}).eq("id", agendamento_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar status: {e}")
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
# 1. ÁREA PÚBLICA DE AGENDAMENTO
# -----------------------------------------------------------------------------
if nav == "🙋‍♂️ Cliente (Agendamentos)":
    st.title("📅 Agendamento Online")
    st.write("Selecione o local desejado, preencha seus dados e confirme seu horário.")

    estabelecimentos = fetch_table("estabelecimentos")

    if not estabelecimentos:
        st.info("Nenhum estabelecimento cadastrado no momento. Faça login no Super Admin para cadastrar sua primeira empresa.")
    else:
        emp_map = {f"{e.get('nome')} ({e.get('categoria', 'Geral')})": e for e in estabelecimentos}
        emp_selecionada_label = st.selectbox("Selecione o Estabelecimento*", list(emp_map.keys()))
        empresa_atual = emp_map[emp_selecionada_label]

        st.divider()

        with st.form("form_cliente_agendamento", clear_on_submit=True):
            st.subheader("1. Seus Dados de Contato")
            c1, c2 = st.columns(2)
            with c1:
                c_nome = st.text_input("Seu Nome Completo*")
            with c2:
                c_tel = st.text_input("Seu WhatsApp / Telefone*")

            st.subheader("2. Data e Horário Desejados")
            c3, c4 = st.columns(2)
            with c3:
                c_data = st.date_input("Data do Atendimento")
            with c4:
                c_hora = st.time_input("Horário Preferred")

            st.subheader("3. Pagamento")
            c_pagamento = st.radio(
                "Forma de Pagamento:",
                ["PIX", "Dinheiro", "Maquineta (Cartão no Local)"],
                horizontal=True
            )

            st.caption(f"Unidade selecionada: **{empresa_atual.get('nome')}**")
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
                        st.success("🎉 Agendamento registrado com sucesso!")
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
                    st.error("E-mail ou senha incorretos.")

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

        # SUPER ADMIN
        if role == "SUPER_ADMIN":
            st.title("👑 Painel Super Admin")
            st.write("Cadastre estabelecimentos e configure credenciais de acesso.")

            estabelecimentos = fetch_table("estabelecimentos")
            agendamentos = fetch_table("agendamentos")

            m1, m2 = st.columns(2)
            m1.metric("Empresas Cadastradas", len(estabelecimentos))
            m2.metric("Total de Agendamentos", len(agendamentos))

            st.divider()

            st.subheader("➕ Cadastrar Novo Cliente Empresa")
            with st.form("form_cadastrar_empresa_saas", clear_on_submit=True):
                col_1, col_2 = st.columns(2)
                with col_1:
                    emp_nome = st.text_input("Nome da Empresa / Estabelecimento*")
                    emp_categoria = st.selectbox("Categoria*", ["odontologia", "barbearia", "salao_beleza", "consultorio", "outros"])
                    emp_chave_pix = st.text_input("Chave PIX (Somente Números ou Vazio)")
                    emp_tipo_pix = st.selectbox("Tipo da Chave PIX", ["telefone", "cnpj", "cpf", "email", "aleatoria"])
                with col_2:
                    emp_email = st.text_input("E-mail de Login da Empresa*")
                    emp_senha = st.text_input("Senha de Acesso da Empresa*", type="password")

                btn_salvar = st.form_submit_button("Cadastrar Empresa e Gerar Acesso", type="primary")

                if btn_salvar:
                    if not emp_nome or not emp_email or not emp_senha:
                        st.error("Preencha Nome, E-mail e Senha.")
                    else:
                        novo_est = insert_estabelecimento(
                            nome=emp_nome,
                            categoria=emp_categoria,
                            chave_pix_raw=emp_chave_pix,
                            tipo_chave_pix=emp_tipo_pix
                        )
                        if novo_est:
                            emp_id = novo_est.get("id")
                            st.session_state["empresa_logins"][emp_email] = {
                                "senha": emp_senha,
                                "empresa_id": emp_id,
                                "empresa_nome": emp_nome
                            }
                            st.success(f"Empresa '{emp_nome}' salva no Supabase (ID: {emp_id})!")
                            st.info(f"Login de Acesso Gerado -> E-mail: **{emp_email}** | Senha: **{emp_senha}**")
                            st.rerun()

            st.divider()
            st.subheader("📋 Empresas Salvas no Supabase")
            if estabelecimentos:
                st.dataframe(estabelecimentos, use_container_width=True, hide_index=True)

        # GESTOR DA EMPRESA
        elif role == "ADMIN_EMPRESA":
            company_id = st.session_state["company_id"]
            company_name = st.session_state["company_name"]

            st.title(f"🏢 Painel Gestor - {company_name}")
            st.write("Gerencie os agendamentos recebidos para a sua unidade.")

            todos_agendamentos = fetch_table("agendamentos")
            meus_agendamentos = [
                a for a in todos_agendamentos 
                if str(a.get("estabelecimento_id")) == str(company_id)
            ]

            if not meus_agendamentos:
                st.info("Nenhum agendamento recebido até o momento.")
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
                                if st.button("Recusar/Cancelar", key=f"canc_{item_id}"):
                                    if update_status_agendamento(item_id, "Cancelado"):
                                        st.warning("Cancelado!")
                                        st.rerun()
