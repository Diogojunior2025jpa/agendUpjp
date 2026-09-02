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
# CONEXÃO SUPABASE
# =====================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def conectar_supabase():

    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


supabase = conectar_supabase()



# =====================================================
# SESSÃO
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False


if "usuario" not in st.session_state:
    st.session_state.usuario = None



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

        supabase.table(

            "agendamentos"

        ).update(

            {
                "status": status
            }

        ).eq(

            "id",
            id_agendamento

        ).execute()


        return True


    except Exception as erro:

        st.error(
            f"Erro ao atualizar: {erro}"
        )

        return False





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




def horario_ocupado(data_hora, profissional_id):


    resposta = (

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


    return len(resposta.data) > 0





# =====================================================
# MENU
# =====================================================


st.sidebar.title(
    "⚡ AgendUp"
)



menu = st.sidebar.radio(

    "Menu",

    [

        "📅 Agendar",

        "🔐 Login"

    ]

)
# =====================================================
# ÁREA PÚBLICA — AGENDAMENTO DO CLIENTE
# =====================================================

if menu == "📅 Agendar":

    st.title("📅 Agendamento Online")
    st.write("Escolha o estabelecimento, profissional, serviço, data e horário.")

    # -------------------------------------------------
    # ESTABELECIMENTOS
    # -------------------------------------------------

    estabelecimentos = buscar("estabelecimentos")

    if not estabelecimentos:
        st.warning("Nenhum estabelecimento cadastrado no momento.")
        st.stop()

    mapa_estabelecimentos = {}

    for estabelecimento in estabelecimentos:

        nome_estabelecimento = estabelecimento.get(
            "nome",
            f"Estabelecimento {estabelecimento.get('id')}"
        )

        categoria = estabelecimento.get("categoria", "")

        rotulo = (
            f"{nome_estabelecimento} - {categoria}"
            if categoria
            else nome_estabelecimento
        )

        mapa_estabelecimentos[rotulo] = estabelecimento

    estabelecimento_selecionado = st.selectbox(
        "Estabelecimento",
        list(mapa_estabelecimentos.keys())
    )

    empresa = mapa_estabelecimentos[
        estabelecimento_selecionado
    ]

    empresa_id = empresa.get("id")

    # -------------------------------------------------
    # PROFISSIONAIS
    # -------------------------------------------------

    todos_profissionais = buscar("profissionais")

    profissionais_empresa = []

    for profissional in todos_profissionais:

        try:
            if int(profissional.get("estabelecimento_id")) == int(empresa_id):
                profissionais_empresa.append(profissional)

        except (TypeError, ValueError):
            continue

    if not profissionais_empresa:

        st.warning(
            "Nenhum profissional cadastrado para este estabelecimento."
        )

        st.info(
            "O administrador precisa cadastrar pelo menos um profissional "
            "vinculado a este estabelecimento."
        )

        st.stop()

    mapa_profissionais = {}

    for profissional in profissionais_empresa:

        nome_profissional = profissional.get(
            "nome",
            f"Profissional {profissional.get('id')}"
        )

        especialidade = profissional.get("especialidade")

        if especialidade:
            rotulo_profissional = (
                f"{nome_profissional} — {especialidade}"
            )
        else:
            rotulo_profissional = nome_profissional

        mapa_profissionais[
            rotulo_profissional
        ] = profissional

    profissional_selecionado = st.selectbox(
        "Profissional",
        list(mapa_profissionais.keys())
    )

    profissional = mapa_profissionais[
        profissional_selecionado
    ]

    profissional_id = profissional.get("id")

    # -------------------------------------------------
    # SERVIÇOS
    # -------------------------------------------------

    todos_servicos = buscar("servicos")

    servicos_empresa = []

    for servico_item in todos_servicos:

        try:
            if int(servico_item.get("estabelecimento_id")) == int(empresa_id):
                servicos_empresa.append(servico_item)

        except (TypeError, ValueError):
            continue

    if not servicos_empresa:

        st.warning(
            "Nenhum serviço cadastrado para este estabelecimento."
        )

        st.info(
            "O administrador precisa cadastrar pelo menos um serviço."
        )

        st.stop()

    mapa_servicos = {}

    for servico_item in servicos_empresa:

        nome_servico = servico_item.get(
            "nome",
            f"Serviço {servico_item.get('id')}"
        )

        preco_servico = servico_item.get("preco", 0)

        try:
            preco_formatado = float(preco_servico)
        except (TypeError, ValueError):
            preco_formatado = 0.0

        rotulo_servico = (
            f"{nome_servico} — R$ {preco_formatado:.2f}"
        )

        mapa_servicos[rotulo_servico] = servico_item

    servico_selecionado = st.selectbox(
        "Serviço",
        list(mapa_servicos.keys())
    )

    servico = mapa_servicos[
        servico_selecionado
    ]

    servico_id = servico.get("id")

    preco = servico.get("preco", 0)
    duracao = servico.get("duracao_minutos", 30)

    try:
        preco = float(preco)
    except (TypeError, ValueError):
        preco = 0.0

    try:
        duracao = int(duracao)
    except (TypeError, ValueError):
        duracao = 30

    col_info1, col_info2 = st.columns(2)

    with col_info1:
        st.info(
            f"💰 Valor: R$ {preco:.2f}"
        )

    with col_info2:
        st.info(
            f"⏱️ Duração: {duracao} minutos"
        )

    st.divider()

    # -------------------------------------------------
    # DADOS DO CLIENTE
    # -------------------------------------------------

    st.subheader("Seus dados")

    nome_cliente = st.text_input(
        "Nome completo",
        key="cliente_nome"
    )

    telefone_cliente = st.text_input(
        "WhatsApp com DDD",
        placeholder="Ex.: 83999999999",
        key="cliente_whatsapp"
    )

    # -------------------------------------------------
    # DATA E HORÁRIO
    # -------------------------------------------------

    st.subheader("Data e horário")

    coluna_data, coluna_hora = st.columns(2)

    with coluna_data:

        data_agendamento = st.date_input(
            "Data",
            value=date.today(),
            min_value=date.today(),
            key="data_agendamento"
        )

    with coluna_hora:

        hora_agendamento = st.time_input(
            "Horário",
            value=time(8, 0),
            step=900,
            key="hora_agendamento"
        )

    # -------------------------------------------------
    # RESUMO
    # -------------------------------------------------

    st.divider()

    st.subheader("Resumo do agendamento")

    st.write(
        f"**Estabelecimento:** {empresa.get('nome', '-')}"
    )

    st.write(
        f"**Profissional:** {profissional.get('nome', '-')}"
    )

    st.write(
        f"**Serviço:** {servico.get('nome', '-')}"
    )

    st.write(
        f"**Valor:** R$ {preco:.2f}"
    )

    st.write(
        f"**Data:** {data_agendamento.strftime('%d/%m/%Y')}"
    )

    st.write(
        f"**Horário:** {hora_agendamento.strftime('%H:%M')}"
    )

    # -------------------------------------------------
    # CONFIRMAR AGENDAMENTO
    # -------------------------------------------------

    if st.button(
        "✅ Confirmar Agendamento",
        type="primary",
        use_container_width=True
    ):

        nome_limpo = nome_cliente.strip()
        telefone_limpo = telefone_cliente.strip()

        if not nome_limpo:

            st.error(
                "Informe o seu nome."
            )

        elif not telefone_limpo:

            st.error(
                "Informe o seu WhatsApp."
            )

        elif len(
            "".join(
                caractere
                for caractere in telefone_limpo
                if caractere.isdigit()
            )
        ) < 10:

            st.error(
                "Informe um número de WhatsApp válido com DDD."
            )

        else:

            data_hora_objeto = datetime.combine(
                data_agendamento,
                hora_agendamento
            )

            data_hora_iso = data_hora_objeto.isoformat()

            try:

                ocupado = horario_ocupado(
                    data_hora_iso,
                    profissional_id
                )

            except Exception as erro:

                st.error(
                    f"Não foi possível verificar o horário: {erro}"
                )

                ocupado = True

            if ocupado:

                st.error(
                    "❌ Este profissional já possui um "
                    "agendamento neste horário."
                )

            else:

                cliente_id = criar_cliente(
                    nome_limpo,
                    telefone_limpo
                )

                if not cliente_id:

                    st.error(
                        "Não foi possível cadastrar ou localizar o cliente."
                    )

                else:

                    novo_agendamento = {
                        "cliente_id": cliente_id,
                        "profissional_id": profissional_id,
                        "servico_id": servico_id,
                        "data_hora": data_hora_iso,
                        "status": "pendente"
                    }

                    resultado = inserir(
                        "agendamentos",
                        novo_agendamento
                    )

                    if resultado:

                        st.success(
                            "🎉 Agendamento realizado com sucesso!"
                        )

                        st.write(
                            "Seu agendamento ficará como **pendente** "
                            "até ser confirmado pelo estabelecimento."
                        )

                        if empresa.get("chave_pix"):

                            st.info(
                                f"💳 Chave PIX do estabelecimento: "
                                f"{empresa.get('chave_pix')}"
                            )

                        st.balloons()


# =====================================================
# LOGIN ADMINISTRATIVO
# =====================================================

elif menu == "🔐 Login":

    st.title("🔐 Área Administrativa")

    st.write(
        "Entre para administrar estabelecimentos, "
        "profissionais, serviços e agendamentos."
    )

    email_admin = st.text_input(
        "E-mail",
        key="login_email"
    )

    senha_admin = st.text_input(
        "Senha",
        type="password",
        key="login_senha"
    )

    if st.button(
        "Entrar",
        type="primary",
        use_container_width=True
    ):

        email_normalizado = email_admin.strip().lower()

        usuarios_admin = {
            "admin@agendup.com": "123456",
            "adm@gmail.com": "123456"
        }

        if (
            email_normalizado in usuarios_admin
            and senha_admin == usuarios_admin[email_normalizado]
        ):

            st.session_state.login = True
            st.session_state.usuario = email_normalizado

            st.success(
                "Login realizado com sucesso."
            )

            st.rerun()

        else:

            st.error(
                "E-mail ou senha inválidos."
            )
# =====================================================
# PAINEL ADMINISTRATIVO
# =====================================================


if st.session_state.get("login"):


    st.sidebar.divider()

    st.sidebar.success(
        f"Usuário: {st.session_state.usuario}"
    )


    if st.sidebar.button(
        "🚪 Sair"
    ):

        st.session_state.login = False
        st.session_state.usuario = None

        st.rerun()



    st.title(
        "⚡ Painel Administrativo AgendUp"
    )



    aba_agenda, aba_indicadores = st.tabs(

        [

            "📅 Agenda",

            "📊 Indicadores"

        ]

    )



# =====================================================
# AGENDA
# =====================================================


    with aba_agenda:


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


            clientes = buscar(
                "profiles"
            )


            profissionais = buscar(
                "profissionais"
            )


            servicos = buscar(
                "servicos"
            )



            for agendamento in agendamentos:


                cliente = None

                profissional = None

                servico = None



                for c in clientes:

                    if str(c.get("id")) == str(
                        agendamento.get("cliente_id")
                    ):

                        cliente = c

                        break



                for p in profissionais:

                    if int(p.get("id")) == int(
                        agendamento.get("profissional_id")
                    ):

                        profissional = p

                        break



                for s in servicos:

                    if int(s.get("id")) == int(
                        agendamento.get("servico_id")
                    ):

                        servico = s

                        break



                with st.container(
                    border=True
                ):



                    st.markdown(

f"""
## 📅 Atendimento

👤 **Cliente:**  
{cliente.get('nome') if cliente else 'Não identificado'}

📱 **Telefone:**  
{cliente.get('telefone') if cliente and cliente.get('telefone') else 'Não informado'}

✂️ **Profissional:**  
{profissional.get('nome') if profissional else 'Não encontrado'}

💼 **Serviço:**  
{servico.get('nome') if servico else 'Não encontrado'}

🕒 **Data/Hora:**  
{agendamento.get('data_hora')}

📌 **Status atual:**  
`{agendamento.get('status')}`
"""
                    )



                    col1, col2 = st.columns(2)



                    with col1:


                        if st.button(

                            "✅ Confirmar",

                            key=f"confirmar_{agendamento['id']}",

                            use_container_width=True

                        ):


                            try:


                                resposta = (

                                    supabase

                                    .table(
                                        "agendamentos"
                                    )

                                    .update(

                                        {
                                            "status":
                                            "confirmado"
                                        }

                                    )

                                    .eq(

                                        "id",

                                        agendamento["id"]

                                    )

                                    .execute()

                                )


                                st.success(
                                    "Agendamento confirmado!"
                                )


                                st.rerun()



                            except Exception as erro:


                                st.error(

                                    "Erro ao confirmar:"
                                )


                                st.code(
                                    str(erro)
                                )





                    with col2:


                        if st.button(

                            "❌ Cancelar",

                            key=f"cancelar_{agendamento['id']}",

                            use_container_width=True

                        ):


                            try:


                                resposta = (

                                    supabase

                                    .table(
                                        "agendamentos"
                                    )

                                    .update(

                                        {
                                            "status":
                                            "cancelado"
                                        }

                                    )

                                    .eq(

                                        "id",

                                        agendamento["id"]

                                    )

                                    .execute()

                                )


                                st.warning(
                                    "Agendamento cancelado!"
                                )


                                st.rerun()



                            except Exception as erro:


                                st.error(

                                    "Erro ao cancelar:"
                                )


                                st.code(
                                    str(erro)
                                )



# =====================================================
# INDICADORES
# =====================================================


    with aba_indicadores:


        st.subheader(
            "📊 Indicadores"
        )


        todos = buscar(
            "agendamentos"
        )


        total = len(
            todos
        )


        confirmados = len(

            [

                a for a in todos

                if a.get("status")
                == "confirmado"

            ]

        )


        pendentes = len(

            [

                a for a in todos

                if a.get("status")
                == "pendente"

            ]

        )


        cancelados = len(

            [

                a for a in todos

                if a.get("status")
                == "cancelado"

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
        "⚙️ Administração do AgendUp"
    )


    aba_empresa, aba_profissional, aba_servico, aba_dashboard = st.tabs(

        [

            "🏢 Empresas",

            "👨‍💼 Profissionais",

            "💼 Serviços",

            "📊 Dashboard"

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
            "cadastro_empresa"
        ):


            nome_empresa = st.text_input(
                "Nome do estabelecimento"
            )


            categoria = st.selectbox(

                "Categoria",

                [

                    "Barbearia",

                    "Odontologia",

                    "Estética",

                    "Consultório",

                    "Outros"

                ]

            )


            chave_pix = st.text_input(
                "Chave PIX"
            )


            salvar_empresa = st.form_submit_button(
                "Cadastrar empresa"
            )



            if salvar_empresa:


                dados_empresa = {


                    "nome":
                    nome_empresa,


                    "categoria":
                    categoria,


                    "chave_pix":
                    chave_pix,


                    "tipo_chave_pix":
                    "pix"

                }



                resultado = inserir(

                    "estabelecimentos",

                    dados_empresa

                )



                if resultado:


                    st.success(
                        "Empresa cadastrada!"
                    )


                    st.rerun()





        st.subheader(
            "Empresas existentes"
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


            lista_empresas = {


                e["nome"]:
                e["id"]


                for e in empresas

            }



            empresa_nome = st.selectbox(

                "Empresa",

                lista_empresas.keys(),

                key="empresa_prof"

            )


            empresa_id = lista_empresas[
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



            lista_empresas = {


                e["nome"]:
                e["id"]


                for e in empresas

            }



            empresa_nome = st.selectbox(

                "Empresa",

                lista_empresas.keys(),

                key="empresa_serv"

            )


            empresa_id = lista_empresas[
                empresa_nome
            ]



            nome_servico = st.text_input(

                "Nome do serviço"

            )


            preco = st.number_input(

                "Preço",

                min_value=0.0,

                step=0.50,

                format="%.2f"

            )


            duracao = st.number_input(

                "Duração em minutos",

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
# DASHBOARD
# =====================================================


    with aba_dashboard:


        st.subheader(

            "📊 Visão geral do sistema"

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


        st.divider()


        st.info(

            """
            Próximas evoluções:

            ✅ WhatsApp automático

            ✅ Login individual por empresa

            ✅ Calendário visual

            ✅ Pagamento PIX integrado

            ✅ Planos de assinatura SaaS

            """
        )
