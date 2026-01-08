"""
Image Preprocessor
OpenCV-based preprocessing pipeline for OCR accuracy improvement.
"""

from typing import List, Optional, Tuple
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import io

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ImagePreprocessor:
    """
    Image preprocessing pipeline for OCR.
    
    Applies:
    - Grayscale conversion
    - Adaptive thresholding
    - Noise removal
    - Deskewing
    - Resolution normalization
    """
    
    def __init__(self, target_dpi: int = None):
        self.target_dpi = target_dpi or settings.OCR_DPI
        self.applied_operations: List[str] = []
    
    def preprocess(self, image: np.ndarray, apply_all: bool = True) -> np.ndarray:
        """
        Apply full preprocessing pipeline.
        
        Args:
            image: Input image as numpy array
            apply_all: If True, apply all preprocessing steps
            
        Returns:
            Preprocessed image
        """
        self.applied_operations = []
        
        if apply_all:
            # Convert to grayscale
            image = self.to_grayscale(image)
            
            # Resize for target DPI if needed
            image = self.normalize_resolution(image)
            
            # Remove noise
            image = self.remove_noise(image)
            
            # Deskew
            image = self.deskew(image)
            
            # Adaptive thresholding
            image = self.apply_adaptive_threshold(image)
        
        return image
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale."""
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            self.applied_operations.append("grayscale")
        return image
    
    def normalize_resolution(self, image: np.ndarray, target_height: int = 2000) -> np.ndarray:
        """
        Normalize image resolution for consistent OCR.
        
        Resizes image to have a consistent height while maintaining aspect ratio.
        """
        height, width = image.shape[:2]
        
        if height < target_height:
            scale = target_height / height
            new_width = int(width * scale)
            image = cv2.resize(image, (new_width, target_height), interpolation=cv2.INTER_CUBIC)
            self.applied_operations.append(f"resize_{scale:.2f}x")
        
        return image
    
    def remove_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise using multiple techniques.
        
        - Bilateral filter for edge-preserving smoothing
        - Morphological operations for cleaning
        """
        # Bilateral filter preserves edges while smoothing
        image = cv2.bilateralFilter(image, 9, 75, 75)
        self.applied_operations.append("bilateral_filter")
        
        # Morphological opening to remove small noise
        kernel = np.ones((2, 2), np.uint8)
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        self.applied_operations.append("morph_open")
        
        return image
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew (straighten) a tilted image.
        
        Uses Hough transform to detect lines and compute skew angle.
        """
        try:
            # Find edges
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLinesP(
                edges, 1, np.pi / 180, 
                threshold=100, 
                minLineLength=100, 
                maxLineGap=10
            )
            
            if lines is None or len(lines) == 0:
                return image
            
            # Calculate angles
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                if -45 < angle < 45:  # Only consider near-horizontal lines
                    angles.append(angle)
            
            if not angles:
                return image
            
            # Median angle for robustness
            median_angle = np.median(angles)
            
            # Only deskew if angle is significant
            if abs(median_angle) < 0.5:
                return image
            
            # Rotate image
            height, width = image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            
            # Calculate new image bounds
            cos = np.abs(rotation_matrix[0, 0])
            sin = np.abs(rotation_matrix[0, 1])
            new_width = int((height * sin) + (width * cos))
            new_height = int((height * cos) + (width * sin))
            
            # Adjust rotation matrix
            rotation_matrix[0, 2] += (new_width / 2) - center[0]
            rotation_matrix[1, 2] += (new_height / 2) - center[1]
            
            image = cv2.warpAffine(
                image, rotation_matrix, (new_width, new_height),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            self.applied_operations.append(f"deskew_{median_angle:.2f}deg")
            logger.info(f"Deskewed image by {median_angle:.2f} degrees")
            
        except Exception as e:
            logger.warning(f"Deskew failed: {e}")
        
        return image
    
    def apply_adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """
        Apply adaptive thresholding for better text-background separation.
        """
        # Ensure grayscale
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Adaptive threshold
        image = cv2.adaptiveThreshold(
            image, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2
        )
        
        self.applied_operations.append("adaptive_threshold")
        return image
    
    def apply_otsu_threshold(self, image: np.ndarray) -> np.ndarray:
        """Apply Otsu's binarization."""
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        self.applied_operations.append("otsu_threshold")
        return image
    
    def dilate(self, image: np.ndarray, kernel_size: int = 2) -> np.ndarray:
        """Dilate image to thicken text."""
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        image = cv2.dilate(image, kernel, iterations=1)
        self.applied_operations.append("dilate")
        return image
    
    def erode(self, image: np.ndarray, kernel_size: int = 2) -> np.ndarray:
        """Erode image to thin text."""
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        image = cv2.erode(image, kernel, iterations=1)
        self.applied_operations.append("erode")
        return image
    
    def remove_borders(self, image: np.ndarray) -> np.ndarray:
        """Remove dark borders from scanned documents."""
        # Find contours
        contours, _ = cv2.findContours(
            cv2.bitwise_not(image),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        if not contours:
            return image
        
        # Find the largest contour (likely the page)
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        
        # Crop to content area with small margin
        margin = 10
        x = max(0, x - margin)
        y = max(0, y - margin)
        image = image[y:y+h+margin*2, x:x+w+margin*2]
        
        self.applied_operations.append("remove_borders")
        return image
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast using CLAHE."""
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        image = clahe.apply(image)
        self.applied_operations.append("clahe")
        return image
    
    @staticmethod
    def load_image(path: str) -> np.ndarray:
        """Load image from file path."""
        return cv2.imread(path)
    
    @staticmethod
    def load_image_from_bytes(data: bytes) -> np.ndarray:
        """Load image from bytes."""
        nparr = np.frombuffer(data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    @staticmethod
    def to_pil(image: np.ndarray) -> Image.Image:
        """Convert OpenCV image to PIL Image."""
        if len(image.shape) == 2:
            return Image.fromarray(image)
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    @staticmethod
    def from_pil(pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV image."""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def get_applied_operations(self) -> List[str]:
        """Get list of applied preprocessing operations."""
        return self.applied_operations.copy()

