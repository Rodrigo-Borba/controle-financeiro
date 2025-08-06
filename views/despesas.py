# coding: cp1252

import streamlit as st
import pandas as pd
import calendar
import plotly.express as px
from datetime import datetime
import locale

from controller.planilha import Planilha

locale.setlocale(locale.LC_ALL, 'pt_BR')

st.set_page_config(page_title="Despesas",
                   layout="wide")

# TOP KPI's
st.title(":material/payments: Despesas")
st.markdown("##")


def buscar_despesas():
    if not "planilha_obj" in st.session_state or not st.session_state.planilha_obj:
        st.session_state.planilha_obj = Planilha()
    st.session_state.df_despesas = st.session_state.planilha_obj.buscar_despesas_df()
    return st.session_state.df_despesas


if not "planilha_obj" in st.session_state or not "df_despesas" in st.session_state:
    df = buscar_despesas().copy()
else:
    if st.session_state.df_despesas.empty:
        df = buscar_despesas().copy()
    else:
        df = st.session_state.df_despesas.copy()

df["data"] = pd.to_datetime(df["data"])
df["mes"] = df["data"].dt.month
df["mes_nome"] = df["mes"].apply(lambda x: calendar.month_name[x].capitalize())
df["ano"] = df["data"].dt.year

mes_atual = datetime.now().strftime("%B")
mes_atual = mes_atual.capitalize()
ano_atual = datetime.now().year

st.subheader("Filtro:")

filtro_col1, filtro_col2 = st.columns(2)

with filtro_col1:
    ano = st.selectbox("Ano", df["ano"].unique())

with filtro_col2:
    mes = st.multiselect("Mês", [calendar.month_name[x].capitalize() for x in range(1, 13)],
                         placeholder="Escolher os meses", default=[mes_atual])

df_filtered = df[(df["mes_nome"].isin(mes)) & (df["ano"] == ano)]
df_filtered = df_filtered.sort_values("data")

meses_selecionados = df_filtered["mes_nome"].unique()

gasto_total = int(df_filtered["valor"].sum())
if gasto_total > 0:
    gasto_medio = round(gasto_total / len(mes), 2)
else:
    gasto_medio = 0

coluna_esquerda, coluna_direita = st.columns(2)
with coluna_esquerda:
    st.subheader("Gasto Total:")
    gasto_total = locale.currency(gasto_total, grouping=True, symbol=None)
    st.subheader(f"R$ {gasto_total}")
with coluna_direita:
    st.subheader("Gasto Médio:")
    gasto_medio = locale.currency(gasto_medio, grouping=True, symbol=None)
    st.subheader(f"R$ {gasto_medio}")

st.markdown("---")

# Gasto total mensal
df_valor_mes = df_filtered[["mes", "mes_nome", "valor"]]
df_valor_mes = df_valor_mes.groupby(["mes_nome", "mes"], as_index=False).sum()
df_valor_mes.sort_values("mes", inplace=True)

col1, col2 = st.columns(2)

fig_valor_mes_linha = px.line(df_valor_mes, x="mes_nome", y="valor", title="Soma mensal total por período",
                              labels={"mes_nome": "Mês", "valor": "Valor (R$)"})

col1.plotly_chart(fig_valor_mes_linha)

fig_valor_mes_barra = px.bar(df_valor_mes, x="mes_nome", y="valor", title="Soma mensal total", color='mes_nome',
                             color_discrete_sequence=px.colors.sequential.Plasma,
                             labels={"mes_nome": "Mês", "valor": "Valor (R$)"})

col2.plotly_chart(fig_valor_mes_barra)

st.markdown("---")

# Gasto por categoria
st.subheader("Despesas por categoria")
df_categoria_total = df_filtered[["categoria", "valor"]]
df_categoria_mes = df_filtered[["mes", "mes_nome", "categoria", "valor"]]
df_categoria_total = df_categoria_total.groupby(["categoria"], as_index=False).sum()
df_categoria_total.sort_values("categoria", inplace=True)

df_categoria_mes = df_categoria_mes.groupby(["mes", "mes_nome", "categoria"], as_index=False).sum()
df_categoria_mes.sort_values("mes", inplace=True)

df_categoria_perc = df_categoria_total
valor_cat_tot = df_categoria_perc["valor"].sum()
df_categoria_perc["percentual"] = df_categoria_perc["valor"].apply(
    lambda x: round((100 * float(x) / float(valor_cat_tot)), 2))

fig_categoria_total = px.bar(df_categoria_total, x="categoria", y="valor", title="Soma por categoria - Período",
                             color='categoria', color_discrete_sequence=px.colors.sequential.Plasma,
                             labels={"categoria": "Categoria", "valor": "Valor (R$)"})

fig_categoria_mes = px.histogram(df_categoria_mes, x="mes_nome", y="valor", title="Soma por categoria - Mensal",
                                 color='categoria', barmode="group",
                                 color_discrete_sequence=px.colors.sequential.Plasma,
                                 category_orders={
                                     "mes_nome": meses_selecionados},
                                 labels={"mes_nome": "Mês", "categoria": "Categoria", "valor": "Valor (R$)"})

fig_categoria_perc = px.pie(df_categoria_perc, values="percentual", names="categoria",
                            title="Percentual categoria - período",
                            color_discrete_sequence=px.colors.sequential.Plasma,
                            labels={"percentual": "Percentual", "categoria": "Categoria"})

cat_bt_col1, cat_bt_col2 = st.columns(2)

with cat_bt_col1:
    radio_col_cat = st.radio("Quantas colunas? - Categoria", (1, 2, 3))

