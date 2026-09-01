from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st
from supabase import create_client, Client

st.set_page_config(
    page_title="AgendUp - Plataforma de Agendamentos",
    page_icon="⚡",
    layout="wide",
)

SUPABASE_URL = "https://aphyrkigrszverlsainz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFwaHlya2lncnN6dmVybHNhaW56Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxODMxODYsImV4cCI6MjEwMzc1OTE4Nn0.rsYGRDdyuoMpH-aFLAgG2NF5GJtOltEIu4ANLhaDa60"

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

client = get_supabase_client()

def fetch_data(table_name: str) -> list[dict[str, Any]]:
    try:
        response = client.table(table_name).select("*").execute()
        return response.data or []
    except Exception as e:
        st.error(f"Erro ao carregar {table_name}: {e}")
        return []

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

# Menu do Perfil na Sidebar
st.sidebar.title("⚡ AgendUp")
role = st.sidebar.selectbox(" Selecionar Perfil de Acesso", ["🙋‍♂️ Cliente (Agendar)", "🏢 Admin do Estabelecimento", "👑 Super Admin (Dono do App)"])
st.sidebar.divider()

# -----------------------------------------------------------------------------
# 1. VISÃO DO CLIENTE FINAL (ÁREA PÚBLICA DE AGENDAMENTO)
# -----------------------------------------------------------------------------
if role == "🙋‍♂️ Cliente (Agendar)":
    st.title(" Realizar Agendamento")
    st.write("Escolha a unidade, o serviço, a data e a forma de pagamento.")

    estabelecimentos = fetch_data("estabelecimentos")
    if not estabelecimentos:
        st.warning("Nenhum estabelecimento cadastrado no momento.")
        st.stop()

    estab_map = {e.get("nome", f"Unidade #{e.get('id')}"): e for e in estabelecimentos}
    estab_selected = st.selectbox("Selecione o Estabelecimento / Clínica / Salão", list(estab_map.keys()))
    current_estab = estab_map[estab_selected]
    estab_id = current_estab.get("id")

    # Carrega dados vinculados ao estabelecimento
    all_servicos = fetch_data("servicos")
    all_profs = fetch_data("profissionais")
    
    servicos = [s for s in all_servicos if s.get("estabelecimento_id") == estab_id] or all_servicos
    profissionais = [p for p in all_profs if p.get("estabelecimento_id") == estab_id] or all_profs

    with st.form("form_agendamento_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Seu Nome Completo*")
            telefone = st.text_input("Seu WhatsApp / Telefone*")
            
            servico_map = {f"{s.get('nome')} - R$ {s.get('preco', '0,00')}": s for s in servicos}
            servico_sel = st.selectbox("Serviço Desejado", list(servico_map.keys())) if servico_map else None
            
        with col2:
            data = st.date_input("Data da Consulta / Atendimento")
            hora = st.time_input("Horário Preferencial")
            
            prof_map = {p.get("nome"): p.get("id") for p in profissionais}
            prof_sel = st.selectbox("Profissional Preferencial", list(prof_map.keys())) if prof_map else None
            
            forma_pagamento = st.selectbox("Forma de Pagamento", ["PIX", "Cartão de Crédito", "Cartão de Débito", "Pagar no Local"])

        if servico_sel:
            preco = servico_map[servico_sel].get("preco", 0.0)
            st.info(f"**Total a Pagar:** R$ {preco} | **Forma de Pagamento:** {forma_pagamento}")

        submitted = st.form_submit_button("Confirmar Agendamento", type="primary", use_container_width=True)

        if submitted:
            if not nome or not telefone:
                st.error("Preencha seu nome e telefone para contato.")
            else:
                data_hora = f"{data}T{hora}"
                novo_agendamento = {
                    "cliente_nome": nome,
                    "telefone": telefone,
                    "data_hora": data_hora,
                    "valor": servico_map[servico_sel].get("preco", 0.0) if servico_sel else 0.0,
                    "status": "Pendente PIX" if forma_pagamento == "PIX" else "Aguardando",
                    "estabelecimento_id": estab_id,
                    "profissional_id": prof_map[prof_sel] if prof_sel else None,
                    "forma_pagamento": forma_pagamento
                }
                try:
                    client.table("agendamentos").insert(novo_agendamento).execute()
                    st.success("🎉 Agendamento realizado com sucesso!")
                    if forma_pagamento == "PIX":
                        st.warning("Efetue o pagamento via PIX para o estabelecimento confirmar seu horário.")
                except Exception as e:
                    st.error(f"Erro ao salvar agendamento: {e}")

