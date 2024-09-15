import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import random
import logging
import threading
import re
from datetime import datetime
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def resource_path(relative_path):
    """Obtem o caminho absoluto do recurso, trabalhando com _MEIPASS se existir"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class BingLoginBot:
    def __init__(self, master):
        self.master = master
        master.title("Bing Login Bot")
        master.geometry("600x400")
        master.configure(bg='#f0f0f0')
        master.iconbitmap(resource_path('logo.ico'))

        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Arial', 12), borderwidth=1)
        style.map('TButton', background=[('active', '#0078d7')])

        # Frame principal
        self.frame = ttk.Frame(master, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Labels e botões
        self.label = ttk.Label(self.frame, text="Bing Login Bot", font=("Arial", 24, "bold"))
        self.label.pack(pady=20)

        self.start_button = ttk.Button(self.frame, text="Iniciar Bot", command=self.start_bot, style='TButton')
        self.start_button.pack(pady=10, fill=tk.X)

        self.delete_button = ttk.Button(self.frame, text="Excluir Logins Salvos", command=self.delete_logins, style='TButton')
        self.delete_button.pack(pady=10, fill=tk.X)

        self.quit_button = ttk.Button(self.frame, text="Sair", command=master.quit, style='TButton')
        self.quit_button.pack(pady=10, fill=tk.X)

        self.status_label = ttk.Label(self.frame, text="", font=("Arial", 10), wraplength=580)
        self.status_label.pack(pady=10)

        # Barra de progresso
        self.progress = ttk.Progressbar(self.frame, orient='horizontal', mode='determinate')
        self.progress.pack(pady=10, fill=tk.X)

        # Menu de configurações e sobre
        menubar = tk.Menu(master)
        master.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Configurações", menu=settings_menu)
        settings_menu.add_command(label="Escolher Tema", command=self.choose_theme)
        settings_menu.add_command(label="Backup de Logins", command=self.backup_logins)
        settings_menu.add_command(label="Restaurar Logins", command=self.restore_logins)
        settings_menu.add_command(label="Definir Número de Pesquisas", command=self.set_num_searches)
        settings_menu.add_command(label="Exibir ou Esconder Navegador", command=self.set_browser_visibility)  # Nova opção adicionada

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sobre", menu=help_menu)
        help_menu.add_command(label="Créditos", command=self.show_credits)

        # Adicionar a data e hora no canto superior direito
        self.datetime_label = ttk.Label(master, font=("Arial", 10))
        self.datetime_label.place(relx=1.0, rely=0, anchor="ne")  # Posiciona no canto superior direito

        self.update_time()

        # Carregar configurações
        self.config = self.load_config()

        # Número de pesquisas (padrão: 30)
        self.num_searches = self.config.get("num_searches", 30)

        # Visibilidade do navegador (padrão: exibir)
        self.browser_visible = self.config.get("browser_visible", True)

        # Tema
        theme = self.config.get("theme", "Claro")
        self.apply_theme(theme)

    def update_time(self):
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.datetime_label.config(text=now)
        self.master.after(1000, self.update_time)

    def update_status(self, message):
        self.status_label.config(text=message)
        self.master.update_idletasks()

    def save_login(self, email, senha):
        logins = self.load_logins()
        if not any(login['email'] == email for login in logins):
            logins.append({"email": email, "senha": senha})
            with open(resource_path('logins.json'), 'w') as f:
                json.dump(logins, f)
            return True
        return False

    def load_logins(self):
        if os.path.exists(resource_path('logins.json')):
            with open(resource_path('logins.json'), 'r') as f:
                try:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
                    else:
                        return []
                except json.JSONDecodeError:
                    messagebox.showerror("Erro", "O arquivo de logins está corrompido.")
                    return []
        return []

    def delete_logins(self):
        if os.path.exists(resource_path('logins.json')):
            os.remove(resource_path('logins.json'))
            messagebox.showinfo("Sucesso", "Logins excluídos com sucesso!")
        else:
            messagebox.showinfo("Informação", "Não há logins salvos para excluir.")

    def read_names_from_file(self, filename='nomes.txt'):
        filename = resource_path(filename)
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def extract_numbers(self, text):
        """Extrai e retorna todos os números do texto como uma string."""
        return " ".join(re.findall(r'\d+', text))

    def perform_searches(self, driver, names):
        self.update_status("Iniciando pesquisas...")
        driver.get("https://www.bing.com")
        search_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "sb_form_q"))
        )
        
        available_names = names.copy()
        self.progress['maximum'] = self.num_searches
        
        for i in range(min(self.num_searches, len(available_names))):
            if not available_names:
                self.update_status("Todas as palavras foram usadas. Encerrando as pesquisas.")
                break
            
            name = random.choice(available_names)
            available_names.remove(name)
            
            search_box.clear()
            search_box.send_keys(name)
            search_box.send_keys(Keys.RETURN)
            
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "id_rc"))
                )
                id_rc_content = driver.find_element(By.ID, "id_rc").text
                numbers = self.extract_numbers(id_rc_content)
                self.update_status(f"Pesquisando: {name} ({i+1}/{self.num_searches}) - Pontos atuais: {numbers}")
            except:
                self.update_status(f"Pesquisando: {name} ({i+1}/{self.num_searches}) - Não foi possível ler o conteúdo do id_rc.")
            
            self.progress['value'] = i + 1
            time.sleep(random.uniform(5, 10))
            
            driver.get("https://www.bing.com")
            search_box = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "sb_form_q"))
            )
            
            time.sleep(random.uniform(3, 7))

        self.update_status("Pesquisas concluídas!")
        self.progress['value'] = 0

    def start_bot(self):
        saved_logins = self.load_logins()
        is_saved_login = False
        if saved_logins:
            login_list = "\n".join([f"{i+1}. {login['email']}" for i, login in enumerate(saved_logins)])
            use_saved = messagebox.askyesno("Login Salvo", f"Deseja usar um login salvo?\n\nLogins salvos:\n{login_list}")
            if use_saved:
                login = simpledialog.askinteger("Selecionar Login", "Digite o número do login:", minvalue=1, maxvalue=len(saved_logins))
                if login:
                    email = saved_logins[login-1]["email"]
                    senha = saved_logins[login-1]["senha"]
                    is_saved_login = True
                else:
                    return
            else:
                email = simpledialog.askstring("Login", "Digite seu email, telefone ou Skype:")
                senha = simpledialog.askstring("Login", "Digite sua senha:", show='*')
        else:
            email = simpledialog.askstring("Login", "Digite seu email, telefone ou Skype:")
            senha = simpledialog.askstring("Login", "Digite sua senha:", show='*')

        threading.Thread(target=self.run_bot, args=(email, senha, is_saved_login), daemon=True).start()

    def run_bot(self, email, senha, is_saved_login):
        self.update_status("Iniciando o navegador...")
        options = uc.ChromeOptions()
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun')
        options.add_argument('--password-store=basic')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument("--log-level=3")
        options.add_argument("--start-maximized")
        
        # Configura a visibilidade do navegador
        if not self.browser_visible:
            options.add_argument("--headless")
            options.add_argument('--disable-gpu')
            options.add_argument("--window-size=1920,1080")
        
        driver = uc.Chrome(options=options)

        driver.get("https://login.live.com/")
        self.update_status("Página de login carregada. Inserindo informações...")

        email_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "loginfmt"))
        )
        email_box.send_keys(email)
        email_box.send_keys(Keys.RETURN)
        time.sleep(2)

        senha_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "passwd"))
        )
        senha_box.send_keys(senha)
        senha_box.send_keys(Keys.RETURN)
        time.sleep(2)

        try:
            nao_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "idBtn_Back"))
            )
            nao_button.click()
            time.sleep(2)
        except:
            pass

        if not is_saved_login:
            save_login = messagebox.askyesno("Salvar Login", "Deseja salvar este login?")
            if save_login:
                if self.save_login(email, senha):
                    messagebox.showinfo("Sucesso", "Login salvo com sucesso!")
                else:
                    messagebox.showwarning("Aviso", "Este login já está salvo.")

        names = self.read_names_from_file()
        self.perform_searches(driver, names)

        self.update_status("Bot concluído!")
        driver.quit()

    def choose_theme(self):
        themes = {
            "Claro": ("#f0f0f0", "black"),
            "Escuro": ("#2e2e2e", "white"),
            "Aqua": ("#e0f7fa", "black"),
        }
        theme = simpledialog.askstring("Escolher Tema", "Digite o nome do tema (Claro, Escuro, Aqua):")
        if theme and theme in themes:
            self.config["theme"] = theme
            self.save_config()
            self.apply_theme(theme)
        else:
            messagebox.showwarning("Aviso", "Tema inválido!")

    def apply_theme(self, theme):
        themes = {
            "Claro": ("#f0f0f0", "black"),
            "Escuro": ("#2e2e2e", "white"),
            "Aqua": ("#e0f7fa", "black"),
        }
        if theme in themes:
            bg_color, fg_color = themes[theme]
            self.master.configure(bg=bg_color)
            self.frame.configure(style=f"{theme}.TFrame")
            style = ttk.Style()
            style.configure(f"{theme}.TFrame", background=bg_color)
            style.configure(f"{theme}.TLabel", background=bg_color, foreground=fg_color)
            style.configure(f"{theme}.TButton", background=bg_color, foreground=fg_color)
            self.label.configure(style=f"{theme}.TLabel")
            self.status_label.configure(style=f"{theme}.TLabel")
            self.datetime_label.configure(style=f"{theme}.TLabel")

    def backup_logins(self):
        backup_file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if backup_file:
            logins = self.load_logins()
            with open(backup_file, 'w') as f:
                json.dump(logins, f)
            messagebox.showinfo("Sucesso", "Backup realizado com sucesso!")

    def restore_logins(self):
        backup_file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if backup_file:
            with open(backup_file, 'r') as f:
                logins = json.load(f)
            with open(resource_path('logins.json'), 'w') as f:
                json.dump(logins, f)
            messagebox.showinfo("Sucesso", "Logins restaurados com sucesso!")

    def set_num_searches(self):
        num_searches = simpledialog.askinteger("Definir Número de Pesquisas", "Digite o número de pesquisas (1-100):", minvalue=1, maxvalue=100)
        if num_searches:
            self.num_searches = num_searches
            self.config["num_searches"] = num_searches
            self.save_config()
            messagebox.showinfo("Sucesso", f"Número de pesquisas definido para {num_searches}")

    def set_browser_visibility(self):
        visibility = messagebox.askyesno("Visibilidade do Navegador", "Deseja que o navegador seja exibido durante a execução?")
        self.browser_visible = visibility
        self.config["browser_visible"] = visibility
        self.save_config()
        messagebox.showinfo("Sucesso", f"Visibilidade do navegador definida para {'exibir' if visibility else 'esconder'}")

    def show_credits(self):
        messagebox.showinfo("Créditos", "Desenvolvido por:\nGabriel Ricardo\nVersão 1.24.3\n2024")

    def load_config(self):
        if os.path.exists(resource_path('config.json')):
            with open(resource_path('config.json'), 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    messagebox.showerror("Erro", "O arquivo de configuração está corrompido.")
                    return {}
        return {}

    def save_config(self):
        with open(resource_path('config.json'), 'w') as f:
            json.dump(self.config, f)

if __name__ == "__main__":
    root = tk.Tk()
    app = BingLoginBot(root)
    root.mainloop()
