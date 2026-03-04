import time
from pathlib import Path

import streamlit as st
from PIL import Image

from llama_teacher.retriever import ChatEngineManager
from llama_teacher.video_generator import StreamlitVideoGenerator
from src.config import settings

# Configuration de la page
st.set_page_config(
    page_title=settings.course_title,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personnalisé
st.markdown(
    """
<style>
    .stVideo {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 20px 0;
    }
    .video-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin: 20px 0;
    }
    .progress-container {
        padding: 20px;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin: 20px 0;
    }
    .success-message {
        padding: 15px;
        background-color: #d4edda;
        color: #155724;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- SIDEBAR ---
with st.sidebar:
    # Informations école et prof
    st.markdown(f"## 🏫 {settings.school_name}")
    st.markdown(f"### {settings.course_title}")

    # Photo de profil
    photo_path = Path(settings.teacher_photo)
    if photo_path.exists():
        image = Image.open(photo_path)
        st.image(image, width=180, caption=settings.teacher_name)
    else:
        st.warning("⚠️ Photo du professeur non trouvée.")
        st.markdown(f"**Professeur :** {settings.teacher_name}")

    st.markdown("---")

    # Description
    st.markdown(
        f"""
    **📚 Objectif :** {settings.chat_objective}

    **🎯 Fonctionnalités :**
    - Réponses basées sur vos documents
    - Références aux sources
    - Option réponse vidéo
    """
    )

    st.markdown("---")

    # --- PARAMÈTRES ---
    st.markdown("### ⚙️ Paramètres")

    # Température
    temp = st.slider(
        "Précision vs Créativité",
        0.0,
        1.0,
        settings.temperature,
        help="0 = plus précis, 1 = plus créatif",
    )

    # Option vidéo
    # enable_video = st.checkbox(
    #     "Activer les réponses vidéo",
    #     value=settings.enable_video_response,
    #     help="Générer une réponse vidéo avec ma voix"
    # )
    enable_video = True

    if enable_video:
        use_my_voice = st.checkbox(
            "Utiliser ma voix personnelle",
            value=False,
            help="Utiliser ma voix synthétisée (nécessite ElevenLabs)",
        )

        video_quality = st.select_slider(
            "Qualité vidéo",
            options=["Rapide", "Équilibré", "Haute qualité"],
            value="Rapide",
        )

    st.markdown("---")

    # Boutons d'action
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Effacer la discussion", use_container_width=True):
            if "chat_engine" in st.session_state:
                st.session_state.chat_engine.reset()
            st.session_state.messages = []
            st.rerun()

    with col2:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.rerun()


# --- EN-TÊTE PRINCIPAL ---
st.markdown(
    f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2)'>
        <h1 style='color:white; text-align:center; margin-bottom: 10px;'>
            🎓 {settings.app_title}
        </h1>
        <h3 style='color:#e0e0e0; text-align:center;'>
            {settings.school_name} • Année {settings.annee_universitaire}
        </h3>
    </div>
""",
    unsafe_allow_html=True,
)


# --- INITIALISATION ---
@st.cache_resource
def init_rag_engine():
    """Initialise le moteur RAG"""
    return ChatEngineManager()


@st.cache_resource
def init_video_generator():
    """Initialise le générateur vidéo"""
    return StreamlitVideoGenerator()


# Initialisation
engine_manager = init_rag_engine()
video_generator = init_video_generator()

# Chat engine dans la session
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = engine_manager.get_chat_engine()

# Messages dans la session
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"""
            👋 Bonjour ! Je suis votre assistant pour le cours **{settings.course_title}**.

            Je peux :
            📚 Répondre à vos questions basées sur les documents du cours
            🎥 Générer des réponses vidéo avec la voix de {settings.teacher_name}
            🔍 Vous montrer les sources utilisées

            Posez-moi votre première question !
            """,
        }
    ]

# --- AFFICHAGE DE L'HISTORIQUE ---
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Afficher la vidéo si elle existe dans le message
        if "video_path" in message and message["video_path"]:
            video_path = Path(message["video_path"])
            if video_path.exists():
                st.markdown("---")
                st.markdown("### 🎥 Réponse vidéo")
                with open(video_path, "rb") as f:
                    video_bytes = f.read()
                st.video(video_bytes)

                # Bouton de téléchargement
                st.download_button(
                    label="📥 Télécharger la vidéo",
                    data=video_bytes,
                    file_name=video_path.name,
                    mime="video/mp4",
                )

# --- ZONE DE SAISIE ---
prompt = st.chat_input(f"💭 Posez votre question sur {settings.course_title}...")

