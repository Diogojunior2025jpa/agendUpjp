import streamlit as st
from datetime import date, time
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
def conectar():

    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


supabase = conectar()



# =====================================================
# FUNÇÕES
# =====================================================


def buscar(tabela):

    try:

        resultado = (
            supabase
            .table(tabela)
            .select("*")
            .execute()
        )

        return resultado.data or []

    except Exception as e:

        st.error(
            f"Erro buscando {tabela}: {e}"
        )

        return []



def inserir(tabela, dados):

    try:

        resultado = (
            supabase
            .table(tabela)
            .insert(dados)
            .execute()
        )

        return resultado.data


    except Exception as e:

        st.error(
            f"Erro inserindo: {e}"
        )

        return None



def criar_cliente(nome):

    usuarios = buscar("profiles")


    for u in usuarios:

        if u["nome"].lower() == nome.lower():

            return u["id"]



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



def horario_existe(data_hora, profissional):


    dados = (

        supabase
        .table("agendamentos")
        .select("*")
        .eq(
            "profissional_id",
            profissional
        )
        .eq(
            "data_hora",
            data_hora
        )
        .execute()

    )


    return len(dados.data) > 0




# =====================================================
# MENU
# =====================================================


st.sidebar.title(
    "⚡ AgendUp"
)


opcao = st.sidebar.radio(

    "Navegação",

    [
        "📅 Agendar",
        "🔐 Login"
    ]

)



# =====================================================
# CLIENTE
# =====================================================


