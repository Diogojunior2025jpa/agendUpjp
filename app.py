from __future__ import annotations

from datetime import datetime
from typing import Any

import requests
import streamlit as st

from supabase_client import SupabaseClient, SupabaseConnectorError


st.set_page_config(
    page_title="Agendamentos PIX",
    page_icon="P",
    layout="wide",
)


ID_COLUMN = "id"
STATUS_PENDING = {"pendente", "pending", "aguardando", "aguardando pagamento"}
STATUS_CONFIRMED = {"confirmado", "confirmed"}


def first_value(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def appointment_id(row: dict[str, Any]) -> Any:
    return row.get(ID_COLUMN)


def normalized_status(row: dict[str, Any]) -> str:
    return str(row.get("status", "") or "").strip()


def is_pending(row: dict[str, Any]) -> bool:
    return normalized_status(row).casefold() in STATUS_PENDING


def is_confirmed(row: dict[str, Any]) -> bool:
    return normalized_status(row).casefold() in STATUS_CONFIRMED


def display_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            return value
    return str(value)


def appointment_title(row: dict[str, Any], row_number: int) -> str:
    name = first_value(
        row,
        (
            "cliente_nome",
            "nome_cliente",
            "cliente",
            "nome",
            "name",
        ),
    )
    identifier = row.get(ID_COLUMN)
    if name:
        return str(name)
    if identifier:
        return f"Agendamento #{identifier}"
    return f"Agendamento #{row_number}"


def render_appointment(
    row: dict[str, Any],
    row_number: int,
    client: SupabaseClient,
) -> None:
    status = normalized_status(row) or "Sem status"
    row_id = appointment_id(row)
    pending = is_pending(row)

    with st.container(border=True):
        content_column, action_column = st.columns([4, 1], vertical_alignment="center")
        with content_column:
            st.markdown(f"**{appointment_title(row, row_number)}**")
            date_value = first_value(
                row,
                (
                    "data_hora",
                    "datetime",
                    "data_agendamento",
                    "data",
                    "date",
                ),
            )
            time_value = first_value(row, ("horario", "hora", "time"))
            service_value = first_value(
                row,
                ("servico", "serviço", "service", "procedimento", "descricao"),
            )
            contact_value = first_value(row, ("telefone", "phone", "celular"))

            details: list[str] = []
            if date_value:
                details.append(f"Data: {display_value(date_value)}")
            if time_value:
                details.append(f"Horário: {display_value(time_value)}")
            if service_value:
                details.append(f"Serviço: {display_value(service_value)}")
            if contact_value:
                details.append(f"Contato: {display_value(contact_value)}")
            st.caption(" · ".join(details) if details else "Detalhes do agendamento")

            status_color = "green" if is_confirmed(row) else "orange" if pending else "gray"
            st.markdown(f":{status_color}[Status: **{status}**]")
            with st.expander("Ver dados completos"):
                st.json(row)

        with action_column:
            if pending:
                if row_id in (None, ""):
                    st.warning("Sem identificador")
                elif st.button(
                    "Confirmar PIX",
                    key=f"confirm-pix-{row_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        client.confirm_pix(
                            id_column=ID_COLUMN,
                            appointment_id=row_id,
                            current_status=status,
                        )
                    except SupabaseConnectorError as error:
                        st.error(str(error))
                    else:
                        st.success("PIX confirmado.")
                        st.rerun()
            else:
                st.caption("Sem ação pendente")


def load_appointments(client: SupabaseClient) -> list[dict[str, Any]]:
    return client.list_appointments()


st.title("Agendamentos PIX")
st.write("Acompanhe os agendamentos e confirme os pagamentos PIX pendentes.")

toolbar_column, note_column = st.columns([1, 4])
with toolbar_column:
    if st.button("Atualizar lista", use_container_width=True):
        st.rerun()
with note_column:
    st.caption("Os dados são carregados diretamente da tabela `agendamentos`.")

client = SupabaseClient()
try:
    appointments = load_appointments(client)
except (SupabaseConnectorError, requests.exceptions.RequestException) as error:
    st.error(f"Não foi possível carregar os agendamentos: {error}")
    st.stop()

pending_count = sum(is_pending(row) for row in appointments)
confirmed_count = sum(is_confirmed(row) for row in appointments)
other_count = len(appointments) - pending_count - confirmed_count

metric_columns = st.columns(4)
metric_columns[0].metric("Total", len(appointments))
metric_columns[1].metric("Pendentes", pending_count)
metric_columns[2].metric("Confirmados", confirmed_count)
metric_columns[3].metric("Outros status", other_count)

st.divider()

if not appointments:
    st.info("Nenhum agendamento encontrado na tabela agendamentos.")
else:
    st.subheader("Dados carregados")
    st.dataframe(appointments, use_container_width=True, hide_index=True)
    st.subheader("Agendamentos")
    for index, row in enumerate(appointments, start=1):
        render_appointment(row, index, client)
