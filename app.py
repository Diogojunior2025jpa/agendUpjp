from datetime import datetime, date, time
from typing import Any

import streamlit as st
from supabase import create_client


# ======================================================
# CONFIGURAÇÃO
# ======================================================

st.set_page_config(
    page_title="AgendUp",
    page_icon="⚡",
    layout="wide"
)


# ======================================================
# SUPABASE
# ======================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def conectar_supabase():
    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


supabase = conectar_supabase()



# ======================================================
# SESSÃO
# ======================================================

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "perfil" not in st.session_state:
    st.session_state.perfil = None

if "empresa_id" not in st.session_state:
    st.session_state.empresa_id = None



# ======================================================
# FUNÇÕES BANCO
# ======================================================


def buscar_tabela(tabela):

    try:

        resposta = (
            supabase
            .table(tabela)
            .select("*")
            .execute()
        )

        return resposta.data or []

    except Exception as erro:

        st.error(
            f"Erro buscando {tabela}: {erro}"
        )

        return []



def inserir_agendamento(dados):

    try:

        supabase\
        .table("agendamentos")\
        .insert(dados)\
        .execute()

        return True

    except Exception as erro:

        st.error(
            f"Erro ao salvar agendamento: {erro}"
        )

        return False



def alterar_status(id_agendamento, status):

    try:

        supabase\
        .table("agendamentos")\
        .update({
            "status": status
        })\
        .eq(
            "id",
            id_agendamento
        )\
        .execute()

        return True

    except Exception as erro:

        st.error(
            f"Erro: {erro}"
        )

        return False



# ======================================================
# MENU
# ======================================================

st.sidebar.title(
    "⚡ AgendUp"
)


if st.session_state.usuario:

    menu = "Painel"

else:

    menu = st.sidebar.radio(
        "Menu",
        [
            "📅 Agendar",
            "🔐 Login"
        ]
    )



# ======================================================
# ÁREA CLIENTE
# ======================================================


if menu == "📅 Agendar":


    st.title(
        "📅 Agendamento Online"
    )

    st.write(
        "Escolha o estabelecimento, profissional e serviço."
    )


    estabelecimentos = buscar_tabela(
        "estabelecimentos"
    )


    if not estabelecimentos:

        st.warning(
            "Nenhum estabelecimento cadastrado."
        )

        st.stop()



    empresas = {

        f"{e['nome']} - {e['categoria']}":
        e

        for e in estabelecimentos

    }



    empresa_nome = st.selectbox(

        "Escolha o estabelecimento",

        list(empresas.keys())

    )


    empresa = empresas[empresa_nome]



    # -------------------------
    # PROFISSIONAIS
    # -------------------------


    profissionais = [

        p for p in buscar_tabela("profissionais")

        if p["estabelecimento_id"] == empresa["id"]

    ]



    if profissionais:


        profissionais_map = {

            p["nome"]:
            p

            for p in profissionais

        }


        profissional_nome = st.selectbox(

            "Escolha o profissional",

            list(profissionais_map.keys())

        )


        profissional = profissionais_map[
            profissional_nome
        ]


    else:

        st.warning(
            "Nenhum profissional cadastrado."
        )

        st.stop()



    # -------------------------
    # SERVIÇOS
    # -------------------------


    servicos = [

        s for s in buscar_tabela("servicos")

        if s["estabelecimento_id"] == empresa["id"]

    ]



    if servicos:


        servicos_map = {

            s["nome"]:
            s

            for s in servicos

        }


        servico_nome = st.selectbox(

            "Escolha o serviço",

            list(servicos_map.keys())

        )


        servico = servicos_map[
            servico_nome
        ]


        st.info(
            f"Valor: R$ {servico['preco']}"
        )


    else:

        st.warning(
            "Nenhum serviço cadastrado."
        )

        st.stop()



    st.divider()



    # -------------------------
    # DADOS CLIENTE
    # -------------------------


    nome = st.text_input(
        "Seu nome"
    )


    telefone = st.text_input(
        "WhatsApp"
    )


    col1,col2 = st.columns(2)


    with col1:

        data = st.date_input(
            "Data",
            date.today()
        )


    with col2:

        horario = st.time_input(
            "Horário",
            time(8,0)
        )



    pagamento = st.radio(

        "Pagamento",

        [
            "PIX",
            "Dinheiro",
            "Cartão"
        ]

    )



    if st.button(
        "Confirmar Agendamento",
        type="primary"
    ):


        if not nome or not telefone:


            st.error(
                "Informe nome e telefone."
            )


        else:


            dados = {


                "cliente_id":
                "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",


                "profissional_id":
                profissional["id"],


                "servico_id":
                servico["id"],


                "data_hora":
                f"{data}T{horario}",


                "status":
                "pendente"

            }



            if inserir_agendamento(dados):


                st.success(
                    "✅ Agendamento realizado!"
                )
