#!/usr/bin/env python3
"""
Analyseur FTTE - Recherche PM via nœud PE
Traite des fichiers ZIP contenant des millions de lignes
Logique : Recherche le nœud PE dans cb_nd1 ou cb_nd2 du câble DI
"""

import zipfile
import csv
import sys
from collections import defaultdict
import time
import os
from datetime import datetime

def process_ftte_analysis(zip_path):
    """
    Analyse les fibres FTTE dans un fichier ZIP
    Version 4 : recherche du nœud PE dans cb_nd1 ou cb_nd2
    """
    print(f"Démarrage de l'analyse du fichier: {zip_path}")
    start_time = time.time()
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Vérifier les fichiers requis
            required_files = [
                't_cassette.csv',
                't_position.csv',
                't_fibre.csv',
                't_cable.csv',
                't_site.csv',
                't_local.csv'
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
                # Essayer différents encodages
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        decoded = content.decode(encoding)
                        break
                    except:
                        continue
                
                lines = decoded.splitlines()
                if not lines:
                    print("❌ Fichier t_cassette.csv vide")
                    return
                
                # Détecter le délimiteur
                first_line = lines[0]
                delimiter = ';' if ';' in first_line else ','
                
                reader = csv.DictReader(lines, delimiter=delimiter)
                
                row_count = 0
                for row in reader:
                    row_count += 1
                    # Nettoyer les clés
                    clean_row = {k.strip().replace('\ufeff', ''): v for k, v in row.items() if k}
                    
                    if clean_row.get('cs_type') == 'E' and not clean_row.get('cs_bp_code', '').strip():
                        cassettes_ftte.add(clean_row.get('cs_code', ''))
                
                print(f"   → {row_count} lignes traitées")
            
            print(f"   → {len(cassettes_ftte)} cassettes FTTE trouvées")
            
            if not cassettes_ftte:
                print("❌ Aucune cassette FTTE trouvée")
                return
            
            # 2. Charger les câbles (pour les étiquettes, types et nœuds)
            print("\n🔌 Chargement des câbles...")
            cables = {}
            with zip_file.open('t_cable.csv') as f:
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
                
                pe_count = 0
                for row in reader:
                    clean_row = {k.strip().replace('\ufeff', ''): v.strip() if v else '' 
                                for k, v in row.items() if k}
                    
                    cb_code = clean_row.get('cb_code')
                    cb_nd1 = clean_row.get('cb_nd1', '')
                    cb_nd2 = clean_row.get('cb_nd2', '')
                    
                    # Identifier le nœud PE
                    pe_node = None
                    if cb_nd1.startswith('PE'):
                        pe_node = cb_nd1
                        pe_count += 1
                    elif cb_nd2.startswith('PE'):
                        pe_node = cb_nd2
                        pe_count += 1
                    
                    cables[cb_code] = {
                        'cb_typelog': clean_row.get('cb_typelog'),
                        'cb_etiquet': clean_row.get('cb_etiquet', cb_code),
                        'cb_nd1': cb_nd1,
                        'cb_nd2': cb_nd2,
                        'pe_node': pe_node
                    }
                    
            print(f"   → {len(cables)} câbles chargés")
            print(f"   → {pe_count} câbles avec nœud PE identifié")
            
            # 3. Créer un index des fibres
            print("\n🔍 Création de l'index des fibres...")
            fibre_to_cable = {}
            
            with zip_file.open('t_fibre.csv') as f:
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
                
                fibre_count = 0
                for row in reader:
                    clean_row = {k.strip().replace('\ufeff', ''): v for k, v in row.items() if k}
                    fibre_code = clean_row.get('fo_code')
                    cable_code = clean_row.get('fo_cb_code')
                    
                    if cable_code in cables:
                        fibre_to_cable[fibre_code] = cable_code
                        fibre_count += 1
                    
                    if fibre_count % 500000 == 0 and fibre_count > 0:
                        print(f"   → {fibre_count:,} fibres indexées...")
            
            print(f"   → Total: {len(fibre_to_cable):,} fibres indexées")
            
            # 4. Charger les sites (nœud -> site)
            print("\n🏢 Chargement des sites...")
            noeud_to_site = {}
            with zip_file.open('t_site.csv') as f:
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
                
                pe_sites = 0
                for row in reader:
                    clean_row = {k.strip().replace('\ufeff', ''): v.strip() if v else '' 
                                for k, v in row.items() if k}
                    nd_code = clean_row.get('st_nd_code')
                    st_code = clean_row.get('st_code')
                    if nd_code and st_code:
                        noeud_to_site[nd_code] = st_code
                        if nd_code.startswith('PE'):
                            pe_sites += 1
            
            print(f"   → {len(noeud_to_site)} relations nœud->site chargées")
            print(f"   → dont {pe_sites} nœuds PE")
            
            # 5. Charger les locaux SRO
            print("\n🏢 Chargement des locaux SRO...")
            site_to_local = {}
            with zip_file.open('t_local.csv') as f:
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
                    clean_row = {k.strip().replace('\ufeff', ''): v.strip() if v else '' 
                                for k, v in row.items() if k}
                    if clean_row.get('lc_typelog') == 'SRO':
                        st_code = clean_row.get('lc_st_code')
                        if st_code:
                            site_to_local[st_code] = {
                                'lc_code': clean_row.get('lc_code'),
                                'lc_etiquet': clean_row.get('lc_etiquet')
                            }
            
            print(f"   → {len(site_to_local)} locaux SRO chargés")
            
            # 6. Traiter les positions et écrire les résultats
            print("\n⚙️  Traitement des positions...")
            output_file = f"ftte_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            results_count = 0
            positions_processed = 0
            no_pe_count = 0
            no_site_count = 0
            no_local_count = 0
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Cassette FTTE', 'Fibre Transport', 'Cable Transport',
                    'Fibre Distribution', 'Cable Distribution', 
                    'Noeud PE', 'Site', 'Local PM', 'Etiquette PM'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                with zip_file.open('t_position.csv') as f:
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
                        positions_processed += 1
                        clean_row = {k.strip().replace('\ufeff', ''): v for k, v in row.items() if k}
                        
                        # Vérifier si c'est une cassette FTTE
                        if clean_row.get('ps_cs_code') not in cassettes_ftte:
                            continue
                        
                        # Récupérer les fibres
                        fibre1 = clean_row.get('ps_1')
                        fibre2 = clean_row.get('ps_2')
                        
                        if fibre1 not in fibre_to_cable or fibre2 not in fibre_to_cable:
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
                            continue
                        
                        # Récupérer le nœud PE du câble DI
                        pe_node = cable_di.get('pe_node')
                        if not pe_node:
                            no_pe_count += 1
                            continue
                        
                        # Récupérer le site via le nœud PE
                        site_code = noeud_to_site.get(pe_node)
                        if not site_code:
                            no_site_count += 1
                            continue
                        
                        # Récupérer le local SRO via le site
                        local_info = site_to_local.get(site_code)
                        if not local_info:
                            no_local_count += 1
                            continue
                        
                        # Écrire le résultat
                        writer.writerow({
                            'Cassette FTTE': clean_row['ps_cs_code'],
                            'Fibre Transport': fibre_tr,
                            'Cable Transport': cable_tr['cb_etiquet'],
                            'Fibre Distribution': fibre_di,
                            'Cable Distribution': cable_di['cb_etiquet'],
                            'Noeud PE': pe_node,
                            'Site': site_code,
                            'Local PM': local_info['lc_code'],
                            'Etiquette PM': local_info['lc_etiquet']
                        })
                        results_count += 1
                        
                        if positions_processed % 100000 == 0:
                            print(f"   → {positions_processed:,} positions traitées, {results_count:,} résultats trouvés...")
            
            # Résumé final
            elapsed_time = time.time() - start_time
            print(f"\n✅ Analyse terminée en {elapsed_time:.2f} secondes")
            print(f"\n📊 Résultats:")
            print(f"   - Positions traitées: {positions_processed:,}")
            print(f"   - Connexions FTTE trouvées: {results_count:,}")
            print(f"   - Rejets - Pas de nœud PE: {no_pe_count:,}")
            print(f"   - Rejets - Site non trouvé: {no_site_count:,}")
            print(f"   - Rejets - Local non trouvé: {no_local_count:,}")
            print(f"   - Fichier de sortie: {output_file}")
            if os.path.exists(output_file):
                print(f"   - Taille du fichier: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
            
    except Exception as e:
        print(f"\n❌ Erreur lors du traitement: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) != 2:
        print("Usage: python ftte_analyzer.py <fichier.zip>")
        print("\nExemple:")
        print("  python ftte_analyzer.py 45lor2_SRO-BPI-12387439_REC_TR-DI-RA_V300_20250929-080034_S39.zip")
        sys.exit(1)
    
    zip_path = sys.argv[1]
    
    if not os.path.exists(zip_path):
        print(f"❌ Erreur: Le fichier '{zip_path}' n'existe pas")
        sys.exit(1)
    
    if not zip_path.endswith('.zip'):
        print("❌ Erreur: Le fichier doit être un ZIP")
        sys.exit(1)
    
    process_ftte_analysis(zip_path)

if __name__ == "__main__":
    main()