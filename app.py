import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import pytz

st.set_page_config(
    page_title="Contador de Hora Extra",
    page_icon="⏰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

with open(".streamlit/style.css", "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

TZ_SP = pytz.timezone("America/Sao_Paulo")

DIAS_SEMANA = {
    0: "SEGUNDA-FEIRA",
    1: "TERÇA-FEIRA",
    2: "QUARTA-FEIRA",
    3: "QUINTA-FEIRA",
    4: "SEXTA-FEIRA",
    5: "SÁBADO",
    6: "DOMINGO"
}

NOME_USUARIO = "Amanda Lucas"
VALOR_HORA_PADRAO = 9.10
NOME_PLANILHA = "Horas Extras"
NOME_ABA = "Registros"


@st.cache_resource
def autenticar_google():
    try:
        credentials_dict = st.secrets["google_service_account"]
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        return credentials
    except Exception as e:
        st.error("Erro ao carregar credenciais do Google")
        return None


@st.cache_resource
def conectar_planilha():
    credentials = autenticar_google()
    if not credentials:
        return None

    try:
        client = gspread.authorize(credentials)
        planilha = client.open(NOME_PLANILHA)
        return planilha
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Planilha '{NOME_PLANILHA}' não encontrada")
        return None
    except Exception as e:
        st.error("Erro ao conectar na planilha")
        return None


def obter_aba_registros(planilha):
    try:
        aba = planilha.worksheet(NOME_ABA)
        return aba
    except gspread.exceptions.WorksheetNotFound:
        aba = planilha.add_worksheet(title=NOME_ABA, rows=100, cols=11)
        aba.append_row([
            "nome", "data", "mes", "dia_semana",
            "tipo", "inicio", "fim", "horas",
            "valor_hora", "valor_total", "criado_em"
        ])
        return aba


def formatar_hora(valor_str):
    if not valor_str:
        return None

    apenas_numeros = ''.join(filter(str.isdigit, valor_str))

    if len(apenas_numeros) == 0:
        return None

    if len(apenas_numeros) > 4:
        apenas_numeros = apenas_numeros[:4]

    if len(apenas_numeros) < 4:
        return None

    horas = apenas_numeros[:2]
    minutos = apenas_numeros[2:4]

    try:
        h = int(horas)
        m = int(minutos)
        if 0 <= h < 24 and 0 <= m < 60:
            return f"{h:02d}:{m:02d}"
    except:
        pass

    return None


def calcular_horas(inicio, fim):
    if not inicio or not fim:
        return 0, "0h"

    inicio_h, inicio_m = map(int, inicio.split(":"))
    fim_h, fim_m = map(int, fim.split(":"))

    inicio_min = inicio_h * 60 + inicio_m
    fim_min = fim_h * 60 + fim_m

    if fim_min <= inicio_min:
        return None, None

    total_minutos = fim_min - inicio_min
    horas = total_minutos // 60
    minutos = total_minutos % 60

    valor_decimal = total_minutos / 60

    if minutos == 0:
        formato_visual = f"{horas}h"
    else:
        formato_visual = f"{horas}h {minutos}min"

    return round(valor_decimal, 2), formato_visual


def verificar_duplicidade(aba, data):
    try:
        registros = aba.get_all_values()
        data_str = data.strftime("%d/%m/%Y")
        for i, row in enumerate(registros[1:], start=2):
            if len(row) >= 2 and row[1] == data_str:
                return True, row
    except:
        pass

    return False, None


def salvar_registro(aba, tipo, inicio, fim, horas, valor_hora, valor_total):
    agora = datetime.now(TZ_SP)
    hoje = agora.date()

    data_str = hoje.strftime("%d/%m/%Y")
    mes = hoje.strftime("%m/%Y")
    dia_semana = DIAS_SEMANA[hoje.weekday()]
    criado_em = agora.strftime("%d/%m/%Y %H:%M:%S")

    linha = [
        NOME_USUARIO, data_str, mes, dia_semana,
        tipo, inicio or "", fim or "",
        horas, valor_hora, valor_total, criado_em
    ]

    aba.append_row(linha)
    return True


def obter_resumo_registros(aba):
    try:
        registros = aba.get_all_values()[1:]
        agora = datetime.now(TZ_SP)
        mes_atual = agora.strftime("%m/%Y")

        horas_mes = 0
        horas_semana = 0
        atestados_mes = 0
        total_valor_mes = 0

        data_uma_semana_atras = agora.date() - timedelta(days=7)

        for row in registros:
            if len(row) >= 10:
                tipo = row[4]
                mes = row[2]
                data_str = row[1]

                try:
                    data_registro = datetime.strptime(data_str, "%d/%m/%Y").date()
                except:
                    continue

                if mes == mes_atual:
                    if tipo == "HORA EXTRA":
                        try:
                            horas_decimal = float(row[7]) if row[7] else 0
                            horas_mes += horas_decimal
                            total_valor_mes += float(row[9]) if row[9] else 0
                        except:
                            pass
                    elif tipo == "ATESTADO":
                        atestados_mes += 1

                if data_registro >= data_uma_semana_atras and tipo == "HORA EXTRA":
                    try:
                        horas_decimal = float(row[7]) if row[7] else 0
                        horas_semana += horas_decimal
                    except:
                        pass

        return {
            "horas_mes": round(horas_mes, 2),
            "horas_semana": round(horas_semana, 2),
            "atestados_mes": atestados_mes,
            "valor_mes": round(total_valor_mes, 2)
        }
    except:
        return {
            "horas_mes": 0,
            "horas_semana": 0,
            "atestados_mes": 0,
            "valor_mes": 0
        }


def obter_ultimos_registros(aba, limite=5):
    try:
        registros = aba.get_all_values()[1:]
        registros_reversos = list(reversed(registros))[:limite]
        return registros_reversos
    except:
        return []


def validar_senha():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.markdown("""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
            background: linear-gradient(135deg, #7C3AED 0%, #4C1D95 100%);
        ">
            <div style="
                background: white;
                border-radius: 16px;
                padding: 32px 24px;
                width: 100%;
                max-width: 360px;
                box-shadow: 0 20px 25px rgba(0, 0, 0, 0.1);
            ">
                <h2 style="
                    text-align: center;
                    color: #111827;
                    margin-bottom: 8px;
                    font-size: 1.5rem;
                ">🔐 Acesso Restrito</h2>
                <p style="
                    text-align: center;
                    color: #6B7280;
                    margin-bottom: 24px;
                ">Digite a senha para acessar</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            senha_correta = st.secrets["app_password"]
        except KeyError:
            st.error("Senha não configurada nos secrets")
            st.stop()

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            senha = st.text_input("", type="password", placeholder="Digite a senha")

        if senha:
            if senha == senha_correta:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta")
                st.stop()
        else:
            st.stop()


validar_senha()

agora = datetime.now(TZ_SP)
hoje = agora.date()
dia_semana = DIAS_SEMANA[hoje.weekday()]
data_formatada = hoje.strftime("%d/%m/%Y")

st.markdown("""
<div style="
    background: white;
    padding: 20px 16px;
    margin: -16px -12px 24px -12px;
    border-bottom: 1px solid #E5E7EB;
    display: flex;
    align-items: center;
    justify-content: space-between;
">
    <div>
        <h2 style="
            margin: 0;
            font-size: 1.25rem;
            color: #111827;
        ">⏰ Horas Extras</h2>
        <p style="
            margin: 4px 0 0 0;
            font-size: 0.875rem;
            color: #6B7280;
        ">Bem-vinda, Amanda</p>
    </div>
</div>
""", unsafe_allow_html=True)

planilha = conectar_planilha()

if planilha:
    aba = obter_aba_registros(planilha)
    resumo = obter_resumo_registros(aba)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-card-label">📅 Data de Hoje</div>
            <div class="summary-card-value">{data_formatada}</div>
            <div class="summary-card-secondary">{dia_semana}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-card-label">💰 Total do Mês</div>
            <div class="summary-card-value">R$ {resumo['valor_mes']:.2f}</div>
            <div class="summary-card-secondary">{resumo['horas_mes']:.1f}h</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="height: 8px;"></div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-card-label">📊 Última Semana</div>
            <div class="summary-card-value">{resumo['horas_semana']:.1f}h</div>
            <div class="summary-card-secondary">últimos 7 dias</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-card-label">📋 Atestados</div>
            <div class="summary-card-value">{resumo['atestados_mes']}</div>
            <div class="summary-card-secondary">este mês</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="height: 16px;"></div>
    """, unsafe_allow_html=True)

    if "tipo_selecionado" not in st.session_state:
        st.session_state.tipo_selecionado = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏱️ Hora Extra", use_container_width=True, key="btn_hora"):
            st.session_state.tipo_selecionado = "HORA EXTRA"
    with col2:
        if st.button("📋 Atestado", use_container_width=True, key="btn_atestado"):
            st.session_state.tipo_selecionado = "ATESTADO"

    if st.session_state.tipo_selecionado:
        st.markdown("""
        <div style="height: 20px;"></div>
        """, unsafe_allow_html=True)

        duplicado, registro_existente = verificar_duplicidade(aba, hoje)

        if duplicado:
            st.warning("⚠️ Já existe um registro para hoje")
            if registro_existente:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Tipo:** {registro_existente[4]}")
                with col2:
                    st.markdown(f"**Horas:** {registro_existente[7]}")

                if registro_existente[4] == "HORA EXTRA":
                    st.markdown(f"**Valor:** R$ {registro_existente[9]}")
            st.info("ℹ️ Para corrigir, edite diretamente no Google Sheets.")
        else:
            if st.session_state.tipo_selecionado == "HORA EXTRA":
                st.markdown("""
                <h3 style="
                    margin: 0 0 20px 0;
                    color: #111827;
                    font-size: 1.125rem;
                ">⏱️ Registrar Hora Extra</h3>
                """, unsafe_allow_html=True)

                def atualizar_inicio():
                    valor = st.session_state.inicio_hora_input
                    apenas_numeros = ''.join(filter(str.isdigit, valor))

                    if len(apenas_numeros) > 4:
                        apenas_numeros = apenas_numeros[:4]

                    if len(apenas_numeros) >= 2 and len(apenas_numeros) < 4:
                        formatado = apenas_numeros[:2] + ':' + apenas_numeros[2:]
                        st.session_state.inicio_hora_input = formatado
                    elif len(apenas_numeros) == 4:
                        formatado = apenas_numeros[:2] + ':' + apenas_numeros[2:4]
                        st.session_state.inicio_hora_input = formatado

                def atualizar_fim():
                    valor = st.session_state.fim_hora_input
                    apenas_numeros = ''.join(filter(str.isdigit, valor))

                    if len(apenas_numeros) > 4:
                        apenas_numeros = apenas_numeros[:4]

                    if len(apenas_numeros) >= 2 and len(apenas_numeros) < 4:
                        formatado = apenas_numeros[:2] + ':' + apenas_numeros[2:]
                        st.session_state.fim_hora_input = formatado
                    elif len(apenas_numeros) == 4:
                        formatado = apenas_numeros[:2] + ':' + apenas_numeros[2:4]
                        st.session_state.fim_hora_input = formatado

                col1, col2 = st.columns(2)
                with col1:
                    inicio_input = st.text_input("Início", placeholder="09:00", key="inicio_hora_input", max_chars=5, on_change=atualizar_inicio)
                with col2:
                    fim_input = st.text_input("Fim", placeholder="17:30", key="fim_hora_input", max_chars=5, on_change=atualizar_fim)

                valor_hora = st.number_input("Valor da hora", value=VALOR_HORA_PADRAO, min_value=0.0, step=0.01, key="valor_hora")

                inicio = formatar_hora(inicio_input) if inicio_input else None
                fim = formatar_hora(fim_input) if fim_input else None

                if inicio_input and len(inicio_input) == 5 and not inicio:
                    st.error("❌ Hora inválida")

                if fim_input and len(fim_input) == 5 and not fim:
                    st.error("❌ Hora inválida")

                if inicio and fim:
                    resultado = calcular_horas(inicio, fim)

                    if resultado[0] is None:
                        st.error("❌ O fim precisa ser maior que o início")
                    else:
                        horas_decimal, horas_visual = resultado
                        valor_total = round(horas_decimal * valor_hora, 2)

                        st.markdown("""
                        <div style="height: 12px;"></div>
                        """, unsafe_allow_html=True)

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Horas", horas_visual)
                        with col2:
                            st.metric("Valor/h", f"R$ {valor_hora:.2f}")
                        with col3:
                            st.metric("Total", f"R$ {valor_total:.2f}")

                        st.markdown("""
                        <div style="height: 12px;"></div>
                        """, unsafe_allow_html=True)

                        if st.button("✅ Salvar", use_container_width=True, key="salvar_hora"):
                            if salvar_registro(
                                aba, "HORA EXTRA", inicio, fim,
                                horas_decimal, valor_hora, valor_total
                            ):
                                st.success("✅ Hora extra registrada com sucesso!")
                                st.session_state.tipo_selecionado = None
                                st.rerun()

            else:
                st.markdown("""
                <h3 style="
                    margin: 0 0 20px 0;
                    color: #111827;
                    font-size: 1.125rem;
                ">📋 Registrar Atestado</h3>
                """, unsafe_allow_html=True)

                dia_todo = st.checkbox("Dia todo", value=True, key="dia_todo")

                if dia_todo:
                    st.markdown("""
                    <div class="history-card">
                        <div class="history-card-details">
                            <strong>Período:</strong> Expediente todo<br>
                            <strong>Horas:</strong> 0
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("✅ Salvar", use_container_width=True, key="salvar_atestado_todo"):
                        if salvar_registro(
                            aba, "ATESTADO", "", "",
                            0, 0, 0
                        ):
                            st.success("✅ Atestado registrado com sucesso!")
                            st.session_state.tipo_selecionado = None
                            st.rerun()

                else:
                    def atualizar_inicio_atestado():
                        valor = st.session_state.inicio_atestado_input
                        apenas_numeros = ''.join(filter(str.isdigit, valor))

                        if len(apenas_numeros) > 4:
                            apenas_numeros = apenas_numeros[:4]

                        if len(apenas_numeros) >= 2 and len(apenas_numeros) < 4:
                            formatado = apenas_numeros[:2] + ':' + apenas_numeros[2:]
                            st.session_state.inicio_atestado_input = formatado
                        elif len(apenas_numeros) == 4:
                            formatado = apenas_numeros[:2] + ':' + apenas_numeros[2:4]
                            st.session_state.inicio_atestado_input = formatado

                    def atualizar_fim_atestado():
                        valor = st.session_state.fim_atestado_input
                        apenas_numeros = ''.join(filter(str.isdigit, valor))

                        if len(apenas_numeros) > 4:
                            apenas_numeros = apenas_numeros[:4]

                        if len(apenas_numeros) >= 2 and len(apenas_numeros) < 4:
                            formatado = apenas_numeros[:2] + ':' + apenas_numeros[2:]
                            st.session_state.fim_atestado_input = formatado
                        elif len(apenas_numeros) == 4:
                            formatado = apenas_numeros[:2] + ':' + apenas_numeros[2:4]
                            st.session_state.fim_atestado_input = formatado

                    col1, col2 = st.columns(2)
                    with col1:
                        inicio_input = st.text_input("Início", placeholder="08:00", key="inicio_atestado_input", max_chars=5, on_change=atualizar_inicio_atestado)
                    with col2:
                        fim_input = st.text_input("Fim", placeholder="12:00", key="fim_atestado_input", max_chars=5, on_change=atualizar_fim_atestado)

                    inicio = formatar_hora(inicio_input) if inicio_input else None
                    fim = formatar_hora(fim_input) if fim_input else None

                    if inicio_input and len(inicio_input) == 5 and not inicio:
                        st.error("❌ Hora inválida")

                    if fim_input and len(fim_input) == 5 and not fim:
                        st.error("❌ Hora inválida")

                    if inicio and fim:
                        st.markdown("""
                        <div class="history-card">
                            <div class="history-card-details">
                                <strong>Período:</strong> """ + f"{inicio} - {fim}" + """<br>
                                <strong>Horas:</strong> 0
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("""
                        <div style="height: 12px;"></div>
                        """, unsafe_allow_html=True)

                        if st.button("✅ Salvar", use_container_width=True, key="salvar_atestado_parcial"):
                            if salvar_registro(
                                aba, "ATESTADO", inicio, fim,
                                0, 0, 0
                            ):
                                st.success("✅ Atestado registrado com sucesso!")
                                st.session_state.tipo_selecionado = None
                                st.rerun()

    st.markdown("""
    <div style="height: 20px;"></div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h3 style="
        margin: 0 0 16px 0;
        color: #111827;
        font-size: 1.125rem;
    ">📜 Histórico Recente</h3>
    """, unsafe_allow_html=True)

    ultimos_registros = obter_ultimos_registros(aba, 10)

    if ultimos_registros:
        for registro in ultimos_registros:
            if len(registro) >= 10:
                tipo = registro[4]
                data = registro[1]
                horas = registro[7]
                valor = registro[9]
                dia_semana_reg = registro[3]
                inicio = registro[5]
                fim = registro[6]

                if tipo == "HORA EXTRA":
                    if inicio and fim:
                        periodo = f"{inicio} - {fim}"
                    else:
                        periodo = "N/A"

                    st.markdown(f"""
                    <div class="history-card">
                        <div class="history-card-header">
                            <span class="history-card-type">⏱️ Hora Extra</span>
                            <span class="history-card-date">{data}</span>
                        </div>
                        <div class="history-card-value">R$ {valor if valor else '0.00'}</div>
                        <div class="history-card-details">
                            <strong>Período:</strong> {periodo}<br>
                            <strong>Horas:</strong> {horas if horas else '0'}<br>
                            <strong>Dia:</strong> {dia_semana_reg}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    if inicio and fim:
                        periodo = f"{inicio} - {fim}"
                    else:
                        periodo = "Expediente todo"

                    st.markdown(f"""
                    <div class="history-card">
                        <div class="history-card-header">
                            <span class="history-card-type" style="background: #FED7AA; color: #92400E;">📋 Atestado</span>
                            <span class="history-card-date">{data}</span>
                        </div>
                        <div class="history-card-details">
                            <strong>Período:</strong> {periodo}<br>
                            <strong>Dia:</strong> {dia_semana_reg}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            text-align: center;
            padding: 32px 16px;
            color: #6B7280;
        ">
            <p style="margin: 0;">Nenhum registro ainda</p>
        </div>
        """, unsafe_allow_html=True)
