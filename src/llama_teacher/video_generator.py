import logging
from pathlib import Path
from typing import Optional

# Pour la vidéo
try:
    import numpy as np
    from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, TextClip
    from PIL import Image, ImageDraw, ImageFont

    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("⚠️ MoviePy non installé. Installez: pip install moviepy Pillow")

# ElevenLabs pour votre voix
try:
    from elevenlabs import ElevenLabs

    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

# OpenAI fallback
from openai import OpenAI

from src.config import settings

logger = logging.getLogger(__name__)


class StreamlitVideoGenerator:
    """Générateur de vidéos optimisé pour Streamlit avec corrections RGBA"""

    def __init__(self):
        # Initialiser les clients
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.elevenlabs_client = None

        if (
            hasattr(settings, "elevenlabs_api_key")
            and settings.elevenlabs_api_key
            and ELEVENLABS_AVAILABLE
        ):
            try:
                self.elevenlabs_client = ElevenLabs(api_key=settings.elevenlabs_api_key)
                logger.info("✅ ElevenLabs initialisé")
            except Exception as e:
                logger.warning(f"❌ ElevenLabs non disponible: {e}")

        # Dossiers
        self.video_output_dir = Path(
            getattr(settings, "video_output_dir", "generated_videos")
        )
        self.video_output_dir.mkdir(exist_ok=True)

        # Cache pour Streamlit
        self.video_cache = {}

    def generate_video_response(
        self,
        text_response: str,
        question: str,
        use_my_voice: bool = True,
        progress_callback=None,
    ) -> Optional[Path]:
        """
        Génère une vidéo de réponse
        """
        if not MOVIEPY_AVAILABLE:
            import streamlit as st

            st.error("❌ MoviePy non installé. Exécutez: `pip install moviepy Pillow`")
            return None

        try:
            # Vérifier le cache
            cache_key = f"{question}_{hash(text_response) % 10000}"
            if cache_key in self.video_cache:
                cached_path = Path(self.video_cache[cache_key])
                if cached_path.exists():
                    return cached_path

            if progress_callback:
                progress_callback("Préparation du texte...", 10)

            # Préparer le texte pour l'audio
            audio_text = self._prepare_text_for_audio(text_response)

            # Créer un dossier temporaire
            temp_dir = self.video_output_dir / "temp"
            temp_dir.mkdir(exist_ok=True)

            # Générer l'audio
            if progress_callback:
                progress_callback("Synthèse vocale en cours...", 30)

            audio_path = temp_dir / f"audio_{cache_key}.mp3"

            if use_my_voice and self.elevenlabs_client:
                print("Utilisation de ElevenLabs pour la synthèse vocale...")
                audio_success = self._generate_with_elevenlabs_sync(
                    audio_text, audio_path
                )
            else:
                audio_success = self._generate_with_openai_sync(audio_text, audio_path)

            # Fallback
            if not audio_success:
                audio_success = self._generate_with_openai_sync(audio_text, audio_path)

            if not audio_success:
                raise Exception("Échec de la génération audio")

            # Générer la vidéo
            if progress_callback:
                progress_callback("Création de la vidéo...", 60)

            video_filename = self._generate_video_filename(question)
            video_path = self.video_output_dir / video_filename

            self._create_video_sync(
                audio_path=audio_path,
                text_response=text_response,
                output_path=video_path,
                progress_callback=progress_callback,
            )

            # Nettoyer
            if audio_path.exists():
                audio_path.unlink(missing_ok=True)

            # Mettre en cache
            self.video_cache[cache_key] = str(video_path)

            if progress_callback:
                progress_callback("Vidéo générée avec succès !", 100)

            return video_path

        except Exception as e:
            logger.error(f"❌ Erreur génération vidéo: {str(e)}", exc_info=True)
            return None

    def _prepare_image_clip(self, duration: float):
        """Prépare le clip image - CORRECTION RGBA"""
        try:
            # Trouver l'image
            img_path = None

            # Essayer teacher_image_path
            if hasattr(settings, "teacher_image_path"):
                img_path = Path(settings.teacher_image_path)

            # Fallback sur teacher_photo
            if not img_path or not img_path.exists():
                img_path = Path(
                    getattr(settings, "teacher_photo", "assets/teacher.jpg")
                )

            if img_path.exists():
                # Ouvrir l'image
                img = Image.open(img_path)

                # CORRECTION: Gérer les modes d'image
                if img.mode == "RGBA":
                    # RGBA -> RGB avec fond blanc
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])
                    img = rgb_img
                elif img.mode == "P":
                    # Mode palette -> RGB
                    img = img.convert("RGB")
                elif img.mode not in ["RGB", "L"]:
                    # Autres modes -> RGB
                    img = img.convert("RGB")

            else:
                # Créer une image par défaut
                img = Image.new("RGB", (720, 1280), color=(41, 128, 185))
                draw = ImageDraw.Draw(img)

                # Ajouter du texte
                try:
                    # Essayer différentes polices
                    fonts_to_try = [
                        "arial.ttf",
                        "C:/Windows/Fonts/arial.ttf",
                        "/System/Library/Fonts/Helvetica.ttc",
                    ]
                    font = None
                    for font_path in fonts_to_try:
                        try:
                            font = ImageFont.truetype(font_path, 60)
                            break
                        except:
                            continue

                    if font is None:
                        font = ImageFont.load_default()

                except:
                    font = ImageFont.load_default()

                # Ajouter le nom
                teacher_name = getattr(settings, "teacher_name", "Professeur")
                draw.text(
                    (360, 640),
                    teacher_name,
                    fill=(255, 255, 255),
                    font=font,
                    anchor="mm",
                )

        except Exception as e:
            logger.error(f"Erreur chargement image: {e}")
            # Image de secours simple
            img = Image.new("RGB", (720, 1280), color=(41, 128, 185))

        # Redimensionner
        img_resized = img.resize((720, 1280), Image.Resampling.LANCZOS)

        # DOUBLE VÉRIFICATION: Toujours convertir en RGB
        if img_resized.mode != "RGB":
            img_resized = img_resized.convert("RGB")

        # Sauvegarder temporairement
        temp_img_path = self.video_output_dir / "temp_image_streamlit.jpg"

        # FORCER l'enregistrement en JPEG avec qualité élevée
        img_resized.save(temp_img_path, "JPEG", quality=95, optimize=True)

        # Créer le clip
        clip = ImageClip(str(temp_img_path), duration=duration)

        # Effet de zoom subtil
        def zoom_effect(t):
            zoom = 1.0 + 0.01 * np.sin(t * 0.3)  # Réduit l'effet
            return zoom

        # Appliquer l'effet
        try:
            clip = clip.resize(zoom_effect)
        except:
            # Si l'effet échoue, garder le clip tel quel
            pass

        return clip

    def _create_video_sync(
        self,
        audio_path: Path,
        text_response: str,
        output_path: Path,
        progress_callback=None,
    ) -> None:
        """Crée la vidéo de manière synchrone"""
        try:
            # Charger l'audio
            audio_clip = AudioFileClip(str(audio_path))
            duration = min(audio_clip.duration, 120)  # Max 2 minutes

            # Préparer l'image
            if progress_callback:
                progress_callback("Préparation de l'image...", 70)

            image_clip = self._prepare_image_clip(duration)

            # Combiner
            video_clip = image_clip.set_audio(audio_clip)

            # Ajouter des sous-titres pour les réponses courtes
            if len(text_response.split()) < 60 and progress_callback:
                progress_callback("Ajout des sous-titres...", 80)

                subtitle = self._create_subtitle(
                    text_response, duration, video_clip.size
                )
                if subtitle:
                    video_clip = CompositeVideoClip([video_clip, subtitle])

            # Exporter
            if progress_callback:
                progress_callback("Exportation de la vidéo...", 90)

            # Paramètres d'export optimisés
            video_clip.write_videofile(
                str(output_path),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                preset="fast",
                threads=4,
                verbose=False,
                logger=None,
                ffmpeg_params=["-crf", "23"],  # Qualité équilibrée
            )

            # Nettoyer
            video_clip.close()
            audio_clip.close()

            # Supprimer l'image temporaire
            temp_img = self.video_output_dir / "temp_image_streamlit.jpg"
            if temp_img.exists():
                temp_img.unlink()

        except Exception as e:
            logger.error(f"Erreur création vidéo: {e}")
            raise

    def _create_subtitle(self, text: str, duration: float, video_size: tuple):
        """Crée des sous-titres"""
        try:
            # Limiter la longueur
            words = text.split()
            if len(words) > 30:  # Réduit pour plus de lisibilité
                text = " ".join(words[:30]) + "..."

            txt_clip = TextClip(
                text,
                fontsize=26,  # Légèrement réduit
                color="white",
                font="Arial-Bold",
                stroke_color="black",
                stroke_width=1,
                size=(video_size[0] * 0.8, None),  # Largeur réduite
                method="caption",
                align="center",
                interline=2,  # Espacement entre lignes
            )

            # Position en bas avec marge
            txt_clip = txt_clip.set_position(("center", "bottom-120"))
            txt_clip = txt_clip.set_duration(duration)

            return txt_clip

        except Exception as e:
            logger.warning(f"Impossible de créer sous-titre: {e}")
            return None

    def _generate_with_elevenlabs_sync(self, text: str, output_path: Path) -> bool:
        """Version synchrone pour ElevenLabs"""
        if not self.elevenlabs_client:
            return False

        try:
            # Limiter la longueur
            max_chars = 2500  # Réduit pour plus de rapidité
            if len(text) > max_chars:
                text = text[:max_chars] + "... (suite disponible dans le texte)"

            # Récupérer l'ID de voix
            voice_id = getattr(settings, "elevenlabs_voice_id", None)
            if not voice_id:
                # Liste de voix par défaut françaises
                default_voices = ["Rachel", "Bella", "Antoni"]
                voice_id = default_voices[0]

            # Générer
            audio = self.elevenlabs_client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                voice_settings={
                    "stability": 0.7,
                    "similarity_boost": 0.9,
                    "style": 0.8,
                },
            )

            # Sauvegarder
            with open(output_path, "wb") as f:
                for chunk in audio:
                    if chunk:
                        f.write(chunk)

            return True

        except Exception as e:
            logger.error(f"Erreur ElevenLabs: {e}")
            return False

    def _generate_with_openai_sync(self, text: str, output_path: Path) -> bool:
        """Version synchrone pour OpenAI TTS"""
        try:
            max_chars = 3000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."

            voice = getattr(settings, "openai_voice", "onyx")

            response = self.openai_client.audio.speech.create(
                model="tts-1", voice=voice, input=text, speed=1.0
            )

            response.stream_to_file(str(output_path))
            return True

        except Exception as e:
            logger.error(f"Erreur OpenAI TTS: {e}")
            return False

    def _prepare_text_for_audio(self, text: str) -> str:
        """Adapte le texte pour la synthèse vocale"""
        import re

        # Remplacer les abréviations
        replacements = {
            "NLP": "Natural Language Processing",
            "ML": "Machine Learning",
            "AI": "Intelligence Artificielle",
            "DL": "Deep Learning",
            "RNN": "réseau neuronal récurrent",
            "CNN": "réseau neuronal convolutionnel",
            "LSTM": "L S T M",
            "BERT": "B E R T",
            "GPT": "G P T",
            "TF-IDF": "T F I D F",
        }

        for abbr, full in replacements.items():
            text = text.replace(abbr, f" {full} ")

        # Nettoyer
        text = re.sub(r"\s+", " ", text).strip()

        # Ajouter une introduction
        intro = "Bonjour, voici la réponse à votre question. "
        return intro + text

    def _generate_video_filename(self, question: str) -> str:
        """Génère un nom de fichier unique"""
        import hashlib
        import time

        content = f"{question}_{time.time()}"
        hash_str = hashlib.md5(content.encode()).hexdigest()[:8]

        # Nom lisible
        import re

        safe_question = re.sub(r"[^\w\s-]", "", question[:15])
        safe_question = safe_question.replace(" ", "_").lower()

        return f"response_{safe_question}_{hash_str}.mp4"

    def cleanup_temp_files(self):
        """Nettoie les fichiers temporaires"""
        import time

        current_time = time.time()

        # Nettoyer les vidéos de plus de 6h
        for video_file in self.video_output_dir.glob("*.mp4"):
            if video_file.name.startswith("response_"):
                file_age = current_time - video_file.stat().st_mtime
                if file_age > 6 * 3600:  # 6 heures
                    try:
                        video_file.unlink()
                        logger.info(f"Vidéo nettoyée: {video_file.name}")
                    except Exception as e:
                        logger.error(f"Erreur nettoyage: {e}")

        # Nettoyer le dossier temp
        temp_dir = self.video_output_dir / "temp"
        if temp_dir.exists():
            for temp_file in temp_dir.glob("*"):
                try:
                    temp_file.unlink()
                except:
                    pass
