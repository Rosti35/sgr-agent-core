"""Presentation creation agent based on deep research with HTML slide generation."""

from typing import Type

from openai import AsyncOpenAI

from sgr_deep_research.core.agent_definition import AgentConfig
from sgr_deep_research.core.agents.sgr_agent import SGRAgent
from sgr_deep_research.core.models_presentation import PresentationContext
from sgr_deep_research.core.tools import (
    BaseTool,
    ClarificationTool,
    CreateReportTool,
    FinalAnswerTool,
    NextStepToolsBuilder,
    NextStepToolStub,
    WebSearchTool,
)
from sgr_deep_research.core.tools.create_slide_tool import CreateSlideTool
from sgr_deep_research.core.tools.export_presentation_tool import ExportPresentationTool


class PresentationAgent(SGRAgent):
    """Agent for creating presentations based on deep research.

    This agent researches topics and creates HTML-based presentation slides
    that can be exported to PPTX format.

    Workflow:
    1. Research the topic using web search and content extraction
    2. Plan the presentation structure
    3. Create slides one by one using CreateSlideTool
    4. Export the final presentation using ExportPresentationTool
    """

    name: str = "presentation_agent"

    def __init__(
        self,
        task: str,
        openai_client: AsyncOpenAI,
        agent_config: AgentConfig,
        toolkit: list[Type[BaseTool]],
        def_name: str | None = None,
        **kwargs: dict,
    ):
        super().__init__(
            task=task,
            openai_client=openai_client,
            agent_config=agent_config,
            toolkit=toolkit,
            def_name=def_name,
            **kwargs,
        )
        # Initialize presentation context
        self._context.custom_context = PresentationContext()

    async def _prepare_tools(self) -> Type[NextStepToolStub]:
        """Prepare tool classes with current context limits and presentation state."""
        tools = set(self.toolkit)

        # Get presentation context
        pres_context = self._context.custom_context
        has_slides = isinstance(pres_context, PresentationContext) and pres_context.get_slide_count() > 0

        # If max iterations reached, force completion
        if self._context.iteration >= self.config.execution.max_iterations:
            if has_slides:
                tools = {ExportPresentationTool}
            else:
                tools = {FinalAnswerTool}

        # Remove clarification tool if max clarifications reached
        if self._context.clarifications_used >= self.config.execution.max_clarifications:
            tools -= {ClarificationTool}

        # Remove web search if max searches reached
        if self._context.searches_used >= self.config.search.max_searches:
            tools -= {WebSearchTool}

        # Don't allow CreateReportTool for presentation agent (use ExportPresentationTool instead)
        tools -= {CreateReportTool}

        return NextStepToolsBuilder.build_NextStepTools(list(tools))

    async def _prepare_context(self) -> list[dict]:
        """Prepare conversation context with presentation-specific information."""
        base_context = await super()._prepare_context()

        # Add presentation status to context if slides exist
        pres_context = self._context.custom_context
        if isinstance(pres_context, PresentationContext) and pres_context.slides:
            slides_info = (
                f"\n\n[PRESENTATION STATUS]\n"
                f"Title: {pres_context.title or 'Not set'}\n"
                f"Slides created: {pres_context.get_slide_count()}\n"
                f"Slides summary:\n{pres_context.get_slides_summary()}"
            )
            # Append to the last user message or system message
            if base_context:
                base_context[-1]["content"] += slides_info

        return base_context