if opcao == "📅 Agendar":


    st.title(
        "📅 Agendamento Online"
    )


    st.write(
        "Escolha o local, profissional e serviço."
    )



    estabelecimentos = buscar(
        "estabelecimentos"
    )



    if not estabelecimentos:

        st.warning(
            "Nenhum estabelecimento cadastrado."
        )

        st.stop()



    empresas = {}

    for e in estabelecimentos:

        empresas[
            f"{e['nome']} - {e['categoria']}"
        ] = e



    empresa_nome = st.selectbox(

        "Estabelecimento",

        empresas.keys()

    )



    empresa = empresas[empresa_nome]



    # -------------------------
    # PROFISSIONAIS
    # -------------------------


    profissionais = []


    for p in buscar("profissionais"):


        if int(p["estabelecimento_id"]) == int(empresa["id"]):

            profissionais.append(p)



    if not profissionais:


        st.warning(

            "Nenhum profissional cadastrado para este estabelecimento."

        )

        st.stop()



    profissionais_dict = {

        p["nome"]: p

        for p in profissionais

    }



    profissional_nome = st.selectbox(

        "Profissional",

        profissionais_dict.keys()

    )



    profissional = profissionais_dict[
        profissional_nome
    ]



    # -------------------------
    # SERVIÇOS
    # -------------------------


    servicos = []


    for s in buscar("servicos"):


        if int(s["estabelecimento_id"]) == int(empresa["id"]):

            servicos.append(s)



    if not servicos:


        st.warning(

            "Nenhum serviço cadastrado."

        )

        st.stop()



    servicos_dict = {


        s["nome"]: s

        for s in servicos

    }



    servico_nome = st.selectbox(

        "Serviço",

        servicos_dict.keys()

    )


    servico = servicos_dict[servico_nome]



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



    c1,c2 = st.columns(2)



    with c1:

        data = st.date_input(

            "Data",

            date.today()

        )



    with c2:

        hora = st.time_input(

            "Horário",

            time(8,0)

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


            data_hora = (

                f"{data}T{hora}"

            )



            if horario_existe(

                data_hora,

                profissional["id"]

            ):


                st.error(

                    "Horário já ocupado."

                )


            else:


                cliente_id = criar_cliente(

                    nome

                )



                novo_agendamento = {


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



                resultado = inserir(

                    "agendamentos",

                    novo_agendamento

                )



                if resultado:


                    st.success(

                        "✅ Agendamento realizado com sucesso!"

                    )
# =====================================================
# LOGIN ADMINISTRATIVO
# =====================================================


if opcao == "🔐 Login":


    st.title(
        "🔐 Área Administrativa"
    )


    email = st.text_input(
        "E-mail"
    )


    senha = st.text_input(
        "Senha",
        type="password"
    )



    if st.button(
        "Entrar"
    ):


        usuarios_validos = {


            "admin@agendup.com":

            "123456",


            "adm@gmail.com":

            "123456"

        }



        if email in usuarios_validos and senha == usuarios_validos[email]:


            st.session_state["login"] = True

            st.session_state["usuario"] = email


            st.success(
                "Login realizado!"
            )


            st.rerun()



        else:


            st.error(

                "Usuário ou senha inválidos."

            )





# =====================================================
# PAINEL ADMINISTRATIVO
# =====================================================


if st.session_state.get("login"):


    st.sidebar.success(

        f"Logado: {st.session_state.usuario}"

    )



    if st.sidebar.button(

        "Sair"

    ):


        st.session_state.login = False

        st.session_state.usuario = None

        st.rerun()



    st.title(

        "⚡ Painel AgendUp"

    )



    aba1, aba2 = st.tabs(

        [

            "📅 Agenda",

            "📊 Indicadores"

        ]

    )



# =====================================================
# AGENDA
# =====================================================


    with aba1:


        st.subheader(

            "Agendamentos realizados"

        )



        agendamentos = buscar(

            "agendamentos"

        )



        profissionais = buscar(

            "profissionais"

        )


        servicos = buscar(

            "servicos"

        )


        clientes = buscar(

            "profiles"

        )



        if not agendamentos:


            st.info(

                "Nenhum agendamento encontrado."

            )



        else:



            for ag in agendamentos:



                profissional = next(

                    (

                        p for p in profissionais

                        if int(p["id"]) == int(ag["profissional_id"])

                    ),

                    None

                )



                servico = next(

                    (

                        s for s in servicos

                        if int(s["id"]) == int(ag["servico_id"])

                    ),

                    None

                )



                cliente = next(

                    (

                        c for c in clientes

                        if c["id"] == ag["cliente_id"]

                    ),

                    None

                )



                with st.container(border=True):


                    st.markdown(

                        f"""

### 📅 Atendimento


**Cliente:**

{cliente['nome'] if cliente else 'Não identificado'}



**Profissional:**

{profissional['nome'] if profissional else 'Não encontrado'}



**Serviço:**

{servico['nome'] if servico else 'Não encontrado'}



**Data/Hora:**

{ag['data_hora']}



**Status:**

{ag['status']}

"""

                    )



                    c1,c2 = st.columns(2)



                    with c1:


                        if st.button(

                            "✅ Confirmar",

                            key=f"confirma_{ag['id']}"

                        ):



                            (

                                supabase

                                .table("agendamentos")

                                .update({

                                    "status":

                                    "confirmado"

                                })

                                .eq(

                                    "id",

                                    ag["id"]

                                )

                                .execute()

                            )


                            st.success(

                                "Agendamento confirmado."

                            )


                            st.rerun()



                    with c2:


                        if st.button(

                            "❌ Cancelar",

                            key=f"cancela_{ag['id']}"

                        ):



                            (

                                supabase

                                .table("agendamentos")

                                .update({

                                    "status":

                                    "cancelado"

                                })

                                .eq(

                                    "id",

                                    ag["id"]

                                )

                                .execute()

                            )


                            st.warning(

                                "Agendamento cancelado."

                            )


                            st.rerun()





# =====================================================
# INDICADORES
# =====================================================


    with aba2:


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

                x for x in buscar("agendamentos")

                if x["status"] == "confirmado"

            ]

        )



        pendentes = len(

            [

                x for x in buscar("agendamentos")

                if x["status"] == "pendente"

            ]

        )



        cancelados = len(

            [

                x for x in buscar("agendamentos")

                if x["status"] == "cancelado"

            ]

        )



        c1,c2,c3,c4 = st.columns(4)



        c1.metric(

            "Total",

            total

        )


        c2.metric(

            "Confirmados",

            confirmados

        )


        c3.metric(

            "Pendentes",

            pendentes

        )


        c4.metric(

            "Cancelados",

            cancelados

        )
# =====================================================
# CADASTROS ADMINISTRATIVOS
# =====================================================


if st.session_state.get("login"):


    st.divider()


    st.header(
        "⚙️ Cadastros do Sistema"
    )


    aba_empresa, aba_profissional, aba_servico = st.tabs(

        [

            "🏢 Empresas",

            "👨‍💼 Profissionais",

            "💼 Serviços"

        ]

    )



