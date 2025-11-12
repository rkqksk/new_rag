"""
Voice Search Service - Whisper API Integration
Speech-to-Text for product search
Version: v8.4.0
"""

import logging
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path
import whisper
import torch

logger = logging.getLogger(__name__)


class VoiceSearchService:
    """Voice search with Whisper STT"""

    SUPPORTED_LANGUAGES = ['ko', 'en', 'ja', 'zh']
    DEFAULT_MODEL = 'base'  # tiny, base, small, medium, large

    def __init__(self, model_size: str = DEFAULT_MODEL):
        """
        Initialize voice search service

        Args:
            model_size: Whisper model size (tiny/base/small/medium/large)
        """
        self.model_size = model_size
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f'Voice search initialized: {model_size} on {self.device}')

    def load_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            logger.info(f'Loading Whisper {self.model_size} model...')
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info('Whisper model loaded')

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        task: str = 'transcribe'
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text

        Args:
            audio_data: Audio file bytes (mp3, wav, m4a, etc.)
            language: Language code ('ko', 'en', 'ja', 'zh') or auto-detect
            task: 'transcribe' or 'translate' (to English)

        Returns:
            {
                'text': str,
                'language': str,
                'confidence': float,
                'segments': List[dict],
                'duration': float
            }
        """
        try:
            # Load model if not loaded
            self.load_model()

            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name

            try:
                # Transcribe
                options = {
                    'task': task,
                    'fp16': self.device == 'cuda',
                }

                if language:
                    options['language'] = language

                result = self.model.transcribe(temp_path, **options)

                # Extract results
                transcript = result['text'].strip()
                detected_language = result.get('language', language or 'unknown')

                # Calculate average confidence
                segments = result.get('segments', [])
                if segments:
                    avg_confidence = sum(s.get('no_speech_prob', 0) for s in segments) / len(segments)
                    confidence = 1.0 - avg_confidence
                else:
                    confidence = 0.95

                logger.info(f'Transcribed: "{transcript}" ({detected_language}, conf={confidence:.2f})')

                return {
                    'text': transcript,
                    'language': detected_language,
                    'confidence': confidence,
                    'segments': segments,
                    'duration': result.get('duration', 0),
                    'success': True,
                }

            finally:
                # Clean up temp file
                Path(temp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f'Voice transcription failed: {e}')
            return {
                'text': '',
                'language': language or 'unknown',
                'confidence': 0.0,
                'segments': [],
                'duration': 0,
                'success': False,
                'error': str(e),
            }

    async def voice_search(
        self,
        audio_data: bytes,
        language: Optional[str] = 'ko',
        search_engine=None
    ) -> Dict[str, Any]:
        """
        Complete voice search pipeline: STT + Product Search

        Args:
            audio_data: Audio bytes
            language: Language code
            search_engine: SearchEngine instance for product search

        Returns:
            {
                'transcript': str,
                'language': str,
                'confidence': float,
                'products': List[dict],
                'query_time_ms': float
            }
        """
        import time

        start_time = time.time()

        # 1. Transcribe audio
        transcription = await self.transcribe_audio(audio_data, language)

        if not transcription['success']:
            return {
                'transcript': '',
                'language': language,
                'confidence': 0.0,
                'products': [],
                'error': transcription.get('error'),
                'query_time_ms': (time.time() - start_time) * 1000,
            }

        transcript = transcription['text']

        # 2. Search products if search_engine provided
        products = []
        if search_engine and transcript:
            try:
                # TODO: Integrate with actual search engine
                # products = await search_engine.search(transcript, top_k=10)
                pass
            except Exception as e:
                logger.error(f'Product search failed: {e}')

        query_time = (time.time() - start_time) * 1000

        return {
            'transcript': transcript,
            'language': transcription['language'],
            'confidence': transcription['confidence'],
            'products': products,
            'query_time_ms': query_time,
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            'model_size': self.model_size,
            'device': self.device,
            'loaded': self.model is not None,
            'supported_languages': self.SUPPORTED_LANGUAGES,
        }


# Singleton instance
_voice_search_service = None


def get_voice_search_service(model_size: str = 'base') -> VoiceSearchService:
    """Get voice search service singleton"""
    global _voice_search_service
    if _voice_search_service is None:
        _voice_search_service = VoiceSearchService(model_size)
    return _voice_search_service
