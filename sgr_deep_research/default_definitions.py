import os

import sgr_deep_research.core.tools as tools
from sgr_deep_research.core.agent_definition import AgentDefinition
from sgr_deep_research.core.agents.presentation_agent import PresentationAgent
from sgr_deep_research.core.agents.sgr_agent import SGRAgent
from sgr_deep_research.core.agents.sgr_auto_tool_calling_agent import SGRAutoToolCallingAgent
from sgr_deep_research.core.agents.sgr_so_tool_calling_agent import SGRSOToolCallingAgent
from sgr_deep_research.core.agents.sgr_tool_calling_agent import SGRToolCallingAgent
from sgr_deep_research.core.agents.tool_calling_agent import ToolCallingAgent

DEFAULT_TOOLKIT = [
    tools.ClarificationTool,
    tools.GeneratePlanTool,
    tools.AdaptPlanTool,
    tools.FinalAnswerTool,
    tools.WebSearchTool,
    tools.ExtractPageContentTool,
    tools.CreateReportTool,
]

PRESENTATION_TOOLKIT = [
    tools.ClarificationTool,
    tools.GeneratePlanTool,
    tools.AdaptPlanTool,
    tools.FinalAnswerTool,
    tools.WebSearchTool,
    tools.ExtractPageContentTool,
    tools.CreateSlideTool,
    tools.ExportPresentationTool,
]


def get_default_agents_definitions() -> dict[str, AgentDefinition]:
    """Get default agent definitions.

    This function creates agent definitions lazily to avoid issues with
    configuration initialization order.

    Returns:
        Dictionary of default agent definitions keyed by agent name
    """
    # Path to presentation system prompt
    presentation_prompt_path = os.path.join(
        os.path.dirname(__file__), "core/prompts/presentation_system_prompt.txt"
    )

    agents = [
        AgentDefinition(
            name="sgr_agent",
            base_class=SGRAgent,
            tools=DEFAULT_TOOLKIT,
        ),
        AgentDefinition(
            name="tool_calling_agent",
            base_class=ToolCallingAgent,
            tools=DEFAULT_TOOLKIT,
        ),
        AgentDefinition(
            name="sgr_tool_calling_agent",
            base_class=SGRToolCallingAgent,
            tools=DEFAULT_TOOLKIT,
        ),
        AgentDefinition(
            name="sgr_auto_tool_calling_agent",
            base_class=SGRAutoToolCallingAgent,
            tools=DEFAULT_TOOLKIT,
        ),
        AgentDefinition(
            name="sgr_so_tool_calling_agent",
            base_class=SGRSOToolCallingAgent,
            tools=DEFAULT_TOOLKIT,
        ),
        AgentDefinition(
            name="presentation_agent",
            base_class=PresentationAgent,
            tools=PRESENTATION_TOOLKIT,
            prompts={
                "system_prompt_file": presentation_prompt_path,
            },
            execution={
                "max_iterations": 25,  # More iterations for creating multiple slides
            },
        ),
    ]
    return {agent.name: agent for agent in agents}
