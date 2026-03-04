import logging
from pathlib import Path
from typing import Any, Dict, Optional

from llama_teacher.retriever import ChatEngineManager
from llama_teacher.video_generator import VideoResponseGenerator

logger = logging.getLogger(__name__)


class RAGVideoService:
    """Service unifié RAG + Vidéo"""

    def __init__(self):
        self.rag_manager = ChatEngineManager()
        self.video_generator = VideoResponseGenerator()
        self.chat_engine = self.rag_manager.get_chat_engine()

    async def query_with_video(
        self,
        question: str,
        generate_video: bool = False,
        use_my_voice: bool = True,
        user_id: Optional[str] = None,
        stream_callback=None,
    ) -> Dict[str, Any]:
        """
        Traite une requête avec option de réponse vidéo

        Args:
            question: Question de l'utilisateur
            generate_video: Générer une réponse vidéo
            use_my_voice: Utiliser votre voix personnelle (si configurée)
            user_id: ID de l'utilisateur
            stream_callback: Callback pour streaming texte

        Returns:
            Dictionnaire avec réponse et métadonnées
        """
        # Dictionnaire de résultat
        result = {
            "question": question,
            "text_response": "",
            "sources": [],
            "video_generated": False,
            "video_path": None,
            "video_url": None,
            "metadata": {"user_id": user_id},
        }

        try:
            # Étape 1: Obtenir la réponse du RAG
            logger.info(f"Traitement de la question: {question[:50]}...")

            if stream_callback:
                # Mode streaming
                streaming_response = self.chat_engine.stream_chat(question)

                response_text = ""
                for token in streaming_response.response_gen:
                    response_text += token
                    if stream_callback:
                        stream_callback(token)

                result["text_response"] = response_text

                # Extraire les sources
                if hasattr(streaming_response, "source_nodes"):
                    result["sources"] = self._extract_sources(
                        streaming_response.source_nodes
                    )

            else:
                # Mode normal
                response = self.chat_engine.chat(question)
                result["text_response"] = str(response)

                if hasattr(response, "source_nodes"):
                    result["sources"] = self._extract_sources(response.source_nodes)

            # Étape 2: Générer la vidéo si demandé
            if generate_video and result["text_response"]:
                logger.info("Génération de la réponse vidéo...")

                video_path = await self.video_generator.generate_video_response(
                    text_response=result["text_response"],
                    question=question,
                    metadata={"user_id": user_id},
                    use_my_voice=use_my_voice,
                )

                if video_path:
                    result["video_generated"] = True
                    result["video_path"] = str(video_path)
                    result["video_url"] = f"/api/videos/{video_path.name}"
                    logger.info(f"Vidéo générée: {video_path.name}")
                else:
                    logger.warning("La génération vidéo a échoué")

            return result

        except Exception as e:
            logger.error(f"Erreur dans query_with_video: {str(e)}", exc_info=True)
            result["error"] = str(e)
            return result

    def _extract_sources(self, source_nodes) -> list:
        """Extrait les sources du RAG"""
        sources = []
        for node in source_nodes[:3]:  # Limiter à 3 sources
            source_info = {
                "text": node.node.text[:150] + "..."
                if len(node.node.text) > 150
                else node.node.text,
                "score": float(node.score) if hasattr(node, "score") else 0.0,
            }

            # Ajouter les métadonnées si disponibles
            if hasattr(node.node, "metadata"):
                source_info["metadata"] = dict(node.node.metadata)

            sources.append(source_info)

        return sources

    async def test_voice_generation(self, text: str = None) -> Dict[str, Any]:
        """Teste la génération de votre voix"""
        test_text = (
            text
            or "Bonjour, ceci est un test de ma voix synthétisée pour le cours de NLP."
        )

        try:
            # Générer un audio test
            temp_dir = Path("generated_videos/temp")
            temp_dir.mkdir(exist_ok=True)
            audio_path = temp_dir / "test_voice.mp3"

            # Essayer ElevenLabs d'abord
            success = False
            if hasattr(self.video_generator, "_generate_with_elevenlabs"):
                success = await self.video_generator._generate_with_elevenlabs(
                    test_text, audio_path
                )

            # Fallback OpenAI
            if not success:
                success = await self.video_generator._generate_with_openai(
                    test_text, audio_path
                )

            if success and audio_path.exists():
                return {
                    "success": True,
                    "message": "Test audio généré avec succès",
                    "audio_path": str(audio_path),
                    "audio_url": f"/api/videos/temp/{audio_path.name}",
                }
            else:
                return {"success": False, "message": "Échec de la génération audio"}

        except Exception as e:
            return {"success": False, "message": f"Erreur: {str(e)}"}
