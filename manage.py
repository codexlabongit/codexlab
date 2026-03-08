import json
import csv
import threading
import http.server
import webbrowser
from datetime import datetime
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox
import random

# ============================================================
# CONFIGURATION CUSTOMTKINTER
# ============================================================
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Thèmes: "blue", "green", "dark-blue"

# ============================================================
# PATHS ET DONNÉES (Identiques à ton script)
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
REVIEWS_FILE = DATA_DIR / "reviews.json"
STATS_FILE = DATA_DIR / "stats.json"

LANGUAGES = ['TypeScript', 'Python', 'JavaScript', 'Go', 'PHP', 'Rust', 'Java', 'C#', 'Ruby', 'Swift', 'Kotlin', 'Dart', 'C++', 'Other']
CATEGORIES = ['Authentication', 'Paiement', 'Dashboard', 'API', 'IA & ChatBot', 'Email', 'Storage', 'DevOps', 'UI Components', 'Bot/Scraper', 'Security', 'Other']
EMOJIS_MAP = {
    'Authentication':'🔐', 'Paiement':'💳', 'Dashboard':'📊', 'API':'⚡',
    'IA & ChatBot':'🤖', 'Email':'📧', 'Storage':'💾', 'DevOps':'🐳',
    'UI Components':'🎨', 'Bot/Scraper':'🕷️', 'Security':'🛡️', 'Other':'📦'
}

def load_json(path, default):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_products(): return load_json(PRODUCTS_FILE, [])
def save_products(p): save_json(PRODUCTS_FILE, p)
def load_reviews():  return 0
def load_stats():    return 0

def generate_id(products):
    nums = []
    for p in products:
        # On vérifie que p est bien un dictionnaire avant d'essayer d'accéder à 'id'
        if isinstance(p, dict) and 'id' in p and isinstance(p['id'], str):
            if '_' in p['id']:
                try:
                    nums.append(int(p['id'].split('_')[1]))
                except (ValueError, IndexError):
                    continue
    next_num = max(nums) + 1 if nums else 1
    return f"prod_{next_num:03d}"

