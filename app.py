from datetime import datetime, date, time
import streamlit as st
from supabase import create_client


# =====================================================
# CONFIGURAÇÃO
# =====================================================

st.set_page_config(
    page_title="AgendUp",
    page_icon="⚡",
    layout="wide"
)


# =====================================================
# SUPABASE
# =====================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def get_supabase():

    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


supabase = get_supabase()



# =====================================================
# SESSÃO
# =====================================================

if "usuario" not in st.session_state:
    st.session_state.usuario = None


if "tipo_usuario" not in st.session_state:
    st.session_state.tipo_usuario = None


if "empresa_id" not in st.session_state:
    st.session_state.empresa_id = None



# =====================================================
# FUNÇÕES BANCO
# =====================================================


def buscar(tabela):

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
            f"Erro ao consultar {tabela}: {erro}"
        )

        return []




def inserir(tabela, dados):

    try:

        resposta = (
            supabase
            .table(tabela)
            .insert(dados)
            .execute()
        )

        return resposta.data


    except Exception as erro:

        st.error(
            f"Erro ao inserir: {erro}"
        )

        return None




def atualizar_status(id_agendamento, status):

    try:

        (
            supabase
            .table("agendamentos")
            .update(
                {
                    "status": status
                }
            )
            .eq(
                "id",
                id_agendamento
            )
            .execute()
        )


        return True


    except Exception as erro:

        st.error(erro)

        return False




def horario_ocupado(data_hora, profissional_id):


    registros = (

        supabase
        .table("agendamentos")
        .select("*")
        .eq(
            "profissional_id",
            profissional_id
        )
        .eq(
            "data_hora",
            data_hora
        )
        .execute()

    )


    return len(registros.data) > 0





def criar_cliente(nome, telefone):


    clientes = buscar("profiles")


    for cliente in clientes:

        if cliente.get("nome") == nome:

            return cliente["id"]



    novo = inserir(

        "profiles",

        {
            "nome": nome,
            "tipo": "cliente"
        }

    )


    if novo:

        return novo[0]["id"]


    return None





# =====================================================
# MENU
# =====================================================


st.sidebar.title(
    "⚡ AgendUp"
)


if st.session_state.usuario:


    menu = "Painel"


else:


    menu = st.sidebar.radio(

        "Navegação",

        [

            "📅 Agendar",

            "🔐 Login"

        ]

    )





# =====================================================
# ÁREA CLIENTE
# =====================================================


if menu == "📅 Agendar":


    st.title(
        "📅 Agendamento Online"
    )


    st.write(
        "Agende seu atendimento em poucos passos."
    )



    estabelecimentos = buscar(
        "estabelecimentos"
    )



    if not estabelecimentos:


        st.warning(
            "Nenhum estabelecimento disponível."
        )

        st.stop()



    empresas = {


        f"{e['nome']} - {e['categoria']}":
        e


        for e in estabelecimentos

    }



    empresa_nome = st.selectbox(

        "Escolha o estabelecimento",

        empresas.keys()

    )



    empresa = empresas[empresa_nome]



    profissionais = [

        p for p in buscar("profissionais")

        if p["estabelecimento_id"] == empresa["id"]

    ]



    if not profissionais:

        st.warning(
            "Nenhum profissional cadastrado."
        )

        st.stop()



    mapa_profissionais = {

        p["nome"]:
        p

        for p in profissionais

    }



    profissional_nome = st.selectbox(

        "Profissional",

        mapa_profissionais.keys()

    )


    profissional = mapa_profissionais[
        profissional_nome
    ]



    servicos = [

        s for s in buscar("servicos")

        if s["estabelecimento_id"] == empresa["id"]

    ]



    mapa_servicos = {

        s["nome"]:
        s

        for s in servicos

    }



    servico_nome = st.selectbox(

        "Serviço",

        mapa_servicos.keys()

    )


    servico = mapa_servicos[
        servico_nome
    ]



    st.info(

        f"Valor: R$ {servico['preco']}"

    )



    st.divider()



    nome = st.text_input(
        "Nome completo"
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
                "Preencha seus dados."
            )


        else:


            data_hora = (
                f"{data}T{horario}"
            )



            if horario_ocupado(

                data_hora,

                profissional["id"]

            ):


                st.error(
                    "Esse horário já está ocupado."
                )


            else:


                cliente_id = criar_cliente(

                    nome,

                    telefone

                )



                agendamento = {


                    "cliente_id":
                    cliente_id,


                    "profissional_id":
                    profissional["id"],


                    "servico_id":
                    servico["id"],


                    "data_hora":
                    data_hora,


                    "status":
                    "pendente"


                }



                if inserir(

                    "agendamentos",

                    agendamento

                ):


                    st.success(

                        "✅ Agendamento criado!"

                    )
                    # =====================================================
