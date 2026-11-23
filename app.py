import os
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf


# ==========================================
# CONFIGURAÇÕES
# ==========================================

st.set_page_config(
    page_title="Dashboard IBOV",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta
BG = "#050911"        # Fundo principal
SURFACE = "#071220"   # Cards e superfícies
LINE = "#374151"      # Bordas e divisórias (ajustado para harmonizar com #1F2937)
TEXT = "#F9FAFB"      # Texto principal
MUTED = "#9CA3AF"     # Texto secundário e rótulos
GOLD = "#E3B448"      # Destaque / Ação principal
UP = "#16A085"        # Destaques positivos
DOWN = "#E05D5D"      # Destaques negativos

ASSET_COLORS = [
    "#5BA4E6", "#3FB68B", "#C58BEA", "#E58A5B",
    "#6FD0D6", "#E26D9A", "#A3C255", "#8E9DF0",
]

LABELS = {"portfolio": "Carteira", "IBOV": "IBOV"}


def label(name):
    return LABELS.get(name, name)


# ==========================================
# ESTILO
# ==========================================

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Instrument+Sans:wght@400;500;600&display=swap');

.stApp, .stApp p, .stApp label, .stApp li, .stApp input,
.stApp textarea, .stApp button, .stApp [data-testid="stMarkdownContainer"] {{
    font-family: 'Instrument Sans', sans-serif;
}}

.stApp {{ background: {BG}; color: {TEXT}; }}

h1, h2, h3 {{
    font-family: 'Newsreader', serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    color: {TEXT};
}}

.block-container {{ padding-top: 4.5rem; max-width: 1280px; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: {SURFACE};
    border-right: 1px solid {LINE};
}}

/* Métricas */
[data-testid="stMetric"] {{
    background: {SURFACE};
    border: 1px solid {LINE};
    border-radius: 10px;
    padding: 14px 16px;
    min-height: 128px;
}}
[data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: 0.85rem; }}
[data-testid="stMetricValue"] {{
    font-family: 'Newsreader', serif;
    font-variant-numeric: tabular-nums;
    font-size: 1.9rem;
}}

/* Abas */
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{
    padding: 10px 16px;
    color: {MUTED};
}}
.stTabs [aria-selected="true"] {{ color: {GOLD}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {GOLD}; }}

/* Contêineres com borda e expanders */
[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: {LINE} !important;
    border-radius: 10px;
}}

/* Cabeçalho */
.hero-title {{
    font-family: 'Newsreader', serif;
    font-size: 2.6rem;
    font-weight: 600;
    line-height: 1.1;
    margin: 0;
}}
.hero-sub {{ color: {MUTED}; margin: 6px 0 0 0; max-width: 62ch; }}

/* Estado vazio */
.empty {{
    background: {SURFACE};
    border: 1px dashed {LINE};
    border-radius: 12px;
    padding: 28px 32px;
    max-width: 640px;
    margin-top: 8px;
}}
.empty h3 {{ margin-top: 0; }}
.empty p {{ color: {MUTED}; margin-bottom: 0; }}

/* Foco visível e movimento reduzido */
button:focus-visible, input:focus-visible {{ outline: 2px solid {GOLD} !important; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; animation: none !important; }} }}
</style>



