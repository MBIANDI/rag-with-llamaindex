from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# On définit la racine du projet proprement avec pathlib
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # --- MÉTADONNÉES DE L'APPLICATION ---
    course_title: str = "Traitement du Langage Naturel (NLP)"
    app_title: str = "🤖🧠🎓 TutorAI - NLP"
    school_name: str = "ISSEA"
    teacher_name: str = "Mme MBIA NDI Marie Thérèse"
    teacher_email: str = "mbialaura12@gmail.com"
    teacher_photo: str = "photo_laura.PNG"
    chat_objective: str = (
        "Répondre aux questions des étudiants sur le support de cours officiel."
    )
    annee_universitaire: str = "2025/2026"
    # --- SECRETS (Chargés depuis le .env) ---
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

    # --- CHEMINS (Basés sur PROJECT_ROOT) ---
    dat_dir: Path = PROJECT_ROOT / "data"
    db_dir: Path = PROJECT_ROOT / "chroma_db"
    user_data_dir: Path = PROJECT_ROOT / "user_data"

    # --- CONFIGURATION NLP (Valeurs par défaut communes) ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_model_name: str = "gpt-4.1-mini"
    use_openai_embeddings: bool = True

    # --- PARAMÈTRES RAG ---
    chunk_size: int = 100
    chunk_overlap: int = 20
    parent_chunk_size: int = 2000
    child_chunk_size: int = 400
    temperature: float = 1.0
    retriever_type: str = "parent"  # "standard"

    # --- PARAMÈTRES DE GÉNÉRATION DE QUESTIONS ---
    num_queries: int = 3  # Nombre de variations de questions à générer
    top_k_fusion: int = 5  # Nombre de documents finaux à garder après fusion

    # Configuration Pydantic
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


# Création de l'instance
settings = Settings()

for folder in [settings.dat_dir, settings.db_dir, settings.user_data_dir]:
    folder.mkdir(parents=True, exist_ok=True)
