"""mcp-zen-of-docs package."""

from __future__ import annotations

from .asset_conversion import convert_svg_file
from .asset_conversion import convert_visual_asset
from .asset_conversion import generate_svg_png_conversion_script
from .asset_conversion import generate_svg_png_conversion_scripts
from .asset_conversion import select_conversion_backend
from .models import AnswerSlotContract
from .models import AnswerSlotType
from .models import AuthoringPrimitive
from .models import CapabilityMatrixItem
from .models import CapabilityMatrixV2Response
from .models import CapabilityStrategy
from .models import CapabilitySupportDetail
from .models import DetectFrameworkRequest
from .models import DetectFrameworkResponse
from .models import DeterministicTurnPlan
from .models import DeterministicTurnStep
from .models import FrameworkDetectionResult
from .models import FrameworkName
from .models import GenerateCliDocsRequest
from .models import GenerateCliDocsResponse
from .models import GenerateMcpToolsDocsRequest
from .models import GenerateMcpToolsDocsResponse
from .models import InteractionQuestionType
from .models import MaterialSnippetRequest
from .models import MaterialSnippetResponse
from .models import MigrationModeContract
from .models import MigrationQualityEnhancementToggles
from .models import ModuleIntentProfile
from .models import ModuleOutputContract
from .models import OnboardingGuidanceContract
from .models import OnboardingSkeletonRequest
from .models import OnboardingSkeletonResponse
from .models import OrchestratorResultContract
from .models import PrimitiveCatalogResponse
from .models import PrimitiveSupportLookupRequest
from .models import PrimitiveSupportLookupResponse
from .models import QualityIssue
from .models import QualityScore
from .models import QuestionItemContract
from .models import RenderPrimitiveSnippetRequest
from .models import RenderPrimitiveSnippetResponse
from .models import RuntimeOnboardingMatrixResponse
from .models import RuntimeTrack
from .models import ScoreDocsQualityRequest
from .models import ScoreDocsQualityResponse
from .models import StoryExplorationStage
from .models import StoryFeedbackLoopState
from .models import StoryGapSeverity
from .models import StoryGenerationRequest
from .models import StoryGenerationResponse
from .models import StoryMigrationMode
from .models import StoryNextQuestionContract
from .models import StorySessionStateContract
from .models import StorySessionStatus
from .models import StoryTurnTransition
from .models import SupportLevel
from .models import SvgPromptRequest
from .models import SvgPromptResponse
from .models import SvgPromptToolkitResponse
from .models import TranslatePrimitiveSyntaxRequest
from .models import TranslatePrimitiveSyntaxResponse
from .models import TurnPlanAction
from .models import VisualAssetBackend
from .models import VisualAssetBackendMetadata
from .models import VisualAssetConversionRequest
from .models import VisualAssetConversionResponse
from .models import VisualAssetFormat
from .models import VisualAssetKind
from .models import VisualAssetSpec
from .server import main
from .server import mcp
from .visual_assets import build_visual_asset_spec
from .visual_assets import generate_svg_prompt
from .visual_assets import generate_svg_prompt_toolkit


__version__ = "0.2.0"
__all__ = [
    "AnswerSlotContract",
    "AnswerSlotType",
    "AuthoringPrimitive",
    "CapabilityMatrixItem",
    "CapabilityMatrixV2Response",
    "CapabilityStrategy",
    "CapabilitySupportDetail",
    "DetectFrameworkRequest",
    "DetectFrameworkResponse",
    "DeterministicTurnPlan",
    "DeterministicTurnStep",
    "FrameworkDetectionResult",
    "FrameworkName",
    "GenerateCliDocsRequest",
    "GenerateCliDocsResponse",
    "GenerateMcpToolsDocsRequest",
    "GenerateMcpToolsDocsResponse",
    "InteractionQuestionType",
    "MaterialSnippetRequest",
    "MaterialSnippetResponse",
    "MigrationModeContract",
    "MigrationQualityEnhancementToggles",
    "ModuleIntentProfile",
    "ModuleOutputContract",
    "OnboardingGuidanceContract",
    "OnboardingSkeletonRequest",
    "OnboardingSkeletonResponse",
    "OrchestratorResultContract",
    "PrimitiveCatalogResponse",
    "PrimitiveSupportLookupRequest",
    "PrimitiveSupportLookupResponse",
    "QualityIssue",
    "QualityScore",
    "QuestionItemContract",
    "RenderPrimitiveSnippetRequest",
    "RenderPrimitiveSnippetResponse",
    "RuntimeOnboardingMatrixResponse",
    "RuntimeTrack",
    "ScoreDocsQualityRequest",
    "ScoreDocsQualityResponse",
    "StoryExplorationStage",
    "StoryFeedbackLoopState",
    "StoryGapSeverity",
    "StoryGenerationRequest",
    "StoryGenerationResponse",
    "StoryMigrationMode",
    "StoryNextQuestionContract",
    "StorySessionStateContract",
    "StorySessionStatus",
    "StoryTurnTransition",
    "SupportLevel",
    "SvgPromptRequest",
    "SvgPromptResponse",
    "SvgPromptToolkitResponse",
    "TranslatePrimitiveSyntaxRequest",
    "TranslatePrimitiveSyntaxResponse",
    "TurnPlanAction",
    "VisualAssetBackend",
    "VisualAssetBackendMetadata",
    "VisualAssetConversionRequest",
    "VisualAssetConversionResponse",
    "VisualAssetFormat",
    "VisualAssetKind",
    "VisualAssetSpec",
    "build_visual_asset_spec",
    "convert_svg_file",
    "convert_visual_asset",
    "generate_svg_png_conversion_script",
    "generate_svg_png_conversion_scripts",
    "generate_svg_prompt",
    "generate_svg_prompt_toolkit",
    "main",
    "mcp",
    "select_conversion_backend",
]
