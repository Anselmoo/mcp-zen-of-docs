# Plan — Framework-Native Init as Core Onboarding Feature

## Core Insight

Each documentation framework has an authoritative CLI init command that creates the **official,
up-to-date folder structure**. The right approach: run these CLIs in a tmp dir, copy the results
back — always current, never a frozen snapshot we maintain manually.

The `run_ephemeral_install` mechanism in `generators.py` already does exactly this
(uvx/npx tmp-and-copy pattern). It's just broken and not wired into onboarding.

## What Each Framework Init Actually Creates (Verified by Running the CLI)

| Framework  | CLI command                         | Installer | Source subdir | Files created                                           | docs_root         |
|------------|-------------------------------------|-----------|---------------|---------------------------------------------------------|-------------------|
| Zensical   | `uvx zensical new .`               | uvx       | `.` (no sub)  | `zensical.toml`, `docs/index.md`, `docs/markdown.md`, `.github/workflows/docs.yml` | `docs/` |
| Docusaurus | `npx create-docusaurus@latest site classic --typescript --skip-install` | npx | `site/` | `site/docs/`, `site/docusaurus.config.ts`, `site/sidebars.ts` | `docs/` |
| VitePress  | `npx vitepress@latest init docs`   | npx       | `.` (no sub)  | `docs/.vitepress/config.mts`, `docs/index.md`          | `docs/`           |
| Starlight  | `npm create astro@latest site -- --template starlight --no-install --no-git --yes` | npx | `site/` | `site/src/content/docs/guides/example.md`, `site/src/content/docs/reference/example.md`, `site/astro.config.mjs` | `src/content/docs/` |

**Key nuance — Docusaurus and Starlight create a named subdir** (`site/`). The copy step must
strip that prefix: `site/docs/` → `docs/`, `site/astro.config.mjs` → `astro.config.mjs`, etc.

**VitePress requires stdin defaults** — `npx vitepress init docs` is interactive; pipe `"\n\n\n\n"` to accept all defaults.

## Root Causes (with exact locations)

| # | Root cause | Location |
|---|---|---|
| 1 | `_build_ephemeral_cmd` uvx flags wrong — `--with`/`--python-prefix` are uv pip flags, not CLI runner flags | `generators.py:1546-1555` |
| 2 | `EphemeralInstallRequest` missing `source_subdir` + `stdin_input` fields | `models.py:1005` |
| 3 | `run_ephemeral_install` not registered as `@mcp.tool` | `server.py` — no registration |
| 4 | No `FrameworkInitSpec` model or `FRAMEWORK_INIT_SPECS` dict with verified CLI commands | Missing |
| 5 | No `init_framework_structure` high-level MCP tool | Missing |
| 6 | `onboard_project(mode=full)` never calls framework init | `server.py:961-995` |
| 7 | `scaffold_doc` hardcodes `docs/` root — wrong for Starlight (`src/content/docs/`) | `validators.py:~479` |
| 8 | `plan_docs` uses same `_FULL_SECTIONS` for all 4 frameworks | `generators.py:~1808` |

## Planned Changes

### F0 — Fix `_build_ephemeral_cmd` for uvx (`generators.py:1546`)
**Current bug**: `["uvx", "--with", package, "--python-prefix", str(tmp_dir), command, *args]`

`--with` and `--python-prefix` are uv's Python-script runner flags. For CLI tools like
`zensical`, the correct call is just `uvx <command> <args>` — uvx creates an isolated env automatically.

**Fix**:
```python
if request.installer == "uvx":
    return ["uvx", request.command, *request.args]
return ["npx", "--yes", request.package, *request.args]
```

### F1 — Extend `EphemeralInstallRequest` (`models.py:1005`)
Add two new optional fields:
```python
source_subdir: str | None = Field(
    default=None,
    description="If the init command creates a named subdirectory (e.g. 'site'), "
                "copy artifacts from tmp_dir/source_subdir rather than tmp_dir.",
)
stdin_input: str | None = Field(
    default=None,
    description="Text to pipe to stdin for non-interactive CLIs (e.g. VitePress accepts "
                "newlines to confirm all prompts).",
)
```

Also update `run_ephemeral_install` in `generators.py`:
- Pass `input=request.stdin_input` to `subprocess.run`
- In `_copy_ephemeral_artifacts`, use `tmp_dir / source_subdir` as the base when `source_subdir` is set