# LOGIN ADMINISTRATIVO
# =====================================================


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



        # LOGIN TEMPORÁRIO MVP
        #
        # posteriormente será migrado
        # para Supabase Auth


        if (

            email == "admin@agendup.com"

            and senha == "123456"

        ):


            st.session_state.usuario = email

            st.session_state.tipo_usuario = "ADMIN"

            st.success(
                "Login realizado"
            )

            st.rerun()



        else:


            st.error(
                "Usuário ou senha inválidos"
            )





# =====================================================
# PAINEL ADMINISTRATIVO
# =====================================================


if st.session_state.usuario:


    st.sidebar.divider()


    st.sidebar.write(
        "Usuário conectado:"
    )


    st.sidebar.success(

        st.session_state.usuario

    )



    if st.sidebar.button(
        "Sair"
    ):


        st.session_state.usuario = None

        st.session_state.tipo_usuario = None

        st.rerun()



    st.title(
        "⚡ Painel AgendUp"
    )



    abas = st.tabs(

        [

            "📅 Agenda",

            "📊 Indicadores"

        ]

    )



# =====================================================
# AGENDA
# =====================================================


    with abas[0]:


        st.subheader(

            "Agendamentos"

        )



        agendamentos = buscar(

            "agendamentos"

        )



        if not agendamentos:


            st.info(

                "Nenhum agendamento encontrado."

            )



        else:



            profissionais = buscar(

                "profissionais"

            )


            servicos = buscar(

                "servicos"

            )


            clientes = buscar(

                "profiles"

            )




            for agendamento in agendamentos:



                profissional = next(

                    (

                        p for p in profissionais

                        if p["id"] ==
                        agendamento["profissional_id"]

                    ),

                    None

                )



                servico = next(

                    (

                        s for s in servicos

                        if s["id"] ==
                        agendamento["servico_id"]

                    ),

                    None

                )



                cliente = next(

                    (

                        c for c in clientes

                        if c["id"] ==
                        agendamento["cliente_id"]

                    ),

                    None

                )



                with st.container(
                    border=True
                ):



                    st.markdown(

                        f"""

### 📅 Atendimento


**Cliente:** 

{cliente['nome'] if cliente else 'Não identificado'}



**Profissional:** 

{profissional['nome'] if profissional else 'N/A'}



**Serviço:** 

{servico['nome'] if servico else 'N/A'}



**Data/Hora:** 

{agendamento['data_hora']}



**Status:**

`{agendamento['status']}`

"""

                    )



                    col1,col2 = st.columns(2)



                    with col1:


                        if st.button(

                            "✅ Confirmar",

                            key=f"confirmar_{agendamento['id']}"

                        ):



                            alterar_status(

                                agendamento["id"],

                                "confirmado"

                            )


                            st.success(

                                "Agendamento confirmado"

                            )


                            st.rerun()



                    with col2:


                        if st.button(

                            "❌ Cancelar",

                            key=f"cancelar_{agendamento['id']}"

                        ):



                            alterar_status(

                                agendamento["id"],

                                "cancelado"

                            )


                            st.warning(

                                "Agendamento cancelado"

                            )


                            st.rerun()





# =====================================================
# INDICADORES
# =====================================================


    with abas[1]:


        st.subheader(

            "Indicadores"

        )


        total = len(

            buscar(

                "agendamentos"

            )

        )


        confirmados = len(

            [

                a for a in buscar("agendamentos")

                if a["status"] == "confirmado"

            ]

        )


        cancelados = len(

            [

                a for a in buscar("agendamentos")

                if a["status"] == "cancelado"

            ]

        )



        c1,c2,c3 = st.columns(3)



        c1.metric(

            "Total",

            total

        )


        c2.metric(

            "Confirmados",

            confirmados

        )


        c3.metric(

            "Cancelados",

            cancelados

        )
        # =====================================================
# SUPER ADMIN
# =====================================================


