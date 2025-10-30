# Analyseur FTTE - Fiber To The Enterprise

## 🎯 Description

Cet outil analyse les infrastructures de fibre optique FTTE pour tracer le chemin des fibres depuis les cassettes FTTE jusqu'aux Points de Mutualisation (PM) en passant par les nœuds PE.

## 🚀 Utilisation

### Option 1 : Version Web (Recommandée pour GitHub Pages)

1. Visitez https://[votre-username].github.io/FTTE_FIBER/
2. Cliquez sur "Lancer l'app"
3. Glissez-déposez votre fichier ZIP
4. Téléchargez les résultats CSV

### Option 2 : Version Desktop

Nécessite Python 3.x installé

```bash
# Windows
run_ftte_analyzer.bat

# Linux/Mac
python ftte_analyzer.py votre_fichier.zip
```

## 📊 Format des données

### Fichiers d'entrée requis (dans le ZIP)
- `t_cassette.csv` - Cassettes de fibres
- `t_position.csv` - Connexions entre fibres
- `t_fibre.csv` - Fibres individuelles
- `t_cable.csv` - Câbles contenant les fibres
- `t_site.csv` - Sites et nœuds
- `t_local.csv` - Locaux techniques

### Fichier de sortie
CSV avec les colonnes :
- Cassette FTTE
- Fibre Transport
- Cable Transport
- Fibre Distribution
- Cable Distribution
- Noeud PE
- Site
- Local PM
- Etiquette PM

## 🔧 Logique de traitement

1. **Identification des cassettes FTTE** : Type 'E' sans code BP
2. **Traçage des connexions** : Via les positions de fibres
3. **Recherche du nœud PE** : Dans cb_nd1 ou cb_nd2 du câble DI
4. **Remontée au PM** : Nœud PE → Site → Local SRO

## 📝 Déploiement sur GitHub Pages

1. Créez un repository sur GitHub
2. Uploadez tous les fichiers
3. Activez GitHub Pages dans Settings → Pages
4. Source : Deploy from a branch
5. Branch : main, folder: / (root)
6. Votre app sera disponible sur https://[username].github.io/[repo-name]/

## 📄 License

MIT