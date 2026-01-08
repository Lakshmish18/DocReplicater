"""
OpenAI Client
Section-aware AI content generation.
"""

from typing import Optional, List, Dict
from openai import OpenAI

from app.config import settings
from app.domain.entities.content_section import ContentSection, SectionType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    """
    OpenAI client for section-aware content generation.
    
    Rules:
    - Operates per section only
    - Never modifies design
    - Respects section type, length constraints, tone
    - No full-document rewriting
    """
    
    # Section type prompts
    SECTION_PROMPTS = {
        SectionType.TITLE: "Write a compelling title for the document.",
        SectionType.HEADING_1: "Write a clear and descriptive main section heading.",
        SectionType.HEADING_2: "Write a clear subsection heading.",
        SectionType.HEADING_3: "Write a clear sub-subsection heading.",
        SectionType.PARAGRAPH: "Write a well-structured paragraph.",
        SectionType.BULLET_LIST: "Write bullet points as a list.",
        SectionType.NUMBERED_LIST: "Write numbered items as a list.",
        SectionType.QUOTE: "Write an appropriate quote or cited text.",
        SectionType.CAPTION: "Write a brief, descriptive caption.",
    }
    
    def __init__(self):
        self.client = None
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured")
            return
        
        try:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def is_available(self) -> bool:
        """Check if AI is available."""
        return self.client is not None
    
    def generate_content(
        self,
        section: ContentSection,
        prompt: str,
        context: Optional[Dict] = None,
        tone: str = "professional",
        max_length: Optional[int] = None,
    ) -> str:
        """
        Generate content for a specific section.
        
        Args:
            section: The content section to generate for
            prompt: User's prompt/request
            context: Additional context (nearby sections, document intent)
            tone: Desired tone (professional, casual, academic, etc.)
            max_length: Maximum word count
            
        Returns:
            Generated content string
        """
        if not self.is_available():
            raise RuntimeError("OpenAI client not available")
        
        # Build system prompt based on section type
        system_prompt = self._build_system_prompt(section, context, tone, max_length)
        
        # Build user prompt
        user_prompt = self._build_user_prompt(section, prompt, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_length or self.max_tokens,
                temperature=0.7,
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"Generated content for section {section.id}: {len(content)} chars")
            
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise RuntimeError(f"Failed to generate content: {str(e)}")
    
    def _build_system_prompt(
        self,
        section: ContentSection,
        context: Optional[Dict],
        tone: str,
        max_length: Optional[int],
    ) -> str:
        """Build the system prompt for content generation."""
        base_prompt = self.SECTION_PROMPTS.get(
            section.section_type, 
            "Write appropriate content for this section."
        )
        
        system_prompt = f"""You are a professional content writer. Your task is to generate content for a specific section of a document.

IMPORTANT RULES:
1. Generate content ONLY for the specified section type
2. Do NOT add any formatting markers (no #, *, etc.)
3. Return ONLY the content text, nothing else
4. Match the specified tone and style
5. Respect any length constraints

Section Type: {section.section_type.value}
Task: {base_prompt}
Tone: {tone}"""
        
        if max_length:
            system_prompt += f"\nMaximum Length: approximately {max_length} words"
        
        if context:
            if context.get("document_purpose"):
                system_prompt += f"\nDocument Purpose: {context['document_purpose']}"
            if context.get("target_audience"):
                system_prompt += f"\nTarget Audience: {context['target_audience']}"
        
        return system_prompt
    
    def _build_user_prompt(
        self,
        section: ContentSection,
        prompt: str,
        context: Optional[Dict],
    ) -> str:
        """Build the user prompt for content generation."""
        user_prompt = f"User Request: {prompt}\n"
        
        # Add original content for reference
        if section.original_content:
            user_prompt += f"\nOriginal Content (for reference):\n{section.original_content[:500]}\n"
        
        # Add context from nearby sections
        if context and context.get("nearby_sections"):
            user_prompt += "\nContext from nearby sections:\n"
            for nearby in context["nearby_sections"][:3]:
                user_prompt += f"- {nearby[:200]}...\n"
        
        user_prompt += "\nGenerate the content now:"
        
        return user_prompt
    
    def suggest_improvements(
        self,
        section: ContentSection,
        context: Optional[Dict] = None,
    ) -> List[str]:
        """
        Suggest improvements for existing content.
        
        Returns list of improvement suggestions.
        """
        if not self.is_available():
            raise RuntimeError("OpenAI client not available")
        
        if not section.content:
            return ["Section is empty. Add content first."]
        
        system_prompt = """You are a professional editor. Analyze the given content and provide 3-5 specific suggestions for improvement.
Focus on:
- Clarity and readability
- Grammar and style
- Structure and flow
- Engagement and impact

Return suggestions as a numbered list."""
        
        user_prompt = f"""Section Type: {section.section_type.value}
Content:
{section.content}

Provide improvement suggestions:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=500,
                temperature=0.5,
            )
            
            suggestions_text = response.choices[0].message.content.strip()
            
            # Parse numbered suggestions
            suggestions = []
            for line in suggestions_text.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    # Remove number prefix
                    suggestion = line.lstrip("0123456789.-) ").strip()
                    if suggestion:
                        suggestions.append(suggestion)
            
            return suggestions or ["No specific improvements suggested."]
            
        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            return [f"Could not generate suggestions: {str(e)}"]
    
    def adjust_tone(
        self,
        section: ContentSection,
        target_tone: str,
    ) -> str:
        """
        Adjust the tone of existing content.
        
        Args:
            section: Content section to adjust
            target_tone: Target tone (professional, casual, academic, etc.)
            
        Returns:
            Adjusted content
        """
        if not self.is_available():
            raise RuntimeError("OpenAI client not available")
        
        if not section.content:
            raise ValueError("Section has no content to adjust")
        
        system_prompt = f"""You are a professional editor. Rewrite the given content to match the target tone while:
1. Preserving the core message and information
2. Maintaining approximately the same length
3. Keeping the same structure
4. Not adding any formatting markers

Target Tone: {target_tone}"""
        
        user_prompt = f"""Original Content:
{section.content}

Rewrite with {target_tone} tone:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Tone adjustment failed: {e}")
            raise RuntimeError(f"Failed to adjust tone: {str(e)}")