### F2 — New `templates/init_specs.py` with `FrameworkInitSpec` + `FRAMEWORK_INIT_SPECS`
New file encoding the verified CLI commands:
```python
FRAMEWORK_INIT_SPECS: dict[FrameworkName, FrameworkInitSpec] = {
    FrameworkName.ZENSICAL: FrameworkInitSpec(
        framework=FrameworkName.ZENSICAL,
        installer="uvx", package="zensical", command="zensical",
        init_args=["new", "."], source_subdir=None, stdin_input=None,
        copy_artifacts=["zensical.toml", "docs/", ".github/workflows/docs.yml"],
        docs_root=Path("docs"),
    ),
    FrameworkName.DOCUSAURUS: FrameworkInitSpec(
        framework=FrameworkName.DOCUSAURUS,
        installer="npx", package="create-docusaurus@latest", command="create-docusaurus@latest",
        init_args=["site", "classic", "--typescript", "--skip-install"],
        source_subdir="site", stdin_input=None,
        copy_artifacts=["docs/", "docusaurus.config.ts", "sidebars.ts"],
        docs_root=Path("docs"),
    ),
    FrameworkName.VITEPRESS: FrameworkInitSpec(
        framework=FrameworkName.VITEPRESS,
        installer="npx", package="vitepress@latest", command="vitepress@latest",
        init_args=["init", "docs"], source_subdir=None, stdin_input="\n\n\n\n",
        copy_artifacts=["docs/"],
        docs_root=Path("docs"),
    ),
    FrameworkName.STARLIGHT: FrameworkInitSpec(
        framework=FrameworkName.STARLIGHT,
        installer="npx", package="create-astro@latest", command="create-astro@latest",
        init_args=["site", "--", "--template", "starlight", "--no-install", "--no-git", "--yes"],
        source_subdir="site", stdin_input=None,
        copy_artifacts=["src/content/docs/", "astro.config.mjs", "package.json"],
        docs_root=Path("src/content/docs"),
    ),
}
```

`FrameworkInitSpec` model goes in `models.py` (Pydantic, frozen=True, all fields with `Field(description=...)`).

### F3 — Register `run_ephemeral_install` as `@mcp.tool` (`server.py`)
Simple exposure — the function exists, just needs the decorator + import:
```python
@mcp.tool(name="run_ephemeral_install", ...)
def run_ephemeral_install_tool(request: EphemeralInstallRequest) -> EphemeralInstallResponse:
    """Run a uvx or npx command in a temporary directory and copy artifacts back."""
    from .generators import run_ephemeral_install
    return run_ephemeral_install(request)
```

### F4 — New `init_framework_structure` MCP tool (`generators.py` + `server.py`)
High-level tool: framework name → look up spec → call run_ephemeral_install → return structured response.

New models in `models.py`:
- `InitFrameworkStructureRequest(framework, project_root, overwrite)`
- `InitFrameworkStructureResponse(status, framework, docs_root, copied_artifacts, message, cli_command)`

Implementation in `generators.py`:
```python
def init_framework_structure_impl(request: InitFrameworkStructureRequest) -> InitFrameworkStructureResponse:
    spec = FRAMEWORK_INIT_SPECS[request.framework]
    ephemeral = EphemeralInstallRequest(
        package=spec.package, command=spec.command, args=spec.init_args,
        copy_artifacts=spec.copy_artifacts, project_root=request.project_root,
        installer=spec.installer, source_subdir=spec.source_subdir, stdin_input=spec.stdin_input,
    )
    result = run_ephemeral_install(ephemeral)
    return InitFrameworkStructureResponse(
        status=result.status, framework=request.framework,
        docs_root=spec.docs_root, copied_artifacts=result.copied_artifacts or [],
        message=result.message,
        cli_command=" ".join([spec.installer, spec.command, *spec.init_args]),
    )
```

### F5 — Wire into `onboard_project(mode=full)` (`server.py:875`)
Add `scaffold_docs: bool = False` parameter. When `True` and mode is `full` or `init`:
1. After `init_project_impl`, call `detect_docs_context_impl(project_root)` to detect framework
2. Call `init_framework_structure_impl(framework, project_root)`
3. Add `framework_init_result: InitFrameworkStructureResponse | None` to `OnboardProjectResponse`

### F6 — Framework-aware `scaffold_doc` + `plan_docs`
After F2 (init specs) exist:
- **`scaffold_doc`** (`validators.py:~479`): when `framework` param is given, use
  `FRAMEWORK_INIT_SPECS[framework].docs_root` instead of hardcoded `Path("docs")`
- **`plan_docs`** (`generators.py:~1808`): add `_FRAMEWORK_PAGES` dict with paths
  matching each framework's canonical init output:
  - Zensical: `docs/index.md`, `docs/markdown.md`
  - Docusaurus: `docs/intro.md`, `docs/tutorial-basics/`, `docs/tutorial-extras/`
  - VitePress: `docs/index.md`, `docs/guide/`, `docs/reference/`
  - Starlight: `src/content/docs/index.mdx`, `src/content/docs/guides/`, `src/content/docs/reference/`

### F7 — Tests
- `tests/test_ephemeral_init.py`: uvx cmd fix, `FrameworkInitSpec` model validation, `source_subdir` stripping, `stdin_input` forwarding
- `tests/test_framework_scaffold.py`: Starlight scaffold → `src/content/docs/`, Docusaurus → `docs/`
- `tests/test_plan_docs.py`: each framework returns correct page paths
- Run full suite (469 currently passing), fix any regressions

## Dependency Order
```
F0 (fix uvx cmd) ─────────────────────┐
F1 (extend EphemeralInstallRequest) ──┤─→ F3 (expose as tool) ──→ F4 (init_framework tool) ──→ F5 (onboard wiring)
F2 (FrameworkInitSpec + SPECS) ───────┘                ↓
                                               F6 (scaffold_doc / plan_docs) ──→ F7 (tests)
```
