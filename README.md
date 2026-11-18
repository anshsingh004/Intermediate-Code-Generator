# Intermediate Code Generator

A lightweight Python compiler front-to-middle end that parses arithmetic expressions and generates three classic intermediate representations:

1. **Three-Address Code (TAC)**
2. **Quadruples** `[Index, Op, Arg1, Arg2, Result]`
3. **Triples** `[Index, Op, Arg1, Arg2]`

Built with a hand-written lexer and recursive-descent parser (standard library only) and rendered interactively via **Streamlit**.

---

## Pipeline

```
Source text ──> Lexer ──> Tokens ──> Parser ──> AST ──> Code Generator ──> TAC / Quadruples / Triples (Streamlit)
```

- **Lexer (`lexer.py`)**: Regex-based tokeniser with exact 1-based column tracking.
- **Parser (`syntax_parser.py`)**: Hand-written recursive descent with 2-token lookahead for assignments vs bare expressions, building left-associative ASTs.
- **Code Generator (`code_generator.py`)**: Post-order tree walk emitting 4-field instructions, continuous temporary allocation (`t1`, `t2`, ...), identifier collision avoidance, and conversion to TAC, Quadruples, and Triples.

---

## Project Structure

```
Intermediate-Code-Generator/
├── app.py               # Streamlit web interface
├── lexer.py             # Tokenization and line/column tracking
├── syntax_parser.py     # Recursive descent parser
├── ast_nodes.py         # AST node dataclasses
├── code_generator.py    # AST -> TAC / Quadruples / Triples
├── errors.py            # Unified CompilerError exception
├── verify.py            # 18-case automated test suite
├── requirements.txt     # streamlit
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the application

```bash
streamlit run app.py
```

Open your browser at **`http://localhost:8501`**.

---

## Running Verification Tests

Run the headless 18-test regression suite:

```bash
python verify.py
```
