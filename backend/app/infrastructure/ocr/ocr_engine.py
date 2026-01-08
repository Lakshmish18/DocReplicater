"""
OCR Engine
Tesseract-based OCR with preprocessing and layout preservation.
"""

import time
from typing import List, Optional, Tuple, Dict
from pathlib import Path
from uuid import UUID
import numpy as np
import cv2
from PIL import Image
import fitz  # PyMuPDF for PDF to image conversion
import pytesseract
from pytesseract import Output

from app.config import settings
from app.domain.entities.ocr_metadata import OCRMetadata, OCRBlock, BoundingBox
from app.domain.entities.content_section import ContentSection, SectionType
from app.domain.entities.design_schema import DesignSchema, StyleToken, PageSetup, FontStyle, FontWeight
from app.infrastructure.ocr.image_preprocessor import ImagePreprocessor
from app.infrastructure.ocr.layout_analyzer import LayoutAnalyzer
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OCREngine:
    """
    OCR Engine using Tesseract.
    
    Features:
    - PDF page to image conversion
    - Image preprocessing pipeline
    - Text extraction with bounding boxes
    - Confidence scoring
    - Layout-aware processing
    """
    
    def __init__(self, language: str = None, dpi: int = None):
        self.language = language or settings.OCR_LANGUAGE
        self.dpi = dpi or settings.OCR_DPI
        self.preprocessor = ImagePreprocessor(target_dpi=self.dpi)
        self.layout_analyzer = LayoutAnalyzer()
        
        # Configure Tesseract path if specified
        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
    
    def process_document(
        self, 
        file_path: str, 
        document_id: UUID,
        is_pdf: bool = True
    ) -> Tuple[OCRMetadata, DesignSchema, List[ContentSection]]:
        """
        Process a scanned document through the complete OCR pipeline.
        
        Returns:
            Tuple of (OCRMetadata, DesignSchema, List[ContentSection])
        """
        start_time = time.time()
        logger.info(f"Starting OCR processing: {file_path}")
        
        # Initialize metadata
        ocr_metadata = OCRMetadata(
            document_id=document_id,
            engine_name="tesseract",
            engine_version=pytesseract.get_tesseract_version().vstring,
            language=self.language,
            dpi=self.dpi,
        )
        
        # Convert to images and process
        if is_pdf:
            images, page_dimensions = self._pdf_to_images(file_path)
            ocr_metadata.page_dimensions = page_dimensions
        else:
            images = [self._load_image(file_path)]
            ocr_metadata.page_dimensions = {1: {"width": images[0].shape[1], "height": images[0].shape[0]}}
        
        ocr_metadata.total_pages = len(images)
        
        # Process each page
        all_blocks = []
        for page_num, image in enumerate(images, 1):
            logger.info(f"Processing page {page_num}/{len(images)}")
            
            # Preprocess image
            processed = self.preprocessor.preprocess(image)
            
            # Extract text with OCR
            blocks = self._extract_text_blocks(processed, page_num)
            all_blocks.extend(blocks)
            
            for block in blocks:
                ocr_metadata.add_block(block)
        
        # Store preprocessing operations
        ocr_metadata.preprocessing_applied = self.preprocessor.get_applied_operations()
        
        # Analyze layout to reconstruct structure
        analyzed_blocks = self.layout_analyzer.analyze(all_blocks)
        
        # Infer margins and columns
        ocr_metadata.detected_margins = self.layout_analyzer.detect_margins(all_blocks)
        ocr_metadata.detected_columns = self.layout_analyzer.detect_columns(all_blocks)
        
        # Create design schema from OCR results
        design_schema = self._create_design_schema(document_id, ocr_metadata, analyzed_blocks)
        
        # Create content sections from blocks
        sections = self._create_content_sections(document_id, analyzed_blocks)
        
        # Calculate processing time
        ocr_metadata.processing_time_seconds = time.time() - start_time
        
        logger.info(
            f"OCR complete: {len(sections)} sections, "
            f"avg confidence: {ocr_metadata.average_confidence:.1f}%, "
            f"time: {ocr_metadata.processing_time_seconds:.2f}s"
        )
        
        return ocr_metadata, design_schema, sections
    
    def _pdf_to_images(self, pdf_path: str) -> Tuple[List[np.ndarray], Dict[int, Dict]]:
        """Convert PDF pages to images."""
        images = []
        page_dimensions = {}
        
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Render at high DPI
            zoom = self.dpi / 72  # 72 is default PDF DPI
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert to numpy array
            img = np.frombuffer(pix.samples, dtype=np.uint8)
            img = img.reshape(pix.height, pix.width, pix.n)
            
            # Convert to BGR for OpenCV
            if pix.n == 4:  # RGBA
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:  # RGB
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            images.append(img)
            page_dimensions[page_num + 1] = {
                "width": page.rect.width,
                "height": page.rect.height,
            }
        
        doc.close()
        return images, page_dimensions
    
    def _load_image(self, image_path: str) -> np.ndarray:
        """Load an image file."""
        return cv2.imread(image_path)
    
    def _extract_text_blocks(self, image: np.ndarray, page_number: int) -> List[OCRBlock]:
        """
        Extract text blocks with position and confidence data.
        """
        blocks = []
        
        # Convert to PIL for Tesseract
        if len(image.shape) == 2:
            pil_image = Image.fromarray(image)
        else:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Get detailed OCR data
        ocr_data = pytesseract.image_to_data(
            pil_image,
            lang=self.language,
            output_type=Output.DICT,
            config='--psm 6'  # Assume uniform block of text
        )
        
        # Group words into blocks
        current_block = None
        current_block_num = -1
        
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            conf = float(ocr_data['conf'][i])
            block_num = ocr_data['block_num'][i]
            
            if not text or conf < 0:
                continue
            
            # New block
            if block_num != current_block_num:
                if current_block and current_block.text.strip():
                    blocks.append(current_block)
                
                current_block = OCRBlock(
                    text="",
                    page_number=page_number,
                    confidence=0,
                    bounding_box=BoundingBox(
                        x=ocr_data['left'][i],
                        y=ocr_data['top'][i],
                        width=ocr_data['width'][i],
                        height=ocr_data['height'][i],
                    ),
                )
                current_block_num = block_num
            
            # Add word to current block
            if current_block:
                if current_block.text:
                    current_block.text += " "
                current_block.text += text
                
                # Update confidence (running average)
                if conf >= 0:
                    if current_block.confidence == 0:
                        current_block.confidence = conf
                    else:
                        current_block.confidence = (current_block.confidence + conf) / 2
                
                # Expand bounding box
                new_bbox = BoundingBox(
                    x=ocr_data['left'][i],
                    y=ocr_data['top'][i],
                    width=ocr_data['width'][i],
                    height=ocr_data['height'][i],
                )
                current_block.bounding_box = current_block.bounding_box.merge(new_bbox)
        
        # Add last block
        if current_block and current_block.text.strip():
            blocks.append(current_block)
        
        # Estimate font sizes and styles
        self._estimate_font_properties(blocks, image.shape[:2])
        
        logger.info(f"Extracted {len(blocks)} text blocks from page {page_number}")
        return blocks
    
    def _estimate_font_properties(self, blocks: List[OCRBlock], image_size: Tuple[int, int]) -> None:
        """
        Estimate font properties from block characteristics.
        """
        if not blocks:
            return
        
        # Calculate average block height to estimate base font size
        heights = [b.bounding_box.height for b in blocks if b.bounding_box]
        if not heights:
            return
        
        avg_height = np.median(heights)
        
        for block in blocks:
            if not block.bounding_box:
                continue
            
            # Estimate font size from height (rough approximation)
            # Assuming typical line height is about 1.2x font size
            block.font_size = round(block.bounding_box.height / 1.2 * 72 / self.dpi, 1)
            
            # Detect if likely bold (taller than average for same font size)
            if block.bounding_box.height > avg_height * 1.3:
                block.is_bold = True
            
            # Detect alignment based on x position
            page_width = image_size[1]
            x_center = block.bounding_box.x + block.bounding_box.width / 2
            
            if x_center < page_width * 0.35:
                block.alignment = "left"
            elif x_center > page_width * 0.65:
                block.alignment = "right"
            else:
                block.alignment = "center"
    
    def _create_design_schema(
        self, 
        document_id: UUID, 
        ocr_metadata: OCRMetadata,
        blocks: List[OCRBlock]
    ) -> DesignSchema:
        """
        Create a design schema from OCR results.
        """
        # Estimate page setup from OCR metadata
        first_page = ocr_metadata.page_dimensions.get(1, {})
        page_setup = PageSetup(
            width=first_page.get("width", 8.5 * 72) / 72,
            height=first_page.get("height", 11 * 72) / 72,
            margin_top=ocr_metadata.detected_margins.get("top", 1.0),
            margin_bottom=ocr_metadata.detected_margins.get("bottom", 1.0),
            margin_left=ocr_metadata.detected_margins.get("left", 1.0),
            margin_right=ocr_metadata.detected_margins.get("right", 1.0),
            columns=ocr_metadata.detected_columns,
        )
        
        # Create style tokens from block analysis
        style_tokens = self._infer_style_tokens_from_blocks(blocks)
        
        schema = DesignSchema(
            document_id=document_id,
            page_setup=page_setup,
            style_tokens=style_tokens,
            default_font_family="Arial",  # Unknown from OCR
            default_font_size=12.0,
            heading_hierarchy=["H1", "H2", "H3"],
            extracted_from="ocr",
            confidence_score=ocr_metadata.average_confidence / 100,
        )
        
        schema.lock()
        return schema
    
    def _infer_style_tokens_from_blocks(self, blocks: List[OCRBlock]) -> Dict[str, StyleToken]:
        """Infer style tokens from OCR block analysis."""
        tokens = {}
        
        # Collect font sizes
        sizes = [b.font_size for b in blocks if b.font_size]
        if not sizes:
            return DesignSchema.create_default_tokens()
        
        sizes = sorted(set(sizes), reverse=True)
        
        # Create tokens based on size distribution
        if len(sizes) >= 1:
            tokens["Title"] = StyleToken(
                name="Title",
                font=FontStyle(family="Arial", size=sizes[0], weight=FontWeight.BOLD),
                space_after=24
            )
        
        if len(sizes) >= 2:
            tokens["H1"] = StyleToken(
                name="H1",
                font=FontStyle(family="Arial", size=sizes[1] if len(sizes) > 1 else sizes[0] * 0.8, weight=FontWeight.BOLD),
                space_before=18,
                space_after=12
            )
        
        if len(sizes) >= 3:
            tokens["H2"] = StyleToken(
                name="H2",
                font=FontStyle(family="Arial", size=sizes[2] if len(sizes) > 2 else sizes[0] * 0.7, weight=FontWeight.BOLD),
                space_before=14,
                space_after=8
            )
        
        # Body is most common size
        from collections import Counter
        size_counts = Counter([b.font_size for b in blocks if b.font_size])
        body_size = size_counts.most_common(1)[0][0] if size_counts else 12.0
        
        tokens["Body"] = StyleToken(
            name="Body",
            font=FontStyle(family="Arial", size=body_size, weight=FontWeight.NORMAL),
            line_spacing=1.15,
            space_after=8
        )
        
        return tokens
    
    def _create_content_sections(
        self, 
        document_id: UUID, 
        blocks: List[OCRBlock]
    ) -> List[ContentSection]:
        """Create content sections from analyzed OCR blocks."""
        sections = []
        
        for idx, block in enumerate(blocks):
            section = ContentSection.from_ocr_block(block, document_id, idx)
            sections.append(section)
        
        return sections

