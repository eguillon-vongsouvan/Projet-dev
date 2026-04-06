# GCS2-UE7-2 DevSecOps — Semaine 1

Projet : plateforme de gestion académique sécurisée (Flask + MySQL + Docker + CI/CD).

## Objectifs (Semaine 1)

1. Application Flask fonctionnelle avec RBAC complet (Administrateur, Professeur, Étudiant) + exigences de sécurité (hash bcrypt, CSRF, requêtes paramétrées, headers sécurité, sessions).
2. Base MySQL configurée + schéma + seed de données de test.
3. Conteneurs Docker (`Dockerfile`, `docker-compose.yml`).
4. Pipeline CI/CD GitHub Actions.

## Lancer le projet en local

### Prérequis

- Docker Desktop (ou Docker Engine)
- (Optionnel) Python 3.12+ pour exécuter hors conteneur

### Démarrage via Docker Compose

1. Créer la base et initialiser le schéma :
   - le script `scripts/init_db.py` s’exécute automatiquement lors du `docker compose up` (voir `docker-compose.yml`).
2. Lancer :
   - `docker compose up --build`
3. Ouvrir :
   - `http://localhost:5000`

## Comptes de test (seed)

Les comptes sont insérés par `scripts/init_db.py` (exécuté au démarrage via `docker-compose.yml`).

> Note : les mots de passe ne sont fournis qu’à des fins de seed/démo (TP).

### Identifiants (seed)

- Administrateur : `admin` / `Admin123!`
- Professeur : `prof1` / `Prof123!`
- Étudiant : `stud1` / `Stud123!`

## Parcours Semaine 1 (fonctionnel)

1. Se connecter :
   - ouvrir `http://localhost:5000/auth/login`
2. RBAC côté serveur :
   - `admin` : crée des classes, assigne des étudiants, crée des emplois du temps, crée des utilisateurs
   - `prof1` : crée une évaluation pour ses classes, saisit les notes (notes chiffrées en base)
   - `stud1` : consulte uniquement ses notes et son emploi du temps

## CI/CD (GitHub Actions)

Le workflow est dans `.github/workflows/ci-cd.yml`.

Pour déclencher le pipeline :

1. Créer le dépôt Git (si besoin) :
   - `git init`
   - `git branch -M main`
2. Commiter et pousser :
   - `git add .`
   - `git commit -m "Semaine 1: ossature Flask sécurisée + CI/CD"`
   - `git remote add origin <URL>`
   - `git push -u origin main`


## Sécurité / conventions

- Hash des mots de passe : `bcrypt`
- CSRF : `Flask-WTF` (`CSRFProtect`)
- Requêtes SQL : paramétrées (pas de concaténation)
- Chiffrement : les notes sont chiffrées côté application (Fernet) avant insertion en base
- Headers sécurité : `Content-Security-Policy`, `X-Frame-Options`, etc.

