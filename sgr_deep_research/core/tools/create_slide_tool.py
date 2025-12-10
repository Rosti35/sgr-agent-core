"""Tool for creating individual HTML slides for presentations."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Literal

from pydantic import Field

from sgr_deep_research.core.base_tool import BaseTool
from sgr_deep_research.core.models_presentation import PresentationContext, SlideData

if TYPE_CHECKING:
    from sgr_deep_research.core.agent_definition import AgentConfig
    from sgr_deep_research.core.models import ResearchContext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CreateSlideTool(BaseTool):
    """Create a single presentation slide with HTML content.

    Use this tool to create ONE slide at a time. Each slide should be self-contained
    with proper HTML structure. Call this tool multiple times to create a full presentation.

    IMPORTANT: Create slides in logical order (title slide first, then content slides).
    """

    reasoning: str = Field(description="Why this slide is being created and what it contributes to the presentation")
    slide_title: str = Field(description="Title displayed on the slide")
    layout: Literal["title", "content", "two_column", "bullet_points", "image_focus", "quote", "comparison"] = Field(
        description="Slide layout type determining the structure"
    )
    html_content: str = Field(
        description="Complete HTML content for the slide body. Use semantic HTML with proper structure. "
        "Include inline CSS styles for layout and design. Content should be visually appealing and professional. "
        "Use <div>, <h1>-<h6>, <p>, <ul>, <li>, <strong>, <em> tags as appropriate."
    )
    background_color: str = Field(
        default="#ffffff",
        description="Background color for the slide (hex code or CSS color name)"
    )
    text_color: str = Field(
        default="#333333",
        description="Primary text color for the slide (hex code or CSS color name)"
    )
    accent_color: str = Field(
        default="#007bff",
        description="Accent color for highlights, borders, etc. (hex code or CSS color name)"
    )
    speaker_notes: str = Field(
        default="",
        description="Optional speaker notes for this slide (not visible in presentation)"
    )

    def _generate_full_html_slide(self, slide_number: int) -> str:
        """Generate a complete HTML document for the slide."""
        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slide {slide_number}: {self.slide_title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: {self.background_color};
            color: {self.text_color};
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .slide-container {{
            width: 100%;
            max-width: 1280px;
            aspect-ratio: 16 / 9;
            margin: 0 auto;
            padding: 40px 60px;
            display: flex;
            flex-direction: column;
            background-color: {self.background_color};
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}
        .slide-header {{
            margin-bottom: 30px;
            border-bottom: 3px solid {self.accent_color};
            padding-bottom: 20px;
        }}
        .slide-title {{
            font-size: 2.5em;
            font-weight: 700;
            color: {self.text_color};
            margin: 0;
        }}
        .slide-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            overflow: hidden;
        }}
        .slide-number {{
            position: absolute;
            bottom: 20px;
            right: 30px;
            font-size: 0.9em;
            color: {self.accent_color};
            opacity: 0.7;
        }}
        /* Layout-specific styles */
        .two-column {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
        }}
        .bullet-list {{
            font-size: 1.4em;
            line-height: 1.8;
        }}
        .bullet-list li {{
            margin-bottom: 15px;
            padding-left: 10px;
        }}
        .bullet-list li::marker {{
            color: {self.accent_color};
        }}
        .highlight {{
            background: linear-gradient(120deg, {self.accent_color}20 0%, {self.accent_color}40 100%);
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .quote {{
            font-style: italic;
            font-size: 1.6em;
            border-left: 4px solid {self.accent_color};
            padding-left: 30px;
            margin: 20px 0;
        }}
        .centered {{
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
        }}
        h1 {{ font-size: 2.2em; margin-bottom: 20px; color: {self.text_color}; }}
        h2 {{ font-size: 1.8em; margin-bottom: 15px; color: {self.text_color}; }}
        h3 {{ font-size: 1.4em; margin-bottom: 12px; color: {self.text_color}; }}
        p {{ font-size: 1.2em; line-height: 1.6; margin-bottom: 15px; }}
        ul, ol {{ font-size: 1.2em; line-height: 1.8; margin-left: 30px; }}
        li {{ margin-bottom: 10px; }}
        strong {{ color: {self.accent_color}; }}
        .image-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .image-container img {{
            max-width: 100%;
            max-height: 60vh;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        }}
    </style>
</head>
<body>
    <div class="slide-container">
        <div class="slide-header">
            <h1 class="slide-title">{self.slide_title}</h1>
        </div>
        <div class="slide-content">
            {self.html_content}
        </div>
        <div class="slide-number">{slide_number}</div>
    </div>
</body>
</html>'''
        return html_template

    async def __call__(self, context: ResearchContext, config: AgentConfig, **_) -> str:
        # Initialize presentation context if not exists
        if context.custom_context is None:
            context.custom_context = PresentationContext()
        elif not isinstance(context.custom_context, PresentationContext):
            # Convert if exists but is wrong type
            context.custom_context = PresentationContext()

        pres_context: PresentationContext = context.custom_context
        slide_number = pres_context.get_slide_count() + 1

        # Generate full HTML for the slide
        full_html = self._generate_full_html_slide(slide_number)

        # Create slide data
        slide = SlideData(
            slide_number=slide_number,
            title=self.slide_title,
            html_content=full_html,
            layout=self.layout,
            speaker_notes=self.speaker_notes,
        )

        # Add to presentation context
        pres_context.add_slide(slide)

        result = {
            "status": "success",
            "slide_number": slide_number,
            "title": self.slide_title,
            "layout": self.layout,
            "total_slides": pres_context.get_slide_count(),
            "message": f"Slide {slide_number} '{self.slide_title}' created successfully",
        }

        logger.info(
            f"🎨 SLIDE CREATED:\n"
            f"   📊 Slide #{slide_number}: '{self.slide_title}'\n"
            f"   🎯 Layout: {self.layout}\n"
            f"   🎨 Colors: bg={self.background_color}, text={self.text_color}, accent={self.accent_color}\n"
            f"   📝 Total slides: {pres_context.get_slide_count()}\n"
        )

        return json.dumps(result, indent=2, ensure_ascii=False)