if st.session_state.get("tipo_usuario") == "ADMIN":


    st.divider()


    st.header(
        "👑 Super Administração"
    )



    abas_admin = st.tabs(

        [

            "🏢 Empresas",

            "👨‍💼 Profissionais",

            "💼 Serviços",

            "📊 Dashboard"

        ]

    )



# =====================================================
# CADASTRO EMPRESAS
# =====================================================


    with abas_admin[0]:


        st.subheader(

            "Cadastrar estabelecimento"

        )



        with st.form(
            "empresa_form"
        ):


            nome_empresa = st.text_input(

                "Nome da empresa"

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


            chave_pix = st.text_input(

                "Chave PIX"

            )



            salvar = st.form_submit_button(

                "Salvar empresa"

            )



            if salvar:



                dados = {


                    "nome":

                    nome_empresa,


                    "categoria":

                    categoria,


                    "chave_pix":

                    chave_pix,


                    "tipo_chave_pix":

                    "aleatoria"


                }



                resultado = inserir(

                    "estabelecimentos",

                    dados

                )



                if resultado:


                    st.success(

                        "Empresa cadastrada!"

                    )


                    st.rerun()





        st.divider()



        st.subheader(

            "Empresas cadastradas"

        )



        empresas = buscar(

            "estabelecimentos"

        )


        st.dataframe(

            empresas,

            use_container_width=True

        )





# =====================================================
# PROFISSIONAIS
# =====================================================


    with abas_admin[1]:


        st.subheader(

            "Cadastrar profissional"

        )



        empresas = buscar(

            "estabelecimentos"

        )



        if empresas:



            mapa = {


                e["nome"]:
                e["id"]


                for e in empresas

            }



            empresa_nome = st.selectbox(

                "Empresa",

                mapa.keys(),

                key="empresa_prof"

            )


            empresa_id = mapa[

                empresa_nome

            ]



            nome = st.text_input(

                "Nome profissional"

            )


            especialidade = st.text_input(

                "Especialidade"

            )



            if st.button(

                "Cadastrar profissional"

            ):



                dados = {


                    "estabelecimento_id":

                    empresa_id,


                    "nome":

                    nome,


                    "especialidade":

                    especialidade


                }



                resultado = inserir(

                    "profissionais",

                    dados

                )



                if resultado:


                    st.success(

                        "Profissional cadastrado"

                    )


                    st.rerun()





# =====================================================
# SERVIÇOS
# =====================================================


    with abas_admin[2]:


        st.subheader(

            "Cadastrar serviço"

        )



        empresas = buscar(

            "estabelecimentos"

        )



        if empresas:



            mapa = {


                e["nome"]:
                e["id"]


                for e in empresas

            }



            empresa_nome = st.selectbox(

                "Empresa",

                mapa.keys(),

                key="empresa_servico"

            )



            empresa_id = mapa[

                empresa_nome

            ]



            nome_servico = st.text_input(

                "Nome do serviço"

            )


            preco = st.number_input(

                "Preço",

                min_value=0.0

            )


            duracao = st.number_input(

                "Duração (minutos)",

                min_value=5,

                value=30

            )



            if st.button(

                "Cadastrar serviço"

            ):



                dados = {


                    "estabelecimento_id":

                    empresa_id,


                    "nome":

                    nome_servico,


                    "preco":

                    preco,


                    "duracao_minutos":

                    duracao


                }



                resultado = inserir(

                    "servicos",

                    dados

                )



                if resultado:


                    st.success(

                        "Serviço cadastrado"

                    )


                    st.rerun()





# =====================================================
# DASHBOARD
# =====================================================


    with abas_admin[3]:


        st.subheader(

            "📊 Visão geral"

        )



        total_empresas = len(

            buscar(

                "estabelecimentos"

            )

        )



        total_profissionais = len(

            buscar(

                "profissionais"

            )

        )



        total_servicos = len(

            buscar(

                "servicos"

            )

        )



        total_agendamentos = len(

            buscar(

                "agendamentos"

            )

        )




        c1,c2,c3,c4 = st.columns(4)



        c1.metric(

            "Empresas",

            total_empresas

        )


        c2.metric(

            "Profissionais",

            total_profissionais

        )


        c3.metric(

            "Serviços",

            total_servicos

        )


        c4.metric(

            "Agendamentos",

            total_agendamentos

        )
