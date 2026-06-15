# Configuration CORS - Frontend

## 🔓 CORS Activé

La configuration CORS a été ajoutée à `main.py` pour autoriser les requêtes cross-origin du frontend.

## Origines Autorisées

```python
allow_origins=[
    "http://localhost:5173",    # Vite default (Vue, React, Svelte)
    "http://localhost:3000",    # Alternative port
    "http://localhost:5173/",   # With trailing slash
]
```

## Mise en Place

Le frontend sur `http://localhost:5173` peut maintenant faire des requêtes à l'API sans erreur CORS :

```javascript
// Frontend (Vue/React/etc)
const token = "your_token_here";

// Enregistrement
fetch('http://localhost:8000/users/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'john', password: 'pw' }),
  credentials: 'include'
});

// Upload avec token
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/image_process/upload_image/', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData,
  credentials: 'include'
});
```

## Configuration Production

Pour la production, adaptez les origines autorisées:

```python
allow_origins=[
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

## Options de Déploiement

### Avec Docker
```dockerfile
ENV CORS_ORIGINS=https://yourdomain.com
```

### Avec Variables d'Environnement
```python
import os

allow_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
```

## Tester CORS

```bash
# Test depuis terminal
curl -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:8000/users/register -v

# Vous devez voir:
# Access-Control-Allow-Origin: http://localhost:5173 ✅
```

## Notes

- ✅ `allow_credentials=True` : Cookies et autorisation inclus
- ✅ `allow_methods=["*"]` : GET, POST, DELETE, etc.
- ✅ `allow_headers=["*"]` : Tous les headers (including Authorization)

## Erreurs Courants

**Erreur: "No 'Access-Control-Allow-Origin' header"**
- ✅ Vérifiez que le frontend utilise `http://localhost:5173` exact
- ✅ Vérifiez que `credentials: 'include'` est présent dans fetch
- ✅ Redémarrez le serveur après modification

**Le frontend sur port 3000?**
- ✅ Ajoutez à `allow_origins`: `"http://localhost:3000"`
- ✅ Relancez l'API

