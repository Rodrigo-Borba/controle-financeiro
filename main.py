# coding: cp1252
import time

import streamlit as st
import pandas as pd

# Lista de categorias
CATEGORIAS_DESPESA = [
    "Lazer",
    "Presente",
    "Energia",
    "Internet",
    "Transporte",
    "Boleto",
    "Investimento",
    "Alimentação",
    "Refeição",
    "Pix",
    "Streaming",
    "Assinatura",
    "Farmácia",
    "Não identificada",
    "Cuidados pessoais"
]

# Lista de categorias
CATEGORIAS_RECEITA = [
    "Salário",
    "Pix",
    "Resgate",
    "Reembolso"
]

# Lista de categorias
METODO_PAGAMENTO = [
    "Pix",
    "Crédito",
    "Débito",
    "Transferência"
]

USUARIOS_VALIDOS = st.secrets["USUARIOS_VALIDOS"]


def login_screen():
    st.header("Faça o log in para acessar o aplicativo")
    st.button("Log in com Google", on_click=st.login)


if not st.user.is_logged_in:
    login_screen()
elif st.user.email in USUARIOS_VALIDOS:
    geral_pagina = st.Page(
        page="views/geral.py",
        title="Geral",
        icon=":material/paid:",
        default=True
    )

    despesas_pagina = st.Page(
        page="views/despesas.py",
        title="Despesas",
        icon=":material/payments:"
    )

    pg = st.navigation({
        f"Dashboard de {st.user.name}": [geral_pagina, despesas_pagina],
    })

    with st.sidebar:
        @st.dialog("Adicionar Receita")
        def formulario_receita():
            data_form_receita = st.date_input(label="Data da receita*")
            descricao_form_receita = st.selectbox(label="Descrição*",
                                                  options=st.session_state.df_receitas["descricao"].unique(),
                                                  accept_new_options=True, index=None)
            categoria_form_receita = st.selectbox(label="Categoria*", options=CATEGORIAS_RECEITA, index=None)
            valor_form_receita = st.number_input(label="Valor em R$*")

            st.markdown("**Campos Obrigatórios**")

            botao_enviar_receita = st.button(label="Enviar")
            if botao_enviar_receita:
                if not data_form_receita or not descricao_form_receita or not categoria_form_receita or not valor_form_receita:
                    st.error("Preencher campos obrigatórios")
                else:
                    nova_receita = {
                        "data": pd.to_datetime(data_form_receita),
                        "descricao": descricao_form_receita,
                        "categoria": categoria_form_receita,
                        "valor": valor_form_receita
                    }
                    nova_linha_receita = pd.Series(nova_receita)
                    df_inicial_receita = st.session_state.df_receitas
                    df_final_receita = pd.concat([df_inicial_receita, nova_linha_receita.to_frame().T],
                                                 ignore_index=True)
                    st.session_state.planilha_obj.atualizar_planilha_receitas(df=df_final_receita)
                    st.session_state.df_receitas = df_final_receita
                    st.session_state.df_receitas.sort_values("data", inplace=True, ascending=False)


        @st.dialog("Adicionar Despesa")
        def formulario_despesa():
            data_form = st.date_input(label="Data da despesa*")
            descricao_form = st.selectbox(label="Descrição*",
                                          options=st.session_state.df_despesas["descricao"].unique(),
                                          accept_new_options=True, index=None)
            if descricao_form == "Uber" or descricao_form == "99":
                categoria_default = next((i for i, despesa in enumerate(CATEGORIAS_DESPESA) if despesa == "Transporte"),
                                         None)
                metodo_default = next((i for i, pagamento in enumerate(METODO_PAGAMENTO) if pagamento == "Crédito"),
                                      None)
            elif descricao_form == "Amazon Prime" or descricao_form == "Meli+" or descricao_form == "Spotify" or descricao_form == "HBO Max":
                categoria_default = next((i for i, despesa in enumerate(CATEGORIAS_DESPESA) if despesa == "Streaming"),
                                         None)
                metodo_default = next((i for i, pagamento in enumerate(METODO_PAGAMENTO) if pagamento == "Crédito"),
                                      None)
            elif descricao_form == "Gympass" or descricao_form == "Google One" or descricao_form == "Sócio Náutico" or descricao_form == "Gamepass" or descricao_form == "TIM":
                categoria_default = next((i for i, despesa in enumerate(CATEGORIAS_DESPESA) if despesa == "Assinatura"),
                                         None)
                metodo_default = next((i for i, pagamento in enumerate(METODO_PAGAMENTO) if pagamento == "Crédito"),
                                      None)
            else:
                categoria_default = None
                metodo_default = None

            categoria_form = st.selectbox(label="Categoria*", options=CATEGORIAS_DESPESA, index=categoria_default)
            metodo_pagamento_form = st.selectbox(label="Método de pagamento*", options=METODO_PAGAMENTO,
                                                 index=metodo_default)

            if metodo_pagamento_form == "Crédito":
                radio_parcelado = st.radio(
                    "Parcelado?",
                    ["Não", "Sim"]
                )
            else:
                radio_parcelado = "Não"

            if radio_parcelado == "Sim":
                numero_parcelas = st.selectbox("Quantas parcelas?",
                                               list(range(1, 100)))

            valor_form = st.number_input(label="Valor em R$*")

            st.markdown("**Campos Obrigatórios**")

            botao_enviar = st.button(label="Enviar")
            if botao_enviar:
                if not data_form or not descricao_form or not categoria_form or not metodo_pagamento_form or not valor_form:
                    st.error("Preencher campos obrigatórios")
                else:
                    nova_despesa = {
                        "data": pd.to_datetime(data_form),
                        "descricao": descricao_form,
                        "categoria": categoria_form,
                        "metodo_pagamento": metodo_pagamento_form,
                        "valor": valor_form
                    }
                    nova_linha = pd.Series(nova_despesa)
                    df_inicial = st.session_state.df_despesas

                    if radio_parcelado == "Sim":
                        valor_parcelado = round(float(valor_form / numero_parcelas), 2)
                        df_final = df_inicial
                        for parcela in range(numero_parcelas):
                            nova_linha.data = pd.to_datetime(data_form) + pd.DateOffset(months=parcela)
                            nova_linha.valor = valor_parcelado
                            df_final = pd.concat([df_final, nova_linha.to_frame().T], ignore_index=True)
                    else:
                        df_final = pd.concat([df_inicial, nova_linha.to_frame().T], ignore_index=True)

                    st.session_state.planilha_obj.atualizar_planilha_despesas(df=df_final)
                    st.session_state.df_despesas = df_final
                    st.session_state.df_despesas.sort_values("data", inplace=True, ascending=False)


        sel_despesa_receita = st.selectbox(label="Escolha o que quer adicionar:", options=["Despesa", "Receita"])

        if sel_despesa_receita == "Despesa":
            st.button(
                "Adicionar Despesa",
                on_click=formulario_despesa
            )
        else:
            st.button(
                "Adicionar Receita",
                on_click=formulario_receita
            )

        st.divider()

        st.button("Logout", on_click=st.logout)

    pg.run()
else:
    st.error("Usuário inválido")
    time.sleep(2)
    st.logout()
