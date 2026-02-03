import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Dimensionnement LTE 4G", page_icon="📡", layout="wide")

# --- TITRE ET INTRODUCTION ---
st.title("📡 Outil de Dimensionnement & Planification LTE (4G)")
st.markdown("""
Cette application permet aux ingénieurs télécoms de dimensionner un réseau LTE :
1.  **Couverture :** Calcul du rayon de cellule via le modèle Cost-231 Hata.
2.  **Capacité :** Estimation du nombre d'eNodeB nécessaires.
3.  **Simulation :** Visualisation graphique de la position des sites.
""")

# --- BARRE LATÉRALE (PARAMÈTRES) ---
st.sidebar.header("1. Paramètres de la Zone")
surface = st.sidebar.number_input("Surface de la zone (km²)", value=25.0, step=1.0)
type_zone = st.sidebar.selectbox("Type d'environnement", ["Urbain Dense", "Urbain", "Suburbain", "Rural"])

st.sidebar.header("2. Paramètres Réseau")
frequence = st.sidebar.selectbox("Fréquence (MHz)", [800, 1800, 2600], index=1)
bande = st.sidebar.selectbox("Bande passante (MHz)", [1.4, 3, 5, 10, 15, 20], index=3)
hauteur_bts = st.sidebar.slider("Hauteur eNodeB (m)", 20, 60, 30)
hauteur_ue = st.sidebar.slider("Hauteur Utilisateur (m)", 1, 10, 2)

st.sidebar.header("3. Paramètres Trafic")
densite_user = st.sidebar.number_input("Densité Utilisateurs (hab/km²)", value=1500)
penetration = st.sidebar.slider("Taux de pénétration 4G (%)", 10, 100, 70)
trafic_par_user = st.sidebar.number_input("Trafic moyen par user (Mbps)", value=2.5)

# --- FONCTIONS DE CALCUL (LOGIQUE MÉTIER) ---
def calcul_cost231_hata(f, h_b, h_m, d, env):
    # Formule standard Cost-231 Hata pour le Path Loss
    # f: Mhz, h_b: m, h_m: m, d: km
    
    # Constantes de base
    a_hm = (1.1 * math.log10(f) - 0.7) * h_m - (1.56 * math.log10(f) - 0.8)
    
    # Perte de base (Urbain)
    Lu = 46.3 + 33.9 * math.log10(f) - 13.82 * math.log10(h_b) - a_hm + (44.9 - 6.55 * math.log10(h_b)) * math.log10(d)
    
    if env == "Urbain Dense":
        path_loss = Lu + 3 # Correction métropole (cm = 3dB)
    elif env == "Urbain":
        path_loss = Lu
    elif env == "Suburbain":
        path_loss = Lu - 2 * (math.log10(f/28))**2 - 5.4
    else: # Rural
        path_loss = Lu - 4.78 * (math.log10(f))**2 + 18.33 * math.log10(f) - 40.94
        
    return path_loss

def calcul_rayon(mapl, f, h_b, h_m, env):
    # Inversion de la formule Hata pour trouver la distance (d) à partir du MAPL
    # C'est une approximation itérative ou mathématique inverse
    # Pour simplifier ici, on utilise une estimation basée sur le MAPL typique LTE
    
    # Constantes simplifiées pour l'inversion
    c1 = 46.3 + 33.9 * math.log10(f) - 13.82 * math.log10(h_b)
    # Correction a_hm
    a_hm = (1.1 * math.log10(f) - 0.7) * h_m - (1.56 * math.log10(f) - 0.8)
    
    correction_env = 0
    if env == "Urbain Dense": correction_env = 3
    elif env == "Suburbain": correction_env = -2 * (math.log10(f/28))**2 - 5.4
    elif env == "Rural": correction_env = -4.78 * (math.log10(f))**2 + 18.33 * math.log10(f) - 40.94
    
    # Formule : MAPL = A + B * log10(d)  =>  log10(d) = (MAPL - A) / B
    A = c1 - a_hm + correction_env
    B = 44.9 - 6.55 * math.log10(h_b)
    
    log_d = (mapl - A) / B
    d = 10 ** log_d
    return d

# --- INTERFACE PRINCIPALE (ONGLETS) ---
tab1, tab2, tab3 = st.tabs(["📊 Résultats Dimensionnement", "🗺️ Carte de Simulation", "📉 Bilan de Liaison"])

