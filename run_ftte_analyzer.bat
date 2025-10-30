@echo off
echo ========================================
echo Analyseur FTTE - Recherche via Noeud PE
echo ========================================
echo.

:: Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installé ou n'est pas dans le PATH
    echo Veuillez installer Python depuis https://www.python.org/
    pause
    exit /b 1
)

:: Demander le fichier ZIP
set /p zipfile="Glissez-déposez votre fichier ZIP ici et appuyez sur Entrée: "

:: Retirer les guillemets si présents
set zipfile=%zipfile:"=%

:: Exécuter l'analyse
echo.
echo Démarrage de l'analyse (recherche noeud PE)...
echo.
python ftte_analyzer.py "%zipfile%"

echo.
echo ========================================
echo Traitement terminé
echo ========================================
pause