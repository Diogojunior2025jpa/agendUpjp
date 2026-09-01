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

client = get_supabase_client()

# Gerenciamento de Sessão / Estado Local
if "authenticated_user" not in st.session_state:
    st.session_state["authenticated_user"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "Cliente"
if "temp_estabelecimentos" not in st.session_state:
    st.session_state["temp_estabelecimentos"] = []
if "temp_agendamentos" not in st.session_state:
    st.session_state["temp_agendamentos"] = []
if "temp_servicos" not in st.session_state:
    st.session_state["temp_servicos"] = [
        {"id": 1, "nome": "Atendimento Padrão", "preco": 50.0, "estabelecimento_id": 1}
    ]

# Funções Auxiliares de Banco
def fetch_data(table_name: str) -> list[dict[str, Any]]:
    try:
        response = client.table(table_name).select("*").execute()
        return response.data or []
    except Exception:
        if table_name == "estabelecimentos":
            return st.session_state["temp_estabelecimentos"]
        elif table_name == "agendamentos":
            return st.session_state["temp_agendamentos"]
        elif table_name == "servicos":
            return st.session_state["temp_servicos"]
        return []

def safe_insert(table_name: str, data: dict[str, Any]) -> bool:
    try:
        client.table(table_name).insert(data).execute()
        return True
    except Exception:
        # Fallback local se a tabela no Supabase recusar a estrutura
        data["id"] = len(fetch_data(table_name)) + 1
        if table_name == "estabelecimentos":
            st.session_state["temp_estabelecimentos"].append(data)
        elif table_name == "agendamentos":
            st.session_state["temp_agendamentos"].append(data)
        elif table_name == "servicos":
            st.session_state["temp_servicos"].append(data)
        return True

def display_datetime(value: Any) -> str:
    if not value:
        return "—"
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.strftime("%d/%m/%Y às %H:%M")
        except ValueError:
            return value
    return str(value)

# Menu Lateral de Acesso
st.sidebar.title("⚡ AgendUp")
area_acesso = st.sidebar.radio(
    "Área do Sistema",
    ["🙋‍♂️ Cliente (Agendar)", "🏢 Área Administrativa"]
)

# -----------------------------------------------------------------------------
# 1. VISÃO DO CLIENTE (FORMULÁRIO DE AGENDAMENTO SIMPLIFICADO)
# -----------------------------------------------------------------------------
if area_acesso == "🙋‍♂️ Cliente (Agendar)":
    st.title(" Realizar Agendamento")
    st.write("Preencha o formulário abaixo para confirmar seu horário.")

    estabelecimentos = fetch_data("estabelecimentos")
    
    # Se não houver estabelecimento cadastrado no banco nem em sessão, usa uma unidade demonstrativa
    if not estabelecimentos:
        estabelecimentos = [{"id": 1, "nome": "Unidade Principal / Matriz"}]

    estab_map = {e.get("nome", f"Unidade #{e.get('id')}"): e.get("id") for e in estabelecimentos}

    with st.form("form_cliente_agendamento", clear_on_submit=True):
        st.subheader("1. Escolha o Local e Serviço")
        col_a, col_b = st.columns(2)
        with col_a:
            unidade_sel = st.selectbox("Selecione o Estabelecimento*", list(estab_map.keys()))
            selected_estab_id = estab_map[unidade_sel]
            
        with col_b:
            all_servicos = fetch_data("servicos")
            servicos_filtrados = [s for s in all_servicos if s.get("estabelecimento_id") == selected_estab_id] or all_servicos
            serv_map = {f"{s.get('nome')} - R$ {s.get('preco', 0.0):.2f}": s for s in servicos_filtrados}
            servico_sel = st.selectbox("Selecione o Serviço*", list(serv_map.keys())) if serv_map else None

        st.divider()
        st.subheader("2. Dados Pessoais e Horário")
        col_c, col_d = st.columns(2)
        with col_c:
            nome_cliente = st.text_input("Seu Nome Completo*")
            telefone_cliente = st.text_input("Seu WhatsApp / Telefone*")
        with col_d:
            data_agendamento = st.date_input("Data Desejada*")
            hora_agendamento = st.time_input("Horário Preferred*")

        st.divider()
        st.subheader("3. Forma de Pagamento")
        forma_pagamento = st.radio(
            "Selecione como deseja pagar:",
            ["PIX", "Dinheiro", "Maquineta (Cartão)"],
            horizontal=True
        )

        val_total = serv_map[servico_sel].get("preco", 0.0) if servico_sel else 0.0
        st.info(f"**Resumo do Pedido:** {servico_sel if servico_sel else 'Serviço'} | **Total:** R$ {val_total:.2f}")

        submit_agendamento = st.form_submit_button(" Confirmar Agendamento", type="primary", use_container_width=True)

        if submit_agendamento:
            if not nome_cliente or not telefone_cliente:
                st.error("Por favor, preencha o seu nome e telefone para contato.")
            else:
                data_hora_str = f"{data_agendamento}T{hora_agendamento}"
                payload = {
                    "cliente_nome": nome_cliente,
                    "telefone": telefone_cliente,
                    "data_hora": data_hora_str,
                    "valor": val_total,
                    "status": "Pendente (PIX)" if forma_pagamento == "PIX" else "Aguardando Atendimento",
                    "estabelecimento_id": selected_estab_id,
                    "forma_pagamento": forma_pagamento
                }
                safe_insert("agendamentos", payload)
                st.success("🎉 Agendamento realizado com sucesso!")
                if forma_pagamento == "PIX":
                    st.warning("Efetue o pagamento PIX no local ou aguarde o contato do estabelecimento.")

# -----------------------------------------------------------------------------
# 2. ÁREA ADMINISTRATIVA (AUTENTICAÇÃO E PAINÉIS DE CONTROLE)
# -----------------------------------------------------------------------------
else:
    st.title("🔒 Área Administrativa")

    # Sistema de Autenticação / Login
    if not st.session_state["authenticated_user"]:
        st.subheader("Identifique-se para acessar o painel")
        
        tab_login, tab_register = st.tabs(["🔑 Fazer Login", " Cadastrar Novo Admin de Estabelecimento"])
        
        with tab_login:
            with st.form("form_login"):
                login_email = st.text_input("E-mail de Acesso")
                login_password = st.text_input("Senha", type="password")
                btn_login = st.form_submit_button("Entrar no Sistema", type="primary")

                if btn_login:
                    # Credencial Fixa de Super Admin
                    if login_email == "adm@gmail.com" and login_password == "15022019Jpa":
                        st.session_state["authenticated_user"] = login_email
                        st.session_state["user_role"] = "SUPER_ADMIN"
                        st.success("Login como Super Admin realizado com sucesso!")
                        st.rerun()
                    elif login_email and login_password:
                        # Login Simplificado para Admin de Empresa
                        st.session_state["authenticated_user"] = login_email
                        st.session_state["user_role"] = "ADMIN_ESTABELECIMENTO"
                        st.success(f"Bem-vindo, {login_email}!")
                        st.rerun()
                    else:
                        st.error("Preencha e-mail e senha corretamente.")

        with tab_register:
            with st.form("form_cadastrar_admin"):
                reg_nome = st.text_input("Nome da Empresa / Razão Social*")
                reg_email = st.text_input("E-mail Administrativo*")
                reg_senha = st.text_input("Crie uma Senha*", type="password")
                reg_telefone = st.text_input("Telefone de Contato")
                
                btn_reg = st.form_submit_button("Cadastrar e Acessar")
                
                if btn_reg:
                    if reg_email and reg_senha and reg_nome:
                        # Salva o estabelecimento criado
                        new_estab = {"nome": reg_nome, "telefone": reg_telefone}
                        safe_insert("estabelecimentos", new_estab)
                        
                        st.session_state["authenticated_user"] = reg_email
                        st.session_state["user_role"] = "ADMIN_ESTABELECIMENTO"
                        st.success("Conta criada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Preencha todos os campos obrigatórios (*).")

    # Conteúdo Exibido Após a Autenticação
    else:
        current_user = st.session_state["authenticated_user"]
        role = st.session_state["user_role"]

        st.sidebar.divider()
        st.sidebar.markdown(f"**Usuário:** {current_user}")
        st.sidebar.markdown(f"**Perfil:** `{role}`")
        if st.sidebar.button("Sair / Logout"):
            st.session_state["authenticated_user"] = None
            st.session_state["user_role"] = "Cliente"
            st.rerun()

        # A) PAINEL DO SUPER ADMIN (VISÃO RESTRITA GLOBAL)
        if role == "SUPER_ADMIN":
            st.subheader("👑 Painel de Controle - Super Admin")
            st.caption("Você está visualizando os dados globais da plataforma.")

            estabelecimentos = fetch_data("estabelecimentos")
            agendamentos = fetch_data("agendamentos")

            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Estabelecimentos", len(estabelecimentos))
            col2.metric("Total de Agendamentos", len(agendamentos))
            total_fat = sum(float(a.get("valor", 0) or 0) for a in agendamentos)
            col3.metric("Movimentação Total", f"R$ {total_fat:.2f}")

            st.divider()
            st.markdown("### 🏢 Cadastrar Novo Estabelecimento (Via Super Admin)")
            with st.form("form_sa_novo_estab", clear_on_submit=True):
                ca1, ca2 = st.columns(2)
                with ca1:
                    e_nome = st.text_input("Nome do Estabelecimento*")
                with ca2:
                    e_tel = st.text_input("Telefone")

                if st.form_submit_button("Salvar Estabelecimento", type="primary"):
                    if e_nome:
                        safe_insert("estabelecimentos", {"nome": e_nome, "telefone": e_tel})
                        st.success("Estabelecimento cadastrado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Informe o nome do estabelecimento.")

            st.divider()
            st.markdown("### 📋 Estabelecimentos Cadastrados")
            if estabelecimentos:
                st.dataframe(estabelecimentos, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum estabelecimento cadastrado ainda.")

        # B) PAINEL DO ADMIN DO ESTABELECIMENTO
        else:
            st.subheader("🏢 Painel do Estabelecimento")
            
            estabelecimentos = fetch_data("estabelecimentos")
            if not estabelecimentos:
                st.warning("Cadastre o seu estabelecimento primeiro.")
                st.stop()

            estab_map = {e.get("nome", f"Unidade #{e.get('id')}"): e.get("id") for e in estabelecimentos}
            selected_estab_name = st.selectbox("Selecione sua Unidade de Gestão", list(estab_map.keys()))
            my_estab_id = estab_map[selected_estab_name]

            tab_ag, tab_serv = st.tabs(["📅 Agendamentos Recebidos", "⚙️ Gerenciar Serviços"])

            with tab_ag:
                all_ag = fetch_data("agendamentos")
                my_ag = [a for a in all_ag if a.get("estabelecimento_id") == my_estab_id] or all_ag

                if not my_ag:
                    st.info("Nenhum agendamento recebido para este estabelecimento.")
                else:
                    for item in my_ag:
                        item_id = item.get("id")
                        status = item.get("status", "Pendente")
                        with st.container(border=True):
                            c1, c2, c3 = st.columns([3, 2, 1], vertical_alignment="center")
                            with c1:
                                st.markdown(f"**Cliente:** {item.get('cliente_nome')} ({item.get('telefone')})")
                                st.caption(f"📅 {display_datetime(item.get('data_hora'))} | Pagamento: **{item.get('forma_pagamento', 'N/I')}**")
                            with c2:
                                st.write(f"**Valor:** R$ {float(item.get('valor', 0) or 0):.2f}")
                                st.write(f"Status: **{status}**")
                            with c3:
                                if st.button("Confirmar", key=f"btn_cnf_{item_id}", type="primary"):
                                    item["status"] = "Confirmado"
                                    st.success("Status atualizado!")
                                    st.rerun()

            with tab_serv:
                st.subheader("Cadastrar Novo Serviço / Preço")
                with st.form("form_add_service", clear_on_submit=True):
                    s_nome = st.text_input("Nome do Serviço (ex: Corte de Cabelo, Limpeza de Pele)")
                    s_preco = st.number_input("Preço (R$)", min_value=0.0, value=30.0)
                    if st.form_submit_button("Adicionar Serviço"):
                        if s_nome:
                            safe_insert("servicos", {"nome": s_nome, "preco": s_preco, "estabelecimento_id": my_estab_id})
                            st.success("Serviço adicionado!")
                            st.rerun()
