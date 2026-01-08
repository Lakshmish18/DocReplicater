"""
PDF Generator
Generates PDF documents from design schema and content sections.
"""

from typing import List, Optional
from pathlib import Path
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image as RLImage, ListFlowable, ListItem
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.domain.entities.design_schema import DesignSchema, StyleToken, FontWeight, TextAlignment
from app.domain.entities.content_section import ContentSection, SectionType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PDFGenerator:
    """
    Generates PDF documents with preserved formatting.
    
    Uses ReportLab for PDF generation.
    """
    
    ALIGNMENT_MAP = {
        TextAlignment.LEFT: TA_LEFT,
        TextAlignment.CENTER: TA_CENTER,
        TextAlignment.RIGHT: TA_RIGHT,
        TextAlignment.JUSTIFY: TA_JUSTIFY,
    }
    
    def __init__(self, design_schema: DesignSchema):
        self.schema = design_schema
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self) -> None:
        """Set up PDF styles from design schema."""
        for token_name, token in self.schema.style_tokens.items():
            try:
                self._create_style(token)
            except Exception as e:
                logger.warning(f"Failed to create style {token_name}: {e}")
    
    def _create_style(self, token: StyleToken) -> None:
        """Create a paragraph style from token."""
        # Determine alignment
        alignment = self.ALIGNMENT_MAP.get(token.alignment, TA_LEFT)
        
        # Determine font name
        font_name = self._get_font_name(token.font.family, token.font.weight)
        
        style = ParagraphStyle(
            name=token.name,
            fontName=font_name,
            fontSize=token.font.size,
            leading=token.font.size * token.line_spacing,
            alignment=alignment,
            spaceBefore=token.space_before,
            spaceAfter=token.space_after,
            firstLineIndent=token.first_line_indent * inch,
            leftIndent=token.left_indent * inch,
            rightIndent=token.right_indent * inch,
            textColor=self._hex_to_color(token.font.color),
        )
        
        self.styles.add(style)
    
    def _get_font_name(self, family: str, weight: FontWeight) -> str:
        """Get appropriate font name for family and weight."""
        # Map common font families to ReportLab built-in fonts
        family_map = {
            "arial": "Helvetica",
            "helvetica": "Helvetica",
            "times new roman": "Times-Roman",
            "times": "Times-Roman",
            "courier": "Courier",
            "courier new": "Courier",
        }
        
        base_font = family_map.get(family.lower(), "Helvetica")
        
        # Add weight suffix
        if weight in [FontWeight.BOLD, FontWeight.SEMIBOLD, FontWeight.EXTRABOLD]:
            if base_font == "Helvetica":
                return "Helvetica-Bold"
            elif base_font == "Times-Roman":
                return "Times-Bold"
            elif base_font == "Courier":
                return "Courier-Bold"
        
        return base_font
    
    def generate(self, sections: List[ContentSection], output_path: str) -> str:
        """
        Generate PDF from content sections.
        
        Args:
            sections: List of content sections in order
            output_path: Path to save the document
            
        Returns:
            Path to generated document
        """
        logger.info(f"Generating PDF with {len(sections)} sections")
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate page size
        page_setup = self.schema.page_setup
        page_width = page_setup.width * inch
        page_height = page_setup.height * inch
        
        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=(page_width, page_height),
            topMargin=page_setup.margin_top * inch,
            bottomMargin=page_setup.margin_bottom * inch,
            leftMargin=page_setup.margin_left * inch,
            rightMargin=page_setup.margin_right * inch,
        )
        
        # Build content
        story = []
        for section in sections:
            elements = self._create_elements(section)
            story.extend(elements)
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF saved to {output_path}")
        
        return output_path
    
    def _create_elements(self, section: ContentSection) -> List:
        """Create flowable elements for a section."""
        elements = []
        
        if section.section_type == SectionType.TABLE:
            elements.extend(self._create_table(section))
        elif section.section_type in [SectionType.BULLET_LIST, SectionType.NUMBERED_LIST]:
            elements.extend(self._create_list(section))
        elif section.section_type == SectionType.PAGE_BREAK:
            elements.append(PageBreak())
        elif section.section_type == SectionType.IMAGE:
            elements.extend(self._create_image(section))
        else:
            elements.extend(self._create_paragraph(section))
        
        return elements
    
    def _create_paragraph(self, section: ContentSection) -> List:
        """Create paragraph elements."""
        elements = []
        
        # Get style
        style_name = section.style_token
        try:
            style = self.styles[style_name]
        except KeyError:
            # Map section type to default styles
            style_mapping = {
                SectionType.TITLE: "Title",
                SectionType.HEADING_1: "Heading1",
                SectionType.HEADING_2: "Heading2",
                SectionType.HEADING_3: "Heading3",
                SectionType.PARAGRAPH: "Normal",
            }
            style_name = style_mapping.get(section.section_type, "Normal")
            try:
                style = self.styles[style_name]
            except KeyError:
                style = self.styles["Normal"]
        
        # Create paragraph
        text = self._escape_html(section.content)
        para = Paragraph(text, style)
        elements.append(para)
        
        return elements
    
    def _create_table(self, section: ContentSection) -> List:
        """Create table elements."""
        elements = []
        
        if not section.table_data:
            return elements
        
        # Create table
        table = Table(section.table_data)
        
        # Style the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        table.setStyle(style)
        elements.append(table)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_list(self, section: ContentSection) -> List:
        """Create list elements."""
        elements = []
        
        is_numbered = section.section_type == SectionType.NUMBERED_LIST
        bullet_type = "1" if is_numbered else "bullet"
        
        items = []
        for item in section.list_items:
            text = self._escape_html(item)
            items.append(ListItem(Paragraph(text, self.styles["Normal"])))
        
        list_flow = ListFlowable(
            items,
            bulletType=bullet_type,
            start=1 if is_numbered else None,
        )
        
        elements.append(list_flow)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_image(self, section: ContentSection) -> List:
        """Create image elements."""
        elements = []
        
        if not section.image_path:
            return elements
        
        try:
            img = RLImage(section.image_path, width=5*inch)
            elements.append(img)
            
            if section.image_alt_text:
                caption = Paragraph(
                    self._escape_html(section.image_alt_text),
                    self.styles.get("Caption", self.styles["Normal"])
                )
                elements.append(caption)
        except Exception as e:
            logger.warning(f"Failed to add image: {e}")
            text = f"[Image: {section.image_alt_text or 'Image'}]"
            elements.append(Paragraph(text, self.styles["Normal"]))
        
        elements.append(Spacer(1, 12))
        return elements
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters for ReportLab."""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
    
    @staticmethod
    def _hex_to_color(hex_color: str) -> colors.Color:
        """Convert hex color to ReportLab color."""
        if not hex_color:
            return colors.black
        hex_color = hex_color.lstrip('#')
        try:
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            return colors.Color(r, g, b)
        except (ValueError, IndexError):
            return colors.black

