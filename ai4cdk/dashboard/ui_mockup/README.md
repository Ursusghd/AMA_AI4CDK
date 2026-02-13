AI4CKD UI Mockup
=================

Preview the static HTML/CSS mockup or the Streamlit preview.

Quick preview (Streamlit):

```bash
streamlit run dashboard/src/ui_mockup.py --server.port=8502
```

Use the sidebar `Thème` control in the Streamlit preview to toggle `light` / `dark`.

Files:
- `index.html` — maquette statique (HTML + link vers `styles.css`)
- `styles.css` — styles principaux
- `dashboard/src/ui_mockup.py` — Streamlit wrapper qui inline le CSS et affiche la maquette

# UI mockup — AI4CKD

Fichiers de maquette pour l'interface AI4CKD (HTML + CSS) et un aperçu Streamlit.

Prévisualiser:

1. Ouvrir le HTML directement dans un navigateur :

```bash
# depuis le dossier dashboard/ui_mockup
start index.html   # Windows
# ou ouvrir index.html dans votre navigateur
```

2. Aperçu Streamlit (préféré pour visualiser depuis le projet):

```bash
streamlit run dashboard/src/ui_mockup.py --server.port=8502
```

Notes:
- Palette: bleu médical profond, accents vert/orange/rouge pour les catégories de risque.
- Cette maquette est statique : les contrôles d'input sont visuels et non connectés au modèle.
- Pour une version interactive, intégrer les composants HTML dans `st.form` ou reconstruire en composants Streamlit.
