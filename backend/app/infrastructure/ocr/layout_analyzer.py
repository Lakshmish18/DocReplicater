"""
Layout Analyzer
Reconstructs document layout from OCR blocks.
"""

from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import numpy as np

from app.domain.entities.ocr_metadata import OCRBlock, BoundingBox
from app.domain.entities.content_section import SectionType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LayoutAnalyzer:
    """
    Analyzes OCR output to reconstruct document layout.
    
    Features:
    - Text block grouping by position
    - Heading/paragraph detection
    - Column detection
    - Margin estimation
    - Reading order determination
    """
    
    def __init__(self):
        self.page_blocks: Dict[int, List[OCRBlock]] = defaultdict(list)
    
    def analyze(self, blocks: List[OCRBlock]) -> List[OCRBlock]:
        """
        Analyze blocks and enhance with layout information.
        
        Returns blocks sorted in reading order with inferred types.
        """
        if not blocks:
            return []
        
        # Group blocks by page
        self.page_blocks.clear()
        for block in blocks:
            self.page_blocks[block.page_number].append(block)
        
        # Process each page
        analyzed_blocks = []
        for page_num in sorted(self.page_blocks.keys()):
            page_blocks = self.page_blocks[page_num]
            
            # Sort into reading order
            sorted_blocks = self._sort_reading_order(page_blocks)
            
            # Group related blocks (merge if needed)
            grouped_blocks = self._group_blocks(sorted_blocks)
            
            # Infer block types
            typed_blocks = self._infer_block_types(grouped_blocks)
            
            analyzed_blocks.extend(typed_blocks)
        
        logger.info(f"Layout analysis complete: {len(analyzed_blocks)} blocks")
        return analyzed_blocks
    
    def _sort_reading_order(self, blocks: List[OCRBlock]) -> List[OCRBlock]:
        """
        Sort blocks in reading order (top-to-bottom, left-to-right).
        
        Handles multi-column layouts.
        """
        if not blocks:
            return []
        
        # First, detect if multi-column
        columns = self._detect_column_boundaries(blocks)
        
        if len(columns) <= 1:
            # Single column - simple top-to-bottom sort
            return sorted(
                blocks,
                key=lambda b: (
                    b.bounding_box.y if b.bounding_box else 0,
                    b.bounding_box.x if b.bounding_box else 0,
                )
            )
        
        # Multi-column - sort within columns
        sorted_blocks = []
        for col_start, col_end in columns:
            col_blocks = [
                b for b in blocks
                if b.bounding_box and col_start <= b.bounding_box.x + b.bounding_box.width / 2 < col_end
            ]
            col_blocks.sort(key=lambda b: b.bounding_box.y if b.bounding_box else 0)
            sorted_blocks.extend(col_blocks)
        
        return sorted_blocks
    
    def _detect_column_boundaries(self, blocks: List[OCRBlock]) -> List[Tuple[float, float]]:
        """
        Detect column boundaries based on block positions.
        
        Returns list of (start_x, end_x) tuples for each column.
        """
        if not blocks:
            return [(0, float('inf'))]
        
        # Get x positions of block centers
        x_centers = []
        for block in blocks:
            if block.bounding_box:
                center = block.bounding_box.x + block.bounding_box.width / 2
                x_centers.append(center)
        
        if not x_centers:
            return [(0, float('inf'))]
        
        # Find gaps in x distribution that might indicate columns
        x_centers.sort()
        
        # Use histogram to find column centers
        if len(x_centers) < 5:
            return [(0, float('inf'))]
        
        # Simple heuristic: look for significant gaps
        gaps = []
        for i in range(1, len(x_centers)):
            gap = x_centers[i] - x_centers[i-1]
            if gap > 50:  # Significant gap threshold
                gaps.append((i, gap))
        
        if not gaps:
            return [(0, float('inf'))]
        
        # If we found a significant gap, assume 2 columns
        if len(gaps) >= 1:
            # Find the largest gap
            largest_gap_idx = max(gaps, key=lambda g: g[1])[0]
            boundary = (x_centers[largest_gap_idx-1] + x_centers[largest_gap_idx]) / 2
            
            return [
                (0, boundary),
                (boundary, float('inf'))
            ]
        
        return [(0, float('inf'))]
    
    def _group_blocks(self, blocks: List[OCRBlock]) -> List[OCRBlock]:
        """
        Group nearby blocks that likely belong together.
        
        Merges blocks that are vertically close and horizontally aligned.
        """
        if not blocks or len(blocks) < 2:
            return blocks
        
        grouped = []
        current_group = [blocks[0]]
        
        for i in range(1, len(blocks)):
            current = blocks[i]
            prev = current_group[-1]
            
            if self._should_merge(prev, current):
                current_group.append(current)
            else:
                # Merge current group into single block
                merged = self._merge_blocks(current_group)
                grouped.append(merged)
                current_group = [current]
        
        # Don't forget the last group
        if current_group:
            merged = self._merge_blocks(current_group)
            grouped.append(merged)
        
        return grouped
    
    def _should_merge(self, block1: OCRBlock, block2: OCRBlock) -> bool:
        """
        Determine if two blocks should be merged.
        """
        if not block1.bounding_box or not block2.bounding_box:
            return False
        
        # Check vertical proximity
        vertical_gap = block2.bounding_box.y - (block1.bounding_box.y + block1.bounding_box.height)
        
        # Allow merging if gap is less than typical line height
        max_gap = block1.bounding_box.height * 1.5
        
        if vertical_gap > max_gap or vertical_gap < -10:
            return False
        
        # Check horizontal alignment
        x1_center = block1.bounding_box.x + block1.bounding_box.width / 2
        x2_center = block2.bounding_box.x + block2.bounding_box.width / 2
        
        # Allow some horizontal variation
        horizontal_diff = abs(x1_center - x2_center)
        max_horizontal_diff = max(block1.bounding_box.width, block2.bounding_box.width) * 0.5
        
        if horizontal_diff > max_horizontal_diff:
            return False
        
        # Check similar font sizes
        if block1.font_size and block2.font_size:
            size_diff = abs(block1.font_size - block2.font_size)
            if size_diff > 4:  # More than 4pt difference
                return False
        
        return True
    
    def _merge_blocks(self, blocks: List[OCRBlock]) -> OCRBlock:
        """Merge multiple blocks into one."""
        if len(blocks) == 1:
            return blocks[0]
        
        # Combine text
        combined_text = "\n".join(b.text for b in blocks if b.text)
        
        # Merge bounding boxes
        merged_bbox = blocks[0].bounding_box
        for block in blocks[1:]:
            if block.bounding_box and merged_bbox:
                merged_bbox = merged_bbox.merge(block.bounding_box)
        
        # Average confidence
        confidences = [b.confidence for b in blocks if b.confidence > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Use properties from first block (usually the title/heading)
        first = blocks[0]
        
        return OCRBlock(
            id=first.id,
            text=combined_text,
            bounding_box=merged_bbox,
            page_number=first.page_number,
            confidence=avg_confidence,
            font_size=first.font_size,
            is_bold=first.is_bold,
            is_italic=first.is_italic,
            alignment=first.alignment,
            block_type=first.block_type,
        )
    
    def _infer_block_types(self, blocks: List[OCRBlock]) -> List[OCRBlock]:
        """
        Infer semantic types for blocks (heading, paragraph, etc.).
        """
        if not blocks:
            return []
        
        # Collect font size statistics
        sizes = [b.font_size for b in blocks if b.font_size]
        if not sizes:
            return blocks
        
        avg_size = np.mean(sizes)
        max_size = max(sizes)
        
        for block in blocks:
            if not block.font_size:
                block.block_type = "text"
                continue
            
            # Infer type based on font size relative to average
            if block.font_size >= max_size * 0.95:
                block.block_type = "title"
            elif block.font_size > avg_size * 1.3 or block.is_bold:
                block.block_type = "heading"
            elif block.font_size < avg_size * 0.85:
                block.block_type = "caption"
            else:
                block.block_type = "text"
        
        return blocks
    
    def detect_margins(self, blocks: List[OCRBlock]) -> Dict[str, float]:
        """
        Detect page margins from block positions.
        
        Returns margins in inches (assuming 72 DPI for PDF coordinates).
        """
        if not blocks:
            return {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}
        
        # Assume standard letter size (612 x 792 points)
        page_width = 612
        page_height = 792
        
        # Find extremes
        min_x = float('inf')
        min_y = float('inf')
        max_x = 0
        max_y = 0
        
        for block in blocks:
            if not block.bounding_box:
                continue
            
            bbox = block.bounding_box
            min_x = min(min_x, bbox.x)
            min_y = min(min_y, bbox.y)
            max_x = max(max_x, bbox.x + bbox.width)
            max_y = max(max_y, bbox.y + bbox.height)
        
        if min_x == float('inf'):
            return {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}
        
        # Convert to inches
        return {
            "top": min_y / 72,
            "bottom": (page_height - max_y) / 72,
            "left": min_x / 72,
            "right": (page_width - max_x) / 72,
        }
    
    def detect_columns(self, blocks: List[OCRBlock]) -> int:
        """Detect number of columns in the document."""
        columns = self._detect_column_boundaries(blocks)
        return len(columns)

