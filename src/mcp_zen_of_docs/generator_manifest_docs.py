"""Project manifest documentation generation helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .models import GenerateProjectManifestDocsResponse
from .models import ManifestType


__all__ = ["generate_project_manifest_docs"]


def _coerce_path(value: Path | str | None) -> Path | None:
    """Convert optional path-like input into a Path instance."""
    if value in (None, ""):
        return None
    return Path(value)


def _dedup_blank_lines(lines: list[str]) -> str:
    """Join lines, collapsing consecutive blank lines into one."""
    cleaned: list[str] = []
    prev_blank = False
    for line in lines:
        if line == "" and prev_blank:
            continue
        cleaned.append(line)
        prev_blank = line == ""
    return "\n".join(cleaned).rstrip() + "\n"


def _generate_pyproject_markdown(toml_path: Path) -> tuple[str, str, str]:
    """Parse pyproject.toml and return rendered markdown plus name/version."""
    import tomllib  # noqa: PLC0415

    with toml_path.open("rb") as fh:
        data = tomllib.load(fh)

    project = data.get("project", {})
    name = project.get("name", "")
    version = project.get("version", "")
    description = project.get("description", "")
    readme = project.get("readme", "")
    requires_python = project.get("requires-python", "")
    scripts = project.get("scripts", {})
    deps: list[str] = project.get("dependencies", [])
    dep_groups: dict[str, list[str]] = data.get("dependency-groups", {})
    build_system: dict[str, object] = data.get("build-system", {})
    tool: dict[str, object] = data.get("tool", {})

    lines: list[str] = [
        f"# {name}" if name else "# Project",
        "",
        f"> {description}" if description else "",
        "",
        "---",
        "",
        "## Project Metadata",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **Name** | `{name}` |",
        f"| **Version** | `{version}` |",
        f"| **Python** | `{requires_python}` |",
        *([f"| **Readme** | `{readme}` |"] if readme else []),
        "",
    ]
    if scripts:
        lines += [
            "## Entry-Point Scripts",
            "",
            "| Script | Entry Point |",
            "| ------ | ----------- |",
            *[f"| `{key}` | `{value}` |" for key, value in scripts.items()],
            "",
        ]
    if deps:
        lines += [
            "## Runtime Dependencies",
            "",
            "| Package |",
            "| ------- |",
            *[f"| `{dep}` |" for dep in deps],
            "",
        ]
    for group_name, group_deps in dep_groups.items():
        title = group_name.replace("-", " ").title()
        lines += [
            f"## {title} Dependencies (`{group_name}` group)",
            "",
            "| Package |",
            "| ------- |",
            *[f"| `{dep}` |" for dep in group_deps],
            "",
        ]
    if build_system:
        backend = build_system.get("build-backend", "")
        requires_build = build_system.get("requires", [])
        lines += [
            "## Build System",
            "",
            f"- **Backend:** `{backend}`",
            *(f"- **Requires:** `{requirement}`" for requirement in requires_build),
            "",
        ]
    for tool_key, tool_title in [
        ("pytest", "pytest"),
        ("ruff", "ruff"),
        ("ty", "ty (type checker)"),
        ("poe", "Poe the Poet tasks"),
    ]:
        tool_data = tool.get(tool_key)
        if not tool_data:
            continue
        lines += [f"## `[tool.{tool_key}]` — {tool_title}", ""]
        if isinstance(tool_data, dict):
            if tool_key == "poe" and "tasks" in tool_data:
                lines += ["| Task | Command |", "| ---- | ------- |"]
                for task_name, task_value in tool_data["tasks"].items():
                    cmd = task_value if isinstance(task_value, str) else str(task_value)
                    lines.append(f"| `poe {task_name}` | `{cmd}` |")
                lines.append("")
            else:
                lines += ["```toml", *[f"{k} = {v!r}" for k, v in tool_data.items()], "```", ""]
        lines.append("")
    return _dedup_blank_lines(lines), name, version


def _generate_nodejs_markdown(manifest_path: Path) -> tuple[str, str, str]:
    """Parse package.json and return rendered markdown plus name/version."""
    import json  # noqa: PLC0415

    data: dict[str, object] = json.loads(manifest_path.read_text(encoding="utf-8"))
    name = str(data.get("name", ""))
    version = str(data.get("version", ""))
    description = str(data.get("description", ""))
    main = str(data.get("main", ""))
    license_ = str(data.get("license", ""))
    engines: dict[str, str] = data.get("engines", {})
    scripts: dict[str, str] = data.get("scripts", {})
    deps: dict[str, str] = data.get("dependencies", {})
    dev_deps: dict[str, str] = data.get("devDependencies", {})
    peer_deps: dict[str, str] = data.get("peerDependencies", {})

    lines: list[str] = [
        f"# {name}" if name else "# Project",
        "",
        f"> {description}" if description else "",
        "",
        "---",
        "",
        "## Package Metadata",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **Name** | `{name}` |",
        f"| **Version** | `{version}` |",
        *([f"| **License** | `{license_}` |"] if license_ else []),
        *([f"| **Main** | `{main}` |"] if main else []),
        *(
            [f"| **Engines** | {', '.join(f'`{k}: {v}`' for k, v in engines.items())} |"]
            if engines
            else []
        ),
        "",
    ]
    if scripts:
        lines += [
            "## Scripts",
            "",
            "| Script | Command |",
            "| ------ | ------- |",
            *[f"| `npm run {k}` | `{v}` |" for k, v in scripts.items()],
            "",
        ]
    if deps:
        lines += [
            "## Dependencies",
            "",
            "| Package | Version |",
            "| ------- | ------- |",
            *[f"| `{k}` | `{v}` |" for k, v in deps.items()],
            "",
        ]
    if dev_deps:
        lines += [
            "## Dev Dependencies",
            "",
            "| Package | Version |",
            "| ------- | ------- |",
            *[f"| `{k}` | `{v}` |" for k, v in dev_deps.items()],
            "",
        ]
    if peer_deps:
        lines += [
            "## Peer Dependencies",
            "",
            "| Package | Version |",
            "| ------- | ------- |",
            *[f"| `{k}` | `{v}` |" for k, v in peer_deps.items()],
            "",
        ]
    return _dedup_blank_lines(lines), name, version


def _as_str_object_dict(value: object) -> dict[str, object]:
    """Normalize loose mapping-like input into a string-keyed dict."""
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _as_str_list_dict(value: object) -> dict[str, list[str]]:
    """Normalize loose mapping-like input into string lists keyed by strings."""
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for key, item in value.items():
        if isinstance(item, list):
            normalized[str(key)] = [str(entry) for entry in item]
    return normalized


def _as_str_list(value: object) -> list[str]:
    """Normalize loose sequence input into a list of strings."""
    if not isinstance(value, list):
        return []
    return [str(entry) for entry in value]


def _generate_cargo_markdown(manifest_path: Path) -> tuple[str, str, str]:
    """Parse Cargo.toml and return rendered markdown plus name/version."""
    import tomllib  # noqa: PLC0415

    with manifest_path.open("rb") as fh:
        data = tomllib.load(fh)

    pkg = _as_str_object_dict(data.get("package"))
    name = str(pkg.get("name", ""))
    version = str(pkg.get("version", ""))
    edition = str(pkg.get("edition", ""))
    description = str(pkg.get("description", ""))
    license_ = str(pkg.get("license", ""))
    rust_version = str(pkg.get("rust-version", ""))
    deps = _as_str_object_dict(data.get("dependencies"))
    dev_deps = _as_str_object_dict(data.get("dev-dependencies"))
    features = _as_str_list_dict(data.get("features"))

    def _dep_version(value: object) -> str:
        if isinstance(value, str):
            return value
        dep_config = _as_str_object_dict(value)
        if dep_config:
            return str(dep_config.get("version", "workspace"))
        return str(value)

    lines: list[str] = [
        f"# {name}" if name else "# Project",
        "",
        f"> {description}" if description else "",
        "",
        "---",
        "",
        "## Crate Metadata",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **Name** | `{name}` |",
        f"| **Version** | `{version}` |",
        *([f"| **Edition** | `{edition}` |"] if edition else []),
        *([f"| **MSRV** | `{rust_version}` |"] if rust_version else []),
        *([f"| **License** | `{license_}` |"] if license_ else []),
        "",
    ]
    if deps:
        lines += [
            "## Dependencies",
            "",
            "| Crate | Version |",
            "| ----- | ------- |",
            *[f"| `{k}` | `{_dep_version(v)}` |" for k, v in deps.items()],
            "",
        ]
    if dev_deps:
        lines += [
            "## Dev Dependencies",
            "",
            "| Crate | Version |",
            "| ----- | ------- |",
            *[f"| `{k}` | `{_dep_version(v)}` |" for k, v in dev_deps.items()],
            "",
        ]
    if features:
        lines += ["## Feature Flags", ""]
        for feat_name, feat_deps in features.items():
            enables = ", ".join(f"`{dep}`" for dep in feat_deps) if feat_deps else "*(no extras)*"
            lines.append(f"- **`{feat_name}`** — enables: {enables}")
        lines.append("")
    return _dedup_blank_lines(lines), name, version


def _generate_gomod_markdown(manifest_path: Path) -> tuple[str, str, str]:
    """Parse go.mod and return rendered markdown plus module/version."""
    import re  # noqa: PLC0415

    content = manifest_path.read_text(encoding="utf-8")
    module_match = re.search(r"^module\s+(\S+)", content, re.MULTILINE)
    go_match = re.search(r"^go\s+(\S+)", content, re.MULTILINE)
    module = module_match.group(1) if module_match else ""
    go_version = go_match.group(1) if go_match else ""
    name = module.split("/")[-1]

    requires = re.findall(r"^\s+(\S+)\s+(\S+)", content, re.MULTILINE)
    direct = [
        (module_name, version)
        for module_name, version in requires
        if not version.endswith("// indirect")
    ]

    lines: list[str] = [
        f"# {name}" if name else "# Go Module",
        "",
        "---",
        "",
        "## Module Metadata",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **Module** | `{module}` |",
        f"| **Go Version** | `{go_version}` |",
        "",
    ]
    if direct:
        lines += [
            "## Direct Dependencies",
            "",
            "| Module | Version |",
            "| ------ | ------- |",
            *[f"| `{module_name}` | `{version}` |" for module_name, version in direct],
            "",
        ]
    return _dedup_blank_lines(lines), module, go_version


def _generate_gemfile_markdown(manifest_path: Path) -> tuple[str, str, str]:
    """Parse Gemfile or gemspec and return rendered markdown plus name/version."""
    import re  # noqa: PLC0415

    content = manifest_path.read_text(encoding="utf-8")
    name = ""
    version = ""
    if manifest_path.suffix == ".gemspec":
        name_match = re.search(r'\.name\s*=\s*["\']([^"\']+)["\']', content)
        version_match = re.search(r'\.version\s*=\s*["\']([^"\']+)["\']', content)
        name = name_match.group(1) if name_match else ""
        version = version_match.group(1) if version_match else ""

    gems = re.findall(r"""gem\s+['"]([\w\-]+)['"](?:,\s*['"~>=<^! ]*([^'"\n]+))?""", content)
    ruby_match = re.search(r"^ruby\s+['\"]([^'\"]+)['\"]", content, re.MULTILINE)
    ruby_version = ruby_match.group(1) if ruby_match else ""

    display_name = name or manifest_path.stem
    lines: list[str] = [
        f"# {display_name}",
        "",
        "---",
        "",
        "## Gemfile Metadata",
        "",
        "| Field | Value |",
        "| ----- | ----- |",
        f"| **File** | `{manifest_path.name}` |",
        *([f"| **Ruby** | `{ruby_version}` |"] if ruby_version else []),
        *([f"| **Version** | `{version}` |"] if version else []),
        "",
    ]
    if gems:
        lines += [
            "## Gems",
            "",
            "| Gem | Version Constraint |",
            "| --- | ----------------- |",
            *[
                f"| `{gem}` | `{constraint.strip()}` |"
                if constraint.strip()
                else f"| `{gem}` | *(any)* |"
                for gem, constraint in gems
            ],
            "",
        ]
    return _dedup_blank_lines(lines), display_name, version


type ManifestParser = Callable[[Path], tuple[str, str, str]]


_MANIFEST_CANDIDATES: list[tuple[str, ManifestType, ManifestParser]] = [
    ("pyproject.toml", ManifestType.PYTHON, _generate_pyproject_markdown),
    ("package.json", ManifestType.NODEJS, _generate_nodejs_markdown),
    ("Cargo.toml", ManifestType.RUST, _generate_cargo_markdown),
    ("go.mod", ManifestType.GO, _generate_gomod_markdown),
    ("Gemfile", ManifestType.RUBY, _generate_gemfile_markdown),
]


def generate_project_manifest_docs(  # noqa: C901, PLR0912
    target: Path | str | None = None,
    output_file: Path | str | None = None,
) -> GenerateProjectManifestDocsResponse:
    """Generate a Markdown reference page from a project manifest."""
    target_path = _coerce_path(target) or Path.cwd()

    if target_path.is_file():
        for filename, manifest_type, parser in _MANIFEST_CANDIDATES:
            if target_path.name == filename or target_path.name.endswith(".gemspec"):
                manifest_path = target_path
                resolved_type = manifest_type
                resolved_parser: ManifestParser | None = parser
                break
        else:
            return GenerateProjectManifestDocsResponse(
                status="error",
                manifest_type=ManifestType.UNKNOWN,
                manifest_file=target_path.name,
                message=f"Unrecognised manifest file: {target_path.name}",
            )
    else:
        manifest_path = None
        resolved_type = ManifestType.UNKNOWN
        resolved_parser = None
        for filename, manifest_type, parser in _MANIFEST_CANDIDATES:
            candidate = target_path / filename
            if candidate.exists():
                manifest_path = candidate
                resolved_type = manifest_type
                resolved_parser = parser
                break
        if manifest_path is None:
            gemspecs = list(target_path.glob("*.gemspec"))
            if gemspecs:
                manifest_path = gemspecs[0]
                resolved_type = ManifestType.RUBY
                resolved_parser = _generate_gemfile_markdown
        if manifest_path is None:
            return GenerateProjectManifestDocsResponse(
                status="error",
                manifest_type=ManifestType.UNKNOWN,
                message=(
                    f"No recognised project manifest found in {target_path}. "
                    "Looked for: pyproject.toml, package.json, Cargo.toml, go.mod, "
                    "Gemfile, *.gemspec"
                ),
            )

    if resolved_parser is None:
        return GenerateProjectManifestDocsResponse(
            status="error",
            manifest_type=resolved_type,
            manifest_file=manifest_path.name,
            message=f"Unable to resolve a parser for {manifest_path.name}.",
        )

    try:
        markdown, name, version = resolved_parser(manifest_path)
    except Exception as exc:  # noqa: BLE001
        return GenerateProjectManifestDocsResponse(
            status="error",
            manifest_type=resolved_type,
            manifest_file=manifest_path.name,
            message=f"Failed to parse {manifest_path.name}: {exc}",
        )

    out_path = _coerce_path(output_file)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")

    return GenerateProjectManifestDocsResponse(
        status="success",
        manifest_type=resolved_type,
        manifest_file=manifest_path.name,
        project_name=name or None,
        project_version=version or None,
        output_file=out_path,
        markdown=markdown,
    )
