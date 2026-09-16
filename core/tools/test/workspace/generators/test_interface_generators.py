# T0 interface-generator invariants: a generated stub must land beside its source, and a
# jsconfig.json must never pretend to be a build config. Both bugs this guards were silent —
# the JS declaration path exited 0 and emitted nothing for years (ROADMAP Batch B item 6).
import json
import re
import subprocess
from pathlib import Path

from conftest import WORKSPACE_ROOT

POSTEDIT = WORKSPACE_ROOT / "core/hooks/postedit/interfaces.sh"
PRECOMMIT = WORKSPACE_ROOT / "core/hooks/commit/generators.py"
# The one place the stubgen and tsc invocations live since 2026-08-20, in Python since the
# os-agnostic port. Both callers above reach it; asking either of them for the flags asks the
# wrong file.
SHARED = WORKSPACE_ROOT / "core/hooks/stubgen/stubs.py"

# Keys tsc silently ignores in a file NAMED jsconfig.json: the name implies noEmit:true.
# Carrying them is how the workspace convinced itself declarations were being generated.
EMIT_KEYS = {"declaration", "emitDeclarationOnly", "outDir", "declarationDir"}


def _tracked(*patterns: str) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", *patterns],
        cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=True, encoding='utf-8'
    ).stdout
    return [WORKSPACE_ROOT / p for p in out.split("\0") if p]


def _templates(script: Path, name: str) -> list[str]:
    """Heredoc bodies the script scaffolds into <dir>/<name>."""
    body = script.read_text(encoding="utf-8")
    pattern = re.compile(
        r'cat > "\$dir/' + re.escape(name) + r'" << \'EOF\'\n(.*?)\nEOF', re.DOTALL
    )
    return pattern.findall(body)


def test_jsconfig_template_carries_no_emit_keys() -> None:
    templates = _templates(POSTEDIT, "jsconfig.json")
    assert templates, "postedit/interfaces.sh no longer scaffolds a jsconfig.json"
    for raw in templates:
        opts = json.loads(raw).get("compilerOptions", {})
        offenders = EMIT_KEYS & set(opts)
        assert not offenders, (
            f"jsconfig.json template declares {sorted(offenders)}, which tsc ignores "
            "because the file name implies noEmit:true. jsconfig is an editor aid; "
            "declarations are emitted per file by the tsc call above it."
        )


def test_tracked_jsconfigs_carry_no_emit_keys() -> None:
    for cfg in _tracked("*jsconfig.json"):
        opts = json.loads(cfg.read_text(encoding="utf-8")).get("compilerOptions", {})
        offenders = EMIT_KEYS & set(opts)
        assert not offenders, (
            f"{cfg.relative_to(WORKSPACE_ROOT)} declares {sorted(offenders)} — "
            "silently ignored, see the jsconfig template in postedit/interfaces.sh"
        )


def test_scaffolded_tsconfig_with_dot_outdir_declares_exclude() -> None:
    """tsc appends outDir to the DEFAULT exclude list, so `"outDir": "."` excludes the
    config's own directory unless exclude is stated — TS18003, zero inputs, no output."""
    for raw in _templates(POSTEDIT, "tsconfig.json"):
        cfg = json.loads(raw)
        if cfg.get("compilerOptions", {}).get("outDir") not in (".", "./"):
            continue
        assert "exclude" in cfg, (
            'tsconfig template sets "outDir": "." without an explicit "exclude". '
            "tsc adds outDir to the default exclude list, so the config excludes "
            "the very directory it is meant to compile (TS18003)."
        )


def test_js_declarations_are_generated_per_file_not_per_project() -> None:
    """`tsc -p <config>` reads its own previous output: our .d.ts sit beside their
    sources, so a project build resolves them as inputs and dies with TS5055."""
    # Comments explain the defect by naming it — match code only.
    code = "\n".join(l for l in SHARED.read_text(encoding="utf-8").splitlines()
                     if not l.lstrip().startswith("#"))
    assert "-p " not in code, (
        "emit_dts uses a tsc project build again — it must emit per file "
        "(--declarationDir), which is the whole reason both hooks share it"
    )
    assert "--declarationDir" in code


