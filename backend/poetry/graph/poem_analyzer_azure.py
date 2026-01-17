"""
Azure OpenAI-Based Poem Analysis and Metadata Extraction

This module provides functions to analyze poems and extract:
- Sound devices (alliteration, rhyme, repetition, assonance, consonance)
- Free verse structure metrics
- Thematic and emotional content

Uses Azure OpenAI (compatible with your existing setup).
"""

import json
import re
from typing import Dict, List, Any, Optional
from openai import AzureOpenAI
import os


class PoemAnalyzer:
    """
    Analyzes poems using Azure OpenAI to extract metadata for the knowledge graph.
    Compatible with your existing Azure setup.
    """
    
    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
        deployment_name: str = "gpt-4"
    ):
        """
        Initialize the analyzer with Azure OpenAI credentials.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint (or set AZURE_OPENAI_ENDPOINT env var)
            api_key: Azure OpenAI API key (or set AZURE_OPENAI_API_KEY env var)
            api_version: API version to use
            deployment_name: Your GPT-4 deployment name
        """
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = api_version
        self.deployment_name = deployment_name
        
        if self.azure_endpoint and self.api_key:
            self.client = AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.api_key,
                api_version=self.api_version
            )
        else:
            self.client = None
    
    def analyze_poem(
        self,
        poem_text: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a poem.
        
        Args:
            poem_text: The full text of the poem
            title: Optional poem title
        
        Returns:
            Dictionary with extracted metadata:
            {
                "themes": [...],
                "imagery": [...],
                "emotions": [...],
                "sound_devices": [...],
                "structure_metadata": {...},
                "sound_metadata": {...}
            }
        """
        if not self.client:
            raise ValueError(
                "Azure OpenAI credentials not provided. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables."
            )
        
        prompt = self._build_analysis_prompt(poem_text, title)
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert poetry analyst. Extract structured metadata from poems."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse the response
        response_text = response.choices[0].message.content
        metadata = self._parse_analysis_response(response_text)
        
        # Add automatic metrics
        auto_metrics = self._extract_automatic_metrics(poem_text)
        metadata["structure_metadata"].update(auto_metrics)
        
        return metadata
    
    def _build_analysis_prompt(self, poem_text: str, title: Optional[str] = None) -> str:
        """Build the prompt for poem analysis."""
        return f"""Analyze this poem and extract the following elements. Return your response as a JSON object.

Poem{f' titled "{title}"' if title else ''}:
{poem_text}

Extract the following:

1. **themes**: List 3-5 main themes (e.g., "urban_life", "transition", "isolation", "hope")

2. **imagery**: List 5-10 key images and symbols (e.g., "dawn", "concrete", "water", "birds")

3. **emotions**: List 2-4 primary emotions conveyed (e.g., "contemplative", "peaceful", "tense", "lonely")

4. **sound_devices**: List all sound devices used:
   - "alliteration" (and note if heavy/moderate/light)
   - "end_rhyme" or "internal_rhyme" or "slant_rhyme"
   - "repetition" (repeated words/phrases)
   - "anaphora" (repeated line beginnings)
   - "assonance" (repeated vowel sounds)
   - "consonance" (repeated consonant sounds)
   - "onomatopoeia"

5. **sound_metadata**: Details about sound patterns:
   - alliteration_density: "high" / "moderate" / "low"
   - rhyme_type: describe the rhyme pattern
   - repetition_phrases: list any repeated phrases
   - repeated_structures: describe any repeated grammatical patterns
   - dominant_sounds: what sounds dominate?

6. **structure_metadata**: Details about free verse structure:
   - form: "free_verse" (or other if applicable)
   - line_count: number of lines
   - stanza_breaks: list showing lines per stanza (e.g., [4, 5, 3])
   - enjambment_lines: list of line numbers with enjambment
   - caesura_lines: list of line numbers with strong mid-line pauses
   - breath_pattern: "regular" / "irregular"
   - line_length_variation: "consistent" / "varied" / "highly_varied"

Return ONLY a valid JSON object with these keys. No markdown, no explanation, just JSON.

Example format:
{{
  "themes": ["urban_life", "transition", "morning"],
  "imagery": ["dawn", "concrete", "towers", "commuters"],
  "emotions": ["contemplative", "peaceful"],
  "sound_devices": ["alliteration", "internal_rhyme", "repetition"],
  "sound_metadata": {{
    "alliteration_density": "high",
    "rhyme_type": "internal and slant rhyme",
    "repetition_phrases": ["the city", "morning light"],
    "repeated_structures": ["each X that Y"],
    "dominant_sounds": "hard consonants (c, t, d)"
  }},
  "structure_metadata": {{
    "form": "free_verse",
    "line_count": 12,
    "stanza_breaks": [4, 4, 4],
    "enjambment_lines": [2, 5, 9],
    "caesura_lines": [3, 7],
    "breath_pattern": "regular",
    "line_length_variation": "consistent"
  }}
}}"""
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the LLM response into structured metadata."""
        # Try to extract JSON from the response
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Assume the whole response is JSON
            json_str = response_text.strip()
        
        try:
            metadata = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Fallback: return empty structure
            print(f"Failed to parse LLM response: {e}")
            metadata = {
                "themes": [],
                "imagery": [],
                "emotions": [],
                "sound_devices": [],
                "sound_metadata": {},
                "structure_metadata": {}
            }
        
        # Ensure all required keys exist
        required_keys = [
            "themes", "imagery", "emotions", "sound_devices",
            "sound_metadata", "structure_metadata"
        ]
        for key in required_keys:
            if key not in metadata:
                metadata[key] = {} if "metadata" in key else []
        
        return metadata
    
    def _extract_automatic_metrics(self, poem_text: str) -> Dict[str, Any]:
        """
        Extract basic metrics automatically without LLM.
        These supplement the LLM analysis with precise counts.
        """
        lines = poem_text.strip().split('\n')
        
        # Count non-empty lines
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Simple syllable approximation
        line_lengths = [self._estimate_syllables(line) for line in non_empty_lines]
        
        # Detect stanza breaks (empty lines)
        stanza_breaks = []
        current_stanza_length = 0
        for line in lines:
            if line.strip():
                current_stanza_length += 1
            else:
                if current_stanza_length > 0:
                    stanza_breaks.append(current_stanza_length)
                    current_stanza_length = 0
        if current_stanza_length > 0:
            stanza_breaks.append(current_stanza_length)
        
        return {
            "actual_line_count": len(non_empty_lines),
            "line_lengths": line_lengths,
            "avg_line_length": sum(line_lengths) / len(line_lengths) if line_lengths else 0,
            "detected_stanza_breaks": stanza_breaks if len(stanza_breaks) > 1 else None,
            "total_words": sum(len(line.split()) for line in non_empty_lines)
        }
    
    def _estimate_syllables(self, text: str) -> int:
        """
        Rough syllable count estimation.
        For better accuracy, consider adding pyphen library.
        """
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^a-z\s]', '', text)
        
        # Count vowel groups
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in text:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent e
        if text.endswith('e'):
            syllable_count -= 1
        
        # Ensure at least 1 syllable per word
        word_count = len(text.split())
        return max(syllable_count, word_count)
    
    def quick_extract_sound_devices(self, poem_text: str) -> List[str]:
        """
        Quick extraction of obvious sound devices without full LLM analysis.
        Useful for batch processing or when you want faster results.
        """
        sound_devices = []
        
        lines = poem_text.lower().split('\n')
        words = poem_text.lower().split()
        
        # Check for end rhyme
        last_words = [line.strip().split()[-1] if line.strip().split() else "" 
                     for line in lines if line.strip()]
        if len(set(last_words)) < len(last_words) * 0.8:
            sound_devices.append("end_rhyme")
        
        # Check for alliteration
        for i in range(len(words) - 1):
            if words[i] and words[i+1] and words[i][0] == words[i+1][0]:
                if "alliteration" not in sound_devices:
                    sound_devices.append("alliteration")
                break
        
        # Check for repetition
        word_counts = {}
        for word in words:
            if len(word) > 3:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        if any(count > 1 for count in word_counts.values()):
            sound_devices.append("repetition")
        
        # Check for anaphora
        first_words = [line.strip().split()[0] if line.strip().split() else ""
                      for line in lines if line.strip()]
        if len(first_words) != len(set(first_words)):
            sound_devices.append("anaphora")
        
        return sound_devices


# ==================== USAGE EXAMPLE ====================

def example_usage():
    """
    Example of how to use the PoemAnalyzer with Azure OpenAI.
    """
    # Initialize analyzer (uses env vars)
    analyzer = PoemAnalyzer()
    
    # Example poem
    poem_text = """Dawn breaks over Peachtree Street
Commuters rise like urban flowers
The city breathes its first deep breath
Before the rush, before the stress"""
    
    try:
        # Analyze the poem
        metadata = analyzer.analyze_poem(poem_text, title="Morning on Peachtree")
        
        print("Extracted Metadata:")
        print(f"Themes: {metadata['themes']}")
        print(f"Sound Devices: {metadata['sound_devices']}")
        print(f"Structure: {metadata['structure_metadata']}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are set")


if __name__ == "__main__":
    example_usage()
