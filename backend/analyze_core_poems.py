#!/usr/bin/env python3
"""
Analyze core poems to extract actual themes/motifs the analyzer detects.
This will establish the ground truth for what themes exist in the canon.
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from poetry.graph.poem_analyzer_azure import PoemAnalyzer

def analyze_core_poems():
    """Analyze all core poems and report themes."""
    poems_dir = backend_dir / "poems"
    core_poem_files = [
        "The_Silent_Station.txt",
        "Pigeon_Police.txt", 
        "Heavy_Cranes.txt",
        "Children_of_the_Woods.txt",
        "Convector_Howlers.txt",
        "Cornelius_of_the_Rock.txt",
        "In_Era_of_Silent.txt",
        "The_Dreams_from_Mistren_Peachtree_Street.txt",
        "The_Edible_Play.txt",
        "The_Music_Is_Always_On.txt",
    ]
    
    analyzer = PoemAnalyzer()
    all_themes = {}
    all_imagery = {}
    all_emotions = {}
    
    print("=" * 70)
    print("ANALYZING CORE POEMS TO EXTRACT CANONICAL THEMES")
    print("=" * 70)
    
    for poem_file in core_poem_files:
        poem_path = poems_dir / poem_file
        
        if not poem_path.exists():
            print(f"⚠️ {poem_file} not found")
            continue
        
        with open(poem_path, 'r') as f:
            poem_text = f.read()
        
        poem_title = poem_file.replace('.txt', '')
        print(f"\n📖 Analyzing: {poem_title}")
        print("-" * 70)
        
        try:
            analysis = analyzer.analyze_poem(poem_text, poem_title)
            
            themes = analysis.get('themes', [])
            imagery = analysis.get('imagery', [])
            emotions = analysis.get('emotions', [])
            
            print(f"   Themes: {themes}")
            print(f"   Imagery: {imagery}")
            print(f"   Emotions: {emotions}")
            
            all_themes[poem_title] = themes
            all_imagery[poem_title] = imagery
            all_emotions[poem_title] = emotions
            
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
    
    # Summary statistics
    print(f"\n{'='*70}")
    print("CANONICAL THEME SUMMARY")
    print(f"{'='*70}")
    
    # Aggregate themes
    theme_frequency = {}
    for themes in all_themes.values():
        for theme in themes:
            theme_lower = str(theme).lower()
            theme_frequency[theme_lower] = theme_frequency.get(theme_lower, 0) + 1
    
    print("\n📊 Most Frequent Themes:")
    for theme, freq in sorted(theme_frequency.items(), key=lambda x: x[1], reverse=True):
        print(f"   {theme}: {freq} poems")
    
    # Aggregate imagery
    imagery_frequency = {}
    for images in all_imagery.values():
        for img in images:
            img_lower = str(img).lower()
            imagery_frequency[img_lower] = imagery_frequency.get(img_lower, 0) + 1
    
    print("\n🎨 Most Frequent Imagery:")
    for img, freq in sorted(imagery_frequency.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {img}: {freq} poems")
    
    # Aggregate emotions
    emotion_frequency = {}
    for emotions in all_emotions.values():
        for emotion in emotions:
            emotion_lower = str(emotion).lower()
            emotion_frequency[emotion_lower] = emotion_frequency.get(emotion_lower, 0) + 1
    
    print("\n💭 Most Frequent Emotions:")
    for emotion, freq in sorted(emotion_frequency.items(), key=lambda x: x[1], reverse=True):
        print(f"   {emotion}: {freq} poems")
    
    # Output structured data
    print(f"\n{'='*70}")
    print("STRUCTURED OUTPUT (for narrative_engine update)")
    print(f"{'='*70}")
    
    output = {
        "canonical_themes": list(dict.fromkeys([t for themes in all_themes.values() for t in themes])),
        "canonical_imagery": list(dict.fromkeys([i for images in all_imagery.values() for i in images])),
        "canonical_emotions": list(dict.fromkeys([e for emotions in all_emotions.values() for e in emotions])),
        "theme_frequency": theme_frequency,
        "imagery_frequency": imagery_frequency,
        "emotion_frequency": emotion_frequency,
    }
    
    print(json.dumps(output, indent=2))
    
    # Save for reference
    output_file = backend_dir / "reports" / "canonical_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n✅ Analysis saved to {output_file}")

if __name__ == "__main__":
    analyze_core_poems()
