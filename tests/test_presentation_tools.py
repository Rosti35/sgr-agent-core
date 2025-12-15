"""Tests for presentation creation and export tools."""

import os
import tempfile
from unittest.mock import MagicMock

import pytest

from sgr_deep_research.core.agent_definition import ExecutionConfig
from sgr_deep_research.core.models import ResearchContext
from sgr_deep_research.core.models_presentation import PresentationContext, SlideData
from sgr_deep_research.core.tools.create_slide_tool import CreateSlideTool
from sgr_deep_research.core.tools.export_presentation_tool import (
    ExportPresentationTool,
    HTMLSlideParser,
    hex_to_rgb,
)


class TestHexToRgb:
    """Tests for hex_to_rgb function."""

    def test_hex_to_rgb_full(self):
        assert hex_to_rgb("#ffffff") == (255, 255, 255)
        assert hex_to_rgb("#000000") == (0, 0, 0)
        assert hex_to_rgb("#007bff") == (0, 123, 255)

    def test_hex_to_rgb_short(self):
        assert hex_to_rgb("#fff") == (255, 255, 255)
        assert hex_to_rgb("#000") == (0, 0, 0)

    def test_hex_to_rgb_no_hash(self):
        assert hex_to_rgb("ffffff") == (255, 255, 255)
        assert hex_to_rgb("007bff") == (0, 123, 255)


class TestHTMLSlideParser:
    """Tests for HTMLSlideParser class."""

    def test_parse_simple_html(self):
        html = """
        <html>
        <body>
            <h1 class="slide-title">Test Title</h1>
            <div class="slide-content">
                <p>This is a paragraph.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </div>
        </body>
        </html>
        """
        parser = HTMLSlideParser(html)
        title = parser.get_title()
        elements = parser.get_content_elements()

        assert title == "Test Title"
        assert len(elements) >= 2  # paragraph and list

    def test_parse_heading(self):
        html = """
        <div class="slide-content">
            <h2>Sub Heading</h2>
            <p>Some text</p>
        </div>
        """
        parser = HTMLSlideParser(html)
        elements = parser.get_content_elements()

        heading_elements = [e for e in elements if e.get('type') == 'heading']
        assert len(heading_elements) >= 1
        assert heading_elements[0]['text'] == "Sub Heading"

    def test_parse_list(self):
        html = """
        <div class="slide-content">
            <ul>
                <li>First item</li>
                <li>Second item</li>
                <li>Third item</li>
            </ul>
        </div>
        """
        parser = HTMLSlideParser(html)
        elements = parser.get_content_elements()

        list_elements = [e for e in elements if e.get('type') == 'list']
        assert len(list_elements) >= 1
        assert len(list_elements[0]['items']) == 3


class TestCreateSlideTool:
    """Tests for CreateSlideTool."""

    @pytest.fixture
    def mock_context(self):
        context = ResearchContext()
        context.custom_context = PresentationContext()
        return context

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.execution = ExecutionConfig()
        return config

    @pytest.mark.asyncio
    async def test_create_slide_basic(self, mock_context, mock_config):
        tool = CreateSlideTool(
            reasoning="Creating a test slide",
            slide_title="Test Slide",
            layout="content",
            html_content="<p>Test content</p>",
        )

        result = await tool(mock_context, mock_config)

        assert '"status": "success"' in result
        assert '"slide_number": 1' in result
        assert mock_context.custom_context.get_slide_count() == 1

    @pytest.mark.asyncio
    async def test_create_multiple_slides(self, mock_context, mock_config):
        # Create first slide
        tool1 = CreateSlideTool(
            reasoning="First slide",
            slide_title="Slide 1",
            layout="title",
            html_content="<h1>Welcome</h1>",
        )
        await tool1(mock_context, mock_config)

        # Create second slide
        tool2 = CreateSlideTool(
            reasoning="Second slide",
            slide_title="Slide 2",
            layout="bullet_points",
            html_content="<ul><li>Point 1</li><li>Point 2</li></ul>",
        )
        await tool2(mock_context, mock_config)

        assert mock_context.custom_context.get_slide_count() == 2
        assert mock_context.custom_context.slides[0].slide_number == 1
        assert mock_context.custom_context.slides[1].slide_number == 2

    @pytest.mark.asyncio
    async def test_slide_html_generation(self, mock_context, mock_config):
        tool = CreateSlideTool(
            reasoning="Test HTML generation",
            slide_title="HTML Test",
            layout="content",
            html_content="<p>Content</p>",
            background_color="#f0f0f0",
            text_color="#222222",
            accent_color="#ff5500",
        )

        await tool(mock_context, mock_config)

        slide = mock_context.custom_context.slides[0]
        assert "HTML Test" in slide.html_content
        assert "#f0f0f0" in slide.html_content
        assert "#222222" in slide.html_content
        assert "#ff5500" in slide.html_content


