# CodexLab — Documentation

## Structure des fichiers

```
codexlab/
├── index.html          ← Le site (ouvrir dans le navigateur)
├── manage.py           ← Script Python pour gérer les produits
├── data/
│   ├── products.json   ← Base de données des produits
│   ├── reviews.json    ← Tous les avis clients
│   └── stats.json      ← Statistiques affichées sur le site
└── README.md
```

## Lancer le site

### Option 1 — Avec le script Python (RECOMMANDÉ)
```bash
python manage.py serve
```
Ouvre automatiquement le navigateur sur http://localhost:8080

### Option 2 — Manuellement
```bash
# Python 3
python -m http.server 8080 --directory .
# Puis ouvrir : http://localhost:8080
```

> ⚠️ Ne pas ouvrir `index.html` directement en `file://` sous Chrome
> (les requêtes JSON échoueront). Utilisez un serveur local.
> Firefox fonctionne directement en file://.

---

## Gérer les produits

### Ajouter un produit
```bash
python manage.py add
```
Guide interactif : nom, description, prix, langage, fonctionnalités, etc.

### Lister les produits
```bash
python manage.py list
```

### Modifier un produit
```bash
python manage.py edit
```

### Supprimer un produit
```bash
python manage.py delete
```

### Voir les stats
```bash
python manage.py stats
```

### Voir les avis clients
```bash
python manage.py reviews
```

### Exporter en CSV
```bash
python manage.py export
```

---

## Configuration

### Changer l'email de contact
Dans `index.html`, ligne :
```javascript
const CONTACT_EMAIL = 'contact@codexlab.fr';
```
Remplacez par votre adresse email.

### Modifier les stats affichées (compteurs)
Éditez `data/stats.json` :
```json
{
  "total_products": 4,
  "total_developers": 48000,
  "satisfaction_pct": 99,
  "languages_supported": 24
}
```
`total_products` est mis à jour automatiquement à chaque `manage.py add/delete`.

---

## Comment fonctionnent les avis

- Les visiteurs peuvent laisser un avis directement depuis la fiche produit
- Les avis sont sauvegardés dans `localStorage` du navigateur du visiteur
- Les avis sont aussi affichés dans la section globale "Ce qu'ils en disent"
- Vous pouvez voir tous les avis avec `python manage.py reviews`

---

## Format d'un produit (products.json)

```json
{
  "id": "prod_001",
  "name": "Nom du produit",
  "category": "Authentication",
  "language": "TypeScript",
  "emoji": "🔐",
  "price": 49,
  "description": "Description complète...",
  "features": ["Feature 1", "Feature 2", "Feature 3"],
  "downloads": 1247,
  "rating": 4.9,
  "reviews_count": 218,
  "lines_of_code": 3840,
  "size_kb": 124,
  "created_at": "2024-11-15",
  "tags": ["nextjs", "auth", "typescript"]
}
```
