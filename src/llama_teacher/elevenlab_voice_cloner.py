# app/services/elevenlabs_voice_cloner.py
import logging
from pathlib import Path

from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)


class ElevenLabsVoiceCloner:
    """Clone votre voix avec ElevenLabs (très bon résultats)"""

    def __init__(self, api_key: str):
        self.client = ElevenLabs(api_key=api_key)

    def clone_my_voice(self, audio_samples: list, voice_name: str = "ma_voix"):
        """
        Clone votre voix avec ElevenLabs

        Args:
            audio_samples: Liste de chemins vers vos enregistrements
            voice_name: Nom de votre voix

        Returns:
            Voice ID
        """
        try:
            # Préparer les fichiers
            files = []
            for sample_path in audio_samples[:5]:  # Limiter à 5 échantillons
                if Path(sample_path).exists():
                    files.append(open(sample_path, "rb"))

            if len(files) < 3:
                raise ValueError("Au moins 3 échantillons audio requis")

            # Créer la voix
            voice = self.client.voices.add(
                name=voice_name,
                files=files,
                description=f"Voix de {voice_name} pour réponses pédagogiques",
            )

            # Fermer les fichiers
            for file in files:
                file.close()

            logger.info(f"✅ Voix clonée: {voice.name} (ID: {voice.voice_id})")
            return voice.voice_id

        except Exception as e:
            logger.error(f"❌ Erreur clonage ElevenLabs: {e}")
            raise

    def generate_with_my_voice(self, text: str, voice_id: str, output_path: Path):
        """Génère du speech avec votre voix clonée"""
        audio = self.client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2",
            voice_settings={
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.4,
                "use_speaker_boost": True,
            },
        )

        # Sauvegarder
        with open(output_path, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
