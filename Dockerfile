FROM python:3.11-slim

# Définition du dossier de travail
WORKDIR /app

# Installation des dépendances (séparé pour profiter du cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de TOUT le dossier actuel vers /app
# Cela inclut app.py ET le dossier rag/ avec tout son contenu
COPY . .

# On expose le port de Gradio
EXPOSE 7860

# On lance l'app
CMD ["python", "app.py"]