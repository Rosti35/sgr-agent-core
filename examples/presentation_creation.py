"""Example demonstrating the Presentation Agent for creating PowerPoint presentations.

This example shows how to use the PresentationAgent to:
1. Research a topic
2. Create HTML-based slides
3. Export to PPTX format

Prerequisites:
- Set up your config.yaml with API keys (OpenAI and Tavily)
- Install python-pptx: pip install python-pptx
"""

import asyncio

from sgr_deep_research.core.agent_config import GlobalConfig
from sgr_deep_research.core.agent_factory import AgentFactory


async def create_presentation(topic: str):
    """Create a presentation on the given topic.

    Args:
        topic: The subject matter for the presentation
    """
    # Get the presentation agent definition
    config = GlobalConfig()
    agent_def = config.agents.get("presentation_agent")

    if agent_def is None:
        print("Error: presentation_agent not found in configuration")
        print("Available agents:", list(config.agents.keys()))
        return

    # Create the agent with the task
    task = f"""Create a professional presentation about: {topic}

Requirements:
- Create 8-10 slides covering the topic comprehensively
- Start with a title slide
- Include an overview/agenda slide
- Cover key points with supporting details
- End with a summary/conclusion slide
- Use a modern, professional design
"""

    print(f"🎨 Creating presentation about: {topic}")
    print("-" * 50)

    # Create and execute the agent
    agent = await AgentFactory.create(agent_def, task)

    # Stream the execution
    async for event in agent.streaming_generator:
        if hasattr(event, "chunk"):
            print(event.chunk, end="", flush=True)

    # Start execution in background
    asyncio.create_task(agent.execute())

    # Wait for completion by consuming the stream
    async for event in agent.streaming_generator:
        pass

    print("\n" + "-" * 50)
    print(f"✅ Presentation creation complete!")
    print(f"📁 Check the 'reports' folder for your presentation files")


async def main():
    # Example topics to create presentations about
    topics = [
        "The Future of Artificial Intelligence in Healthcare",
        # "Climate Change and Renewable Energy Solutions",
        # "Introduction to Quantum Computing",
    ]

    for topic in topics:
        await create_presentation(topic)


if __name__ == "__main__":
    asyncio.run(main())


