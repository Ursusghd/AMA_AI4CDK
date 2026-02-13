import os
import pandas as pd
import numpy as np
import requests
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns
import re
import warnings
import joblib
from catboost import CatBoostClassifier
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.preprocessing import LabelEncoder, RobustScaler
from imblearn.over_sampling import ADASYN, SMOTE
from imblearn.combine import SMOTETomek
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.model_selection import learning_curve
from sklearn.inspection import permutation_importance

warnings.filterwarnings('ignore')

# --- Configuration ---
RESULTS_DIR = "./results"
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

def train_optimized_pipeline_local():
    print("--- Step 1: Data Acquisition ---")
    # Utilisation de data_drive.csv local s'il existe, sinon téléchargement
    csv_local = "data_drive.csv"
    
    if os.path.exists(csv_local):
        print(f"Loading local file: {csv_local}")
        df = pd.read_csv(csv_local, low_memory=False)
    else:
        print("Local file not found, downloading from Google Sheets...")
        sheet_id = "1a4iZPf93nLejpL7d7LYnF9JliV10etsJS8ia-bw1MXg"
        gid = "356971483"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.content.decode('utf-8')), low_memory=False)
    
    print(f"Loaded {len(df)} rows.")

    # --- Preprocessing Helpers ---
    def clean_binary(val):
        if pd.isna(val): return 0
        s = str(val).strip().lower()
        if s in ['oui', 'yes', 'true', '1', 'positive', 'positif', 'présent', 'present']: return 1
        if s in ['non', 'no', 'false', '0', 'negative', 'negatif', 'absent']: return 0
        return 0

    def clean_numeric(val):
        if pd.isna(val): return np.nan
        val = str(val).strip().replace(',', '.')
        val = re.sub(r'[^\d.-]', '', val)
        try: return float(val) if val else np.nan
        except: return np.nan

    # --- Target Preparation ---
    target_col = "Stage de l'IRC"
    df = df.dropna(subset=[target_col]).copy()
    df = df[df[target_col] != '0%']
    
    def map_target(val):
        s = str(val).strip().upper()
        if '3A' in s: return 'G3A'
        if '3B' in s: return 'G3B'
        if '1' in s: return 'G1'
        if '2' in s: return 'G2'
        if '4' in s: return 'G4'
        if '5' in s: return 'G5'
        return s
    df['Target'] = df[target_col].apply(map_target)

    # --- Feature Engineering ---
    print("--- Step 2: Extracting Medical Intelligence v2 ---")
    data = df.copy()
    data.columns = [c.strip() for c in data.columns]

    def get_col_safe(df, col_name, default_val=0):
        if col_name in df.columns:
            return df[col_name]
        return pd.Series([default_val] * len(df), index=df.index)

    def impute_by_target(df, col):
        if col not in df.columns: return
        df[col] = df[col].apply(clean_numeric)
        df[col] = df.groupby('Target')[col].transform(lambda x: x.fillna(x.median()))
        df[col] = df[col].fillna(df[col].median())

    num_cols = ['Age', 'Créatinine (mg/L)', 'Urée (g/L)', 'Hb (g/dL)', 'TA (mmHg)/Systole', 'TA (mmHg)/Diastole', 'Poids (Kg)', 'Taille (m)', 'K^+ (meq/L)']
    for c in num_cols: impute_by_target(data, c)

    # Echographie
    def check_atrophy(row):
        rg = str(row.get('Grosseur Rein Gauche', '')).lower()
        rd = str(row.get('Grosseur Rein Droit', '')).lower()
        for term in ['petit', 'réduit', 'reduit', 'atrophie']:
            if term in rg or term in rd: return 1
        return 0
    data['Atrophie_Renale'] = data.apply(check_atrophy, axis=1)
    
    col_diff = 'DiffÃ©renciation des reins' # Adaptation encoding CSV si besoin
    if col_diff not in data.columns:
        col_diff = [c for c in data.columns if 'Diff' in c and 'renciation' in c][0]
        
    data['Index_Differenciation'] = data[col_diff].apply(lambda x: 1 if any(t in str(x).lower() for t in ['mauvaise', 'absente']) else 0)
    
    data['Presence_Kyste_Calcul'] = ((get_col_safe(data, 'Kyste').apply(clean_binary) == 1) | 
                                    (get_col_safe(data, 'Calcul RÃ©nal').apply(clean_binary) == 1)).astype(int)
    
    data['Score_Echo_Total'] = data['Atrophie_Renale'] + data['Index_Differenciation'] + data['Presence_Kyste_Calcul']

    # Syndromes
    data['Syndrome_Anemique'] = ((data['Hb (g/dL)'] < 10).astype(int) + get_col_safe(data, 'AnÃ©mie').apply(clean_binary)).clip(0, 1)
    data['Surcharge_Hydrosodee'] = 0
    for c in ['OMI', 'Bouffissure du Visage', 'RÃ¢les crÃ©pitants']:
        if c in data.columns: data['Surcharge_Hydrosodee'] += data[c].apply(clean_binary)

    # Ratios
    data['Ratio_K_Hb'] = data['K^+ (meq/L)'] / (data['Hb (g/dL)'] + 0.1)
    data['Ratio_Uree_Creat'] = data['Urée (g/L)'] / (data['Créatinine (mg/L)'] / 10.0 + 0.1)
    
    # Clairance Cockcroft
    def calc_cockcroft(row):
        try:
            age = float(row['Age'])
            poids = float(row['Poids (Kg)'])
            creat_mg_dl = float(row['Créatinine (mg/L)']) / 10.0
            sexe = str(row.get('Sexe', 'M')).upper()
            if creat_mg_dl <= 0.1: return 120
            cl_cr = ((140 - age) * poids) / (72 * creat_mg_dl)
            if 'F' in sexe: cl_cr *= 0.85
            return cl_cr
        except: return 70
    data['Clairance_Cockcroft'] = data.apply(calc_cockcroft, axis=1)

    # CKD-EPI 2021
    def calc_epi(row):
        cr = row['Créatinine (mg/L)'] / 10.0
        if cr <= 0: cr = 0.9
        age = row['Age']
        sex_m = 1 if 'M' in str(row.get('Sexe', 'M')) else 0
        if sex_m:
            return 142 * (min(cr/0.9, 1)**-0.302) * (max(cr/0.9, 1)**-1.2) * (0.9938**age) * 1.012
        else:
            return 142 * (min(cr/0.7, 1)**-0.241) * (max(cr/0.7, 1)**-1.2) * (0.9938**age) * 0.9938
    data['eDFG_CKD_EPI'] = data.apply(calc_epi, axis=1)

    data['Gap_Formules'] = data['eDFG_CKD_EPI'] - data['Clairance_Cockcroft']
    data['Score_Surcharge_Bio'] = ((data['K^+ (meq/L)'] > 5.0).astype(int) + (data['Urée (g/L)'] > 1.5).astype(int) + data['Surcharge_Hydrosodee'])
    data['Pression_Pulsee'] = data['TA (mmHg)/Systole'] - data['TA (mmHg)/Diastole']
    
    h_m = np.where(data['Taille (m)'] > 3, data['Taille (m)'] / 100.0, data['Taille (m)'])
    data['IMC'] = data['Poids (Kg)'] / (h_m**2 + 0.1)

    # Interactions
    data['Interaction_eDFG_Hb'] = data['eDFG_CKD_EPI'] * (data['Hb (g/dL)'] + 0.1)
    data['eDFG_Norm_Age'] = data['eDFG_CKD_EPI'] / (data['Age'] + 1)
    data['Creat_Norm_Age'] = (data['Créatinine (mg/L)']/10.0) * (data['Age'] + 1) / 100.0
    data['Score_Anemie_Renale'] = (data['Hb (g/dL)'] + 0.1) * data['eDFG_CKD_EPI'] / 100.0
    data['Interaction_IMC_eDFG'] = data['IMC'] * data['eDFG_CKD_EPI'] / 100.0

    # --- Step 3: Architecture ---
    features = [
        'eDFG_CKD_EPI', 'Clairance_Cockcroft', 'Gap_Formules', 'Score_Echo_Total', 
        'Ratio_K_Hb', 'Ratio_Uree_Creat', 'Score_Surcharge_Bio',
        'Syndrome_Anemique', 'Pression_Pulsee', 'IMC', 'Age',
        'Interaction_eDFG_Hb', 'eDFG_Norm_Age', 'Creat_Norm_Age', 
        'Score_Anemie_Renale', 'Interaction_IMC_eDFG'
    ]
    
    X = data[features].fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(data['Target'])

    # SMOTE-Tomek filtering
    mask = np.isin(y, np.where(np.bincount(y) >= 6)[0])
    X, y = X[mask], y[mask]
    y = le.fit_transform(data.loc[mask, 'Target'])

    # Class Weights
    class_counts = np.bincount(y)
    base_weights = len(y) / (len(class_counts) * class_counts)
    for cls in range(len(class_counts)//3, 2*len(class_counts)//3 + 1):
        if cls < len(base_weights): base_weights[cls] *= 1.5
    
    class_weight_dict = {i: base_weights[i] for i in range(len(base_weights))}

    # Stacking Classifier
    estimators = [
        ('cat', CatBoostClassifier(verbose=0, depth=5, iterations=600, class_weights=list(base_weights), loss_function='MultiClass')),
        ('xgb', XGBClassifier(n_estimators=250, max_depth=3, reg_lambda=50, learning_rate=0.05, eval_metric='mlogloss')),
        ('rf', RandomForestClassifier(n_estimators=600, max_depth=5, class_weight=class_weight_dict, random_state=42))
    ]
    
    stacking_model = StackingClassifier(
        estimators=estimators, 
        final_estimator=LogisticRegression(C=0.2, class_weight=class_weight_dict, max_iter=1000),
        cv=5
    )

    pipeline = ImbPipeline([
        ('scaler', RobustScaler()),
        ('smote_tomek', SMOTETomek(random_state=42, smote=SMOTE(random_state=42, k_neighbors=2))),
        ('classifier', stacking_model)
    ])

    # Training
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print("\nTraining...")
    pipeline.fit(X_train, y_train)
    
    # Results
    y_pred = pipeline.predict(X_test)
    print("\n[Validation Report]:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # Save Results
    print(f"\nSaving results to {RESULTS_DIR}...")
    
    # 1. Confusion Matrix
    fig, ax = plt.subplots(figsize=(10, 8))
    ConfusionMatrixDisplay.from_estimator(pipeline, X_test, y_test, display_labels=le.classes_, cmap='magma', normalize='true', ax=ax)
    plt.title('Normalized Confusion Matrix')
    #plt.savefig(f"{RESULTS_DIR}/confusion_matrix.png")
    
    # 2. Permutation Importance
    print("Calculating Permutation Importance...")
    perm_importance = permutation_importance(pipeline, X_test, y_test, n_repeats=10, random_state=42)
    sorted_idx = perm_importance.importances_mean.argsort()
    plt.figure(figsize=(10, 8))
    plt.barh(np.array(features)[sorted_idx], perm_importance.importances_mean[sorted_idx])
    plt.title("Permutation Importance")
    plt.tight_layout()
    #plt.savefig(f"{RESULTS_DIR}/feature_importance.png")

    # 3. Models
    #joblib.dump(pipeline, f"{RESULTS_DIR}/renal_stacking_pipeline_local.joblib")
    #joblib.dump(le, f"{RESULTS_DIR}/label_encoder_local.joblib")
    
    print("\n✅ Success! All artifacts saved locally.")

if __name__ == "__main__":
    train_optimized_pipeline_local()
