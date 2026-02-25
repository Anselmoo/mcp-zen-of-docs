"""Framework-native CLI init specifications for the ephemeral tmp-and-copy pattern.

Each entry in ``FRAMEWORK_INIT_SPECS`` encodes the exact CLI command verified to work
for scaffolding a framework's canonical folder structure. The specs are used by
``init_framework_structure`` to run the official init tool in a temporary directory
and copy the results back — guaranteeing the output always matches the framework's
current release.

Verification commands run to produce these specs:
  - Zensical:   ``uvx zensical new .``
  - Docusaurus: ``npx create-docusaurus@latest site classic --typescript --skip-install``
  - VitePress:  ``npx vitepress@latest init docs``  (piped newlines for defaults)
  - Starlight:  ``npm create astro@latest site -- --template starlight --no-install --no-git --yes``
"""

from __future__ import annotations

from pathlib import Path

from mcp_zen_of_docs.domain.contracts import FrameworkName
from mcp_zen_of_docs.models import FrameworkInitSpec


__all__ = ["FRAMEWORK_INIT_SPECS"]

FRAMEWORK_INIT_SPECS: dict[FrameworkName, FrameworkInitSpec] = {
    # -------------------------------------------------------------------------
    # Zensical — modern static site generator by the Material for MkDocs team
    # Config: zensical.toml  # noqa: ERA001
    # Creates: zensical.toml, docs/index.md, docs/markdown.md,
    #          .github/workflows/docs.yml
    # -------------------------------------------------------------------------
    FrameworkName.ZENSICAL: FrameworkInitSpec(
        framework=FrameworkName.ZENSICAL,
        installer="uvx",
        package="zensical",
        command="zensical",
        init_args=["new", "."],
        source_subdir=None,
        copy_artifacts=["zensical.toml", "docs/", ".github/workflows/docs.yml"],
        docs_root=Path("docs"),
        stdin_input=None,
    ),
    # -------------------------------------------------------------------------
    # Docusaurus — Meta's React-based docs framework
    # Config: docusaurus.config.ts + sidebars.ts  # noqa: ERA001
    # Creates: site/ subdir with docs/, src/, blog/, static/, package.json, etc.
    # We copy only the docs skeleton, config, and sidebar — not blog/src/static.
    # -------------------------------------------------------------------------
    FrameworkName.DOCUSAURUS: FrameworkInitSpec(
        framework=FrameworkName.DOCUSAURUS,
        installer="npx",
        package="create-docusaurus@latest",
        command="create-docusaurus@latest",
        init_args=["site", "classic", "--typescript", "--skip-install"],
        source_subdir="site",
        copy_artifacts=["docs/", "docusaurus.config.ts", "sidebars.ts"],
        docs_root=Path("docs"),
        stdin_input=None,
    ),
    # -------------------------------------------------------------------------
    # VitePress — Vite-powered static site generator by the Vue team
    # Config: docs/.vitepress/config.mts
    # Creates: docs/.vitepress/config.mts, docs/index.md (via interactive prompts)
    # stdin_input pipes newlines to accept all prompts with defaults.
    # -------------------------------------------------------------------------
    FrameworkName.VITEPRESS: FrameworkInitSpec(
        framework=FrameworkName.VITEPRESS,
        installer="npx",
        package="vitepress@latest",
        command="vitepress@latest",
        init_args=["init", "docs"],
        source_subdir=None,
        copy_artifacts=["docs/"],
        docs_root=Path("docs"),
        stdin_input="\n\n\n\n",
    ),
    # -------------------------------------------------------------------------
    # Starlight — Astro's official documentation theme
    # Config: astro.config.mjs + package.json  # noqa: ERA001
    # Creates: site/ subdir with src/content/docs/guides/, src/content/docs/reference/
    # docs_root is src/content/docs — NOT docs/ like the other frameworks.
    # -------------------------------------------------------------------------
    FrameworkName.STARLIGHT: FrameworkInitSpec(
        framework=FrameworkName.STARLIGHT,
        installer="npx",
        package="create-astro@latest",
        command="create-astro@latest",
        init_args=[
            "site",
            "--",
            "--template",
            "starlight",
            "--no-install",
            "--no-git",
            "--yes",
        ],
        source_subdir="site",
        copy_artifacts=["src/content/docs/", "astro.config.mjs", "package.json"],
        docs_root=Path("src/content/docs"),
        stdin_input=None,
    ),
}