def test_neither_hook_re_inlines_the_call_it_shares() -> None:
    """The extraction only holds while both callers keep calling.

    Four near-identical tsc invocations and two stubgen ones drifted a flag at a time before
    2026-08-20; nothing noticed, because each copy worked. A new raw invocation in either
    fragment is that drift restarting, so it is the thing to fail on — not the flags, which
    the case above now checks in one place.
    """
    for script in (POSTEDIT, PRECOMMIT):
        code = "\n".join(l for l in script.read_text(encoding="utf-8").splitlines()
                          if not l.lstrip().startswith("#"))
        assert "stubs.py" in code or "stubs." in code, (
            f"{script.name} no longer reaches the shared emitters"
        )
        # `--declarationDir` is the PER-FILE call's signature, and only that one was
        # duplicated. The pre-commit TypeScript step's `tsc -p <cfg> --incremental` is a
        # different shape — once per project, not once per file — and stays where it is.
        assert "--declarationDir" not in code, (
            f"{script.name} spells out the per-file tsc call again — call emit_dts"
        )
        assert "--quiet" not in code, (
            f"{script.name} spells out a stubgen call again — call emit_pyi"
        )


def _stub_out_dir(path: str, cwd: Path) -> str:
    """The shared helper's answer, relative to `cwd` — asked of the module, not of a shell.

    It returns an absolute path now that it is Python; the relative form is what the two cases
    below are actually about, so the comparison is made here rather than by changing what the
    helper returns to suit a test.
    """
    import stubs
    return stubs.stub_out_dir(cwd / path).relative_to(cwd.resolve()).as_posix()


def test_stub_output_root_climbs_out_of_the_package(tmp_path: Path) -> None:
    """stubgen mirrors package structure under -o, so passing the file's OWN directory
    wrote `pkg/pkg/*.pyi`. The output root must be the directory above the package root."""
    pkg = tmp_path / "outer" / "pkg" / "sub"
    pkg.mkdir(parents=True)
    for d in (tmp_path / "outer" / "pkg", pkg):
        (d / "__init__.py").write_text("", encoding="utf-8", newline='\n')
    (pkg / "mod.py").write_text("# mod\n", encoding="utf-8", newline='\n')
    assert _stub_out_dir("outer/pkg/sub/mod.py", tmp_path) == "outer"


def test_stub_output_root_is_unchanged_outside_a_package(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "mod.py").write_text("# mod\n", encoding="utf-8", newline='\n')
    assert _stub_out_dir("plain/mod.py", tmp_path) == "plain"


def test_the_stubgen_output_root_comes_from_the_shared_helper() -> None:
    """One caller now — emit_pyi — so the assertion follows it there.

    What it guards is unchanged: passing the file's own directory to stubgen is what wrote a
    mirror of the path inside itself, deleted by hand three times before the cause was named.
    """
    body = SHARED.read_text(encoding="utf-8")
    assert "stub_out_dir" in body, "emit_pyi computes the stubgen -o path itself"
    assert '-o "$dir"' not in body, (
        "emit_pyi passes the file's own directory to stubgen again"
    )


def _repeated_run(parts: tuple[str, ...]) -> str | None:
    """Detect a path that mirrors part of itself: `a/a` or `a/b/a/b` — the signature of a
    generator resolving its output root against the wrong anchor."""
    for width in (1, 2):
        for i in range(len(parts) - 2 * width + 1):
            run = parts[i:i + width]
            if run == parts[i + width:i + 2 * width]:
                return "/".join(run * 2)
    return None


def test_no_generated_stub_sits_in_a_doubled_path() -> None:
    offenders = []
    for stub in _tracked("*.pyi", "*.d.ts", "*.dart.api"):
        rel = stub.relative_to(WORKSPACE_ROOT)
        doubled = _repeated_run(rel.parts[:-1])
        if doubled:
            offenders.append(f"{rel} (mirrors '{doubled}')")
    assert not offenders, (
        "generated stubs sit inside a mirror of their own path — the output root was "
        "resolved against the wrong anchor:\n  " + "\n  ".join(offenders)
    )
