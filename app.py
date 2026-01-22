import os

import streamlit as st
from PIL import Image

from llama_teacher.retriever import ChatEngineManager
from src.config import settings

st.set_page_config(page_title=settings.course_title, page_icon="🎓", layout="wide")


with st.sidebar:
    # --- INFO ÉCOLE & PROF ---
    st.markdown(f"## 🏫 {settings.school_name} - {settings.course_title}")

    # Gestion de la photo de profil
    photo_path = settings.teacher_photo
    if os.path.exists(photo_path):
        image = Image.open(photo_path)
        st.image(image, width=150, caption=settings.teacher_name)
    else:
        st.warning("⚠️ Image 'prof_photo.jpg' non trouvée.")
        st.markdown(f"**Professeur :** {settings.teacher_name}")

    st.markdown("---")
    st.markdown(
        f"""
    **Objectif du bot :** {settings.chat_objective}.
    """
    )

    # Dans la sidebar
    st.markdown("---")
    st.markdown("### ⚙️ Paramètres")
    temp = st.slider("Précision vs Créativité", 0.0, 1.0, settings.temperature)
    # Note : Il faudrait mettre à jour le chat_engine si cette valeur change

    st.markdown("---")
    if st.sidebar.button("🗑️ Effacer la discussion"):
        st.session_state.messages = []
        st.session_state.chat_engine.reset()  # Réinitialise aussi la mémoire du LLM
        st.rerun()


# En-tête personnalisé avec HTML/CSS pour un rendu "pro"
st.markdown(
    f"""
    <div style='background-color:#002b36;padding:20px;border-radius:10px;margin-bottom:20px'>
        <h1 style='color:white;text-align:center;'>{settings.app_title}</h1>
        <h3 style='color:#aeb6bf;text-align:center;'>{settings.school_name} - Année {settings.annee_universitaire}</h3>
    </div>
""",
    unsafe_allow_html=True,
)


# Initialisation persistante du moteur (grâce au cache de Streamlit)
@st.cache_resource
def init_engine():
    return ChatEngineManager()


engine_manager = init_engine()

# On stocke le chat_engine dans la session Streamlit pour garder l'historique
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = engine_manager.get_chat_engine()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Bonjour ! Je suis votre assistant de cours. Posez-moi une question sur le contenu de vos PDFs.",
        }
    ]

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Posez votre question sur le cours..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status(
            "🔍 Recherche dans les supports de cours...", expanded=False
        ) as status:
            response = st.session_state.chat_engine.chat(prompt)
            status.update(label="✅ Réponse trouvée !", state="complete", expanded=False)
        # On affiche la réponse mot par mot
        st.markdown(response)
        # st.markdown(response.response)
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("👍", key=f"up_{len(st.session_state.messages)}"):
                st.toast("Merci pour votre retour !")

        with st.expander("📊 Métadonnées de recherche"):
            # On récupère les scores des nœuds trouvés par le retriever
            scores = [
                node.score for node in response.source_nodes if node.score is not None
            ]
            if scores:
                avg_score = sum(scores) / len(scores)
                st.metric("Confiance moyenne (RAG)", f"{avg_score:.2%}")
            else:
                st.write("Aucun score disponible (recherche par mot-clé).")
            for node in response.source_nodes:
                score = round(node.score, 2) if node.score else "N/A"
                st.info(
                    f"**Document:** {node.metadata.get('file_name')} (Score: {score})\n\n**Extrait:** {node.text[:200]}..."
                )
        st.session_state.messages.append({"role": "assistant", "content": response})