# ======================================================
# LOGIN E ÁREA ADMINISTRATIVA
# ======================================================


elif menu == "🔐 Login":


    st.title(
        "🔐 Acesso Administrativo"
    )


    email = st.text_input(
        "E-mail"
    )


    senha = st.text_input(
        "Senha",
        type="password"
    )



    if st.button(
        "Entrar",
        type="primary"
    ):


        # SUPER ADMIN
        # temporário para MVP


        if (
            email == "admin@agendup.com"
            and senha == "123456"
        ):


            st.session_state.usuario = email

            st.session_state.perfil = "SUPER_ADMIN"

            st.success(
                "Login administrador realizado"
            )

            st.rerun()



        else:


            st.error(
                "Usuário ou senha inválidos"
            )





# ======================================================
# PAINEL LOGADO
# ======================================================


if st.session_state.usuario:


    st.sidebar.divider()


    st.sidebar.write(
        "Usuário:"
    )


    st.sidebar.success(
        st.session_state.usuario
    )



    st.sidebar.write(
        "Perfil:"
    )


    st.sidebar.info(
        st.session_state.perfil
    )



    if st.sidebar.button(
        "Sair"
    ):


        st.session_state.usuario = None

        st.session_state.perfil = None

        st.rerun()



    st.title(
        "⚡ Painel AgendUp"
    )



    abas = st.tabs(
        [
            "📅 Agenda",
            "🏢 Empresas",
            "📊 Indicadores"
        ]
    )



# ======================================================
# AGENDA
# ======================================================


    with abas[0]:


        st.subheader(
            "Agendamentos Recebidos"
        )



        agendamentos = buscar_tabela(
            "agendamentos"
        )



        if not agendamentos:


            st.info(
                "Nenhum agendamento."
            )



        else:



            for ag in agendamentos:



                with st.container(
                    border=True
                ):



                    profissional = next(

                        (
                            p for p in buscar_tabela(
                                "profissionais"
                            )

                            if p["id"] == ag["profissional_id"]

                        ),

                        None

                    )



                    servico = next(

                        (
                            s for s in buscar_tabela(
                                "servicos"
                            )

                            if s["id"] == ag["servico_id"]

                        ),

                        None

                    )



                    st.markdown(

                        f"""
                        ### 📅 Atendimento

                        **Cliente ID:** {ag['cliente_id']}

                        **Profissional:** 
                        {profissional['nome'] if profissional else 'N/A'}

                        **Serviço:**
                        {servico['nome'] if servico else 'N/A'}

                        **Data:**
                        {ag['data_hora']}

                        **Status:**
                        {ag['status']}
                        """

                    )



                    c1,c2 = st.columns(2)



                    with c1:


                        if st.button(

                            "✅ Confirmar",

                            key=f"ok_{ag['id']}"

                        ):


                            alterar_status(

                                ag["id"],

                                "confirmado"

                            )


                            st.success(
                                "Agendamento confirmado"
                            )


                            st.rerun()



                    with c2:


                        if st.button(

                            "❌ Cancelar",

                            key=f"cancel_{ag['id']}"

                        ):


                            alterar_status(

                                ag["id"],

                                "cancelado"

                            )


                            st.warning(
                                "Agendamento cancelado"
                            )


                            st.rerun()
# ======================================================
# SUPER ADMIN
# ======================================================


if st.session_state.get("perfil") == "SUPER_ADMIN":


    st.divider()


    st.header(
        "👑 Administração da Plataforma"
    )



    abas_admin = st.tabs(

        [
            "🏢 Empresas",
            "👨‍💼 Profissionais",
            "💼 Serviços",
            "📊 Dashboard"
        ]

    )