# ============================================================
# INTERFACE GRAPHIQUE
# ============================================================
class CodexLabApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CodexLab — Gestionnaire de Produits")
        self.geometry("900x600")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Données ---
        self.products = load_products()
        self.reviews = load_reviews()

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="CodexLab", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="📊 Dashboard", command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_list = ctk.CTkButton(self.sidebar_frame, text="📦 Produits", command=self.show_products)
        self.btn_list.grid(row=2, column=0, padx=20, pady=10)

        self.btn_add = ctk.CTkButton(self.sidebar_frame, text="➕ Ajouter", command=self.show_add_form)
        self.btn_add.grid(row=3, column=0, padx=20, pady=10)

        self.btn_export = ctk.CTkButton(self.sidebar_frame, text="📥 Exporter CSV", command=self.export_csv, fg_color="transparent", border_width=2)
        self.btn_export.grid(row=4, column=0, padx=20, pady=10)

        self.btn_serve = ctk.CTkButton(self.sidebar_frame, text="🌐 Lancer Serveur", command=self.start_server, fg_color="#28a745", hover_color="#218838")
        self.btn_serve.grid(row=5, column=0, padx=20, pady=10)

        # --- Main Content Frame ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.current_frame = None
        self.show_dashboard()

    def clear_main_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()

    # --- VUE : DASHBOARD ---
    def show_dashboard(self):
        self.clear_main_frame()
        self.products = load_products() # Rafraîchir les données
        
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.grid(row=0, column=0, sticky="nsew")

        title = ctk.CTkLabel(self.current_frame, text="Dashboard Statistiques", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(pady=(0, 20), anchor="w")

        # Cartes de stats
        stats_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10)

        # On utilise "or 0" pour forcer la valeur à 0 si le champ est à null/None
        # On vérifie que p est un dictionnaire avant de faire .get()
        total_dl = sum((p.get('downloads') or 0) for p in self.products if isinstance(p, dict))
        revenue = sum((p.get('price') or 0) * (p.get('downloads') or 0) for p in self.products if isinstance(p, dict))

        self.create_stat_card(stats_frame, "Total Produits", len(self.products), "📦").pack(side="left", expand=True, padx=5)
        self.create_stat_card(stats_frame, "Téléchargements", f"{total_dl:,}", "⬇️").pack(side="left", expand=True, padx=5)
        self.create_stat_card(stats_frame, "Revenu Estimé", f"{revenue:,.0f} €", "💰").pack(side="left", expand=True, padx=5)

    def create_stat_card(self, parent, title, value, icon):
        card = ctk.CTkFrame(parent, corner_radius=15)
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=40)).pack(pady=(15, 5))
        ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=24, weight="bold"), text_color="#1f6aa5").pack()
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14)).pack(pady=(0, 15))
        return card
    def show_products(self):
        self.clear_main_frame()
        self.products = load_products()

        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        
        title = ctk.CTkLabel(self.current_frame, text="Liste des Produits", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(pady=(0, 20), anchor="w")

        scrollable_frame = ctk.CTkScrollableFrame(self.current_frame)
        scrollable_frame.pack(fill="both", expand=True)

        for p in self.products:
            card = ctk.CTkFrame(scrollable_frame, corner_radius=10)
            card.pack(fill="x", pady=5, padx=5)
            
            header = ctk.CTkLabel(card, text=f"{p.get('emoji','')} {p['name']} ({p['id']})", font=ctk.CTkFont(size=16, weight="bold"))
            header.pack(anchor="w", padx=10, pady=(10, 0))
            
            info = ctk.CTkLabel(card, text=f"Prix: {p['price']}€ | Langage: {p['language']} | Catégorie: {p['category']} | Téléchargements: {p.get('downloads',0)}", text_color="gray")
            info.pack(anchor="w", padx=10, pady=(0, 10))

    # --- VUE : AJOUTER UN PRODUIT ---
    def show_add_form(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(self.current_frame, text="Ajouter un Produit", font=ctk.CTkFont(size=28, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # Champs du formulaire
        self.entry_name = self.create_form_row("Nom du produit :", 1)
        self.entry_desc = self.create_form_row("Description :", 2)
        
        ctk.CTkLabel(self.current_frame, text="Catégorie :").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.opt_category = ctk.CTkOptionMenu(self.current_frame, values=CATEGORIES)
        self.opt_category.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.current_frame, text="Langage :").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.opt_lang = ctk.CTkOptionMenu(self.current_frame, values=LANGUAGES)
        self.opt_lang.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        
        self.lines_of_code_raw = self.create_form_row("Nombre de lignes de code:",5)

        self.is_finish = ctk.StringVar(value="Non")
        self.switch_fini = ctk.CTkSwitch(
         self.current_frame, 
         text="Produit Fini ?", 
         variable=self.is_finish, 
         onvalue="Oui", 
         offvalue="Non"
        )
        self.switch_fini.grid(row=9, column=1, padx=10, pady=10, sticky="w")

        self.entry_price = self.create_form_row("Prix (€) :", 6, default="5")
        self.entry_features = self.create_form_row("Fonctionnalités (séparées par des virgules) :", 7)

        btn_save = ctk.CTkButton(self.current_frame, text="Sauvegarder le Produit", font=ctk.CTkFont(weight="bold"), command=self.save_new_product)
        btn_save.grid(row=8, column=0, columnspan=2, pady=30)

    def create_form_row(self, label_text, row, default=""):
        ctk.CTkLabel(self.current_frame, text=label_text).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry = ctk.CTkEntry(self.current_frame, placeholder_text=label_text)
        if default: entry.insert(0, default)
        entry.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        return entry

    def save_new_product(self):
        name = self.entry_name.get().strip()
        desc = self.entry_desc.get().strip()
        cat = self.opt_category.get()
        lang = self.opt_lang.get()
        is_finish = self.is_finish.get()
        price_raw = self.entry_price.get().strip()
        features = [f.strip() for f in self.entry_features.get().split(',') if f.strip()]

        # Validation du prix AVANT conversion
        if not price_raw.isdigit():
            messagebox.showerror("Erreur", "Le prix doit être un nombre entier.")
            return
        
        price = int(price_raw)
        lines_of_code = int(self.lines_of_code_raw.get())

        if not name or not desc:
            messagebox.showerror("Erreur", "Veuillez remplir le nom et la description.")
            return
        types1 = "standard"
        if is_finish== "Non" :
            types1 ="wip"
        new_product = {
            "id": f"prod_{random.randint(100, 999999)}", # Format plus propre pour ton JS
            "name": name,
            "category": cat,
            "type": types1,
            "language": lang,
            "emoji": EMOJIS_MAP.get(cat, '📦'),
            "price": price,
            "description": desc,
            "features": features,
            "downloads": 0,
            "rating": str(random.uniform(4,5))[:3], # Ajouté pour ton JavaScript
            "lines_of_code": lines_of_code,
            "created_at": datetime.now().strftime('%Y-%m-%d'),
            "tags": ["nouveau"]
        }

        self.products.append(new_product)
        save_products(self.products)
        messagebox.showinfo("Succès", f"Produit '{name}' ajouté avec succès !")
        self.show_products() # Rediriger vers la liste

    # --- ACTIONS RAPIDES ---
    def export_csv(self):
        if not self.products:
            messagebox.showwarning("Vide", "Aucun produit à exporter.")
            return
            
        export_path = BASE_DIR / f"export_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        fieldnames = ['id','name','category','language','price','downloads','description','created_at']

        with open(export_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for p in self.products:
                writer.writerow(p)

        messagebox.showinfo("Export réussi", f"Fichier exporté :\n{export_path}")

    def start_server(self):
        port = 8080
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(BASE_DIR), **kwargs)

        def run_server():
            with http.server.HTTPServer(('', port), Handler) as httpd:
                httpd.serve_forever()

        threading.Thread(target=run_server, daemon=True).start()
        webbrowser.open(f'http://localhost:{port}')
        self.btn_serve.configure(text="🌐 Serveur En Ligne", state="disabled", fg_color="gray")

if __name__ == "__main__":
    app = CodexLabApp()
    app.mainloop()