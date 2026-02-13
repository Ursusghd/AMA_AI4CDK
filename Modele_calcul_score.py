import numpy as np
import pandas as pd

# ----------------------------
# 1️⃣ Calcul eGFR CKD-EPI (Adaptation 2021)
# ----------------------------
def calculate_egfr_2021(age, sexe, creat_mg_l):
    """
    Formule CKD-EPI 2021 (sans facteur racial).
    Creative convertie de mg/L en mg/dL.
    """
    if creat_mg_l <= 0:
        return 0.0 # On ne peut pas calculer eGFR sans créatinine
        
    # Conversion mg/L -> mg/dL
    scr = creat_mg_l / 10.0
    
    if "F" in str(sexe).upper():
        kappa = 0.7
        alpha = -0.241
        sex_factor = 1.012
    else:
        kappa = 0.9
        alpha = -0.302
        sex_factor = 1.0
        
    egfr = 142 * (min(scr / kappa, 1) ** alpha) * \
           (max(scr / kappa, 1) ** -1.200) * \
           (0.9938 ** age) * sex_factor
    
    return egfr

# ----------------------------
# 2️⃣ Calcul du Score SR-IRC
# ----------------------------
def calculate_sr_irc_score(age, sexe, egfr, proteinurie_cat, diabete, hta, hb):
    """
    Score Déterministe de Risque d'Insuffisance Rénale Chronique (SR-IRC).
    Somme des points selon les variables cliniques et biologiques.
    """
    score = 0
    
    # 1. eGFR Points
    if egfr < 15: score += 20
    elif egfr < 30: score += 15
    elif egfr < 45: score += 10
    elif egfr < 60: score += 5
    else: score += 0
    
    # 2. Age Points
    if age > 75: score += 6
    elif age >= 65: score += 4
    elif age >= 50: score += 2
    else: score += 0
    
    # 3. Sexe Points
    if "M" in str(sexe).upper():
        score += 1
        
    # 4. Protéinurie Points
    # Categories: "≤1", "]1;2]", ">3"
    if proteinurie_cat == ">3": score += 8
    elif proteinurie_cat == "]1;2]": score += 4
    else: score += 0
    
    # 5. Diabète Points
    if diabete: score += 3
    
    # 6. HTA Points
    if hta: score += 2
    
    # 7. Anémie Points (Hb < 11 g/dL)
    if hb < 11.0: score += 3
    
    return score

def interpret_sr_irc_risk(score):
    """
    Interprétation du risque SR-IRC et recommandations de suivi.
    """
    if score > 40:
        return "Imminent", "⚫", "Dialyse proche", "Hospitalisation / Urgence Néphrologique"
    elif score >= 31:
        return "Très élevé", "🔴", "Préparation dialyse", "Suivi mensuel / Mise en place abord vasculaire"
    elif score >= 21:
        return "Élevé", "🟠", "Suivi trimestriel", "Consultation néphrologique spécialisée"
    elif score >= 11:
        return "Modéré", "🟡", "Contrôle semestriel", "Surveillance biologique régulière"
    else:
        return "Faible", "🟢", "Contrôle annuel", "Mesures de néphroprotection standard"

# ----------------------------
# 3️⃣ Mappage des données CSV
# ----------------------------
def map_csv_row_to_patient(row):
    """
    Transforme une ligne de data_drive.csv en dictionnaire patient nettoyé.
    """
    try:
        # Conversion Helper
        def to_float(val):
            if pd.isna(val) or val == "": return 0.0
            s_val = str(val).lower().replace(",", ".")
            if "négative" in s_val or "trace" in s_val or "absent" in s_val:
                return 0.0
            if ">" in s_val:
                return float(s_val.replace(">", "").strip()) + 0.1
            if "+" in s_val:
                # Approximation: 1+ -> 0.3g/L, 2+ -> 1g/L, 3+ -> 3g/L
                count = s_val.count("+")
                return 3.0 if count >= 3 else 1.0 if count == 2 else 0.3
            try:
                return float(s_val)
            except:
                return 0.0

        patient_id = str(row['ID'])
        age = int(to_float(row['Age']))
        sexe = "M" if "M" in str(row['Sexe']).upper() else "F"
        creat = to_float(row['Créatinine (mg/L)'])
        
        if creat <= 0: return None # Impossible de calculer l'eGFR
        
        # Protéinurie (priorité à la valeur g/24h numérique)
        prot = to_float(row['Protéinurie']) # Col 159
        if prot == 0 and not pd.isna(row['Protéinurie à la bandellette urinaire (g/24h)']):
            # Tentative de récupération depuis la bandelette si dispo
            val_band = str(row['Protéinurie à la bandellette urinaire (g/24h)'])
            if "> 3" in val_band: prot = 4.0
            elif "1" in val_band: prot = 1.5
            
        # Comorbidités (0 ou 1 dans le CSV)
        diabete = int(to_float(row['Personnels Médicaux/Diabète 1'])) or \
                  int(to_float(row['Personnels Médicaux/Diabète 2'])) or \
                  int(to_float(row.get('Causes Majeure après Diagnostic/Diabète', 0)))
        
        hta = int(to_float(row['Personnels Médicaux/HTA'])) or \
              int(to_float(row.get('Causes Majeure après Diagnostic/HTA', 0)))
              
        hb = to_float(row['Hb (g/dL)'])
        if hb == 0: hb = 12.0 # Valeur par défaut si manquante pour éviter fausse anémie systématique

        return {
            "id_patient": patient_id,
            "age": age,
            "sexe": sexe,
            "creatinine_mg_l": creat,
            "proteinurie_24h": prot,
            "diabete": bool(diabete),
            "hta": bool(hta),
            "hb": hb
        }
    except Exception as e:
        # print(f"Erreur mapping ligne {row.get('ID')}: {e}")
        return None

# Mapping pour la protéinurie (bandelette ou 24h)
def categorize_proteinuria(val_24h):
    """Adaptation simplifiée de la protéinurie 24h vers les catégories SR-IRC."""
    if val_24h > 3.0: return ">3"
    if val_24h > 1.0: return "]1;2]"
    return "≤1"
