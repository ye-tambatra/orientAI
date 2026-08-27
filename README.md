# OrientIA

OrientIA est un projet d'agent conversationnel basé sur l'Intelligence Artificielle (RAG), conçu pour fournir des informations et aider à l'orientation des utilisateurs.

## Équipe du Projet

Nous sommes une équipe de 6 personnes réparties sur trois pôles d'expertise :

- **Machine Learning (Classification d'Orientation)** :
  - *Mission* : Collecte, création et prétraitement des jeux de données d'orientation. Conception et entraînement d'un modèle de classification ayant pour but de prédire et recommander le parcours ou la filière idéale pour un utilisateur en fonction de son profil et de ses compétences.
  - *Membres* :
   - RABEMANANTSIMBA Onja Faneva Rinoh                - IGGLIA5 - N 18
   - RANDIMBIARISOA Santatriniaina Charles Ricardo    - IGGLIA5 - N 46

- **Agents IA & RAG (Retrieval-Augmented Generation)** :
  - *Mission* : Création des agents conversationnels intelligents avec gestion de la mémoire contextuelle (historique des discussions). Conception du système RAG incluant la collecte, le traitement et l'indexation de documents issus de sources variées (sites web, brochures). Configuration du système de "Tool calling" (appels de fonctions) pour permettre à l'IA d'interagir dynamiquement avec la base de connaissances.
  - *Membres* :
    - NOFINIAINA NATOLOJANAHARY Tambatra Namelantsoa  - IGGLIA5 - N 03
    

- **Intégration (Frontend & Backend API)** :
  - *Mission* : Développement complet de l'interface utilisateur (Frontend) pour une expérience fluide et interactive. Conception de l'API côté serveur (Backend) et orchestration technique globale. Cette équipe s'est chargée du câblage complexe permettant de faire communiquer l'interface web avec les agents IA, le moteur RAG et le modèle de Machine Learning.
  - *Membres* :
    - ANDRIAMIALINIRINA Fanantenana                    - IGGLIA5 - N 10
    - KOLOINA RASOLOHERISON Raharisoanjatozo Nambinina - IGGLIA5 - N 34
   

## Stack Technologique

Le projet est divisé en deux parties principales : un backend (API) et un frontend (Client).

**Backend (API) :**
- **Langage :** Python
- **Framework Web :** FastAPI, Uvicorn
- **IA & Agents :** Bibliothèque `google-genai` (modèles Gemini) pour la création des agents IA, et LangChain
- **Base de données vectorielle :** ChromaDB (pour le RAG - Retrieval-Augmented Generation)

**Frontend (Client) :**
- **Langage :** TypeScript
- **Framework UI :** React (via Vite)
- **Composants UI :** Material UI (MUI)

## Comment lancer le projet en local

Voici les instructions étape par étape pour configurer et démarrer le projet sur votre machine.

### Prérequis
- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js](https://nodejs.org/en/) (avec `npm`)
- Une clé API Google Gemini valide

### 1. Configuration de l'environnement

À la racine du projet, copiez le fichier d'exemple des variables d'environnement et configurez votre clé API :

```bash
cp .env.example .env
```
Ouvrez le fichier `.env` nouvellement créé et remplacez `your-api-key-here` par votre véritable clé d'API Gemini :
```
GEMINI_API_KEY=votre_cle_api_ici
```

### 2. Démarrage du Backend (API)

Ouvrez un terminal à la racine du projet et exécutez les commandes suivantes :

1. **Créer un environnement virtuel :**
   ```bash
   python3 -m venv venv
   ```

2. **Activer l'environnement virtuel :**
   - Sur macOS/Linux :
     ```bash
     source venv/bin/activate
     ```
   - Sur Windows :
     ```bash
     venv\Scripts\activate
     ```

3. **Installer les dépendances :**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optionnel) Indexer les données :**
   Si c'est votre première exécution ou si vous avez modifié les données, vous pouvez (re)construire la base de données vectorielle :
   ```bash
   python rag/indexer.py
   ```

5. **Lancer le serveur API :**
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```
   *L'API sera disponible sur `http://localhost:8000`.*

### 3. Démarrage du Frontend (Client)

Ouvrez un **nouveau terminal**, et naviguez dans le dossier `client` depuis la racine du projet :

1. **Aller dans le dossier frontend :**
   ```bash
   cd client
   ```

2. **Installer les dépendances :**
   ```bash
   npm install
   ```

3. **Lancer le serveur de développement :**
   ```bash
   npm run dev
   ```
   *L'application web sera accessible depuis votre navigateur, généralement sur `http://localhost:5173`.*

## Utilisation
Une fois le backend et le frontend démarrés en parallèle (chacun dans son terminal), ouvrez simplement l'URL locale fournie par Vite (par exemple `http://localhost:5173`) dans votre navigateur pour commencer à discuter avec l'agent OrientIA.
