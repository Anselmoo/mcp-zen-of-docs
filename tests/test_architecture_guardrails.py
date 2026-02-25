from __future__ import annotations

import ast

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
PACKAGE_ROOT = SRC_ROOT / "mcp_zen_of_docs"


def _module_path_for_file(file_path: Path) -> str:
    relative = file_path.relative_to(SRC_ROOT).with_suffix("")
    module_path = ".".join(relative.parts)
    return module_path.removesuffix(".__init__")


def _resolve_from_import_module(file_path: Path, node: ast.ImportFrom) -> str | None:
    if node.module is None and node.level == 0:
        return None
    if node.level == 0:
        return node.module
    module_path = _module_path_for_file(file_path)
    package_parts = module_path.split(".")
    if file_path.stem != "__init__":
        package_parts = package_parts[:-1]
    trim_count = max(node.level - 1, 0)
    if trim_count:
        package_parts = package_parts[:-trim_count]
    if node.module:
        package_parts.extend(node.module.split("."))
    return ".".join(part for part in package_parts if part)


def _collect_imports(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        module_name = _resolve_from_import_module(file_path, node)
        if module_name:
            imports.add(module_name)
    return imports


def _assert_no_forbidden_imports(
    file_paths: list[Path],
    forbidden_prefixes: tuple[str, ...],
) -> None:
    violations: list[str] = []
    for file_path in file_paths:
        imports = _collect_imports(file_path)
        violations.extend(
            f"{file_path.relative_to(REPO_ROOT)} -> {module_name}"
            for module_name in sorted(imports)
            if module_name.startswith(forbidden_prefixes)
        )
    assert violations == [], "Forbidden cross-layer imports detected:\n" + "\n".join(violations)


def test_domain_layer_has_no_transport_or_runtime_dependencies() -> None:
    domain_files = sorted((PACKAGE_ROOT / "domain").glob("*.py"))
    _assert_no_forbidden_imports(
        domain_files,
        forbidden_prefixes=(
            "mcp_zen_of_docs.frameworks",
            "mcp_zen_of_docs.infrastructure",
            "mcp_zen_of_docs.interfaces",
            "mcp_zen_of_docs.server",
            "mcp_zen_of_docs.cli",
            "fastmcp",
            "typer",
            "subprocess",
        ),
    )


def test_generators_use_infrastructure_gateways_not_framework_runtime_imports() -> None:
    generator_imports = _collect_imports(PACKAGE_ROOT / "generators.py")
    assert "mcp_zen_of_docs.frameworks" not in generator_imports
    assert "mcp_zen_of_docs.infrastructure" in generator_imports


def test_infrastructure_layer_does_not_import_business_policy_modules() -> None:
    infrastructure_files = sorted((PACKAGE_ROOT / "infrastructure").glob("*.py"))
    _assert_no_forbidden_imports(
        infrastructure_files,
        forbidden_prefixes=(
            "mcp_zen_of_docs.modules",
            "mcp_zen_of_docs.validators",
            "mcp_zen_of_docs.generator.orchestrator",
            "mcp_zen_of_docs.generators",
            "mcp_zen_of_docs.interfaces",
            "mcp_zen_of_docs.server",
            "mcp_zen_of_docs.cli",
        ),
    )
