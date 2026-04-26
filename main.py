import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.error
import json
import os
from datetime import datetime

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("700x580")

        self.favorites_file = "favorites.json"
        self.favorites = []
        self.load_favorites()
        self.current_user_data = None

        self.setup_ui()

    def setup_ui(self):
        # --- Поле поиска ---
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(search_frame, text="GitHub логин:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 11))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_user())

        tk.Button(search_frame, text="🔍 Найти", command=self.search_user, 
                  bg="#0366d6", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        # --- Статус ---
        self.status_var = tk.StringVar(value="Введите логин и нажмите Найти или Enter")
        tk.Label(self.root, textvariable=self.status_var, fg="#555").pack(pady=2)

        # --- Основная область ---
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Список результатов поиска
        res_frame = tk.LabelFrame(main_frame, text="Результаты поиска")
        res_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.result_listbox = tk.Listbox(res_frame, font=("Consolas", 10), bg="#f8f9fa", height=10)
        self.result_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Список избранного
        fav_frame = tk.LabelFrame(main_frame, text="Избранные пользователи")
        fav_frame.pack(side="right", fill="both", expand=True, padx=5)

        self.fav_listbox = tk.Listbox(fav_frame, font=("Arial", 10), bg="#f8f9fa", height=10)
        self.fav_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.update_fav_list()

        # --- Кнопки действий ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(btn_frame, text="➕ Добавить в избранное", command=self.add_to_favorites, 
                  bg="#28a745", fg="white").pack(side="left", padx=5, expand=True, fill="x")
        tk.Button(btn_frame, text="🗑 Удалить из избранного", command=self.remove_from_favorites, 
                  bg="#dc3545", fg="white").pack(side="left", padx=5, expand=True, fill="x")

    def search_user(self):
        username = self.search_var.get().strip()
        if not username:
            messagebox.showwarning("Ошибка ввода", "Поле поиска не должно быть пустым!")
            return

        self.current_user_data = None
        self.result_listbox.delete(0, tk.END)
        self.status_var.set("⏳ Загрузка данных с GitHub API...")

        try:
            url = f"https://api.github.com/users/{username}"
            headers = {"User-Agent": "GitHub-User-Finder-App/1.0"}
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            self.current_user_data = data
            
            # Формируем список для отображения
            lines = [
                f"👤 Имя: {data.get('name') or data['login']}",
                f"🔗 Профиль: {data['html_url']}",
                f"📦 Репозиториев: {data['public_repos']} | 👥 Подписчиков: {data['followers']}",
                f"📝 Био: {data.get('bio') or 'Не указана'}",
                f"📍 Локация: {data.get('location') or 'Не указана'}",
                f"📅 Создан: {data['created_at'][:10]}"
            ]
            for line in lines:
                self.result_listbox.insert(tk.END, line)
            self.status_var.set("✅ Пользователь успешно найден!")

        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.status_var.set("❌ Пользователь не найден (404)")
            elif e.code == 403:
                self.status_var.set("⚠️ Превышен лимит запросов GitHub API (60/час). Попробуйте позже.")
            else:
                self.status_var.set(f"❌ Ошибка API: {e.code}")
        except urllib.error.URLError as e:
            self.status_var.set(f"❌ Ошибка сети: проверьте подключение к интернету.")
        except Exception as e:
            self.status_var.set(f"❌ Неизвестная ошибка: {e}")

    def add_to_favorites(self):
        if not self.current_user_data:
            messagebox.showwarning("Внимание", "Сначала найдите пользователя через поиск!")
            return

        login = self.current_user_data["login"]
        if any(f["login"] == login for f in self.favorites):
            messagebox.showinfo("Информация", "Этот пользователь уже в избранном.")
            return

        self.favorites.append({
            "login": login,
            "name": self.current_user_data.get("name"),
            "url": self.current_user_data["html_url"],
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_favorites()
        self.update_fav_list()
        self.status_var.set("✅ Добавлено в избранное!")

    def remove_from_favorites(self):
        idx = self.fav_listbox.curselection()
        if not idx:
            messagebox.showwarning("Внимание", "Выберите пользователя в списке избранного!")
            return

        idx = idx[0]
        removed_name = self.favorites[idx].get("name") or self.favorites[idx]["login"]
        del self.favorites[idx]

        self.save_favorites()
        self.update_fav_list()
        self.status_var.set(f"🗑 {removed_name} удалён из избранного.")

    def update_fav_list(self):
        self.fav_listbox.delete(0, tk.END)
        for user in self.favorites:
            display = f"{user.get('name') or user['login']} (@{user['login']})"
            self.fav_listbox.insert(tk.END, display)

    def save_favorites(self):
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=4)
        except IOError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {e}")

    def load_favorites(self):
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    self.favorites = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.favorites = []

if __name__ == "__main__":
    root = tk.Tk()
    # Опционально: современная тема
    style = ttk.Style()
    style.theme_use("clam")
    app = GitHubUserFinder(root)
    root.mainloop()