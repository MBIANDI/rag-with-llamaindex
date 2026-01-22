# 🎓 Assistant de cours NLP (TutorAI)

[![Python CI](https://github.com/MBIANDI/rag-with-llamaindex/actions/workflows/ci.yml/badge.svg)](https://github.com/MBIANDI/rag-with-llamaindex/actions)

Un agent IA avancé conçu pour assister les enseignants dans la gestion des questions des étudiants et la fourniture de ressources pédagogiques pertinentes.

## 🎯 Vue d'ensemble

L'Assistant Enseignant Intelligent est une application basée sur LLamma_index et Streamlit qui combine :
- **Un modèle de langage conversationnel** pour générer des réponses adaptées
- **Une base de données vectorielle** pour retrouver les documents pertinents
- **Une mémoire conversationnelle** pour maintenir le contexte des discussions
- **Une interface web intuitive** pour faciliter l'interaction

Cette application est particulièrement adaptée pour :
- Répondre aux questions des étudiants sur les matériaux du cours
- Fournir des explications et des clarifications
- Maintenir un contexte de conversation cohérent

## Architecture du Projet

```
rag-with-llamaindex/
├── app.py                 # Application principale
├── pyproject.toml         # Configuration du projet
├── .env                   # Variables d'environnement
├── .pre-commit-config.yaml # Configuration pre-commit
│
├── src/                   # Code source principal
│   ├── config.py          # Configuration de l'application
│   └── llama_teacher/     # Module principal RAG
│       ├── __init__.py
│       ├── prompt.py      # Gestion des prompts
│       ├── retriever.py   # Logique de récupération (RAG)
│       └── __pycache__/
│
├── chroma_db/             # Base de données vectorielle Chroma
│   ├── default__vector_store.json
│   ├── docstore.json
│   ├── graph_store.json
│   ├── image__vector_store.json
│   └── index_store.json
│
├── data/                  # Données sources
├── user_data/             # Données utilisateur
│
├── .github/
│   └── workflows/
│       └── ci.yml         # Pipeline CI/CD
│
├── LICENSE                # Licence CC0
└── README.md              # Ce fichier
```

## 📦 Prérequis

- Python 3.11+
- pip ou Poetry
- Une clé API OpenAI (pour GPT-4o mini)

## 🚀 Installation

### Avec Poetry

```bash
# Cloner le repository
git clone <repository_url>
cd intelligent-teacher-assistant

# Installer les dépendances
poetry install
poetry build
poetry shell
```


## ⚙️ Configuration

### Variables d'environnement

Créer un fichier `.env` à la racine du projet :

```env
OPENAI_API_KEY=votre_clé_api_openai
```


## Structure des Modules

### `src/config.py`
Configuration centralisée de l'application.
Modifier `src/config.py` pour ajuster :

- `CHUNK_SIZE` : Taille des segments (défaut: 1000)
- `CHUNK_OVERLAP` : Chevauchement entre segments (défaut: 200)
- `EMBEDDING_MODEL` : Modèle d'embedding (défaut: `sentence-transformers/all-MiniLM-L6-v2`)
- `TEMPERATURE` : Paramètre de créativité du LLM (défaut: 1.0)

Configuration centralisée de l'application.

### `src/llama_teacher/`
Module principal contenant la logique RAG :
- **`prompt.py`** : Gestion et construction des prompts
- **`retriever.py`** : Récupération de documents et augmentation du contexte

### `chroma_db/`
Stockage persistant des embeddings et des documents avec Chroma.

### Organisation des données

Placer les fichiers PDF dans le dossier `data/` :

```
data/
├── cours_1.pdf
├── cours_2.pdf
└── ressources.pdf
```
Ajouter une photo à la racine et renseignez le nom dans les configs.

## 🔍 Cas d'usage

- **Tutoring automatisé** : Répondre 24/7 aux questions des étudiants
- **Complément pédagogique** : Expliquer les concepts du cours
- **Support étudiant** : Fournir des clarifications rapides
- **Feedback personnalisé** : Adapter les réponses au contexte de la conversation

## 🐛 Dépannage

### Le modèle ne charge pas
- Vérifier la clé API OpenAI dans le fichier `.env`
- S'assurer que la clé a les bonnes permissions

### Pas de résultats de recherche
- Vérifier que les fichiers PDF sont dans le dossier `data/`
- Vérifier que la base de données Chroma a été initialisée
- Augmenter `CHUNK_OVERLAP` pour plus de flexibilité

### Problèmes de mémoire
- Réduire `CHUNK_SIZE` pour des segments plus petits
- Réduire le nombre de documents traités
- Augmenter l'allocation de mémoire RAM

## 📝 Licence

Voir le fichier [LICENSE](LICENSE) pour les détails.

## 👤 Auteurs

- **MBIA NDI Marie Thérèse** - Créatrice principale
  - Email: [mbialaura12@gmail.com](mailto:mbialaura12@gmail.com)

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le repository
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📞 Support

Pour toute question ou problème, veuillez :
- Ouvrir une issue sur GitHub
- Envoyer un email à [mbialaura12@gmail.com](mailto:mbialaura12@gmail.com)
