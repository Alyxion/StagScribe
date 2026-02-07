# StagScribe

A human-readable language for SVG design. `.stag` files compile to SVG and render to PNG via resvg.

## Commands

```bash
poetry install                          # install deps
poetry run pytest                       # run tests
poetry run ruff check src/ tests/       # lint
poetry run mypy src/                    # type check
poetry run stagscribe lint <file.stag>  # validate .stag file
poetry run stagscribe convert <file.stag> -o out.svg  # .stag → .svg
poetry run stagscribe render <file.stag> -o out.png   # .stag → .png
poetry run stagscribe parse <file.stag>               # show AST (debug)
```

## Architecture

```
.stag text → Parser (Lark) → AST → Resolver → Linter → Converter → SVG string → Renderer (resvg) → PNG
```

### Pipeline stages

1. **Parser** (`src/stagscribe/parser/`) — Lark LALR(1) with custom Indenter for whitespace sensitivity. Produces parse tree.
2. **Transformer** (`src/stagscribe/parser/transformer.py`) — Converts Lark parse tree to typed AST nodes.
3. **Linter** (`src/stagscribe/linter/`) — Validates AST: checks structure, element references, units, colors, styles.
4. **Converter** (`src/stagscribe/converter/`) — Two-pass: (1) resolve units+positions to absolute pixels, (2) emit SVG XML.
5. **Renderer** (`src/stagscribe/renderer/`) — resvg-py primary, `resvg` CLI fallback.

### Key directories

- `src/stagscribe/language/` — Language spec: AST nodes, grammar, colors, units
- `src/stagscribe/parser/` — Lexer, parser, tree→AST transformer
- `src/stagscribe/linter/` — Validation rules and diagnostics
- `src/stagscribe/converter/` — AST→SVG conversion, layout, shapes, styles
- `src/stagscribe/renderer/` — SVG→PNG rendering
- `src/stagscribe/cli/` — Click CLI entry points
- `tests/` — Mirrors src structure
- `samples/` — .stag, .svg, .txt triples organized by category

## Language conventions

- Indentation: 2 spaces, no tabs
- Comments: `-- like this`
- Element names in double quotes: `rectangle "Living Room"`
- **No commas anywhere** in the language
- One property per indented line: `fill red`, `stroke black 2 pixels`
- Variable assignment uses `is`: `desk_width is 80`
- Color palette uses `is`: `wall is #FAFAFA`
- Size inline on element line: `rect "Box" 200 by 100`
- Coordinates without commas: `at 50% 20%`, `from 100 200`
- Parenthesized polygon points: `points (8 36) (32 8) (56 36)`
- Space-separated RGB: `fill rgb(128 64 200)`
- Natural positioning: `at center`, `below "Title" with gap 20`
- Place statements use body block for properties:
  ```
  place desk "D1"
    below "Whiteboard" with gap 80
  ```

## Code conventions

- Python 3.13, managed with Poetry
- Type hints on all public functions
- Tests in `tests/` mirroring `src/stagscribe/` structure
- Ruff for linting, mypy for type checking