# ======================================================
# EMPRESAS
# ======================================================


    with abas_admin[0]:


        st.subheader(
            "Cadastrar Estabelecimento"
        )



        with st.form(
            "nova_empresa"
        ):



            nome_empresa = st.text_input(

                "Nome do estabelecimento"

            )



            categoria = st.selectbox(

                "Categoria",

                [

                    "barbearia",

                    "odontologia",

                    "estetica",

                    "consultorio",

                    "outros"

                ]

            )



            pix = st.text_input(

                "Chave PIX"

            )



            salvar_empresa = st.form_submit_button(

                "Cadastrar Empresa"

            )




            if salvar_empresa:



                dados = {


                    "nome":
                    nome_empresa,


                    "categoria":
                    categoria,


                    "chave_pix":
                    pix,


                    "tipo_chave_pix":
                    "aleatoria"


                }



                try:


                    supabase.table(
                        "estabelecimentos"
                    ).insert(
                        dados
                    ).execute()



                    st.success(

                        "Empresa cadastrada!"

                    )


                    st.rerun()



                except Exception as erro:


                    st.error(
                        str(erro)
                    )




        st.divider()


        st.subheader(
            "Empresas cadastradas"
        )


        empresas = buscar_tabela(

            "estabelecimentos"

        )


        st.dataframe(

            empresas,

            use_container_width=True

        )




# ======================================================
# PROFISSIONAIS
# ======================================================


    with abas_admin[1]:


        st.subheader(

            "Cadastrar Profissional"

        )



        empresas = buscar_tabela(

            "estabelecimentos"

        )



        if empresas:


            mapa_empresas = {


                e["nome"]:
                e["id"]


                for e in empresas

            }



            empresa_nome = st.selectbox(

                "Empresa",

                mapa_empresas.keys()

            )



            empresa_id = mapa_empresas[

                empresa_nome

            ]



            nome_profissional = st.text_input(

                "Nome profissional"

            )


            especialidade = st.text_input(

                "Especialidade"

            )



            if st.button(

                "Cadastrar Profissional"

            ):



                dados = {


                    "estabelecimento_id":
                    empresa_id,


                    "nome":
                    nome_profissional,


                    "especialidade":
                    especialidade


                }



                supabase.table(

                    "profissionais"

                ).insert(

                    dados

                ).execute()



                st.success(

                    "Profissional cadastrado"

                )


                st.rerun()




# ======================================================
# SERVIÇOS
# ======================================================



    with abas_admin[2]:


        st.subheader(

            "Cadastrar Serviço"

        )



        empresas = buscar_tabela(

            "estabelecimentos"

        )



        if empresas:



            mapa_empresas = {


                e["nome"]:
                e["id"]


                for e in empresas


            }



            empresa_nome = st.selectbox(

                "Empresa",

                mapa_empresas.keys(),

                key="empresa_servico"

            )



            empresa_id = mapa_empresas[

                empresa_nome

            ]



            nome_servico = st.text_input(

                "Nome serviço"

            )


            duracao = st.number_input(

                "Duração minutos",

                min_value=5,

                value=30

            )


            preco = st.number_input(

                "Preço",

                min_value=0

            )



            if st.button(

                "Cadastrar Serviço"

            ):



                dados = {


                    "estabelecimento_id":

                    empresa_id,


                    "nome":

                    nome_servico,


                    "duracao_minutos":

                    duracao,


                    "preco":

                    preco


                }



                supabase.table(

                    "servicos"

                ).insert(

                    dados

                ).execute()



                st.success(

                    "Serviço cadastrado"

                )


                st.rerun()




# ======================================================
# DASHBOARD
# ======================================================



    with abas_admin[3]:


        st.subheader(

            "Indicadores AgendUp"

        )


        empresas = len(

            buscar_tabela(
                "estabelecimentos"
            )

        )


        profissionais = len(

            buscar_tabela(
                "profissionais"
            )

        )


        servicos = len(

            buscar_tabela(
                "servicos"
            )

        )


        agendamentos = len(

            buscar_tabela(
                "agendamentos"
            )

        )



        c1,c2,c3,c4 = st.columns(4)



        c1.metric(

            "Empresas",

            empresas

        )


        c2.metric(

            "Profissionais",

            profissionais

        )


        c3.metric(

            "Serviços",

            servicos

        )


        c4.metric(

            "Agendamentos",

            agendamentos

        )