"""

st.markdown(CSS, unsafe_allow_html=True)


def style_fig(fig, height=400):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Instrument Sans, sans-serif", color=TEXT),
        margin=dict(l=8, r=8, t=96, b=8),
        height=height,
        title=dict(
            font=dict(family="Newsreader, serif", size=18),
            x=0, y=0.97, yanchor="top",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title=None),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=LINE),
    )
    fig.update_xaxes(gridcolor=LINE, zeroline=False)
    fig.update_yaxes(gridcolor=LINE, zeroline=False)
    return fig


# ==========================================
# DADOS
# ==========================================

@st.cache_data(ttl=3600, show_spinner=False)
def load_prices(tickers, start, end):
    prices = yf.download(
        list(tickers),
        start=start,
        end=end,
        auto_adjust=False,
        multi_level_index=False,
        progress=False,
    )["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])

    prices.columns = [t.removesuffix(".SA") for t in prices.columns]

    ibov = yf.download(
        "^BVSP",
        start=start,
        end=end,
        auto_adjust=False,
        progress=False,
    )["Close"]

    if isinstance(ibov, pd.DataFrame):
        ibov = ibov.iloc[:, 0]

    prices["IBOV"] = ibov
    return prices.dropna()


# ==========================================
# SIDEBAR
# ==========================================

def build_sidebar():
    if os.path.exists("./img/IBOV.png"):
        st.image("./img/IBOV.png")

    st.title("Análise")
    st.caption("Escolha as empresas e o período.")

    ticker_list = pd.read_csv("tickers_ibra.csv", index_col=0)

    tickers = st.multiselect(
        label="Empresas",
        options=ticker_list.iloc[:, 0].dropna().tolist(),
        placeholder="Ex: PETR4, VALE3",
        help="Escolha as ações que deseja comparar e incluir na carteira.",
    )
    st.caption(f"{len(tickers)} empresa(s) selecionada(s)")
    tickers = [t + ".SA" for t in tickers]

    st.divider()

    start_date = st.date_input(
        "De",
        format="DD/MM/YYYY",
        value=datetime(2026, 1, 1),
        help="Primeiro dia do período que deseja analisar.",
    )
    end_date = st.date_input(
        "Até",
        format="DD/MM/YYYY",
        value="today",
        help="Último dia do período que deseja analisar.",
    )

    risk_free_rate = st.number_input(
        "Taxa livre de risco anual (%)",
        min_value=0.0,
        max_value=50.0,
        value=10.5,
        step=0.25,
        key="risk_free_rate",
        help="Taxa de referência usada no cálculo do Índice de Sharpe.",
    ) / 100

    if start_date >= end_date:
        st.error("A data inicial deve ser anterior à data final.")
        return None, None, None

    if not tickers:
        return None, None, None

    with st.spinner("Carregando cotações..."):
        prices = load_prices(tuple(tickers), start_date, end_date)

    if prices.empty:
        st.error("Não encontramos dados para o período selecionado.")
        return None, None, None

    return tickers, prices, risk_free_rate


# ==========================================
# DASHBOARD PRINCIPAL
# ==========================================

def build_main(tickers, prices, risk_free_rate):
    assets = [t.removesuffix(".SA") for t in tickers]

    # ---------- Pesos ----------
    with st.expander("Pesos da carteira (padrão: pesos iguais)"):
        raw_weights = {}
        default_weight = 100 / len(assets)
        cols = st.columns(min(len(assets), 4))

        for i, asset in enumerate(assets):
            with cols[i % len(cols)]:
                raw_weights[asset] = st.number_input(
                    f"{asset} (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=round(default_weight, 2),
                    step=1.0,
                    key=f"weight_{asset}",
                )

        total_weight = sum(raw_weights.values())

        if total_weight <= 0:
            st.error("Defina um peso maior que zero para pelo menos um ativo.")
            return

        weights = np.array([raw_weights[a] / total_weight for a in assets])
        st.caption(
            f"Total informado: {total_weight:.2f}%. "
            "Os pesos são normalizados para 100%."
        )

    # ---------- Cálculos ----------
    all_returns = prices[assets + ["IBOV"]].pct_change().dropna()
    returns = all_returns[assets]
    portfolio_returns = returns.mul(weights, axis=1).sum(axis=1)

    portfolio_index = 100 * (1 + portfolio_returns).cumprod()

    norm_prices = (
        prices[assets + ["IBOV"]].div(prices[assets + ["IBOV"]].iloc[0]) * 100
    )
    norm_prices["portfolio"] = portfolio_index.reindex(norm_prices.index).fillna(100)

    rets = norm_prices.iloc[-1] / 100 - 1

    vols = all_returns.std() * np.sqrt(252)
    vols["portfolio"] = portfolio_returns.std() * np.sqrt(252)

    daily_risk_free = (1 + risk_free_rate) ** (1 / 252) - 1

    def calculate_sharpe(daily_returns):
        volatility = daily_returns.std()
        if volatility == 0 or pd.isna(volatility):
            return np.nan
        return ((daily_returns - daily_risk_free).mean() / volatility) * np.sqrt(252)

    def interpret_sharpe(value):
        if pd.isna(value):
            return "Indisponível"
        if value < 0:
            return "Abaixo da taxa livre de risco"
        if value < 1:
            return "Relação baixa"
        if value < 2:
            return "Relação moderada"
        if value < 3:
            return "Relação elevada"
        return "Muito elevada"

    sharpe_values = {a: calculate_sharpe(all_returns[a]) for a in all_returns.columns}
    sharpe_values["portfolio"] = calculate_sharpe(portfolio_returns)

    # ---------- Resumo da carteira ----------
    diff_ibov = (rets["portfolio"] - rets["IBOV"]) * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Retorno da carteira",
        f"{rets['portfolio']:.2%}",
        f"{diff_ibov:+.2f} p.p. vs IBOV",
        help="Valorização da carteira do início ao fim do período.",
    )
    k2.metric(
        "Retorno do IBOV",
        f"{rets['IBOV']:.2%}",
        help="Valorização do índice no mesmo período.",
    )
    k3.metric(
        "Volatilidade (a.a.)",
        f"{vols['portfolio']:.2%}",
        help="Oscilação dos retornos diários, anualizada com 252 pregões. "
        "Não é uma previsão de perda.",
    )
    k4.metric(
        "Índice de Sharpe",
        f"{sharpe_values['portfolio']:.2f}",
        help="Retorno excedente à taxa livre de risco por unidade de volatilidade.",
    )

    st.write("")

    tab_overview, tab_portfolio, tab_risk, tab_assets, tab_data = st.tabs(
        ["Visão geral", "Carteira", "Risco", "Ativos", "Dados"]
    )

    # ---------- Visão geral ----------
    with tab_overview:
        c1, c2 = st.columns(2, gap="large")

        with c1:
            fig_perf = go.Figure()
            for i, col in enumerate(assets):
                fig_perf.add_trace(go.Scatter(
                    x=norm_prices.index, y=norm_prices[col], name=col,
                    mode="lines", line=dict(width=1.5, color=ASSET_COLORS[i % len(ASSET_COLORS)]),
                ))
            fig_perf.add_trace(go.Scatter(
                x=norm_prices.index, y=norm_prices["IBOV"], name="IBOV",
                mode="lines", line=dict(width=2, color=MUTED, dash="dash"),
            ))
            fig_perf.add_trace(go.Scatter(
                x=norm_prices.index, y=norm_prices["portfolio"], name="Carteira",
                mode="lines", line=dict(width=3.5, color=GOLD),
            ))
            fig_perf.update_layout(
                title="Desempenho relativo (base 100)", hovermode="x unified"
            )
            st.plotly_chart(style_fig(fig_perf, 420), width="stretch")

        with c2:
            risk_return_df = pd.DataFrame({
                "Ativo": [label(a) for a in vols.index],
                "Volatilidade anualizada": vols.values,
                "Retorno no período": rets.reindex(vols.index).values,
                "Índice de Sharpe": pd.Series(sharpe_values).reindex(vols.index).values,
            })

            fig_rr = px.scatter(
                risk_return_df,
                x="Volatilidade anualizada",
                y="Retorno no período",
                text="Ativo",
                color="Índice de Sharpe",
                color_continuous_scale="RdYlGn",
                hover_data={
                    "Volatilidade anualizada": ":.2%",
                    "Retorno no período": ":.2%",
                    "Índice de Sharpe": ":.2f",
                },
                title="Risco e retorno",
            )
            fig_rr.update_traces(
                textposition="top center",
                textfont_color=TEXT,
                marker=dict(size=14, line=dict(width=1, color=BG)),
            )
            fig_rr.update_layout(
                xaxis_tickformat=".0%",
                yaxis_tickformat=".0%",
                coloraxis_colorbar=dict(title="Sharpe"),
            )
            st.plotly_chart(style_fig(fig_rr, 420), width="stretch")

        st.caption(
            "Cada ponto é um ativo, o IBOV ou a carteira. A posição mostra retorno e "
            "volatilidade históricos; a cor mostra o Sharpe. Resultados passados "
            "não garantem desempenho futuro."
        )

    # ---------- Carteira ----------
    with tab_portfolio:
        c1, c2 = st.columns([3, 2], gap="large")

        allocation_df = pd.DataFrame({"Ativo": assets, "Peso": weights})

        with c1:
            fig_alloc = px.pie(
                allocation_df,
                names="Ativo",
                values="Peso",
                hole=0.55,
                title="Alocação da carteira",
                color_discrete_sequence=ASSET_COLORS,
            )
            fig_alloc.update_traces(
                textposition="inside",
                textinfo="label+percent",
                marker=dict(line=dict(color=BG, width=2)),
            )
            fig_alloc.update_layout(showlegend=False)
            st.plotly_chart(style_fig(fig_alloc, 400), width="stretch")

        with c2:
            st.subheader("Pesos")
            st.dataframe(
                allocation_df.assign(Peso=allocation_df["Peso"] * 100),
                hide_index=True,
                width="stretch",
                column_config={
                    "Peso": st.column_config.ProgressColumn(
                        "Peso", format="%.1f%%", min_value=0, max_value=100
                    )
                },
            )

    # ---------- Risco ----------
    with tab_risk:
        c1, c2 = st.columns(2, gap="large")

        with c1:
            st.subheader("Índice de Sharpe")
            sharpe_df = pd.DataFrame({
                "Ativo": [label(a) for a in sharpe_values],
                "Sharpe": list(sharpe_values.values()),
            })
            sharpe_df["Interpretação"] = sharpe_df["Sharpe"].apply(interpret_sharpe)

            st.dataframe(
                sharpe_df.style.format({"Sharpe": "{:.2f}"}),
                hide_index=True,
                width="stretch",
            )

            with st.expander("Como funciona o Índice de Sharpe?"):
                st.markdown(
                    """
                    O Índice de Sharpe mede o retorno excedente de um investimento
                    em relação à sua volatilidade.

                    - Abaixo de 0: retorno inferior à taxa livre de risco.
                    - Entre 0 e 1: relação retorno/risco baixa.
                    - Entre 1 e 2: relação moderada.
                    - Entre 2 e 3: relação elevada.
                    - Acima de 3: resultado muito elevado.

                    Os intervalos são referências didáticas. O resultado depende do
                    período, da taxa livre de risco e das condições do mercado.
                    """
                )

        with c2:
            st.subheader("Correlação")
            correlation = all_returns[assets + ["IBOV"]].corr()

            fig_corr = px.imshow(
                correlation,
                text_auto=".2f",
                color_continuous_scale="RdBu",
                zmin=-1,
                zmax=1,
                aspect="auto",
            )
            fig_corr.update_layout(coloraxis_colorbar=dict(title="Correlação"))
            st.plotly_chart(style_fig(fig_corr, 380), width="stretch")

            with st.expander("Como interpretar a matriz?"):
                st.markdown(
                    """
                    - **Próximo de +1:** os ativos tendem a subir e cair juntos.
                    - **Próximo de 0:** pouca relação linear entre os retornos.
                    - **Próximo de -1:** tendem a se mover em direções opostas.

                    Ativos com correlação menor ajudam na diversificação, mas
                    correlação não elimina risco e muda conforme o mercado.
                    """
                )

    # ---------- Ativos ----------
    with tab_assets:
        items = assets + ["IBOV", "portfolio"]
        per_row = 3

        for start in range(0, len(items), per_row):
            row = st.columns(per_row, gap="medium")

            for col, name in zip(row, items[start:start + per_row]):
                with col.container(border=True):
                    head_a, head_b = st.columns([1, 3], vertical_alignment="center")

                    if name in ("portfolio", "IBOV"):
                        head_b.subheader(label(name))
                    else:
                        head_a.image(
                            f"https://raw.githubusercontent.com/thefintz/icones-b3/main/icones/{name}.png",
                            width=48,
                        )
                        head_b.subheader(name)

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Retorno", f"{rets[name]:.2%}")
                    m2.metric("Volatilidade", f"{vols[name]:.2%}")
                    m3.metric("Sharpe", f"{sharpe_values[name]:.2f}")

    # ---------- Dados ----------
    with tab_data:
        st.subheader("Histórico de preços")
        st.dataframe(
            prices.style.format("{:,.2f}"),
            width="stretch",
        )
        st.download_button(
            "Baixar CSV",
            prices.to_csv().encode("utf-8"),
            file_name="precos.csv",
            mime="text/csv",
        )


# ==========================================
# EXECUÇÃO
# ==========================================

with st.sidebar:
    tickers, prices, risk_free_rate = build_sidebar()

st.markdown(
    """
    <p class="hero-title">Dashboard IBOV</p>
    <p class="hero-sub">Compare ações da B3, monte uma carteira e veja como ela
    se comporta frente ao Ibovespa.</p>
    """,
    unsafe_allow_html=True,
)
st.write("")

if tickers is not None and prices is not None:
    build_main(tickers, prices, risk_free_rate)
else:
    st.markdown(
        """
        <div class="empty">
            <h3>Escolha as empresas da sua carteira</h3>
            <p>Use o menu à esquerda para selecionar uma ou mais ações e definir
            o período. A análise aparece aqui assim que você escolher a primeira.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )