# Solutions pour traiter des millions de lignes

Les navigateurs ont des limites de mémoire (généralement 2-4 GB). Pour traiter des fichiers avec des millions de lignes, voici les solutions recommandées :

## 1. Script Python (Recommandé)

J'ai créé `ftte_analyzer.py` qui :
- Traite les fichiers en streaming (pas de limite mémoire)
- Peut gérer des milliards de lignes
- Génère un fichier CSV avec tous les résultats

### Utilisation :

**Option 1 : Double-cliquer sur `run_ftte_analyzer.bat`**
- Le script vous demandera de glisser-déposer votre fichier ZIP

**Option 2 : En ligne de commande**
```bash
python ftte_analyzer.py votre_fichier.zip
```

### Avantages :
- ✅ Pas de limite de taille
- ✅ Traitement rapide
- ✅ Export CSV complet
- ✅ Affichage de la progression

## 2. Autres solutions possibles

### A. Utiliser une base de données (SQLite)
```python
import sqlite3
import pandas as pd

# Charger les CSV dans SQLite
conn = sqlite3.connect('ftte_data.db')
for csv_file in ['t_cassette.csv', 't_position.csv', ...]:
    df = pd.read_csv(csv_file, delimiter=';')
    df.to_sql(csv_file.replace('.csv', ''), conn, if_exists='replace')

# Faire les jointures SQL
query = """
SELECT ... FROM t_cassette
JOIN t_position ON ...
WHERE cs_type = 'E' AND cs_bp_code IS NULL
"""
```

### B. Utiliser Apache Spark (pour très grandes données)
- Installer PySpark
- Traiter les données en distribué
- Idéal pour > 100 millions de lignes

### C. Utiliser DuckDB (base de données analytique)
```python
import duckdb

conn = duckdb.connect()
# Lire directement depuis le ZIP
conn.execute("CREATE TABLE cassettes AS SELECT * FROM read_csv_auto('t_cassette.csv')")
# Faire les analyses
```

### D. Découper les données
- Diviser le ZIP en plusieurs petits fichiers
- Traiter par batch
- Fusionner les résultats

## Recommandation

Pour votre cas avec des millions de lignes, utilisez le **script Python** fourni :
1. Il est optimisé pour la mémoire
2. Il traite les données en streaming
3. Il génère un CSV complet des résultats

Le HTML/JavaScript n'est pas adapté pour des volumes aussi importants à cause des limites des navigateurs.