# app/tools/multilang.py
from typing import Dict, Optional
from deep_translator import GoogleTranslator
import langdetect
from functools import lru_cache

# Supported languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh-cn': 'Chinese (Simplified)',
    'ar': 'Arabic',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'mr': 'Marathi',
    'ur': 'Urdu'
}

def detect_language(text: str) -> Optional[str]:
    """
    Detect language of input text
    """
    try:
        # Clean text (remove code blocks if present)
        clean_text = text.replace('```', '').strip()
        
        if len(clean_text) < 3:
            return 'en'  # Default to English for very short text
        
        detected = langdetect.detect(clean_text)
        
        # langdetect returns 'zh-cn' as 'zh', normalize it
        if detected == 'zh':
            return 'zh-cn'
        
        return detected if detected in SUPPORTED_LANGUAGES else 'en'
        
    except Exception as e:
        print(f"Language detection failed: {e}")
        return 'en'  # Default to English


@lru_cache(maxsize=100)
def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text from source to target language
    Uses caching to avoid repeated translations
    """
    if source_lang == target_lang:
        return text
    
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        # Handle long text by splitting into chunks
        max_length = 4500  # Google Translate API limit
        
        if len(text) <= max_length:
            return translator.translate(text)
        
        # Split by paragraphs
        paragraphs = text.split('\n\n')
        translated_paragraphs = []
        
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) <= max_length:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    translated_paragraphs.append(translator.translate(current_chunk.strip()))
                current_chunk = para + "\n\n"
        
        if current_chunk:
            translated_paragraphs.append(translator.translate(current_chunk.strip()))
        
        return "\n\n".join(translated_paragraphs)
        
    except Exception as e:
        print(f"Translation failed: {e}")
        return text  # Return original text if translation fails


def process_multilang_query(question: str) -> Dict:
    """
    Process query: detect language and translate if needed
    """
    detected_lang = detect_language(question)
    
    result = {
        'original_text': question,
        'detected_language': detected_lang,
        'language_name': SUPPORTED_LANGUAGES.get(detected_lang, 'Unknown'),
        'needs_translation': detected_lang != 'en',
        'english_text': None
    }
    
    if result['needs_translation']:
        print(f"🌍 Detected language: {result['language_name']}")
        print(f"📝 Translating to English...")
        
        result['english_text'] = translate_text(question, detected_lang, 'en')
        print(f"✓ Translation: {result['english_text'][:100]}...")
    else:
        result['english_text'] = question
    
    return result


def translate_response_back(response: str, target_lang: str) -> str:
    """
    Translate LLM response back to user's language
    """
    if target_lang == 'en':
        return response
    
    print(f"🌍 Translating response back to {SUPPORTED_LANGUAGES.get(target_lang, target_lang)}...")
    translated = translate_text(response, 'en', target_lang)
    print(f"✓ Translation complete")
    
    return translated


def format_multilang_response(
    original_question: str,
    english_question: str,
    english_response: str,
    detected_lang: str
) -> str:
    """
    Format response with language info
    """
    if detected_lang == 'en':
        return english_response
    
    # Translate response back
    translated_response = translate_response_back(english_response, detected_lang)
    
    # Add language indicator
    lang_name = SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)
    
    response_with_note = f"{translated_response}\n\n---\n💬 *Responded in {lang_name}*"
    
    return response_with_note


# Example usage in llm.py:
"""
async def generate_direct_response_multilang(question: str, ...) -> str:
    # 1. Detect and translate if needed
    lang_info = process_multilang_query(question)
    
    # 2. Use English version for LLM
    english_question = lang_info['english_text']
    
    # 3. Generate response in English
    english_response = await generate_direct_response(english_question, ...)
    
    # 4. Translate back to user's language
    final_response = format_multilang_response(
        lang_info['original_text'],
        english_question,
        english_response,
        lang_info['detected_language']
    )
    
    return final_response
"""

# Install required packages:
# pip install deep-translator langdetect