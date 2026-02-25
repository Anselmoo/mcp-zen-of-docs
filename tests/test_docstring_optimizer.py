"""Tests for the docstring audit and optimize tools."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pathlib import Path

from mcp_zen_of_docs.docstring_optimizer import audit_docstrings_impl
from mcp_zen_of_docs.docstring_optimizer import optimize_docstrings_impl
from mcp_zen_of_docs.models import DocstringAuditRequest
from mcp_zen_of_docs.models import DocstringAuditResponse
from mcp_zen_of_docs.models import DocstringLanguage
from mcp_zen_of_docs.models import DocstringOptimizerRequest
from mcp_zen_of_docs.models import DocstringOptimizerResponse
from mcp_zen_of_docs.models import DocstringStyle


__all__: list[str] = []

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_PYTHON_SAMPLE = """\
def greet(name: str) -> str:
    return f"Hello, {name}"


class Greeter:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def greet(self, name: str) -> str:
        return f"{self.prefix} {name}"
"""

_TYPESCRIPT_SAMPLE = """\
export function add(a: number, b: number): number {
    return a + b;
}

export class Calculator {
    multiply(a: number, b: number): number {
        return a * b;
    }
}
"""

_GO_SAMPLE = """\
package main

func Add(a, b int) int {
    return a + b
}

type Calculator struct{}

func (c Calculator) Multiply(a, b int) int {
    return a * b
}
"""

_RUST_SAMPLE = """\
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

pub struct Calculator;

impl Calculator {
    pub fn multiply(&self, a: i32, b: i32) -> i32 {
        a * b
    }
}
"""


# ---------------------------------------------------------------------------
# Model validation tests
# ---------------------------------------------------------------------------


def test_docstring_audit_request_valid(tmp_path: Path) -> None:
    """DocstringAuditRequest accepts valid path + optional language."""
    f = tmp_path / "sample.py"
    f.write_text("def foo(): pass\n")
    req = DocstringAuditRequest(source_path=f)
    assert req.source_path == f
    assert req.language is None


def test_docstring_optimizer_request_valid(tmp_path: Path) -> None:
    """DocstringOptimizerRequest defaults to dry-run (overwrite=False)."""
    f = tmp_path / "sample.py"
    f.write_text("def foo(): pass\n")
    req = DocstringOptimizerRequest(source_path=f)
    assert req.overwrite is False
    assert req.style is None


# ---------------------------------------------------------------------------
# audit_docstrings_impl tests
# ---------------------------------------------------------------------------


def test_audit_python_detects_missing_docstrings(tmp_path: Path) -> None:
    """audit_docstrings_impl finds undocumented Python symbols."""
    f = tmp_path / "sample.py"
    f.write_text(_PYTHON_SAMPLE)
    result = audit_docstrings_impl(DocstringAuditRequest(source_path=f))
    assert isinstance(result, DocstringAuditResponse)
    assert result.total_symbols > 0
    assert result.total_symbols - result.documented_symbols > 0
    assert result.coverage * 100 < 100.0


def test_audit_returns_typed_response(tmp_path: Path) -> None:
    """audit_docstrings_impl always returns DocstringAuditResponse, never dict."""
    f = tmp_path / "sample.py"
    f.write_text("def foo(): pass\n")
    result = audit_docstrings_impl(DocstringAuditRequest(source_path=f))
    assert isinstance(result, DocstringAuditResponse)


def test_audit_typescript_symbols(tmp_path: Path) -> None:
    """audit_docstrings_impl detects TypeScript undocumented symbols."""
    f = tmp_path / "sample.ts"
    f.write_text(_TYPESCRIPT_SAMPLE)
    result = audit_docstrings_impl(
        DocstringAuditRequest(source_path=f, language=DocstringLanguage.TYPESCRIPT)
    )
    assert result.total_symbols >= 2
    assert result.language == DocstringLanguage.TYPESCRIPT


def test_audit_fully_documented_file(tmp_path: Path) -> None:
    """audit_docstrings_impl reports 100% coverage for a fully documented file."""
    f = tmp_path / "sample.py"
    documented_source = (
        '"""Module."""\n\n'
        "def greet(name: str) -> str:\n"
        '    """Greet a person.\n\n'
        "    Args:\n"
        "        name: The name.\n\n"
        "    Returns:\n"
        "        Greeting string.\n"
        '    """\n'
        '    return f"Hello, {name}"\n'
    )
    f.write_text(documented_source)
    result = audit_docstrings_impl(DocstringAuditRequest(source_path=f))
    assert result.coverage * 100 == 100.0


