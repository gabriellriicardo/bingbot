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

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sobre", menu=help_menu)
        help_menu.add_command(label="Créditos", command=self.show_credits)

        # Adicionar a data e hora no canto superior direito
        self.datetime_label = ttk.Label(master, font=("Arial", 10))
        self.datetime_label.place(relx=1.0, rely=0, anchor="ne")  # Posiciona no canto superior direito

        self.update_time()

        # Número de pesquisas (padrão: 30)
        self.num_searches = 30

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
        self.update_status("Iniciando o bot...")
        options = uc.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        driver = uc.Chrome(options=options)
        
        try:
            self.update_status("Carregando página de login...")
            driver.get("https://login.live.com/")
            logging.info("Página de login carregada")

            self.update_status("Inserindo email...")
            email_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.NAME, "loginfmt"))
            )
            email_field.send_keys(email)
            logging.info("Email inserido")
            
            next_button = driver.find_element(By.ID, "idSIButton9")
            next_button.click()
            logging.info("Botão 'Próximo' clicado")
            
            self.update_status("Inserindo senha...")
            password_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.NAME, "passwd"))
            )
            password_field.send_keys(senha)
            logging.info("Senha inserida")
            
            sign_in_button = driver.find_element(By.ID, "idSIButton9")
            sign_in_button.click()
            logging.info("Botão 'Entrar' clicado")
            
            time.sleep(5)

            try:
                stay_signed_in_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "idBtn_Back"))
                )
                stay_signed_in_button.click()
            except:
                logging.info("Botão 'Ficar conectado' não apareceu ou já foi tratado")
            
            if not is_saved_login:
                # Pergunta ao usuário se deseja salvar o login apenas se não for um login já salvo
                save_login = messagebox.askyesno("Salvar Login", "Deseja salvar este login para uso futuro?")
                if save_login:
                    if self.save_login(email, senha):
                        self.update_status("Login salvo com sucesso!")
                    else:
                        self.update_status("Login já estava salvo!")
                else:
                    self.update_status("Login não foi salvo.")
            else:
                self.update_status("Usando login salvo.")

            self.update_status("Realizando pesquisas...")
            names = self.read_names_from_file('nomes.txt')
            self.perform_searches(driver, names)
        except Exception as e:
            logging.error(f"Ocorreu um erro: {e}")
            self.update_status(f"Ocorreu um erro: {e}")
        finally:
            driver.quit()

    def show_credits(self):
        messagebox.showinfo("Créditos", "Desenvolvido por Gabriel Ricardo.\nVersão 1.0"")

    def choose_theme(self):
        themes = ['clam', 'alt', 'default', 'classic']
        selected_theme = simpledialog.askstring("Escolher Tema", f"Escolha um tema:\n{', '.join(themes)}")
        if selected_theme in themes:
            ttk.Style().theme_use(selected_theme)
        else:
            messagebox.showerror("Erro", "Tema inválido. Escolha um tema válido.")

    def backup_logins(self):
        logins = self.load_logins()
        if logins:
            backup_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if backup_path:
                with open(backup_path, 'w') as f:
                    json.dump(logins, f)
                messagebox.showinfo("Sucesso", "Backup realizado com sucesso!")
        else:
            messagebox.showinfo("Informação", "Não há logins salvos para fazer backup.")

    def restore_logins(self):
        backup_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if backup_path:
            try:
                with open(backup_path, 'r') as f:
                    logins = json.load(f)
                with open(resource_path('logins.json'), 'w') as f:
                    json.dump(logins, f)
                messagebox.showinfo("Sucesso", "Logins restaurados com sucesso!")
            except json.JSONDecodeError:
                messagebox.showerror("Erro", "Arquivo de backup corrompido ou inválido.")

    def set_num_searches(self):
        new_num = simpledialog.askinteger("Definir Número de Pesquisas", 
                                          "Digite o número de pesquisas desejado:", 
                                          minvalue=1, 
                                          initialvalue=self.num_searches)
        if new_num:
            self.num_searches = new_num
            messagebox.showinfo("Sucesso", f"Número de pesquisas definido para {self.num_searches}.")

if __name__ == "__main__":
    root = tk.Tk()
    bot = BingLoginBot(root)
    root.mainloop()
