"""
PDF Parser
Extracts design schema and content sections from text-based PDFs.
"""

from typing import List, Tuple, Optional, Dict
from pathlib import Path
from uuid import UUID
import fitz  # PyMuPDF
import pdfplumber

from app.domain.entities.document import Document as DocumentEntity
from app.domain.entities.design_schema import (
    DesignSchema, StyleToken, PageSetup, FontStyle, FontWeight, TextAlignment
)
from app.domain.entities.content_section import ContentSection, SectionType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PDFParser:
    """
    Parser for text-based PDF files.
    
    Uses PyMuPDF (fitz) for structure extraction and pdfplumber for text extraction.
    
    Extracts:
    - Page layout and dimensions
    - Text blocks with formatting
    - Content hierarchy
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._font_stats: Dict[str, int] = {}
        self._size_stats: Dict[float, int] = {}
    
    def parse(self, document_id: UUID) -> Tuple[DesignSchema, List[ContentSection]]:
        """
        Parse the PDF file and extract design schema and content sections.
        
        Returns:
            Tuple of (DesignSchema, List[ContentSection])
        """
        logger.info(f"Parsing PDF: {self.file_path}")
        
        # First pass: collect statistics for design inference
        self._analyze_document()
        
        # Extract design schema
        design_schema = self._extract_design_schema(document_id)
        
        # Extract content sections
        sections = self._extract_content_sections(document_id)
        
        logger.info(f"Extracted {len(sections)} sections from PDF")
        
        return design_schema, sections
    
    def _analyze_document(self) -> None:
        """Analyze document to collect font and size statistics."""
        doc = fitz.open(self.file_path)
        
        for page in doc:
            blocks = page.get_text("dict", flags=11)["blocks"]
            
            for block in blocks:
                if block.get("type") != 0:  # Not text
                    continue
                
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font = span.get("font", "unknown")
                        size = round(span.get("size", 12), 1)
                        
                        self._font_stats[font] = self._font_stats.get(font, 0) + 1
                        self._size_stats[size] = self._size_stats.get(size, 0) + 1
        
        doc.close()
    
    def _extract_design_schema(self, document_id: UUID) -> DesignSchema:
        """Extract design schema from PDF."""
        doc = fitz.open(self.file_path)
        page = doc[0]
        
        # Extract page setup
        page_rect = page.rect
        page_setup = PageSetup(
            width=page_rect.width / 72,  # Convert points to inches
            height=page_rect.height / 72,
            orientation="portrait" if page_rect.width < page_rect.height else "landscape",
            margin_top=1.0,  # Default margins (hard to detect in PDF)
            margin_bottom=1.0,
            margin_left=1.0,
            margin_right=1.0,
        )
        
        doc.close()
        
        # Infer style tokens from statistics
        style_tokens = self._infer_style_tokens()
        
        # Get dominant font
        default_font = max(self._font_stats, key=self._font_stats.get) if self._font_stats else "Arial"
        default_size = max(self._size_stats, key=self._size_stats.get) if self._size_stats else 12.0
        
        schema = DesignSchema(
            document_id=document_id,
            page_setup=page_setup,
            style_tokens=style_tokens,
            default_font_family=self._normalize_font_name(default_font),
            default_font_size=default_size,
            heading_hierarchy=["H1", "H2", "H3"],
            extracted_from="pdf",
            confidence_score=0.9,  # PDF extraction has some uncertainty
        )
        
        schema.lock()
        return schema
    
    def _infer_style_tokens(self) -> Dict[str, StyleToken]:
        """Infer style tokens from font statistics."""
        tokens = {}
        
        if not self._size_stats:
            return DesignSchema.create_default_tokens()
        
        # Sort sizes to identify hierarchy
        sizes = sorted(self._size_stats.keys(), reverse=True)
        
        # Get dominant font
        default_font = max(self._font_stats, key=self._font_stats.get) if self._font_stats else "Arial"
        default_font = self._normalize_font_name(default_font)
        
        # Create tokens based on size distribution
        if len(sizes) >= 1:
            tokens["Title"] = StyleToken(
                name="Title",
                font=FontStyle(family=default_font, size=sizes[0], weight=FontWeight.BOLD),
                alignment=TextAlignment.CENTER,
                space_after=24
            )
        
        if len(sizes) >= 2:
            tokens["H1"] = StyleToken(
                name="H1",
                font=FontStyle(family=default_font, size=sizes[1] if len(sizes) > 1 else sizes[0] * 0.8, weight=FontWeight.BOLD),
                space_before=18,
                space_after=12
            )
        
        if len(sizes) >= 3:
            tokens["H2"] = StyleToken(
                name="H2",
                font=FontStyle(family=default_font, size=sizes[2] if len(sizes) > 2 else sizes[0] * 0.7, weight=FontWeight.BOLD),
                space_before=14,
                space_after=8
            )
        
        # Body is the most common size
        body_size = max(self._size_stats, key=self._size_stats.get) if self._size_stats else 12.0
        tokens["Body"] = StyleToken(
            name="Body",
            font=FontStyle(family=default_font, size=body_size, weight=FontWeight.NORMAL),
            line_spacing=1.15,
            space_after=8
        )
        
        return tokens
    
    def _extract_content_sections(self, document_id: UUID) -> List[ContentSection]:
        """Extract content sections from PDF."""
        sections = []
        order_index = 0
        
        doc = fitz.open(self.file_path)
        
        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict", flags=11)["blocks"]
            
            for block in blocks:
                if block.get("type") != 0:  # Not text
                    continue
                
                # Combine lines into block text
                block_text = ""
                block_size = 12.0
                is_bold = False
                
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                        block_size = max(block_size, span.get("size", 12))
                        if "bold" in span.get("font", "").lower():
                            is_bold = True
                    block_text += line_text + "\n"
                
                block_text = block_text.strip()
                if not block_text:
                    continue
                
                # Determine section type from font size
                section_type, style_token = self._infer_section_type(block_size, is_bold)
                
                section = ContentSection(
                    document_id=document_id,
                    order_index=order_index,
                    page_number=page_num + 1,
                    section_type=section_type,
                    content=block_text,
                    original_content=block_text,
                    style_token=style_token,
                    editable=True,
                    ai_enabled=True,
                    bounding_box={
                        "x": block.get("bbox", [0])[0],
                        "y": block.get("bbox", [0, 0])[1],
                        "width": block.get("bbox", [0, 0, 0])[2] - block.get("bbox", [0])[0],
                        "height": block.get("bbox", [0, 0, 0, 0])[3] - block.get("bbox", [0, 0])[1],
                    }
                )
                
                sections.append(section)
                order_index += 1
        
        doc.close()
        
        # Also extract tables using pdfplumber
        sections.extend(self._extract_tables(document_id, order_index))
        
        return sections
    
    def _infer_section_type(self, font_size: float, is_bold: bool) -> Tuple[SectionType, str]:
        """Infer section type from font characteristics."""
        sizes = sorted(self._size_stats.keys(), reverse=True) if self._size_stats else [20, 16, 14, 12]
        
        if font_size >= sizes[0] * 0.9:
            return SectionType.TITLE, "Title"
        elif font_size >= sizes[1] * 0.9 if len(sizes) > 1 else font_size >= 18:
            return SectionType.HEADING_1, "H1"
        elif font_size >= sizes[2] * 0.9 if len(sizes) > 2 else font_size >= 14:
            return SectionType.HEADING_2, "H2"
        elif is_bold and font_size >= 12:
            return SectionType.HEADING_3, "H3"
        else:
            return SectionType.PARAGRAPH, "Body"
    
    def _extract_tables(self, document_id: UUID, start_index: int) -> List[ContentSection]:
        """Extract tables from PDF using pdfplumber."""
        sections = []
        order_index = start_index
        
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    
                    for table in tables:
                        if not table:
                            continue
                        
                        # Clean table data
                        table_data = []
                        headers = []
                        
                        for row_idx, row in enumerate(table):
                            cleaned_row = [cell.strip() if cell else "" for cell in row]
                            if row_idx == 0:
                                headers = cleaned_row
                            table_data.append(cleaned_row)
                        
                        section = ContentSection(
                            document_id=document_id,
                            order_index=order_index,
                            page_number=page_num + 1,
                            section_type=SectionType.TABLE,
                            content="",
                            original_content="",
                            style_token="Body",
                            table_data=table_data,
                            table_headers=headers,
                            editable=True,
                            ai_enabled=False,
                        )
                        
                        sections.append(section)
                        order_index += 1
                        
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
        
        return sections
    
    @staticmethod
    def _normalize_font_name(font: str) -> str:
        """Normalize font names to standard families."""
        font_lower = font.lower()
        
        if "arial" in font_lower:
            return "Arial"
        elif "times" in font_lower:
            return "Times New Roman"
        elif "helvetica" in font_lower:
            return "Helvetica"
        elif "courier" in font_lower:
            return "Courier New"
        elif "calibri" in font_lower:
            return "Calibri"
        elif "cambria" in font_lower:
            return "Cambria"
        elif "georgia" in font_lower:
            return "Georgia"
        
        # Return original if no match
        return font.split("-")[0].split("+")[0]  # Remove style suffixes
    
    def get_page_count(self) -> int:
        """Get the number of pages in the PDF."""
        doc = fitz.open(self.file_path)
        count = len(doc)
        doc.close()
        return count

