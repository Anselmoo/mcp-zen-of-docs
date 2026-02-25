"""Template primitives for deterministic docs and workflow rendering."""

from __future__ import annotations

from .boilerplate import DOC_BOILERPLATE_BRICK_REGISTRY
from .boilerplate import DOC_BOILERPLATE_REGISTRY
from .boilerplate import BoilerplateBrick
from .boilerplate import BoilerplateBrickId
from .boilerplate import BoilerplateTemplate
from .boilerplate import BoilerplateTemplateId
from .boilerplate import iter_doc_boilerplate_templates
from .boilerplate import render_deployment_environments_brick
from .copilot_assets import COPILOT_ASSET_TEMPLATE_REGISTRY
from .copilot_assets import CopilotAssetTemplate
from .copilot_assets import CopilotAssetTemplateId
from .copilot_assets import render_copilot_asset_content
from .docs_deploy_workflows import render_docs_deploy_workflow
from .init_specs import FRAMEWORK_INIT_SPECS


__all__ = [
    "COPILOT_ASSET_TEMPLATE_REGISTRY",
    "DOC_BOILERPLATE_BRICK_REGISTRY",
    "DOC_BOILERPLATE_REGISTRY",
    "FRAMEWORK_INIT_SPECS",
    "BoilerplateBrick",
    "BoilerplateBrickId",
    "BoilerplateTemplate",
    "BoilerplateTemplateId",
    "CopilotAssetTemplate",
    "CopilotAssetTemplateId",
    "iter_doc_boilerplate_templates",
    "render_copilot_asset_content",
    "render_deployment_environments_brick",
    "render_docs_deploy_workflow",
]
