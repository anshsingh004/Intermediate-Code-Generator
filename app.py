"""
app.py – Streamlit UI for the Intermediate Code Generator.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

from errors import CompilerError
from lexer import tokenize
from syntax_parser import parse
from code_generator import generate

# ---------------------------------------------------------------------------
# Colour palette
#   #FFC1CB  – pink   → input card background, section badge accents
#   #33AE81  – green  → primary buttons, section headings, table headers
#   #094782  – navy   → title, body text, code block border
# ---------------------------------------------------------------------------

PINK  = "#FFC1CB"
GREEN = "#33AE81"
NAVY  = "#094782"

st.markdown(f"""
<style>
/* ── Global body & background ───────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {{
    background-color: #FFFFFF;
    color: {NAVY};
}}

/* ── Top toolbar / header bar ───────────────────────────────────────── */
[data-testid="stHeader"] {{
    background-color: {NAVY};
}}

/* ── Title ───────────────────────────────────────────────────────────── */
h1 {{
    color: {NAVY} !important;
    border-bottom: 3px solid {GREEN};
    padding-bottom: 6px;
}}

/* ── Section subheadings (h2/h3) ─────────────────────────────────────── */
h2, h3 {{
    color: {GREEN} !important;
}}

/* ── Text-area label ─────────────────────────────────────────────────── */
label[data-testid="stTextAreaLabel"],
.stTextArea label {{
    color: {NAVY} !important;
    font-weight: 600;
}}

/* ── Text-area input box ─────────────────────────────────────────────── */
textarea {{
    background-color: {PINK}22 !important;   /* 13 % opacity pink tint */
    border: 2px solid {GREEN} !important;
    border-radius: 8px !important;
    color: {NAVY} !important;
    font-family: monospace !important;
}}
textarea:focus {{
    border-color: {NAVY} !important;
    box-shadow: 0 0 0 2px {GREEN}55 !important;
}}

/* ── Caption / hint text ─────────────────────────────────────────────── */
small, [data-testid="stCaptionContainer"] {{
    color: {NAVY}99 !important;
}}

/* ── Primary button ──────────────────────────────────────────────────── */
[data-testid="stBaseButton-primary"] button,
div.stButton > button[kind="primary"] {{
    background-color: {GREEN} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 0.45rem 1.6rem !important;
    transition: background-color 0.2s ease;
}}
div.stButton > button[kind="primary"]:hover {{
    background-color: {NAVY} !important;
}}

/* ── Code block (TAC) ────────────────────────────────────────────────── */
[data-testid="stCode"], .stCode {{
    border: 2px solid {NAVY} !important;
    border-radius: 8px !important;
    background-color: {NAVY}0D !important;   /* 5 % navy tint */
}}
[data-testid="stCode"] code {{
    color: {NAVY} !important;
    font-size: 0.93rem !important;
}}

/* ── Dataframe / table ───────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 2px solid {GREEN} !important;
    border-radius: 8px !important;
    overflow: hidden;
}}

/* ── Divider ─────────────────────────────────────────────────────────── */
hr {{
    border-color: {PINK} !important;
    border-width: 2px !important;
}}

/* ── Info / error boxes ──────────────────────────────────────────────── */
[data-testid="stAlert"] {{
    border-radius: 8px !important;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.title("Intermediate Code Generator")
st.markdown(
    "Converts arithmetic expressions into **Three-Address Code**, "
    "**Quadruples**, and **Triples**."
)

# ---------------------------------------------------------------------------
# Input area
# ---------------------------------------------------------------------------

DEFAULT_INPUT = "x = a + b * c - d / e\ny = -a * (b + c)"

source = st.text_area(
    label="Source expression(s)",
    value=DEFAULT_INPUT,
    height=140,
    key="source_input",
)
st.caption("One statement per line, for example `x = a + b * c`.")

generate_clicked = st.button("Generate Code", type="primary")

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

if generate_clicked:
    # 1. Split into lines, preserve original line numbers (1-based).
    raw_lines = source.splitlines()
    numbered_lines = [
        (lineno + 1, text)
        for lineno, text in enumerate(raw_lines)
        if text.strip()          # skip blank / whitespace-only lines
    ]

    if not numbered_lines:
        st.info("Please enter at least one expression.")
        st.stop()

    # 2. Lex + parse every non-empty line.
    asts = []
    error_occurred = False

    for lineno, text in numbered_lines:
        try:
            tokens = tokenize(text, lineno)
            ast    = parse(tokens, lineno)
            asts.append(ast)
        except CompilerError as err:
            st.error(str(err))
            error_occurred = True
            break          # stop at first error, show nothing else

    if error_occurred:
        st.stop()

    # 3. Generate intermediate code.
    tac, quadruples, triples = generate(asts)

    if not tac:
        st.info(
            "No intermediate code is needed: the input contains only "
            "bare literals or identifiers."
        )
        st.stop()

    # 4. Display results.
    st.divider()

    # --- Three-Address Code -------------------------------------------
    st.subheader("Three-Address Code")
    st.code("\n".join(tac), language=None)

    # --- Quadruples ---------------------------------------------------
    st.subheader("Quadruples")
    quad_df = pd.DataFrame(
        quadruples,
        columns=["Index", "Op", "Arg1", "Arg2", "Result"],
    )
    quad_df = quad_df.set_index("Index")
    st.dataframe(quad_df, use_container_width=True)

    # --- Triples ------------------------------------------------------
    st.subheader("Triples")
    triple_df = pd.DataFrame(
        triples,
        columns=["Index", "Op", "Arg1", "Arg2"],
    )
    triple_df = triple_df.set_index("Index")
    st.dataframe(triple_df, use_container_width=True)
