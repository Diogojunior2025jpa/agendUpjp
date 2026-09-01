from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st
from supabase import create_client, Client

# Configuração da página e tema visual
st.set_page_config(
    page_title="AgendUp - Gestão de Agendamentos",
    page_icon="📅",
    layout="wide",
)

# Credenciais Supabase
SUPABASE_URL = "https://aphyrkigrszverlsainz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFwaHlya2lncnN6dmVybHNhaW56Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxODMxODYsImV4cCI6MjEwMzc1OTE4Nn0.rsYGRDdyuoMpH-aFLAgG2NF5GJtOltEIu4ANLhaDa60"

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

client = get_supabase_client()

# Normalizações e Helpers
ID_COLUMN = "id"
STATUS_PENDING = {"pendente", "pending", "aguardando", "aguardando pagamento"}
STATUS_CONFIRMED = {"confirmado", "confirmed"}

def fetch_data(table_name: str) -> list[dict[str, Any]]:
    try:
        response = client.table(table_name).select("*").execute()
        return response.data or []
    except Exception as e:
        st.error(f"Erro ao carregar dados de {table_name}: {e}")
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

# Barra Lateral - Navegação e Filtro Global
st.sidebar.title("⚡ AgendUp")
st.sidebar.caption("Sistema Multissetorial de Agendamentos")

menu = st.sidebar.radio(
    "Navegação",
    [" Painel Principal", " Novo Agendamento", " Serviços & Profissionais", " Configurações"],
)

# Carregamento prévio dos estabelecimentos
estabelecimentos = fetch_data("estabelecimentos")
estab_options = {e.get("nome", f"Estabelecimento #{e.get('id')}"): e.get("id") for e in estabelecimentos}

if estab_options:
    selected_estab_name = st.sidebar.selectbox("Filtrar por Unidade", list(estab_options.keys()))
    selected_estab_id = estab_options[selected_estab_name]
else:
    selected_estab_id = None
    st.sidebar.info("Nenhum estabelecimento cadastrado.")

# TAB 1: PAINEL PRINCIPAL
if menu == " Painel Principal":
    st.title(" Painel de Operações")
    st.write("Gerencie os agendamentos, confirme pagamentos via PIX e filtre por status.")

    raw_agendamentos = fetch_data("agendamentos")
    
    # Filtrar por estabelecimento se selecionado
    if selected_estab_id:
        agendamentos = [a for a in raw_agendamentos if a.get("estabelecimento_id") == selected_estab_id]
    else:
        agendamentos = raw_agendamentos

    # Métrica Rápida
    pendentes = [a for a in agendamentos if str(a.get("status", "")).casefold() in STATUS_PENDING]
    confirmados = [a for a in agendamentos if str(a.get("status", "")).casefold() in STATUS_CONFIRMED]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total na Unidade", len(agendamentos))
    col2.metric("Pendentes (PIX)", len(pendentes))
    col3.metric("Confirmados", len(confirmados))
    col4.metric("Outros Status", len(agendamentos) - len(pendentes) - len(confirmados))

    st.divider()

    # Filtros visuais
    filter_status = st.segmented_control(
        "Filtrar por Status",
        options=["Todos", "Pendentes", "Confirmados"],
        default="Todos"
    )

    filtered_list = agendamentos
    if filter_status == "Pendentes":
        filtered_list = pendentes
    elif filter_status == "Confirmados":
        filtered_list = confirmados

    if not filtered_list:
        st.info("Nenhum agendamento localizado para os filtros selecionados.")
    else:
        for item in filtered_list:
            item_id = item.get("id")
            status = str(item.get("status", "Pendente")).capitalize()
            is_pending = str(item.get("status", "")).casefold() in STATUS_PENDING
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1], vertical_alignment="center")
                with c1:
                    st.markdown(f"### {item.get('cliente_nome', 'Cliente sem nome')}")
                    st.caption(f"📅 **Data:** {display_datetime(item.get('data_hora'))} | 📱 **Contato:** {item.get('telefone', 'Não informado')}")
                with c2:
                    status_color = "orange" if is_pending else "green"
                    st.markdown(f"Status: :{status_color}[**{status}**]")
                    st.write(f"**Valor:** R$ {item.get('valor', '0,00')}")
                with c3:
                    if is_pending:
                        if st.button(" Confirmar PIX", key=f"btn_pix_{item_id}", type="primary", use_container_width=True):
                            try:
                                client.table("agendamentos").update({"status": "Confirmado"}).eq("id", item_id).execute()
                                st.success("PIX Confirmado!")
                                st.rerun()
                            except Exception as err:
                                st.error(f"Erro: {err}")
                    else:
                        st.caption(" Concluído")

# TAB 2: NOVO AGENDAMENTO (Criação de Agendamentos)
elif menu == " Novo Agendamento":
    st.title(" Criar Novo Agendamento")
    
    servicos = fetch_data("servicos")
    profissionais = fetch_data("profissionais")

    with st.form("form_novo_agendamento", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nome_cliente = st.text_input("Nome do Cliente*")
            telefone_cliente = st.text_input("Telefone / WhatsApp")
            data_agendamento = st.date_input("Data do Atendimento")
            hora_agendamento = st.time_input("Horário")
        
        with c2:
            servico_map = {s.get("nome", f"Serviço #{s.get('id')}"): s for s in servicos}
            servico_sel = st.selectbox("Selecione o Serviço", list(servico_map.keys())) if servico_map else None
            
            prof_map = {p.get("nome", f"Profissional #{p.get('id')}"): p.get("id") for p in profissionais}
            prof_sel = st.selectbox("Selecione o Profissional", list(prof_map.keys())) if prof_map else None
            
            valor = st.number_input("Valor (R$)", min_value=0.0, value=float(servico_map[servico_sel].get("preco", 0.0)) if servico_sel and "preco" in servico_map[servico_sel] else 0.0)

        submitted = st.form_submit_button("Salvar Agendamento", type="primary")
        
        if submitted:
            if not nome_cliente:
                st.error("Informe o nome do cliente.")
            else:
                data_hora_iso = f"{data_agendamento}T{hora_agendamento}"
                novo_registro = {
                    "cliente_nome": nome_cliente,
                    "telefone": telefone_cliente,
                    "data_hora": data_hora_iso,
                    "valor": valor,
                    "status": "Pendente",
                    "estabelecimento_id": selected_estab_id,
                    "profissional_id": prof_map[prof_sel] if prof_sel else None
                }
                try:
                    client.table("agendamentos").insert(novo_registro).execute()
                    st.success("Agendamento criado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# TAB 3: SERVIÇOS & PROFISSIONAIS
elif menu == " Serviços & Profissionais":
    st.title(" Cadastro de Serviços e Profissionais")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Serviços")
        servicos = fetch_data("servicos")
        if servicos:
            st.dataframe(servicos, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum serviço cadastrado.")
            
    with col_right:
        st.subheader("Profissionais / Atendentes")
        profissionais = fetch_data("profissionais")
        if profissionais:
            st.dataframe(profissionais, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum profissional cadastrado.")

# TAB 4: CONFIGURAÇÕES
elif menu == " Configurações":
    st.title("⚙️ Configurações da Unidade")
    st.write("Ajuste as informações básicas da sua empresa ou área de atuação.")
    
    if estabelecimentos:
        st.json(estabelecimentos)
    else:
        st.info("Nenhuma configuração encontrada.")
