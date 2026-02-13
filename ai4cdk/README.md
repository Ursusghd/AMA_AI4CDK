# AI4CKD - Prédiction et Cartographie de la Maladie Rénale Chronique

AI4CKD est une application web conçue pour aider au dépistage, à la prédiction et à la priorisation des patients atteints de Maladie Rénale Chronique (CKD). Le projet combine une API de prédiction basée sur le Machine Learning et une interface web interactive.

## Fonctionnalités
- **Prédiction Individuelle** : Calcul de l'eDFG et prédiction du stade CKD via un modèle XGBoost.
- **Score de Risque SR-IRC** : Évaluation du risque de progression vers l'insuffisance rénale.
- **Cartographie** : Visualisation de la prévalence et de la sévérité par département.
- **Priorisation** : Liste triée des patients nécessitant une attention urgente.

## Installation et Lancement

### 1. Prérequis
- Python 3.10 ou supérieur
- Accès internet (pour le chargement des bibliothèques cartographiques CDN)

### 2. Configuration de l'environnement
Le projet utilise un environnement virtuel (`venv`) pour isoler les dépendances.
```powershell
# Création et activation de l'environnement (déjà fait lors du setup initial)
python -m venv venv
.\venv\Scripts\activate

# Installation des dépendances
pip install -r requirements.txt
```

### 3. Lancement du Backend (API)
L'API doit être lancée en premier car elle fournit les services de prédiction au Dashboard.
```powershell
# S'assurer que le venv est activé
.\venv\Scripts\python -m src.main
```
*L'API est configurée sur le port **8000**. Documentation Swagger disponible sur `http://localhost:8000/docs`.*

### 4. Lancement du Frontend (Dashboard HTML)
L'interface utilise des fichiers locaux (JSON, GeoJSON) et nécessite donc un serveur local.
```powershell
cd dashboard/ui_mockup
python -m http.server 8080
```
*Ouvrez votre navigateur sur : `http://localhost:8080`*

> [!NOTE]
> Le dashboard est configuré pour communiquer avec l'API sur `http://localhost:8000/predict/stage`.

## Dépannage
Si le modèle ne se charge pas (`model_loaded: false` dans `/health/`), vérifiez que les dépendances suivantes sont bien installées :
- `imbalanced-learn`
- `catboost`
- `xgboost`

Ces bibliothèques sont essentielles car le modèle de prédiction (`.joblib`) les utilise pour désérialiser le pipeline de stacking.

## Structure du Projet
- `src/` : API FastAPI (Routes, Services, Modèles).
- `src/assets/` : Artefacts du modèle ML (`renal_stacking_pipeline_v3.joblib`, `label_encoder_v3.joblib`).
- `dashboard/ui_mockup/` : Interface web et données cartographiques.
- `requirements.txt` : Dépendances Python complètes.

## Technologies Utilisées
- **Backend** : FastAPI, Pydantic, SQLAlchemy, Scikit-learn, XGBoost, CatBoost, Imbalanced-learn.
- **Frontend** : HTML5, Vanilla CSS, JavaScript, Leaflet.js, Chart.js.
