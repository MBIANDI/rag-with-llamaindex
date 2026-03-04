flowchart LR
    A[Photo de l'exercice] --> B[Vision-LLM<br>GPT-4o/Gemini];
    B -- Transcription --> C{Détection du type<br>d'exercice};
    C -- Math --> D[Agent Maths];
    C -- Grammaire --> E[Agent Français];
    C -- Histoire --> F[Agent Histoire];

    D --> G[Générateur de Pistes<br>sans donner la réponse];
    G --> H[Réponse à l'enfant];