# ---------------------------------------------------------------------------
# optimize_docstrings_impl tests
# ---------------------------------------------------------------------------


def test_optimize_python_inserts_stubs(tmp_path: Path) -> None:
    """optimize_docstrings_impl inserts Google-style stubs for Python."""
    f = tmp_path / "sample.py"
    f.write_text(_PYTHON_SAMPLE)
    result = optimize_docstrings_impl(DocstringOptimizerRequest(source_path=f))
    assert isinstance(result, DocstringOptimizerResponse)
    assert result.symbols_optimized > 0
    assert result.output is not None
    assert '"""' in result.output


def test_optimize_dry_run_does_not_write_file(tmp_path: Path) -> None:
    """optimize_docstrings_impl with overwrite=False does not modify the file."""
    f = tmp_path / "sample.py"
    original = _PYTHON_SAMPLE
    f.write_text(original)
    optimize_docstrings_impl(DocstringOptimizerRequest(source_path=f, overwrite=False))
    assert f.read_text() == original


def test_optimize_overwrite_writes_file(tmp_path: Path) -> None:
    """optimize_docstrings_impl with overwrite=True writes patched content."""
    f = tmp_path / "sample.py"
    f.write_text(_PYTHON_SAMPLE)
    result = optimize_docstrings_impl(DocstringOptimizerRequest(source_path=f, overwrite=True))
    assert result.symbols_optimized > 0
    assert '"""' in f.read_text()


def test_optimize_typescript_jsdoc(tmp_path: Path) -> None:
    """optimize_docstrings_impl inserts JSDoc stubs for TypeScript."""
    f = tmp_path / "sample.ts"
    f.write_text(_TYPESCRIPT_SAMPLE)
    result = optimize_docstrings_impl(
        DocstringOptimizerRequest(
            source_path=f, language=DocstringLanguage.TYPESCRIPT, style=DocstringStyle.JSDOC
        )
    )
    assert isinstance(result, DocstringOptimizerResponse)
    assert result.output is not None
    assert "/**" in result.output


def test_optimize_go_godoc(tmp_path: Path) -> None:
    """optimize_docstrings_impl inserts GoDoc comments for Go."""
    f = tmp_path / "sample.go"
    f.write_text(_GO_SAMPLE)
    result = optimize_docstrings_impl(
        DocstringOptimizerRequest(
            source_path=f, language=DocstringLanguage.GO, style=DocstringStyle.GODOC
        )
    )
    assert isinstance(result, DocstringOptimizerResponse)
    assert result.output is not None
    assert "// Add" in result.output or "// Calculator" in result.output


def test_optimize_rust_rustdoc(tmp_path: Path) -> None:
    """optimize_docstrings_impl inserts RustDoc comments for Rust."""
    f = tmp_path / "sample.rs"
    f.write_text(_RUST_SAMPLE)
    result = optimize_docstrings_impl(
        DocstringOptimizerRequest(
            source_path=f, language=DocstringLanguage.RUST, style=DocstringStyle.RUSTDOC
        )
    )
    assert isinstance(result, DocstringOptimizerResponse)
    assert result.output is not None
    assert "///" in result.output


def test_optimize_already_documented_noop(tmp_path: Path) -> None:
    """optimize_docstrings_impl makes no changes when all symbols are documented."""
    f = tmp_path / "sample.py"
    content = (
        '"""Module."""\n\n'
        "def greet(name: str) -> str:\n"
        '    """Greet a person."""\n'
        '    return f"Hello, {name}"\n'
    )
    f.write_text(content)
    result = optimize_docstrings_impl(DocstringOptimizerRequest(source_path=f))
    assert result.symbols_optimized == 0