# -----------------------------------------------------------------------------
# 2. VISÃO DO ADMIN DO ESTABELECIMENTO (EMPRESA)
# -----------------------------------------------------------------------------
elif role == "🏢 Admin do Estabelecimento":
    st.title(" Painel Administrativo da Unidade")
    
    estabelecimentos = fetch_data("estabelecimentos")
    if not estabelecimentos:
        st.info("Cadastre uma empresa na aba Super Admin primeiro.")
        st.stop()

    estab_map = {e.get("nome"): e.get("id") for e in estabelecimentos}
    estab_sel_name = st.sidebar.selectbox("Sua Empresa / Unidade", list(estab_map.keys()))
    my_estab_id = estab_map[estab_sel_name]

    tab1, tab2 = st.tabs([" Agendamentos Recebidos", " Servicos e Profissionais"])

    with tab1:
        st.subheader(f"Gestão de Horários - {estab_sel_name}")
        all_agendamentos = fetch_data("agendamentos")
        my_agendamentos = [a for a in all_agendamentos if a.get("estabelecimento_id") == my_estab_id]

        if not my_agendamentos:
            st.info("Nenhum agendamento recebido até o momento.")
        else:
            for item in my_agendamentos:
                item_id = item.get("id")
                status = item.get("status", "Pendente")
                is_pending = "pendente" in str(status).lower() or "aguardando" in str(status).lower()

                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 1], vertical_alignment="center")
                    with c1:
                        st.markdown(f"**Cliente:** {item.get('cliente_nome')} ({item.get('telefone')})")
                        st.caption(f"📅 {display_datetime(item.get('data_hora'))} | Pagamento: {item.get('forma_pagamento', 'PIX')}")
                    with c2:
                        st.write(f"**Valor:** R$ {item.get('valor', '0,00')} | Status: **{status}**")
                    with c3:
                        if is_pending:
                            if st.button("Confirmar Pagamento", key=f"adm_pay_{item_id}", type="primary"):
                                client.table("agendamentos").update({"status": "Confirmado"}).eq("id", item_id).execute()
                                st.success("Atualizado!")
                                st.rerun()

    with tab2:
        col_s, col_p = st.columns(2)
        with col_s:
            st.subheader(" Cadastrar Serviço")
            with st.form("add_service"):
                s_nome = st.text_input("Nome do Serviço")
                s_preco = st.number_input("Preço (R$)", min_value=0.0)
                if st.form_submit_button("Salvar Serviço"):
                    client.table("servicos").insert({"nome": s_nome, "preco": s_preco, "estabelecimento_id": my_estab_id}).execute()
                    st.success("Serviço Cadastrado!")
                    st.rerun()

        with col_p:
            st.subheader(" Cadastrar Profissional")
            with st.form("add_prof"):
                p_nome = st.text_input("Nome do Profissional")
                p_cargo = st.text_input("Especialidade / Cargo")
                if st.form_submit_button("Salvar Profissional"):
                    client.table("profissionais").insert({"nome": p_nome, "cargo": p_cargo, "estabelecimento_id": my_estab_id}).execute()
                    st.success("Profissional Cadastrado!")
                    st.rerun()

# -----------------------------------------------------------------------------
# 3. VISÃO DO SUPER ADMIN (GESTOR GLOBAL DA PLATAFORMA SAAS)
# -----------------------------------------------------------------------------
elif role == "👑 Super Admin (Dono do App)":
    st.title(" Painel Global do Sistema (Super Admin)")
    st.write("Gerencie todos os estabelecimentos contratantes e visualize as estatísticas do SaaS.")

    estabelecimentos = fetch_data("estabelecimentos")
    agendamentos = fetch_data("agendamentos")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Empresas Cadastradas", len(estabelecimentos))
    c2.metric("Total de Agendamentos na Plataforma", len(agendamentos))
    c3.metric("Faturamento Processado", f"R$ {sum(float(a.get('valor', 0) or 0) for a in agendamentos if 'confirm' in str(a.get('status')).lower()):,.2f}")

    st.divider()

    st.subheader("🏢 Cadastrar Nova Empresa / Estabelecimento")
    with st.form("form_novo_estabelecimento", clear_on_submit=True):
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            e_nome = st.text_input("Nome do Estabelecimento / Razão Social*")
            e_segmento = st.selectbox("Segmento", ["Barbearia", "Clínica Odontológica", "Salão de Beleza", "Estúdio de Tatuagem", "Consultório Médico", "Outros"])
        with col_e2:
            e_telefone = st.text_input("Telefone do Responsável")
            e_cidade = st.text_input("Cidade/UF")

        if st.form_submit_button("Cadastrar Empresa", type="primary"):
            if e_nome:
                client.table("estabelecimentos").insert({
                    "nome": e_nome,
                    "segmento": e_segmento,
                    "telefone": e_telefone,
                    "cidade": e_cidade
                }).execute()
                st.success("Empresa adicionada com sucesso ao sistema!")
                st.rerun()
            else:
                st.error("Informe o nome da empresa.")

    st.divider()
    st.subheader("📋 Lista de Empresas Cadastradas")
    if estabelecimentos:
        st.dataframe(estabelecimentos, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma empresa cadastrada.")
