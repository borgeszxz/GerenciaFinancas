import customtkinter as ctk
import matplotlib.pyplot as plt
from tkinter import messagebox, ttk
import pandas as pd
import sqlite3
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class FinanceManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gerenciador de Finanças Pessoais")
        self.geometry("900x600")
        self.configure(padx=20, pady=20)

        self.conn = sqlite3.connect("finance_manager.db")
        self.cursor = self.conn.cursor()
        self.create_table()

        self.setup_ui()
        self.load_data()

    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS finances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            descricao TEXT,
            valor REAL,
            data TEXT
        )
        """)
        self.conn.commit()

    def setup_ui(self):
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(self.input_frame, text="Tipo:", anchor="w").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.type_combobox = ctk.CTkComboBox(self.input_frame, values=["Receita", "Despesa"], width=120)
        self.type_combobox.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(self.input_frame, text="Descrição:", anchor="w").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.description_entry = ctk.CTkEntry(self.input_frame, width=250)
        self.description_entry.grid(row=0, column=3, padx=10, pady=10)

        ctk.CTkLabel(self.input_frame, text="Valor:", anchor="w").grid(row=0, column=4, padx=10, pady=10, sticky="w")
        self.value_entry = ctk.CTkEntry(self.input_frame, width=100)
        self.value_entry.grid(row=0, column=5, padx=10, pady=10)

        self.add_button = ctk.CTkButton(self.input_frame, text="Adicionar", command=self.add_entry, width=100)
        self.add_button.grid(row=0, column=6, padx=10, pady=10)

        self.visual_frame = ctk.CTkFrame(self)
        self.visual_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.tree = ttk.Treeview(self.visual_frame, columns=("ID", "Tipo", "Descrição", "Valor", "Data"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Descrição", text="Descrição")
        self.tree.heading("Valor", text="Valor (R$)")
        self.tree.heading("Data", text="Data")
        self.tree.column("ID", width=50)
        self.tree.pack(fill="both", expand=True, pady=10)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2d2d2d",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#2d2d2d")
        style.configure("Treeview.Heading",
                        background="#1f1f1f",
                        foreground="white",
                        font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#1f6aa5")])

        self.graph_button = ctk.CTkButton(self.visual_frame, text="Exibir Gráfico", command=self.show_graph, width=150)
        self.graph_button.pack(pady=5, side="left", padx=10)

        self.delete_button = ctk.CTkButton(self.visual_frame, text="Remover Selecionado", command=self.delete_entry, width=150)
        self.delete_button.pack(pady=5, side="right", padx=10)

    def add_entry(self):
        tipo = self.type_combobox.get()
        descricao = self.description_entry.get()
        valor = self.value_entry.get()

        if not tipo or not descricao or not valor:
            messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
            return

        try:
            valor = float(valor)
        except ValueError:
            messagebox.showerror("Erro", "O valor deve ser um número.")
            return

        self.cursor.execute("INSERT INTO finances (tipo, descricao, valor, data) VALUES (?, ?, ?, datetime('now'))",
                            (tipo, descricao, valor))
        self.conn.commit()

        messagebox.showinfo("Sucesso", "Entrada adicionada com sucesso!")
        self.clear_inputs()
        self.load_data()

    def clear_inputs(self):
        self.type_combobox.set("")
        self.description_entry.delete(0, ctk.END)
        self.value_entry.delete(0, ctk.END)

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.cursor.execute("SELECT * FROM finances")
        rows = self.cursor.fetchall()

        for row in rows:
            id_, tipo, descricao, valor, data = row
            data_formatada = pd.to_datetime(data).strftime("%H:%M %d/%m/%Y")
            self.tree.insert("", "end", values=(id_, tipo, descricao, valor, data_formatada))

    def delete_entry(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Erro", "Nenhum item selecionado para remoção.")
            return

        item = self.tree.item(selected_item)
        entry_id = item["values"][0]

        self.cursor.execute("DELETE FROM finances WHERE id = ?", (entry_id,))
        self.conn.commit()

        messagebox.showinfo("Sucesso", "Entrada removida com sucesso!")
        self.load_data()

    def show_graph(self):
        self.cursor.execute("SELECT tipo, SUM(valor) FROM finances GROUP BY tipo")
        grouped_data = dict(self.cursor.fetchall())

        if not grouped_data:
            messagebox.showwarning("Atenção", "Não há dados para exibir.")
            return

        graph_window = ctk.CTkToplevel(self)
        graph_window.title("Gráfico de Receitas vs Despesas")
        graph_window.geometry("600x400")

        fig, ax = plt.subplots(figsize=(5, 4))
        color_map = {"Receita": "green", "Despesa": "red"}
        ax.bar(grouped_data.keys(), grouped_data.values(), color=[color_map[key] for key in grouped_data.keys()])
        ax.set_title("Receitas vs Despesas", fontsize=14)
        ax.set_ylabel("Valor (R$)", fontsize=12)
        ax.set_xlabel("Tipo", fontsize=12)

        for i, value in enumerate(grouped_data.values()):
            ax.text(i, value + 5, f"{value:.2f}", ha='center', va='bottom')

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    app = FinanceManagerApp()
    app.mainloop()