class TestExportPresentationTool:
    """Tests for ExportPresentationTool."""

    @pytest.fixture
    def mock_context_with_slides(self):
        context = ResearchContext()
        pres_context = PresentationContext(title="Test Presentation")

        # Add some test slides
        pres_context.add_slide(SlideData(
            slide_number=1,
            title="Introduction",
            html_content="""
            <!DOCTYPE html>
            <html>
            <head><title>Slide 1</title></head>
            <body>
                <div class="slide-container">
                    <div class="slide-header">
                        <h1 class="slide-title">Introduction</h1>
                    </div>
                    <div class="slide-content">
                        <p>Welcome to the presentation</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            layout="title",
        ))

        pres_context.add_slide(SlideData(
            slide_number=2,
            title="Key Points",
            html_content="""
            <!DOCTYPE html>
            <html>
            <head><title>Slide 2</title></head>
            <body>
                <div class="slide-container">
                    <div class="slide-header">
                        <h1 class="slide-title">Key Points</h1>
                    </div>
                    <div class="slide-content">
                        <ul>
                            <li>First point</li>
                            <li>Second point</li>
                            <li>Third point</li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """,
            layout="bullet_points",
        ))

        context.custom_context = pres_context
        return context

    @pytest.fixture
    def mock_config_with_temp_dir(self):
        config = MagicMock()
        config.execution = ExecutionConfig()
        config.execution.reports_dir = tempfile.mkdtemp()
        return config

    @pytest.mark.asyncio
    async def test_export_creates_pptx(self, mock_context_with_slides, mock_config_with_temp_dir):
        tool = ExportPresentationTool(
            reasoning="Exporting test presentation",
            presentation_title="Test Export",
            author="Test Author",
            summary="A test presentation for unit testing",
        )

        result = await tool(mock_context_with_slides, mock_config_with_temp_dir)

        assert '"status": "success"' in result
        assert '"total_slides": 2' in result

        # Check that PPTX file was created
        reports_dir = mock_config_with_temp_dir.execution.reports_dir
        pptx_files = [f for f in os.listdir(reports_dir) if f.endswith('.pptx')]
        assert len(pptx_files) == 1

    @pytest.mark.asyncio
    async def test_export_creates_html_folder(self, mock_context_with_slides, mock_config_with_temp_dir):
        tool = ExportPresentationTool(
            reasoning="Testing HTML export",
            presentation_title="HTML Folder Test",
            summary="Testing HTML folder creation",
        )

        await tool(mock_context_with_slides, mock_config_with_temp_dir)

        # Check that HTML folder was created
        reports_dir = mock_config_with_temp_dir.execution.reports_dir
        html_dirs = [d for d in os.listdir(reports_dir) if d.endswith('_html')]
        assert len(html_dirs) == 1

        # Check HTML files exist
        html_dir_path = os.path.join(reports_dir, html_dirs[0])
        html_files = os.listdir(html_dir_path)
        assert len(html_files) == 2
        assert 'slide_01.html' in html_files
        assert 'slide_02.html' in html_files

    @pytest.mark.asyncio
    async def test_export_no_slides_error(self, mock_config_with_temp_dir):
        context = ResearchContext()
        context.custom_context = PresentationContext()

        tool = ExportPresentationTool(
            reasoning="Testing empty slides",
            presentation_title="Empty Test",
            summary="Should fail",
        )

        result = await tool(context, mock_config_with_temp_dir)
        assert '"status": "error"' in result
        assert "No slides to export" in result

    @pytest.mark.asyncio
    async def test_export_no_context_error(self, mock_config_with_temp_dir):
        context = ResearchContext()
        # No custom_context set

        tool = ExportPresentationTool(
            reasoning="Testing no context",
            presentation_title="No Context Test",
            summary="Should fail",
        )

        result = await tool(context, mock_config_with_temp_dir)
        assert '"status": "error"' in result


class TestPresentationContext:
    """Tests for PresentationContext model."""

    def test_add_slide(self):
        context = PresentationContext()
        slide = SlideData(
            slide_number=1,
            title="Test",
            html_content="<p>Test</p>",
            layout="content",
        )
        context.add_slide(slide)

        assert context.get_slide_count() == 1
        assert context.slides[0].title == "Test"

    def test_get_slides_summary(self):
        context = PresentationContext()
        context.add_slide(SlideData(
            slide_number=1,
            title="Intro",
            html_content="<p>Intro</p>",
            layout="title",
        ))
        context.add_slide(SlideData(
            slide_number=2,
            title="Content",
            html_content="<p>Content</p>",
            layout="bullet_points",
        ))

        summary = context.get_slides_summary()
        assert "Slide 1: Intro" in summary
        assert "Slide 2: Content" in summary

    def test_empty_slides_summary(self):
        context = PresentationContext()
        summary = context.get_slides_summary()
        assert summary == "No slides created yet."


class TestSlideData:
    """Tests for SlideData model."""

    def test_slide_data_creation(self):
        slide = SlideData(
            slide_number=1,
            title="My Slide",
            html_content="<p>Content</p>",
            layout="content",
            speaker_notes="Notes for presenter",
        )

        assert slide.slide_number == 1
        assert slide.title == "My Slide"
        assert slide.layout == "content"
        assert slide.speaker_notes == "Notes for presenter"

    def test_slide_data_defaults(self):
        slide = SlideData(
            slide_number=1,
            title="Test",
            html_content="<p>Test</p>",
        )

        assert slide.layout == "content"
        assert slide.speaker_notes == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




