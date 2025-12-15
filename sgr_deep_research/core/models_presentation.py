"""Models for presentation creation agent."""

from pydantic import BaseModel, Field


class SlideData(BaseModel):
    """Data for a single presentation slide."""

    slide_number: int = Field(description="Slide number in presentation")
    title: str = Field(description="Slide title")
    html_content: str = Field(description="Full HTML content of the slide")
    layout: str = Field(default="content", description="Slide layout type (title, content, two_column, image, etc.)")
    speaker_notes: str = Field(default="", description="Speaker notes for the slide")


class PresentationContext(BaseModel):
    """Context for storing presentation slides during creation."""

    title: str = Field(default="", description="Presentation title")
    theme: str = Field(default="modern", description="Presentation theme")
    slides: list[SlideData] = Field(default_factory=list, description="List of created slides")

    def add_slide(self, slide: SlideData) -> None:
        """Add a slide to the presentation."""
        self.slides.append(slide)

    def get_slide_count(self) -> int:
        """Get the total number of slides."""
        return len(self.slides)

    def get_slides_summary(self) -> str:
        """Get a summary of all slides for LLM context."""
        if not self.slides:
            return "No slides created yet."
        summary = []
        for slide in self.slides:
            summary.append(f"Slide {slide.slide_number}: {slide.title} ({slide.layout})")
        return "\n".join(summary)