# =====================================================
# EMPRESAS
# =====================================================


    with aba_empresa:


        st.subheader(

            "Cadastrar estabelecimento"

        )


        with st.form(

            "form_empresa"

        ):


            nome_empresa = st.text_input(

                "Nome"

            )


            categoria_empresa = st.selectbox(

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



            salvar_empresa = st.form_submit_button(

                "Salvar"

            )



            if salvar_empresa:



                dados = {


                    "nome":

                    nome_empresa,


                    "categoria":

                    categoria_empresa,


                    "chave_pix":

                    chave_pix,


                    "tipo_chave_pix":

                    "telefone"

                }



                resultado = inserir(

                    "estabelecimentos",

                    dados

                )



                if resultado:


                    st.success(

                        "Empresa cadastrada com sucesso!"

                    )


                    st.rerun()





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


    with aba_profissional:


        st.subheader(

            "Cadastrar profissional"

        )



        empresas = buscar(

            "estabelecimentos"

        )



        if empresas:


            mapa_empresas = {


                e["nome"]:

                e["id"]


                for e in empresas

            }



            empresa_nome = st.selectbox(

                "Estabelecimento",

                mapa_empresas.keys(),

                key="empresa_profissional"

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

                "Cadastrar profissional"

            ):



                dados = {


                    "estabelecimento_id":

                    empresa_id,


                    "nome":

                    nome_profissional,


                    "especialidade":

                    especialidade

                }



                resultado = inserir(

                    "profissionais",

                    dados

                )



                if resultado:


                    st.success(

                        "Profissional cadastrado!"

                    )


                    st.rerun()



        else:


            st.warning(

                "Cadastre uma empresa primeiro."

            )





# =====================================================
# SERVIÇOS
# =====================================================


    with aba_servico:


        st.subheader(

            "Cadastrar serviço"

        )



        empresas = buscar(

            "estabelecimentos"

        )



        if empresas:


            mapa_empresas = {


                e["nome"]:

                e["id"]


                for e in empresas

            }



            empresa_nome = st.selectbox(

                "Estabelecimento",

                mapa_empresas.keys(),

                key="empresa_servico"

            )



            empresa_id = mapa_empresas[

                empresa_nome

            ]



            nome_servico = st.text_input(

                "Nome serviço"

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

                        "Serviço cadastrado!"

                    )


                    st.rerun()



        else:


            st.warning(

                "Cadastre uma empresa primeiro."

            )
# =====================================================
# DASHBOARD GERAL
# =====================================================


if st.session_state.get("login"):


    st.divider()


    st.header(
        "📊 Dashboard AgendUp"
    )



    empresas = buscar(

        "estabelecimentos"

    )


    profissionais = buscar(

        "profissionais"

    )


    servicos = buscar(

        "servicos"

    )


    agendamentos = buscar(

        "agendamentos"

    )



    # -----------------------------
    # MÉTRICAS
    # -----------------------------


    col1,col2,col3,col4 = st.columns(4)



    with col1:

        st.metric(

            "🏢 Empresas",

            len(empresas)

        )



    with col2:

        st.metric(

            "👨‍💼 Profissionais",

            len(profissionais)

        )



    with col3:

        st.metric(

            "💼 Serviços",

            len(servicos)

        )



    with col4:

        st.metric(

            "📅 Agendamentos",

            len(agendamentos)

        )



    st.divider()



    # -----------------------------
    # FATURAMENTO ESTIMADO
    # -----------------------------


    faturamento = 0


    for ag in agendamentos:


        if ag.get("status") == "confirmado":


            servico = next(

                (

                    s for s in servicos

                    if int(s["id"]) == int(ag["servico_id"])

                ),

                None

            )


            if servico:


                faturamento += float(

                    servico.get(

                        "preco",

                        0

                    )

                )



    st.subheader(

        "💰 Faturamento estimado"

    )


    st.metric(

        "Confirmados",

        f"R$ {faturamento:.2f}"

    )



    st.divider()



    # -----------------------------
    # ÚLTIMOS AGENDAMENTOS
    # -----------------------------


    st.subheader(

        "📅 Últimos agendamentos"

    )



    if agendamentos:


        for ag in agendamentos[-10:]:



            cliente = next(

                (

                    c for c in buscar("profiles")

                    if c["id"] == ag["cliente_id"]

                ),

                None

            )



            servico = next(

                (

                    s for s in servicos

                    if int(s["id"]) == int(ag["servico_id"])

                ),

                None

            )



            st.write(

                f"""

**Cliente:** {cliente['nome'] if cliente else 'N/A'}

  
**Serviço:** {servico['nome'] if servico else 'N/A'}

  
**Data:** {ag['data_hora']}

  
**Status:** {ag['status']}

---

"""

            )


    else:


        st.info(

            "Ainda não existem agendamentos."

        )
