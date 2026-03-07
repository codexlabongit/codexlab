#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════╗
║          CodexLab — Gestionnaire de produits          ║
║  Utilisez ce script pour ajouter/gérer vos produits   ║
╚═══════════════════════════════════════════════════════╝

USAGE:
  python manage.py add        → Ajouter un nouveau produit (interactif)
  python manage.py list       → Lister tous les produits
  python manage.py delete     → Supprimer un produit
  python manage.py edit       → Modifier un produit existant
  python manage.py stats      → Voir les statistiques du site
  python manage.py reviews    → Voir tous les avis clients
  python manage.py export     → Exporter les produits en CSV
  python manage.py serve      → Lancer un serveur local (ouvre le site)
"""

import json
import os
import sys
import csv
import http.server
import webbrowser
import threading
import re
from datetime import datetime
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
REVIEWS_FILE = DATA_DIR / "reviews.json"
STATS_FILE = DATA_DIR / "stats.json"

# ============================================================
# COLORS FOR TERMINAL
# ============================================================
class C:
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    GREEN   = '\033[92m'
    CYAN    = '\033[96m'
    YELLOW  = '\033[93m'
    RED     = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE    = '\033[94m'
    DIM     = '\033[2m'
    ACCENT  = '\033[38;5;86m'   # Teal like --accent

def banner():
    print(f"""
{C.ACCENT}╔══════════════════════════════════════════════════════╗
║   {C.BOLD}CodexLab — Gestionnaire de Produits{C.RESET}{C.ACCENT}              ║
║   {C.DIM}Marketplace de code premium{C.RESET}{C.ACCENT}                       ║
╚══════════════════════════════════════════════════════╝{C.RESET}
""")

def success(msg): print(f"  {C.GREEN}✓{C.RESET}  {msg}")
def error(msg):   print(f"  {C.RED}✗{C.RESET}  {msg}")
def info(msg):    print(f"  {C.CYAN}→{C.RESET}  {msg}")
def warn(msg):    print(f"  {C.YELLOW}⚠{C.RESET}  {msg}")
def sep():        print(f"  {C.DIM}{'─' * 52}{C.RESET}")

# ============================================================
# DATA HELPERS
# ============================================================
def load_json(path, default):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        save_json(path, default)
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_products(): return load_json(PRODUCTS_FILE, [])
def save_products(p): save_json(PRODUCTS_FILE, p)
def load_reviews():  return load_json(REVIEWS_FILE, [])
def load_stats():    return load_json(STATS_FILE, {"total_products":0,"total_developers":0,"satisfaction_pct":99,"languages_supported":24})
def save_stats(s):   save_json(STATS_FILE, s)

def generate_id(products):
    nums = [int(p['id'].split('_')[1]) for p in products if '_' in p.get('id','')]
    next_num = max(nums) + 1 if nums else 1
    return f"prod_{next_num:03d}"

def update_stats(products):
    s = load_stats()
    s['total_products'] = len(products)
    s['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    save_stats(s)

# ============================================================
# PROMPT HELPERS
# ============================================================
def ask(prompt, default=None, required=True):
    disp = f"{C.CYAN}{prompt}{C.RESET}"
    if default: disp += f" {C.DIM}[{default}]{C.RESET}"
    disp += " : "
    while True:
        val = input(disp).strip()
        if not val and default:
            return default
        if val or not required:
            return val
        warn("Ce champ est requis.")

def ask_int(prompt, default=None, min_val=0, max_val=99999):
    while True:
        val = ask(prompt, str(default) if default is not None else None)
        try:
            v = int(val)
            if min_val <= v <= max_val:
                return v
            warn(f"Entrez un nombre entre {min_val} et {max_val}.")
        except ValueError:
            warn("Entrez un nombre entier valide.")

def ask_float(prompt, default=None, min_val=0, max_val=99999):
    while True:
        val = ask(prompt, str(default) if default is not None else None)
        try:
            v = float(val)
            if min_val <= v <= max_val:
                return v
            warn(f"Entrez un nombre entre {min_val} et {max_val}.")
        except ValueError:
            warn("Entrez un nombre valide (ex: 4.8).")

def ask_list(prompt, default=None):
    info(f"Entrez les éléments séparés par des virgules.")
    val = ask(prompt, default)
    return [x.strip() for x in val.split(',') if x.strip()]

def ask_choice(prompt, choices, default=None):
    for i, c in enumerate(choices, 1):
        print(f"    {C.DIM}{i}.{C.RESET} {c}")
    while True:
        idx = ask(f"{prompt} (1-{len(choices)})", str(choices.index(default)+1) if default in choices else None)
        try:
            v = int(idx)
            if 1 <= v <= len(choices):
                return choices[v-1]
            warn(f"Entrez un nombre entre 1 et {len(choices)}.")
        except ValueError:
            # Check if they typed the value directly
            if idx in choices: return idx
            warn("Choix invalide.")

# ============================================================
# COMMANDS
# ============================================================
def cmd_add():
    banner()
    print(f"  {C.BOLD}Ajouter un nouveau produit{C.RESET}\n")
    sep()

    products = load_products()

    LANGUAGES = ['TypeScript','Python','JavaScript','Go','PHP','Rust','Java','C#','Ruby','Swift','Kotlin','Dart','C++','Other']
    CATEGORIES = ['Authentication','Paiement','Dashboard','API','IA & ChatBot','Email','Storage','DevOps','UI Components','Bot/Scraper','Security','Other']
    EMOJIS_MAP = {
        'Authentication':'🔐','Paiement':'💳','Dashboard':'📊','API':'⚡',
        'IA & ChatBot':'🤖','Email':'📧','Storage':'💾','DevOps':'🐳',
        'UI Components':'🎨','Bot/Scraper':'🕷️','Security':'🛡️','Other':'📦'
    }

    print(f"\n  {C.BOLD}Informations générales{C.RESET}")
    name        = ask("Nom du produit", required=True)
    description = ask("Description complète", required=True)

    print(f"\n  {C.BOLD}Catégorie et langage{C.RESET}")
    category    = ask_choice("Catégorie", CATEGORIES)
    language    = ask_choice("Langage principal", LANGUAGES)
    emoji       = ask("Emoji (laisser vide = auto)", required=False) or EMOJIS_MAP.get(category, '📦')

    print(f"\n  {C.BOLD}Prix et statistiques{C.RESET}")
    price       = ask_int("Prix en € (entier)", default=29, min_val=1)
    downloads   = ask_int("Nombre de téléchargements initiaux", default=0)
    rating      = ask_float("Note initiale (0-5)", default=5.0, min_val=0, max_val=5)
    reviews_count = ask_int("Nombre d'avis initial", default=0)
    lines_of_code = ask_int("Lignes de code (optionnel)", default=0)
    size_kb     = ask_int("Taille en KB (optionnel)", default=0)

    print(f"\n  {C.BOLD}Fonctionnalités{C.RESET}")
    features    = ask_list("Fonctionnalités (séparées par des virgules)", default="Feature 1, Feature 2")

    print(f"\n  {C.BOLD}Tags{C.RESET}")
    tags        = ask_list("Tags (séparés par des virgules)", default="code, premium")

    product = {
        "id"           : generate_id(products),
        "name"         : name,
        "category"     : category,
        "language"     : language,
        "emoji"        : emoji,
        "price"        : price,
        "description"  : description,
        "features"     : features,
        "downloads"    : downloads,
        "rating"       : round(rating, 1),
        "reviews_count": reviews_count,
        "lines_of_code": lines_of_code if lines_of_code > 0 else None,
        "size_kb"      : size_kb if size_kb > 0 else None,
        "created_at"   : datetime.now().strftime('%Y-%m-%d'),
        "tags"         : [t.lower().strip() for t in tags]
    }

    print(f"\n  {C.BOLD}Récapitulatif{C.RESET}")
    sep()
    print(f"  {C.CYAN}ID          :{C.RESET} {product['id']}")
    print(f"  {C.CYAN}Nom         :{C.RESET} {product['name']}")
    print(f"  {C.CYAN}Catégorie   :{C.RESET} {product['emoji']} {product['category']}")
    print(f"  {C.CYAN}Langage     :{C.RESET} {product['language']}")
    print(f"  {C.CYAN}Prix        :{C.RESET} {C.ACCENT}{product['price']}€{C.RESET}")
    print(f"  {C.CYAN}Desc.       :{C.RESET} {product['description'][:60]}...")
    print(f"  {C.CYAN}Fonctions   :{C.RESET} {', '.join(product['features'][:3])}...")
    sep()

    confirm = ask("Confirmer l'ajout ? (o/n)", default="o")
    if confirm.lower() in ('o', 'oui', 'y', 'yes'):
        products.append(product)
        save_products(products)
        update_stats(products)
        success(f"Produit '{name}' ajouté avec l'ID {product['id']}")
        info(f"Total produits : {len(products)}")
    else:
        warn("Ajout annulé.")

def cmd_list():
    banner()
    products = load_products()
    reviews  = load_reviews()

    if not products:
        warn("Aucun produit dans la base.")
        return

    print(f"  {C.BOLD}Liste des produits ({len(products)}){C.RESET}\n")
    sep()

    for p in products:
        prod_reviews = [r for r in reviews if r.get('product_id') == p['id']]
        avg = round(sum(r['rating'] for r in prod_reviews) / len(prod_reviews), 1) if prod_reviews else p.get('rating', '—')
        print(f"\n  {C.ACCENT}{p['id']}{C.RESET}  {C.BOLD}{p.get('emoji','')} {p['name']}{C.RESET}")
        print(f"      {C.DIM}Prix:{C.RESET} {C.GREEN}{p['price']}€{C.RESET}   "
              f"{C.DIM}Lang:{C.RESET} {p['language']}   "
              f"{C.DIM}Catégorie:{C.RESET} {p['category']}")
        print(f"      {C.DIM}Note:{C.RESET} {avg}★   "
              f"{C.DIM}DL:{C.RESET} {p.get('downloads',0)}   "
              f"{C.DIM}Avis:{C.RESET} {len(prod_reviews)}/{p.get('reviews_count',0)}   "
              f"{C.DIM}Ajouté:{C.RESET} {p.get('created_at','—')}")
        print(f"      {C.DIM}{p['description'][:70]}...{C.RESET}")

    sep()
    print(f"\n  {C.DIM}Fichier : {PRODUCTS_FILE}{C.RESET}")

def cmd_delete():
    banner()
    products = load_products()
    if not products:
        warn("Aucun produit à supprimer.")
        return

    print(f"  {C.BOLD}Supprimer un produit{C.RESET}\n")
    for i, p in enumerate(products, 1):
        print(f"  {C.DIM}{i}.{C.RESET} [{p['id']}] {p.get('emoji','')} {p['name']} — {C.GREEN}{p['price']}€{C.RESET}")

    pid = ask("\nID du produit à supprimer (ex: prod_001)", required=True)
    prod = next((p for p in products if p['id'] == pid), None)
    if not prod:
        error(f"Produit '{pid}' introuvable.")
        return

    print(f"\n  {C.RED}Supprimer :{C.RESET} {prod.get('emoji','')} {prod['name']}")
    confirm = ask("Confirmer la suppression ? (o/n)", default="n")
    if confirm.lower() in ('o', 'oui', 'y', 'yes'):
        products = [p for p in products if p['id'] != pid]
        save_products(products)
        update_stats(products)
        success(f"Produit '{pid}' supprimé.")
    else:
        warn("Suppression annulée.")

def cmd_edit():
    banner()
    products = load_products()
    if not products:
        warn("Aucun produit à modifier.")
        return

    print(f"  {C.BOLD}Modifier un produit{C.RESET}\n")
    for i, p in enumerate(products, 1):
        print(f"  {C.DIM}{i}.{C.RESET} [{p['id']}] {p.get('emoji','')} {p['name']} — {C.GREEN}{p['price']}€{C.RESET}")

    pid = ask("\nID du produit à modifier (ex: prod_001)", required=True)
    idx = next((i for i, p in enumerate(products) if p['id'] == pid), None)
    if idx is None:
        error(f"Produit '{pid}' introuvable.")
        return

    p = products[idx]
    print(f"\n  {C.BOLD}Modification de : {p.get('emoji','')} {p['name']}{C.RESET}")
    info("Laissez vide pour conserver la valeur actuelle.\n")

    fields = [
        ('name', 'Nom', 'str'),
        ('description', 'Description', 'str'),
        ('price', 'Prix €', 'int'),
        ('rating', 'Note (0-5)', 'float'),
        ('downloads', 'Téléchargements', 'int'),
        ('reviews_count', 'Nombre d\'avis', 'int'),
        ('lines_of_code', 'Lignes de code', 'int'),
        ('size_kb', 'Taille KB', 'int'),
        ('language', 'Langage', 'str'),
        ('category', 'Catégorie', 'str'),
        ('emoji', 'Emoji', 'str'),
    ]

    for key, label, typ in fields:
        current = p.get(key, '')
        val = ask(f"{label}", default=str(current) if current is not None else '', required=False)
        if val and val != str(current):
            if typ == 'int':
                try: p[key] = int(val)
                except: pass
            elif typ == 'float':
                try: p[key] = float(val)
                except: pass
            else:
                p[key] = val

    # Features
    update_feat = ask("Modifier les fonctionnalités ? (o/n)", default="n", required=False)
    if update_feat and update_feat.lower() in ('o','y','oui','yes'):
        print(f"  Actuelles : {', '.join(p.get('features', []))}")
        p['features'] = ask_list("Nouvelles fonctionnalités")

    products[idx] = p
    save_products(products)
    update_stats(products)
    success(f"Produit '{pid}' mis à jour.")

def cmd_stats():
    banner()
    products = load_products()
    reviews  = load_reviews()
    stats    = load_stats()

    print(f"  {C.BOLD}Statistiques CodexLab{C.RESET}\n")
    sep()
    print(f"  {C.CYAN}Produits      :{C.RESET} {C.ACCENT}{len(products)}{C.RESET}")
    total_dl = sum(p.get('downloads', 0) for p in products)
    print(f"  {C.CYAN}Télécharg.    :{C.RESET} {C.ACCENT}{total_dl:,}{C.RESET}")
    print(f"  {C.CYAN}Avis clients  :{C.RESET} {C.ACCENT}{len(reviews)}{C.RESET}")
    if reviews:
        avg = sum(r['rating'] for r in reviews) / len(reviews)
        print(f"  {C.CYAN}Note moyenne  :{C.RESET} {C.ACCENT}{avg:.1f}★{C.RESET}")
    print(f"  {C.CYAN}Développeurs  :{C.RESET} {C.ACCENT}{stats.get('total_developers',0):,}{C.RESET}")
    print(f"  {C.CYAN}Satisfaction  :{C.RESET} {C.ACCENT}{stats.get('satisfaction_pct',99)}%{C.RESET}")
    sep()

    if products:
        print(f"\n  {C.BOLD}Top produits (par téléchargements){C.RESET}")
        sorted_p = sorted(products, key=lambda x: x.get('downloads',0), reverse=True)[:5]
        for p in sorted_p:
            bar_len = int(p.get('downloads',0) / max(sorted_p[0].get('downloads',1), 1) * 20)
            bar = C.ACCENT + '█' * bar_len + C.DIM + '░' * (20 - bar_len) + C.RESET
            print(f"  {bar}  {p['name']} ({p.get('downloads',0)} DL)")

    revenue_estimate = sum(p['price'] * p.get('downloads', 0) for p in products)
    print(f"\n  {C.BOLD}Revenu estimé (si 100% conversion):{C.RESET} {C.GREEN}{revenue_estimate:,.0f}€{C.RESET}")
    sep()

def cmd_reviews():
    banner()
    reviews  = load_reviews()
    products = load_products()

    if not reviews:
        warn("Aucun avis pour l'instant.")
        return

    print(f"  {C.BOLD}Avis clients ({len(reviews)}){C.RESET}\n")
    sep()

    for r in reversed(reviews):
        prod = next((p for p in products if p['id'] == r.get('product_id')), None)
        stars = '★' * r['rating'] + '☆' * (5 - r['rating'])
        print(f"\n  {C.YELLOW}{stars}{C.RESET}  {C.BOLD}{r['author']}{C.RESET}  {C.DIM}({r.get('role','')}){C.RESET}")
        if prod:
            print(f"  {C.DIM}Produit :{C.RESET} {prod.get('emoji','')} {prod['name']}")
        print(f"  {C.DIM}Date    :{C.RESET} {r.get('date','—')}")
        print(f"  \"{r['text']}\"")
    sep()

def cmd_export():
    banner()
    products = load_products()
    if not products:
        warn("Aucun produit à exporter.")
        return

    export_path = BASE_DIR / f"export_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    fieldnames = ['id','name','category','language','price','rating','downloads','reviews_count','lines_of_code','size_kb','description','created_at','tags']

    with open(export_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            row = {k: p.get(k, '') for k in fieldnames}
            if isinstance(row['tags'], list): row['tags'] = ', '.join(row['tags'])
            writer.writerow(row)

    success(f"Exporté : {export_path}")

def cmd_serve():
    banner()
    port = 8080

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(BASE_DIR), **kwargs)
        def log_message(self, format, *args):
            print(f"  {C.DIM}[server]{C.RESET} {format % args}")

    def open_browser():
        import time; time.sleep(0.8)
        webbrowser.open(f'http://localhost:{port}')

    threading.Thread(target=open_browser, daemon=True).start()
    info(f"Serveur démarré : {C.ACCENT}http://localhost:{port}{C.RESET}")
    info("Appuyez sur Ctrl+C pour arrêter.\n")
    try:
        with http.server.HTTPServer(('', port), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n  {C.DIM}Serveur arrêté.{C.RESET}")

def cmd_help():
    banner()
    cmds = [
        ("add",     "Ajouter un nouveau produit (interactif)"),
        ("list",    "Lister tous les produits avec détails"),
        ("edit",    "Modifier un produit existant"),
        ("delete",  "Supprimer un produit"),
        ("stats",   "Voir les statistiques du site"),
        ("reviews", "Voir tous les avis clients"),
        ("export",  "Exporter les produits en CSV"),
        ("serve",   "Lancer un serveur local et ouvrir le site"),
    ]
    print(f"  {C.BOLD}Commandes disponibles{C.RESET}\n")
    for cmd, desc in cmds:
        print(f"  {C.ACCENT}python manage.py {cmd:<10}{C.RESET}  {desc}")
    print()

# ============================================================
# ENTRY POINT
# ============================================================
COMMANDS = {
    'add':     cmd_add,
    'list':    cmd_list,
    'edit':    cmd_edit,
    'delete':  cmd_delete,
    'stats':   cmd_stats,
    'reviews': cmd_reviews,
    'export':  cmd_export,
    'serve':   cmd_serve,
    'help':    cmd_help,
}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        cmd_help()
        if len(sys.argv) >= 2:
            error(f"Commande inconnue : '{sys.argv[1]}'")
        sys.exit(0)
    COMMANDS[sys.argv[1]]()
