# PatternGeneratorAPI

Une API FastAPI pour transformer des images selon des palettes de couleurs prédéfinies, avec gestion d'utilisateurs et stockage temporaire d'uploads anonymes.

## 🚀 Fonctionnalités

- ✅ **Upload d'images** : PNG, JPG, JPEG
- ✅ **Transformation de couleurs** : Remplacez les couleurs selon des palettes prédéfinies
- ✅ **Gestion utilisateurs** : Anonymous, Authenticated, Premium
- ✅ **Sécurité** : Authentification par token Bearer, contrôle d'accès, permissions
- ✅ **Fichiers temporaires** : Suppression automatique des uploads anonymes après expiration
- ✅ **REST API** : Endpoints modernes et sécurisés
- ✅ **Stockage sûr** : Écriture atomique, permissions restrictives
- ✅ **Tests complets** : 14 tests unitaires et d'intégration

## 📋 Prérequis

- Python 3.10+
- pip

## 🔧 Installation rapide

```bash
# Clone et entrée
git clone <repository>
cd PatternGeneratorAPI

# Environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installation
pip install -r requirement.txt

# Lancement
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

L'API est disponible à `http://localhost:8000`

### Swagger UI (Documentation interactive)
`http://localhost:8000/docs`

## 🔑 Authentification

L'API utilise l'authentification par **token Bearer**.

### Enregistrement d'un utilisateur
```bash
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "password123",
    "role": "user"
  }'
```

### Connexion
```bash
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "password123"
  }'
```

### Utilisation du token
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/image_process/upload_image/
```

## 📸 Endpoints principaux

### Upload

#### Upload anonyme (1h d'expiration)
```bash
curl -F "file=@image.png" http://localhost:8000/image_process/upload_image/
```

**Réponse:**
```json
{
  "filename": "image.png",
  "anonymous": true,
  "access_token": "abc123...",
  "expires_at": "2026-06-15T16:00:00"
}
```

#### Upload authentifié (pas d'expiration)
```bash
curl -H "Authorization: Bearer TOKEN" \
  -F "file=@image.png" \
  http://localhost:8000/image_process/upload_image/
```

### Traitement

#### Remplacer les couleurs
```bash
curl "http://localhost:8000/image_process/replace_color/image.png/Hama"
```

Palettes disponibles: `Hama`, `Perler`, `Nabbi`, etc.

### Récupération

#### Fichier anonyme
```bash
curl "http://localhost:8000/image_process/get_out_image/colored_image_0.png?access_token=TOKEN" \
  -o result.png
```

#### Fichier authentifié
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/image_process/get_out_image/colored_image_0.png" \
  -o result.png
```

### Suppression

#### Fichier anonyme
```bash
curl -X DELETE "http://localhost:8000/image_process/delete_file/image.png?access_token=TOKEN"
```

#### Fichier authentifié
```bash
curl -X DELETE -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/image_process/delete_file/image.png"
```

## 📊 Types d'utilisateurs

| Type | Upload max | Sortie max | Expiration |
|------|-----------|----------|-----------|
| Anonymous | 100 KB | 64×64 px | 1h |
| Authenticated | 1 MB | 96×96 px | ∞ |
| Premium | 10 MB | 128×128 px | ∞ |

## 🧪 Tests

Exécutez tous les tests:
```bash
pytest -v
```

Exécutez les tests d'un module:
```bash
pytest tests/test_api.py -v
pytest tests/test_db.py -v
pytest tests/test_file_write.py -v
```

Voir `TESTING.md` pour plus de détails.

## 📚 Documentation complète

- `API.md` : Documentation détaillée des endpoints et exemples
- `TESTING.md` : Guide de test et coverage

## 🏗️ Architecture

```
.
├── main.py                      # Application FastAPI
├── models.py                    # Modèles Pydantic
├── db.py                        # Logique SQLite
├── middlewares.py               # Middleware d'authentification
├── image_processer/
│   ├── app.py                  # Endpoints image_process
│   ├── file_utils.py           # Helper écriture sûre de fichiers
│   ├── image_processor.py       # Traitement d'images
│   ├── color_chart.py           # Palette de couleurs
│   └── depends.py              # Dépendances FastAPI
├── tests/
│   ├── test_api.py             # Tests d'intégration (10 tests)
│   ├── test_db.py              # Tests DB (3 tests)
│   └── test_file_write.py      # Tests I/O (1 test)
├── .github/workflows/ci.yml     # CI/CD GitHub Actions
├── requirement.txt              # Dépendances Python
└── pytest.ini                   # Configuration pytest
```

## 🔒 Sécurité

- ✅ Authentification token Bearer
- ✅ Contrôle d'accès basé sur propriété
- ✅ Écriture atomique de fichiers (protection TOCTOU)
- ✅ Sanitisation des noms de fichiers (prévention path traversal)
- ✅ Permissions restrictives sur répertoires (0o750) et fichiers (0o640)
- ✅ Nettoyage automatique des fichiers temporaires expirés
- ✅ Validation des types MIME

## 🚀 CI/CD

Tests automatiques sur PR vers `main` via GitHub Actions:
- Python 3.12
- Tous les tests unitaires et d'intégration
- Timeout 10 minutes

## 📝 Licences

Voir `LICENCE` pour les détails.

## 🤝 Contribution

1. Créez une branche depuis `main`
2. Faire vos changements
3. Écrivez/mettez à jour les tests
4. Soumettez une PR
5. Les tests CI doivent passer

## 📞 Support

- Documentation Swagger: `http://localhost:8000/docs`
- Documentation API: `API.md`
- Guides de test: `TESTING.md`
- Tests comme exemples: `tests/test_api.py`

