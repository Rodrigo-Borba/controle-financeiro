# coding: cp1252

import streamlit as st
import pandas as pd
import calendar
import plotly.express as px
from datetime import datetime
import locale

from controller.planilha import Planilha

locale.setlocale(locale.LC_ALL, 'pt_BR')

st.set_page_config(page_title="Geral",
                   layout="wide")

# TOP KPI's
st.title(":material/paid: Geral")
st.markdown("##")


def buscar_receitas():
    if not "planilha_obj" in st.session_state or not st.session_state.planilha_obj:
        st.session_state.planilha_obj = Planilha()
    st.session_state.df_receitas = st.session_state.planilha_obj.buscar_receitas_df()
    return st.session_state.df_receitas


if not "planilha_obj" in st.session_state or not "df_receitas" in st.session_state:
    df_receitas = buscar_receitas().copy()
else:
    if st.session_state.df_receitas.empty:
        df_receitas = buscar_receitas().copy()
    else:
        df_receitas = st.session_state.df_receitas.copy()


def buscar_despesas():
    if not "planilha_obj" in st.session_state or not st.session_state.planilha_obj:
        st.session_state.planilha_obj = Planilha()
    st.session_state.df_despesas = st.session_state.planilha_obj.buscar_despesas_df()
    return st.session_state.df_despesas


if not "planilha_obj" in st.session_state or not "df_despesas" in st.session_state:
    df_despesas = buscar_despesas().copy()
else:
    if st.session_state.df_despesas.empty:
        df_despesas = buscar_despesas().copy()
    else:
        df_despesas = st.session_state.df_despesas.copy()

# Refinar dados
df_receitas["data"] = pd.to_datetime(df_receitas["data"])
df_despesas["data"] = pd.to_datetime(df_despesas["data"])
df_receitas["mes"] = df_receitas["data"].dt.month
df_despesas["mes"] = df_despesas["data"].dt.month
df_receitas["mes_nome"] = df_receitas["mes"].apply(lambda x: calendar.month_name[x].capitalize())
df_despesas["mes_nome"] = df_despesas["mes"].apply(lambda x: calendar.month_name[x].capitalize())
df_receitas["ano"] = df_receitas["data"].dt.year
df_despesas["ano"] = df_despesas["data"].dt.year

# Recuperar informações de data atual
mes_atual = datetime.now().strftime("%B")
mes_atual_numero = datetime.now().month
mes_atual = mes_atual.capitalize()
ano_atual = datetime.now().year


def buscar_data_fatura_paga():
    dia_atual = int(datetime.now().day)
    mes_fatura = int(mes_atual_numero)
    ano_fatura = int(ano_atual)
    if dia_atual < 18:
        if mes_fatura > 1:
            mes_fatura -= 1
        else:
            mes_fatura = int(12)
            ano_fatura -= 1
    dia_fatura = int(11)
    data_fatura_paga = datetime(ano_fatura, mes_fatura, dia_fatura)
    while not data_fatura_paga.weekday():
        dia_fatura -= 1
        data_fatura_paga = datetime(ano_fatura, mes_fatura, dia_fatura)
    return data_fatura_paga


def buscar_faturas_pagas():
    data_fatura_paga = buscar_data_fatura_paga()
    valor_fatura = \
        df_despesas[(df_despesas["data"] <= data_fatura_paga) & (df_despesas["metodo_pagamento"] == "Crédito")][
            "valor"].sum()
    return valor_fatura


def calcular_saldo_conta():
    valor_fatura = buscar_faturas_pagas()
    valor_pago = \
        df_despesas[(df_despesas["data"] <= datetime.now()) & (df_despesas["metodo_pagamento"] != "Crédito")][
            "valor"].sum()
    valor_receitas = df_receitas[df_receitas["data"] <= datetime.now()]["valor"].sum()
    valor_saldo = valor_receitas - valor_fatura - valor_pago
    return valor_saldo


# Calcular saldo em conta = Receitas atuais - Despesas até a última fatura paga e outras
# despesas que não foram no crédito
saldo_conta = calcular_saldo_conta()

receitas_totais = df_receitas["valor"].sum()
despesas_totais = df_despesas["valor"].sum()

# Saldo total (inclui despesas futuras)
saldo_total = receitas_totais - despesas_totais

saldo_conta = round(saldo_conta, 2)
saldo_total = round(saldo_total, 2)

saldo_col1, saldo_col2 = st.columns(2)

with saldo_col1:
    with st.container(border=True):
        if saldo_conta >= 0:
            cor_saldo = "green"
        else:
            cor_saldo = "red"
        st.subheader("Saldo em conta")
        saldo_conta = locale.currency(saldo_conta, grouping=True, symbol=None)
        st.subheader(f":{cor_saldo}[R$ {saldo_conta}]")

with saldo_col2:
    with st.container(border=True):
        if saldo_total >= 0:
            cor_saldo_total = "green"
        else:
            cor_saldo_total = "red"
        st.subheader("Saldo total:")
        saldo_total = locale.currency(saldo_total, grouping=True, symbol=None)
        st.subheader(f":{cor_saldo_total}[R$ {saldo_total}]")

st.divider()


def buscar_proximas_faturas():
    data_fatura_paga = buscar_data_fatura_paga()
    return df_despesas[(df_despesas["data"] > data_fatura_paga) & (df_despesas["metodo_pagamento"] == "Crédito")]


df_faturas_futuras = buscar_proximas_faturas()

df_faturas_futuras = df_faturas_futuras[["mes", "mes_nome", "valor"]]
df_faturas_futuras = df_faturas_futuras.groupby(["mes_nome", "mes"], as_index=False).sum()
df_faturas_futuras.sort_values("mes", inplace=True)

fig_faturas_futuras = px.bar(df_faturas_futuras, x="mes_nome", y="valor", title="Faturas futuras", color='mes_nome',
                             labels={"mes_nome": "Mês", "valor": "Valor (R$)"})

st.plotly_chart(fig_faturas_futuras)

with st.expander("Editar Receitas"):
    df_receitas_editadas = st.data_editor(st.session_state.df_receitas)


    def atualizar_receitas():
        st.session_state.planilha_obj.atualizar_planilha_receitas(df=df_receitas_editadas)
        st.session_state.df_receitas = df_receitas_editadas
        st.session_state.df_receitas.sort_values("data", inplace=True, ascending=False)


    st.button("Atualizar Receitas",
              on_click=atualizar_receitas)

with st.expander("Editar Despesas"):
    df_despesas_editadas = st.data_editor(st.session_state.df_despesas)


    def atualizar_despesas():
        st.session_state.planilha_obj.atualizar_planilha_despesas(df=df_despesas_editadas)
        st.session_state.df_despesas = df_despesas_editadas
        st.session_state.df_despesas.sort_values("data", inplace=True, ascending=False)


    st.button("Atualizar Despesas",
              on_click=atualizar_despesas)