if st.sidebar.button("LANCER LE DIMENSIONNEMENT", type="primary"):
    
    # 1. Calculs Préliminaires
    mapl_dl = 138.5 # Valeur standard MAPL Downlink (peut être calculée en détail)
    rayon_cellule = calcul_rayon(mapl_dl, frequence, hauteur_bts, hauteur_ue, type_zone)
    
    surface_cellule = 2.6 * (rayon_cellule**2) # Surface hexagone = 2.6 * R²
    
    nb_sites_couverture = math.ceil(surface / surface_cellule)
    
    # Capacité
    total_users = surface * densite_user * (penetration/100)
    capacite_site_estimee = 150 # Mbps (valeur moyenne théorique pour 20MHz)
    if bande < 20: capacite_site_estimee = capacite_site_estimee * (bande/20)
    
    traffic_total_network = total_users * (trafic_par_user / 1000) # Gbps to Mbps approx
    nb_sites_capacite = math.ceil(traffic_total_network / capacite_site_estimee)
    
    final_sites = max(nb_sites_couverture, nb_sites_capacite)
    dist_inter_site = math.sqrt(3) * rayon_cellule

    # --- OBTENIR LES RÉSULTATS ---
    with tab1:
        st.success("Calculs terminés avec succès !")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Nombre de Sites (eNodeB)", f"{final_sites}", delta="Final")
        col2.metric("Rayon de Cellule", f"{rayon_cellule:.2f} km")
        col3.metric("Distance Inter-Site", f"{dist_inter_site:.2f} km")
        
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.info("📌 Dimensionnement Couverture")
            st.write(f"- Surface d'une cellule : **{surface_cellule:.2f} km²**")
            st.write(f"- Sites requis pour couvrir : **{nb_sites_couverture}**")
        
        with c2:
            st.warning("👥 Dimensionnement Capacité")
            st.write(f"- Nombre d'abonnés actifs : **{int(total_users)}**")
            st.write(f"- Sites requis pour trafic : **{nb_sites_capacite}**")

    # --- CARTE DE SIMULATION ---
    with tab2:
        st.subheader("Simulation de l'implantation des eNodeB")
        
        # Génération des points (simulation hexagone simple)
        num_x = int(math.sqrt(final_sites * 1.5)) + 1
        num_y = int(final_sites / num_x) + 2
        
        x_coords = []
        y_coords = []
        
        dx = dist_inter_site
        dy = dist_inter_site * math.sqrt(3) / 2
        
        count = 0
        for i in range(num_x):
            for j in range(num_y):
                if count >= final_sites: break
                x = i * dx
                y = j * dy
                if j % 2 == 1: x += dx / 2 # Décalage hexagone
                
                # Centrer sur la zone
                if x <= math.sqrt(surface)*1.2 and y <= math.sqrt(surface)*1.2:
                    x_coords.append(x)
                    y_coords.append(y)
                    count += 1

        # Plot avec Matplotlib
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Dessin des zones de couverture (Cercles)
        for x, y in zip(x_coords, y_coords):
            circle = plt.Circle((x, y), rayon_cellule, color='blue', alpha=0.1)
            ax.add_patch(circle)
            ax.plot(x, y, 'r^', markersize=10) # Triangle rouge pour eNodeB
            
        ax.set_title(f"Planification de {final_sites} Sites LTE")
        ax.set_xlabel("Distance (km)")
        ax.set_ylabel("Distance (km)")
        ax.set_xlim(-1, math.sqrt(surface) + 2)
        ax.set_ylim(-1, math.sqrt(surface) + 2)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_aspect('equal')
        
        st.pyplot(fig)
        st.caption("Les triangles rouges représentent les eNodeB. Les cercles bleus représentent la couverture théorique.")

    # --- BILAN DE LIAISON ---
    with tab3:
        st.write("Détails du Link Budget utilisé pour le calcul du rayon.")
        df_lb = pd.DataFrame({
            "Paramètre": ["Fréquence", "Bande Passante", "Environnement", "MAPL (Max Path Loss)", "Modèle Propagation"],
            "Valeur": [f"{frequence} MHz", f"{bande} MHz", type_zone, "138.5 dB", "Cost-231 Hata"]
        })
        st.table(df_lb)

else:
    st.info("👈 Veuillez configurer les paramètres dans le menu de gauche et cliquer sur 'LANCER'.")