if prompt:
    # Ajouter le message de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Préparer la réponse
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # Étape 1: Recherche RAG
        with st.status(
            "🔍 Recherche dans les supports de cours...", expanded=True
        ) as status:
            try:
                # Obtenir la réponse du RAG
                response = st.session_state.chat_engine.chat(prompt)
                response_text = str(response)

                # Afficher progressivement
                full_response = ""
                for word in response_text.split():
                    full_response += word + " "
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.02)

                message_placeholder.markdown(full_response)

                # Métadonnées
                status.update(
                    label="✅ Réponse trouvée !", state="complete", expanded=False
                )

            except Exception as e:
                st.error(f"Erreur lors de la recherche: {str(e)}")
                # return

        # Étape 2: Génération vidéo (si activé)
        video_path = None
        if (
            enable_video and len(response_text) > 50
        ):  # Seulement si la réponse est assez longue
            st.markdown("---")

            with st.expander("🎥 Générer une réponse vidéo", expanded=True):
                col1, col2 = st.columns([1, 3])

                # with col1:
                #     generate_video = st.button(
                #         "▶️ Générer la vidéo",
                #         type="primary",
                #         help="Créer une réponse vidéo avec ma voix"
                #     )

                # with col2:
                #     st.info(f"Durée estimée : 30-60 secondes")
                generate_video = True
                if generate_video:
                    # Barre de progression
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Callback pour la progression
                    def update_progress(message, percent):
                        status_text.text(message)
                        progress_bar.progress(percent / 100)

                    # Générer la vidéo
                    try:
                        video_path = video_generator.generate_video_response(
                            text_response=response_text,
                            question=prompt,
                            use_my_voice=use_my_voice,
                            progress_callback=update_progress,
                        )

                        if video_path and video_path.exists():
                            # Afficher la vidéo
                            st.success("✅ Vidéo générée avec succès !")

                            with open(video_path, "rb") as f:
                                video_bytes = f.read()

                            # Lecture de la vidéo
                            st.video(video_bytes)

                            # Bouton de téléchargement
                            col_dl1, col_dl2 = st.columns(2)
                            with col_dl1:
                                st.download_button(
                                    label="📥 Télécharger la vidéo",
                                    data=video_bytes,
                                    file_name=video_path.name,
                                    mime="video/mp4",
                                    use_container_width=True,
                                )

                            with col_dl2:
                                if st.button("♻️ Regénérer", use_container_width=True):
                                    # Supprimer et regénérer
                                    video_path.unlink(missing_ok=True)
                                    st.rerun()

                            # Ajouter le chemin à la réponse
                            response_info = {"video_path": str(video_path)}
                        else:
                            st.warning(
                                "⚠️ La génération vidéo a échoué. Vérifiez les logs."
                            )

                    except Exception as e:
                        st.error(f"❌ Erreur lors de la génération vidéo: {str(e)}")

        # Étape 3: Afficher les métadonnées
        with st.expander("📊 Détails de la recherche", expanded=False):
            # Scores de confiance
            if hasattr(response, "source_nodes") and response.source_nodes:
                scores = [
                    node.score
                    for node in response.source_nodes
                    if node.score is not None
                ]

                if scores:
                    avg_score = sum(scores) / len(scores)
                    col_metric1, col_metric2 = st.columns(2)

                    with col_metric1:
                        st.metric(
                            "Confiance moyenne",
                            f"{avg_score:.1%}",
                            help="Score moyen de similarité avec les documents",
                        )

                    with col_metric2:
                        st.metric(
                            "Sources utilisées",
                            len(response.source_nodes),
                            help="Nombre de documents référencés",
                        )

                # Détails des sources
                st.markdown("### 📚 Sources utilisées")

                for i, node in enumerate(response.source_nodes[:3]):  # Limiter à 3
                    with st.container():
                        col_s1, col_s2 = st.columns([1, 4])

                        with col_s1:
                            score = node.score if node.score else "N/A"
                            if isinstance(score, float):
                                st.metric(f"Source {i+1}", f"{score:.1%}")
                            else:
                                st.metric(f"Source {i+1}", str(score))

                        with col_s2:
                            # Nom du fichier
                            file_name = node.metadata.get(
                                "file_name", "Document inconnu"
                            )
                            st.markdown(f"**📄 {file_name}**")

                            # Extrait
                            excerpt = (
                                node.text[:250] + "..."
                                if len(node.text) > 250
                                else node.text
                            )
                            st.markdown(f"```\n{excerpt}\n```")

                        st.divider()
            else:
                st.info("ℹ️ Aucune source spécifique identifiée (recherche générale)")

        # Étape 4: Boutons de feedback
        st.markdown("---")
        col_fb1, col_fb2, col_fb3 = st.columns([1, 1, 4])

        with col_fb1:
            if st.button("👍 Utile", use_container_width=True):
                st.toast("Merci pour votre retour positif !", icon="✅")
                # Ici, vous pourriez enregistrer ce feedback

        with col_fb2:
            if st.button("👎 À améliorer", use_container_width=True):
                st.toast("Merci pour votre retour. Je vais m'améliorer !", icon="📝")
                # Ici, vous pourriez enregistrer ce feedback

        # Enregistrer la réponse dans l'historique
        response_data = {
            "role": "assistant",
            "content": response_text,
        }

        # Ajouter le chemin vidéo si généré
        if video_path:
            response_data["video_path"] = str(video_path)

        st.session_state.messages.append(response_data)

# --- PIED DE PAGE ---
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown(f"**Enseignant :** {settings.teacher_name}")

with footer_col2:
    st.markdown(f"**Cours :** {settings.course_title}")

with footer_col3:
    st.markdown(f"**Année :** {settings.annee_universitaire}")

# --- SCRIPT DE NETTOYAGE AUTOMATIQUE ---
# Nettoyer les anciennes vidéos au démarrage
if "cleaned_videos" not in st.session_state:
    try:
        video_generator.clear_old_videos(max_age_hours=6)  # Garder 6h
        st.session_state.cleaned_videos = True
    except Exception as e:
        print(f"Erreur nettoyage vidéos: {e}")