with cat_bt_col2:
    if radio_col_cat == 1:
        sel_box_cat_fig = st.selectbox("Qual gráfico quer ver? - Categoria",
                                       ["Valor - Período", "Valor - Mensal", "Percentual - Período"])
    elif radio_col_cat == 2:
        multi_sel_cat_fig = st.multiselect("Qual gráfico quer ver? - Categoria",
                                           ["Valor - Período", "Valor - Mensal", "Percentual - Período"],
                                           max_selections=2)

if radio_col_cat == 1:
    if sel_box_cat_fig == "Valor - Período":
        st.plotly_chart(fig_categoria_total)
    elif sel_box_cat_fig == "Valor - Mensal":
        st.plotly_chart(fig_categoria_mes)
    else:
        st.plotly_chart(fig_categoria_perc)
elif radio_col_cat == 2:
    cat_fig1, cat_fig2 = st.columns(2)
    fig_lista = []
    for categoria in multi_sel_cat_fig:
        if categoria == "Valor - Período":
            fig_lista.append(fig_categoria_total)
        elif categoria == "Valor - Mensal":
            fig_lista.append(fig_categoria_mes)
        else:
            fig_lista.append(fig_categoria_perc)
    if len(fig_lista) == 2:
        cat_fig1.plotly_chart(fig_lista[0])
        cat_fig2.plotly_chart(fig_lista[1])

else:
    cat_fig1, cat_fig2, cat_fig3 = st.columns(3)
    cat_fig1.plotly_chart(fig_categoria_total)
    cat_fig2.plotly_chart(fig_categoria_mes)
    cat_fig3.plotly_chart(fig_categoria_perc)

st.markdown("---")

# Gasto por tipo de pagamento
st.subheader("Despesas por método de pagamento")
df_pagamento_total = df_filtered[["metodo_pagamento", "valor"]]
df_pagamento_mes = df_filtered[["mes", "mes_nome", "metodo_pagamento", "valor"]]

df_pagamento_total = df_pagamento_total.groupby(["metodo_pagamento"], as_index=False).sum()
df_pagamento_total.sort_values("metodo_pagamento", inplace=True)

df_pagamento_mes = df_pagamento_mes.groupby(["mes", "mes_nome", "metodo_pagamento"], as_index=False).sum()
df_pagamento_mes.sort_values("mes", inplace=True)

df_pagamento_perc = df_pagamento_total
valor_pag_tot = df_pagamento_total["valor"].sum()
df_pagamento_perc["percentual"] = df_pagamento_total["valor"].apply(
    lambda x: round((100 * float(x) / float(valor_pag_tot)), 2))

fig_pagamento_total = px.bar(df_pagamento_total, x="metodo_pagamento", y="valor",
                             title="Soma por método de pagamento - Período",
                             color='metodo_pagamento', color_discrete_sequence=px.colors.sequential.Plasma,
                             labels={"metodo_pagamento": "Método de pagamento", "valor": "Valor (R$)"})

fig_pagamento_mes = px.histogram(df_pagamento_mes, x="mes_nome", y="valor",
                                 title="Soma por método de pagamento - Mensal",
                                 color='metodo_pagamento', barmode='group',
                                 color_discrete_sequence=px.colors.sequential.Plasma,
                                 category_orders={
                                     "mes_nome": meses_selecionados},
                                 labels={"mes_nome": "Mês", "metodo_pagamento": "Método de pagamento",
                                         "valor": "Valor (R$)"})

fig_pagamento_perc = px.pie(df_pagamento_perc, values="percentual", names="metodo_pagamento",
                            title="Percentual método de pagamento - período",
                            color_discrete_sequence=px.colors.sequential.Plasma,
                            labels={"percentual": "Percentual", "metodo_pagamento": "Método de pagamento"})

pag_bt_col1, pag_bt_col2 = st.columns(2)

with pag_bt_col1:
    radio_col_pag = st.radio("Quantas colunas? - Método de pagamento", (1, 2, 3))

with pag_bt_col2:
    if radio_col_pag == 1:
        sel_box_pag_fig = st.selectbox("Qual gráfico quer ver? - Método de pagamento",
                                       ["Valor - Período", "Valor - Mensal", "Percentual - Período"])
    elif radio_col_pag == 2:
        multi_sel_pag_fig = st.multiselect("Qual gráfico quer ver? - Método de pagamento",
                                           ["Valor - Período", "Valor - Mensal", "Percentual - Período"],
                                           max_selections=2)

if radio_col_pag == 1:
    if sel_box_pag_fig == "Valor - Período":
        st.plotly_chart(fig_pagamento_total)
    elif sel_box_pag_fig == "Valor - Mensal":
        st.plotly_chart(fig_pagamento_mes)
    else:
        st.plotly_chart(fig_pagamento_perc)
elif radio_col_pag == 2:
    pag_fig1, pag_fig2 = st.columns(2)
    fig_lista_pag = []
    for pagamento in multi_sel_pag_fig:
        if pagamento == "Valor - Período":
            fig_lista_pag.append(fig_pagamento_total)
        elif pagamento == "Valor - Mensal":
            fig_lista_pag.append(fig_pagamento_mes)
        else:
            fig_lista_pag.append(fig_pagamento_perc)
    if len(fig_lista_pag) == 2:
        pag_fig1.plotly_chart(fig_lista_pag[0])
        pag_fig2.plotly_chart(fig_lista_pag[1])

else:
    pag_fig1, pag_fig2, pag_fig3 = st.columns(3)
    pag_fig1.plotly_chart(fig_pagamento_total)
    pag_fig2.plotly_chart(fig_pagamento_mes)
    pag_fig3.plotly_chart(fig_pagamento_perc)

st.markdown("---")
