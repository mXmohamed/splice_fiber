#!/usr/bin/env python3
"""
Version DEBUG de l'analyseur FTTE pour diagnostiquer le problème des cassettes manquantes
"""

import zipfile
import csv
import sys
from collections import defaultdict
import time
import os
from datetime import datetime

def process_ftte_analysis_debug(zip_path):
    """Version debug qui trace toutes les cassettes et leurs rejets"""
    print(f"Démarrage de l'analyse DEBUG du fichier: {zip_path}")
    start_time = time.time()
    
    # Dictionnaire pour tracer les cassettes par PM
    pm_cassettes = defaultdict(set)
    cassette_rejets = defaultdict(lambda: {'count': 0, 'raisons': []})
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Vérifier les fichiers requis
            required_files = [
                't_cassette.csv', 't_position.csv', 't_fibre.csv',
                't_cable.csv', 't_site.csv', 't_local.csv'
            ]
            
            for file_name in required_files:
                if file_name not in zip_file.namelist():
                    print(f"❌ Erreur: Fichier manquant: {file_name}")
                    return
            
            print("✅ Tous les fichiers requis sont présents")
            
            # 1. Charger les cassettes FTTE
            print("\n📋 Chargement des cassettes FTTE...")
            cassettes_ftte = set()
            with zip_file.open('t_cassette.csv') as f:
                content = f.read()
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        decoded = content.decode(encoding)
                        break
                    except:
                        continue
                
                lines = decoded.splitlines()
                delimiter = ';' if ';' in lines[0] else ','
                reader = csv.DictReader(lines, delimiter=delimiter)
                
                for row in reader:
                    clean_row = {k.strip().replace('\ufeff', ''): v for k, v in row.items() if k}
                    if clean_row.get('cs_type') == 'E' and not clean_row.get('cs_bp_code', '').strip():
                        cassettes_ftte.add(clean_row.get('cs_code', ''))
            
            print(f"   → {len(cassettes_ftte)} cassettes FTTE trouvées")
            
            # 2. Charger les câbles
            print("\n🔌 Chargement des câbles...")
            cables = {}
            with zip_file.open('t_cable.csv') as f:
                content = f.read().decode('utf-8', errors='ignore')
                lines = content.splitlines()
                delimiter = ';' if ';' in lines[0] else ','
                reader = csv.DictReader(lines, delimiter=delimiter)
                
                for row in reader:
                    clean_row = {k.strip().replace('\ufeff', ''): v.strip() if v else '' 
                                for k, v in row.items() if k}
                    
                    cb_code = clean_row.get('cb_code')
                    cb_nd1 = clean_row.get('cb_nd1', '')
                    cb_nd2 = clean_row.get('cb_nd2', '')
                    
                    pe_node = None
                    if cb_nd1.startswith('PE'):
                        pe_node = cb_nd1
                    elif cb_nd2.startswith('PE'):
                        pe_node = cb_nd2
                    
                    cables[cb_code] = {
                        'cb_typelog': clean_row.get('cb_typelog'),
                        'cb_etiquet': clean_row.get('cb_etiquet', cb_code),
                        'cb_nd1': cb_nd1,
                        'cb_nd2': cb_nd2,
                        'pe_node': pe_node
                    }
            
            # 3. Créer l'index des fibres
            print("\n🔍 Création de l'index des fibres...")
            fibre_to_cable = {}
            with zip_file.open('t_fibre.csv') as f:
                content = f.read().decode('utf-8', errors='ignore')
                lines = content.splitlines()
                delimiter = ';' if ';' in lines[0] else ','
                reader = csv.DictReader(lines, delimiter=delimiter)
                
                for row in reader:
                    clean_row = {k.strip().replace('\ufeff', ''): v for k, v in row.items() if k}
                    fibre_code = clean_row.get('fo_code')
                    cable_code = clean_row.get('fo_cb_code')
                    
                    if cable_code in cables:
                        fibre_to_cable[fibre_code] = cable_code
            
            # 4. Charger les sites
            print("\n🏢 Chargement des sites...")
            noeud_to_site = {}
            with zip_file.open('t_site.csv') as f:
                content = f.read().decode('utf-8', errors='ignore')
                lines = content.splitlines()
                delimiter = ';' if ';' in lines[0] else ','
                reader = csv.DictReader(lines, delimiter=delimiter)
                
                for row in reader:
                    clean_row = {k.strip().replace('\ufeff', ''): v.strip() if v else '' 
                                for k, v in row.items() if k}
                    nd_code = clean_row.get('st_nd_code')
                    st_code = clean_row.get('st_code')
                    if nd_code and st_code:
                        noeud_to_site[nd_code] = st_code
            
            # 5. Charger les locaux SRO
            print("\n🏢 Chargement des locaux SRO...")
            site_to_local = {}
            with zip_file.open('t_local.csv') as f:
                content = f.read().decode('utf-8', errors='ignore')
                lines = content.splitlines()
                delimiter = ';' if ';' in lines[0] else ','
                reader = csv.DictReader(lines, delimiter=delimiter)
                
                for row in reader:
                    clean_row = {k.strip().replace('\ufeff', ''): v.strip() if v else '' 
                                for k, v in row.items() if k}
                    if clean_row.get('lc_typelog') == 'SRO':
                        st_code = clean_row.get('lc_st_code')
                        if st_code:
                            site_to_local[st_code] = {
                                'lc_code': clean_row.get('lc_code'),
                                'lc_etiquet': clean_row.get('lc_etiquet')
                            }
            
            # 6. Traiter les positions avec debug détaillé
            print("\n⚙️  Traitement des positions avec debug...")
            output_file = f"ftte_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            debug_file = f"ftte_rejets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile, \
                 open(debug_file, 'w', encoding='utf-8') as debugfile:
                
                fieldnames = [
                    'Cassette FTTE', 'Fibre Transport', 'Cable Transport',
                    'Fibre Distribution', 'Cable Distribution', 
                    'Noeud PE', 'Site', 'Local PM', 'Etiquette PM'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                with zip_file.open('t_position.csv') as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    lines = content.splitlines()
                    delimiter = ';' if ';' in lines[0] else ','
                    reader = csv.DictReader(lines, delimiter=delimiter)
                    
                    positions_count = 0
                    for row in reader:
                        positions_count += 1
                        clean_row = {k.strip().replace('\ufeff', ''): v for k, v in row.items() if k}
                        
                        cassette_code = clean_row.get('ps_cs_code')
                        
                        # Vérifier si c'est une cassette FTTE
                        if cassette_code not in cassettes_ftte:
                            continue
                        
                        # Tracer cette cassette
                        cassette_rejets[cassette_code]['count'] += 1
                        
                        # Récupérer les fibres
                        fibre1 = clean_row.get('ps_1')
                        fibre2 = clean_row.get('ps_2')
                        
                        if fibre1 not in fibre_to_cable:
                            cassette_rejets[cassette_code]['raisons'].append(f"Fibre1 {fibre1} non trouvée")
                            continue
                        if fibre2 not in fibre_to_cable:
                            cassette_rejets[cassette_code]['raisons'].append(f"Fibre2 {fibre2} non trouvée")
                            continue
                        
                        # Récupérer les câbles
                        cable1_code = fibre_to_cable[fibre1]
                        cable2_code = fibre_to_cable[fibre2]
                        cable1 = cables[cable1_code]
                        cable2 = cables[cable2_code]
                        
                        # Identifier TR et DI
                        if cable1['cb_typelog'] == 'TR' and cable2['cb_typelog'] == 'DI':
                            cable_tr = cable1
                            cable_di = cable2
                            fibre_tr = fibre1
                            fibre_di = fibre2
                        elif cable1['cb_typelog'] == 'DI' and cable2['cb_typelog'] == 'TR':
                            cable_tr = cable2
                            cable_di = cable1
                            fibre_tr = fibre2
                            fibre_di = fibre1
                        else:
                            cassette_rejets[cassette_code]['raisons'].append(
                                f"Pas TR-DI: {cable1['cb_typelog']}-{cable2['cb_typelog']}")
                            continue
                        
                        # Récupérer le nœud PE
                        pe_node = cable_di.get('pe_node')
                        if not pe_node:
                            cassette_rejets[cassette_code]['raisons'].append(
                                f"Pas de PE dans câble DI {cable_di['cb_etiquet']}")
                            continue
                        
                        # Récupérer le site
                        site_code = noeud_to_site.get(pe_node)
                        if not site_code:
                            cassette_rejets[cassette_code]['raisons'].append(
                                f"Site non trouvé pour PE {pe_node}")
                            continue
                        
                        # Récupérer le local
                        local_info = site_to_local.get(site_code)
                        if not local_info:
                            cassette_rejets[cassette_code]['raisons'].append(
                                f"Local non trouvé pour site {site_code}")
                            continue
                        
                        # Succès! Tracer le PM
                        pm_code = local_info['lc_code']
                        pm_cassettes[pm_code].add(cassette_code)
                        
                        # Écrire le résultat
                        writer.writerow({
                            'Cassette FTTE': cassette_code,
                            'Fibre Transport': fibre_tr,
                            'Cable Transport': cable_tr['cb_etiquet'],
                            'Fibre Distribution': fibre_di,
                            'Cable Distribution': cable_di['cb_etiquet'],
                            'Noeud PE': pe_node,
                            'Site': site_code,
                            'Local PM': local_info['lc_code'],
                            'Etiquette PM': local_info['lc_etiquet']
                        })
                
                # Écrire le rapport de debug
                debugfile.write("=== RAPPORT DEBUG CASSETTES FTTE ===\n\n")
                
                # PM avec plusieurs cassettes
                debugfile.write("PM AVEC PLUSIEURS CASSETTES:\n")
                for pm, cassettes in pm_cassettes.items():
                    if len(cassettes) > 1:
                        debugfile.write(f"PM {pm}: {len(cassettes)} cassettes - {', '.join(cassettes)}\n")
                
                debugfile.write("\n\nCASSETTES REJETÉES ET RAISONS:\n")
                for cassette, info in cassette_rejets.items():
                    if info['raisons']:
                        debugfile.write(f"\nCassette {cassette} (vue {info['count']} fois):\n")
                        for raison in set(info['raisons']):
                            debugfile.write(f"  - {raison}\n")
                
                debugfile.write(f"\n\nSTATISTIQUES:\n")
                debugfile.write(f"Total positions traitées: {positions_count}\n")
                debugfile.write(f"Total cassettes FTTE: {len(cassettes_ftte)}\n")
                debugfile.write(f"Cassettes avec positions: {len(cassette_rejets)}\n")
                debugfile.write(f"PM distincts trouvés: {len(pm_cassettes)}\n")
            
            print(f"\n✅ Analyse terminée!")
            print(f"📊 Fichier de sortie: {output_file}")
            print(f"🔍 Fichier debug: {debug_file}")
            print(f"\nConsultez le fichier debug pour voir pourquoi certaines cassettes sont rejetées!")
            
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) != 2:
        print("Usage: python ftte_analyzer_debug.py <fichier.zip>")
        sys.exit(1)
    
    zip_path = sys.argv[1]
    if not os.path.exists(zip_path):
        print(f"❌ Erreur: Le fichier '{zip_path}' n'existe pas")
        sys.exit(1)
    
    process_ftte_analysis_debug(zip_path)

if __name__ == "__main__":
    main()