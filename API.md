# PatternGeneratorAPI - Documentation

Une API FastAPI pour traiter et transformer les images en couleurs selon des palettes prédéfinies, avec gestion des utilisateurs (anonymes, authentifiés, premium).

## Table des matières

- [Installation](#installation)
- [Démarrage](#démarrage)
- [Authentification](#authentification)
- [Endpoints](#endpoints)
- [Exemples d'utilisation](#exemples-dutilisation)
- [Gestion des fichiers](#gestion-des-fichiers)
- [Erreurs](#erreurs)

## Installation

### Préalables

- Python 3.10+
- pip

### Étapes

1. Clonez le repository et entrez dans le répertoire:
```bash
cd PatternGeneratorAPI
```

2. Créez et activez un environnement virtuel:
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Installez les dépendances:
```bash
pip install -r requirement.txt
```

## Démarrage

Lancez le serveur avec uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera disponible à `http://localhost:8000`

Visualisez la documentation interactive (Swagger UI): `http://localhost:8000/docs`

## Authentification

### Types d'utilisateurs

- **Anonymous** : Pas d'authentification requise. Les fichiers uploadés expirent après 1 heure.
- **Authenticated** : Utilisateur enregistré. Les fichiers n'expirent pas.
- **Premium** : Même que Authenticated (extensible pour futurs bénéfices premium).

### Token Bearer

L'authentification utilise des tokens Bearer dans le header `Authorization`:

```
Authorization: Bearer <token>
```

## Endpoints

### Utilisateurs

#### Enregistrement
```
POST /users/register
```

**Body:**
```json
{
  "username": "john_doe",
  "password": "secure_password",
  "role": "user"
}
```

**Réponse (200):**
```json
{
  "token": "abc123def456..."
}
```

#### Connexion
```
POST /users/login
```

**Body:**
```json
{
  "username": "john_doe",
  "password": "secure_password"
}
```

**Réponse (200):**
```json
{
  "token": "abc123def456..."
}
```

### Upload d'images

#### Upload anonyme
```
POST /image_process/upload_image/
```

**Paramètres:**
- `file` (multipart/form-data, requis) : Fichier PNG/JPG/JPEG

**Réponse (200):**
```json
{
  "filename": "image.png",
  "content_type": "image/png",
  "size": 12345,
  "anonymous": true,
  "expires_at": "2026-06-15T16:00:00.000000",
  "access_token": "a1b2c3d4e5..."
}
```

**Notes:**
- Les fichiers anonymes expirent après 1 heure
- Conserver le `access_token` pour accéder au fichier ultérieurement
- Chaque accès au fichier réinitialise la durée de validité

#### Upload authentifié
```
POST /image_process/upload_image/
Authorization: Bearer <token>
```

**Paramètres:**
- `file` (multipart/form-data, requis) : Fichier PNG/JPG/JPEG

**Réponse (200):**
```json
{
  "filename": "image_auth.png",
  "content_type": "image/png",
  "size": 12345,
  "anonymous": false,
  "expires_at": null
}
```

**Notes:**
- Pas de token d'accès pour les fichiers authentifiés
- Pas d'expiration - les fichiers sont disponibles indéfiniment

### Traitement d'images

#### Remplacer les couleurs
```
GET /image_process/replace_color/{file_name}/{chart}
```

**Paramètres:**
- `file_name` (str, path) : Nom du fichier uploadé
- `chart` (str, path) : Palette de couleurs (ex: "Hama", "Perler", etc.)
- `max_color` (int, query, optionnel) : Nombre max de couleurs (-1 = illimité)
- `max_pixel` (int, query, optionnel) : Taille max en pixels (-1 = limite selon le rôle)

**Réponse (200):**
```json
{
  "process": "started",
  "out_file_name": "colored_image_0.png"
}
```

**Notes:**
- Le traitement se fait en arrière-plan
- Vérifiez le `out_file_name` pour récupérer le résultat

#### Obtenir l'image traitée

**Anonyme:**
```
GET /image_process/get_out_image/{filename}?access_token={access_token}
```

**Authentifié:**
```
GET /image_process/get_out_image/{filename}
Authorization: Bearer <token>
```

**Réponse (200):**
- Fichier image binaire

**Notes:**
- Pour les fichiers anonymes : chaque accès réinitialise la validité (TTL +1h)
- Pour les fichiers authentifiés : accessible par propriétaire uniquement

#### Lister les palettes disponibles
```
GET /image_process/chart_keys/
```

**Réponse (200):**
```json
{
  "chart_keys": ["Hama", "HamaMini", "Nabbi", "Perler", "PerlerMini", ...]
}
```

#### Détails d'une palette
```
GET /image_process/chart_item_details/{key}
```

**Réponse (200):**
```json
{
  "name": "Hama",
  "parent": null,
  "path": "https://beadcolors.eremes.xyz/raw/hama.csv"
}
```

#### Obtenir les couleurs d'une palette
```
GET /image_process/get_chart/{key}
```

**Réponse (200):**
```
CSV data containing colors for the specified chart
```

### Suppression de fichiers

#### Supprimer un fichier anonyme
```
DELETE /image_process/delete_file/{filename}?access_token={access_token}
```

**Réponse (200):**
```json
{
  "success": true,
  "message": "File image.png deleted",
  "filename": "image.png"
}
```

#### Supprimer un fichier authentifié
```
DELETE /image_process/delete_file/{filename}
Authorization: Bearer <token>
```

**Réponse (200):**
```json
{
  "success": true,
  "message": "File image.png deleted",
  "filename": "image.png"
}
```

**Codes d'erreur:**
- `403` : Accès refusé (token invalide ou propriétaire différent)
- `404` : Fichier non trouvé
- `500` : Erreur serveur

## Exemples d'utilisation

### Exemple 1: Upload anonyme, traitement et récupération

```bash
# Upload anonyme
UPLOAD=$(curl -X POST http://localhost:8000/image_process/upload_image/ \
  -F "file=@image.png")
FILENAME=$(echo $UPLOAD | jq -r '.filename')
ACCESS_TOKEN=$(echo $UPLOAD | jq -r '.access_token')

echo "Fichier: $FILENAME"
echo "Token: $ACCESS_TOKEN"

# Traiter l'image (remplacer les couleurs avec palette Hama)
curl -X GET "http://localhost:8000/image_process/replace_color/$FILENAME/Hama"

# Récupérer l'image traitée
curl -X GET "http://localhost:8000/image_process/get_out_image/colored_image_0.png?access_token=$ACCESS_TOKEN" \
  --output resultat.png

# Supprimer le fichier
curl -X DELETE "http://localhost:8000/image_process/delete_file/$FILENAME?access_token=$ACCESS_TOKEN"
```

### Exemple 2: Upload authentifié avec gestion utilisateur

```bash
# Enregistrer un utilisateur
REGISTER=$(curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"mypassword"}')
TOKEN=$(echo $REGISTER | jq -r '.token')

echo "Token d'accès: $TOKEN"

# Upload du fichier
UPLOAD=$(curl -X POST http://localhost:8000/image_process/upload_image/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@image.png")
FILENAME=$(echo $UPLOAD | jq -r '.filename')

# Traiter l'image
curl -X GET "http://localhost:8000/image_process/replace_color/$FILENAME/Perler" \
  -H "Authorization: Bearer $TOKEN"

# Récupérer le résultat
curl -X GET "http://localhost:8000/image_process/get_out_image/colored_image_0.png" \
  -H "Authorization: Bearer $TOKEN" \
  --output resultat.png
```

### Exemple 3: Lister les palettes disponibles

```bash
# Lister les clés disponibles
curl -X GET http://localhost:8000/image_process/chart_keys/

# Obtenir les couleurs d'une palette spécifique
curl -X GET http://localhost:8000/image_process/get_chart/Hama \
  -o palette_hama.csv
```

## Gestion des fichiers

### Limites de taille

| Utilisateur | Upload max | Sortie max (pixels) |
|-------------|-----------|-------------------|
| Anonymous   | 100 KB    | 64 × 64           |
| Authenticated | 1 MB    | 96 × 96           |
| Premium     | 10 MB     | 128 × 128         |

### Durée de validité

- **Anonymous** : 1 heure (réinitialisée à chaque accès)
- **Authenticated** : Illimitée (jusqu'à suppression manuelle)

### Nettoyage automatique

Les fichiers anonymes expirés sont supprimés automatiquement toutes les 60 secondes par une tâche d'arrière-plan.

## Erreurs

### Codes HTTP

| Code | Signification |
|------|-------------|
| 200  | OK |
| 400  | Mauvaise requête |
| 401  | Non authentifié / Identifiants invalides |
| 402  | Taille requise supérieure à la limite (Authenticated) |
| 403  | Accès refusé / Permission insuffisante |
| 404  | Ressource non trouvée |
| 413  | Fichier trop volumineux |
| 415  | Type de contenu non supporté |
| 500  | Erreur serveur |

### Exemples d'erreur

**Fichier não trouvé:**
```json
{
  "status": "image does not exists yet, try again later"
}
```

**Accès refusé:**
```
Forbidden
```

**Taille dépassée:**
```
Image size too big, max size allowed: 102400
```

## Best Practices

1. **Authentification**: Utilisez des tokens Bearer avec HTTPS en production
2. **Fichiers anonymes**: Conservez le `access_token` dans un lieu sûr (localStorage/sessionStorage côté client)
3. **Nettoyage**: Supprimez manuellement les fichiers dont vous n'avez plus besoin
4. **Timeouts**: Accédez régulièrement aux fichiers anonymes pour réinitialiser la durée de validité
5. **Logging**: Monitorez les erreurs 401 et 403 pour détecter les tentatives d'accès non autorisé

## Support

Pour les problèmes ou questions :
- Consultez la documentation Swagger : `http://localhost:8000/docs`
- Vérifiez les logs du serveur
- Lisez les tests unitaires dans `TESTING.md`

