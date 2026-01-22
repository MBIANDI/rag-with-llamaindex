# Utiliser une image Python légère
FROM python:3.11-slim

# Configuration de Python et Poetry
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système et Poetry
RUN apt-get update && apt-get install -y curl build-essential \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean

# Ajouter Poetry au PATH
ENV PATH="/root/.local/bin:$PATH"

# Copier uniquement les fichiers de configuration Poetry
COPY pyproject.toml poetry.lock* ./

# Installer les dépendances (sans les dépendances de dev)
RUN poetry install --no-root --only main

# Copier le reste du code source
COPY . .
RUN poetry install --only main
# Créer les dossiers nécessaires
RUN mkdir -p data chroma_db user_data

# Exposer le port Streamlit
EXPOSE 8501

# Lancer l'application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
