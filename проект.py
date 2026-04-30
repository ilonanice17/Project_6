import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import json
import os

# --- Константы ---
DATA_FILE = "data/expenses.json"
DATE_FORMAT = "%Y-%m-%d"  # Формат даты для ввода и хранения

# --- Класс для приложения ---
class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Трекер расходов")
        self.root.geometry("800x500")  # Устанавливаем начальный размер окна

        # --- Переменные ---
        self.expenses = []
        self.filtered_expenses = []

        # --- Создание виджетов ---
        self.create_widgets()
        self.load_expenses()  # Загружаем данные при старте

    def create_widgets(self):
        # --- Основной фрейм ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- Фрейм для ввода расходов (слева) ---
        input_frame = ttk.LabelFrame(main_frame, text="Добавить расход")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Сумма
        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.amount_entry = ttk.Entry(input_frame, width=30)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Категория
        ttk.Label(input_frame, text="Категория:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.category_combobox = ttk.Combobox(input_frame, width=28, values=["Еда", "Транспорт", "Развлечения", "Коммунальные", "Одежда", "Прочее"])
        self.category_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.category_combobox.set("Еда") # Значение по умолчанию

        # Дата
        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.date_entry = ttk.Entry(input_frame, width=30)
        self.date_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.date_entry.insert(0, datetime.now().strftime(DATE_FORMAT)) # Дата по умолчанию - сегодня

        # Кнопка добавить
        add_button = ttk.Button(input_frame, text="Добавить расход", command=self.add_expense)
        add_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # --- Фрейм для фильтрации и статистики (под полем ввода) ---
        filter_frame = ttk.LabelFrame(main_frame, text="Фильтр и статистика")
        filter_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Фильтр по категории
        ttk.Label(filter_frame, text="Фильтр по категории:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        # Добавляем "Все" как первый вариант для удобства фильтрации
        self.filter_category_combobox = ttk.Combobox(filter_frame, width=28, values=["Все"] + list(self.category_combobox['values']))
        self.filter_category_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.filter_category_combobox.set("Все")
        self.filter_category_combobox.bind("<<ComboboxSelected>>", lambda event: self.filter_expenses())

        # Фильтр по дате (начальная и конечная)
        ttk.Label(filter_frame, text="Дата с:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.filter_start_date_entry = ttk.Entry(filter_frame, width=30)
        self.filter_start_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.filter_start_date_entry.bind("<FocusOut>", lambda event: self.filter_expenses()) # Фильтруем при потере фокуса

        ttk.Label(filter_frame, text="Дата по:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.filter_end_date_entry = ttk.Entry(filter_frame, width=30)
        self.filter_end_date_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.filter_end_date_entry.bind("<FocusOut>", lambda event: self.filter_expenses()) # Фильтруем при потере фокуса

        # Кнопка очистить фильтры
        clear_filter_button = ttk.Button(filter_frame, text="Очистить фильтры", command=self.clear_filters)
        clear_filter_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # Статистика
        self.total_sum_label = ttk.Label(filter_frame, text="Общая сумма: 0.00", font=('Arial', 12, 'bold'))
        self.total_sum_label.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # --- Таблица для отображения расходов (справа) ---
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        # Создаем Treeview
        self.tree = ttk.Treeview(tree_frame, columns=("Date", "Category", "Amount"), show="headings")
        self.tree.heading("Date", text="Дата")
        self.tree.heading("Category", text="Категория")
        self.tree.heading("Amount", text="Сумма")

        # Настройка колонок
        self.tree.column("Date", width=100, anchor="center")
        self.tree.column("Category", width=150, anchor="center")
        self.tree.column("Amount", width=100, anchor="center")

        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # --- Конфигурация растягивания виджетов ---
        main_frame.columnconfigure(1, weight=1) # Таблица растягивается по горизонтали
        main_frame.rowconfigure(0, weight=1)    # Таблица растягивается по вертикали
        main_frame.rowconfigure(1, weight=0)    # Фрейм фильтрации не растягивается сильно

        input_frame.columnconfigure(1, weight=1) # Поле ввода суммы/категории/даты растягивается
        filter_frame.columnconfigure(1, weight=1) # Поле ввода фильтра растягивается

    def add_expense(self):
        amount_str = self.amount_entry.get()
        category = self.category_combobox.get()
        date_str = self.date_entry.get()

        # --- Шаг 6: Проверка корректности ввода ---
        if not self.validate_input(amount_str, date_str):
            return

        try:
            amount = float(amount_str)
            expense_date = datetime.strptime(date_str, DATE_FORMAT).date()

            expense = {
                "date": expense_date.strftime(DATE_FORMAT),
                "category": category,
                "amount": amount
            }

            self.expenses.append(expense)
            # Сортируем все расходы по дате после добавления
            self.expenses.sort(key=lambda x: datetime.strptime(x['date'], DATE_FORMAT))
            self.save_expenses()
            # Обновляем таблицу со всеми расходами
            self.update_table(self.expenses)
            # Перефильтровываем, чтобы обновить статистику и отфильтрованную таблицу
            self.filter_expenses()

            messagebox.showinfo("Успех", "Расход успешно добавлен!")

            # Очищаем поля ввода для нового расхода
            self.amount_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, datetime.now().strftime(DATE_FORMAT))
            self.category_combobox.set("Еда") # Сброс категории по умолчанию

        except ValueError:
            # Эта ошибка уже должна быть перехвачена в validate_input, но на всякий случай
            messagebox.showerror("Ошибка ввода", "Неверный формат суммы или даты.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла непредвиденная ошибка при добавлении: {e}")

    def validate_input(self, amount_str, date_str):
        # Проверка суммы
        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Ошибка ввода", "Сумма должна быть положительным числом.")
                return False
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Сумма должна быть числом.")
            return False

        # Проверка даты
        try:
            datetime.strptime(date_str, DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Ошибка ввода", f"Дата должна быть в формате {DATE_FORMAT}.")
            return False

        return True

    def load_expenses(self):
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.expenses = json.load(f)
                    # Сортируем при загрузке
                    self.expenses.sort(key=lambda x: datetime.strptime(x['date'], DATE_FORMAT))
            except json.JSONDecodeError:
                messagebox.showerror("Ошибка загрузки", "Не удалось прочитать файл данных. Файл может быть поврежден или пуст. Создан новый пустой список.")
                self.expenses = []
            except Exception as e:
                messagebox.showerror("Ошибка загрузки", f"Произошла ошибка при загрузке данных: {e}. Создан новый пустой список.")
                self.expenses = []
        else:
            self.expenses = [] # Если файл не существует или пуст, начинаем с пустого списка

        # Обновляем таблицу и применяем фильтры после загрузки
        self.update_table(self.expenses)
        self.filter_expenses()

    def save_expenses(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.expenses, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Произошла ошибка при сохранении данных: {e}")

    def update_table(self, data_to_display):
        # Очищаем текущую таблицу
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Заполняем таблицу переданными данными
        for expense in data_to_display:
            self.tree.insert("", tk.END, values=(expense['date'], expense['category'], f"{expense['amount']:.2f}"))

    def filter_expenses(self):
        selected_category = self.filter_category_combobox.get()
        start_date_str = self.filter_start_date_entry.get()
        end_date_str = self.filter_end_date_entry.get()

        # Начинаем с полного списка расходов
        self.filtered_expenses = self.expenses.copy()

        # Применяем фильтр по категории
        if selected_category != "Все":
            self.filtered_expenses = [exp for exp in self.filtered_expenses if exp['category'] == selected_category]

        # Применяем фильтр по начальной дате
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, DATE_FORMAT).date()
                self.filtered_expenses = [exp for exp in self.filtered_expenses if datetime.strptime(exp['date'], DATE_FORMAT).date() >= start_date]
            except ValueError:
                # Если формат даты некорректен, игнорируем этот фильтр, но можем уведомить пользователя
                pass
                # messagebox.showwarning("Предупреждение", f"Некорректный формат начальной даты '{start_date_str}'. Фильтр по этой дате проигнорирован.")

        # Применяем фильтр по конечной дате
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, DATE_FORMAT).date()
                self.filtered_expenses = [exp for exp in self.filtered_expenses if datetime.strptime(exp['date'], DATE_FORMAT).date() <= end_date]
            except ValueError:
                pass
                # messagebox.showwarning("Предупреждение", f"Некорректный формат конечной даты '{end_date_str}'. Фильтр по этой дате проигнорирован.")

        # Обновляем таблицу только с отфильтрованными данными
        self.update_table(self.filtered_expenses)
        self.calculate_total_sum()

    def calculate_total_sum(self):
        total = sum(exp['amount'] for exp in self.filtered_expenses)
        self.total_sum_label.config(text=f"Общая сумма: {total:.2f}")

    def clear_filters(self):
        self.filter_category_combobox.set("Все")
        self.filter_start_date_entry.delete(0, tk.END)
        self.filter_end_date_entry.delete(0, tk.END)
        self.filter_expenses() # Применяем фильтры после очистки, чтобы вернуть все данные

# --- Основной блок запуска приложения ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
