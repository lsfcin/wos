# stubgen
> Interface stubs and paper scaffolding, generated on save and on commit.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | Which interface each language gets, what generates it, and the one supported way to lift the size cap while you work. |
| [`dart-api-extract.py`](dart-api-extract.py) | [`dart-api-extract.pyi`](dart-api-extract.pyi) | `extract`, `main` | Extract public Dart API surface into a compact .dart.api stub file |
| [`paper-scaffold.py`](paper-scaffold.py) | [`paper-scaffold.pyi`](paper-scaffold.pyi) | `scaffold`, `main` | paper-scaffold.py: Initialize or adapt a paper directory to workspace standards. new <name>    — create academy/papers/<name>/ from template adapt <path>  — add missing scaffold files to an existing paper Both modes are safe: existing files are never overwritten (skipped with ~). |
| [`stubs.py`](stubs.py) | [`stubs.pyi`](stubs.pyi) | `interface_for`, `stub_out_dir`, `find_stubgen`, `emit_pyi`, `emit_dts` | Generate the interface for ONE file: the single copy of every stub-generator invocation. |
| [`tex-interface-gen.py`](tex-interface-gen.py) | [`tex-interface-gen.pyi`](tex-interface-gen.pyi) | `write_interface`, `check_relationships`, `regenerate_labels`, `bib_check`, `main` | tex-interface-gen.py: Generate .texif interfaces, labels.md, and bib/review checks. |
| [`tex_interface_parser.py`](tex_interface_parser.py) | [`tex_interface_parser.pyi`](tex_interface_parser.pyi) | `line_of`, `extract_braced`, `extract_caption`, `first_prose_snippet`, `find_paper_root` | tex_interface_parser.py: LaTeX source parser for tex-interface-gen.py. Extracts structure, equations, floats, citations, labels, and inputs. |
<!-- routing:end -->
