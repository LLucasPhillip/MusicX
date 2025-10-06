import customtkinter as ctk
import webbrowser
import threading
import random
import time
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

URLS = {
    "Shein": "https://shein.plugg.to/jobs/fetch-shein-orders/{user_id}/{order_id}",
    "Shopee": "https://shopee.plugg.to/jobs/check-shopee-orders/{user_id}/{order_id}",
    "Netshoes": "https://netshoes.plugg.to/netshoes/getOneOrder/{user_id}/EXTERNALUSER/{order_id}",
    "Amazon": "https://amazonv2.plugg.to/admin/orders/import-one-order/{user_id}/{order_id}",
    "Magazine Luiza": "https://magalu.plugg.to/debug/orders/{user_id}/{order_id}",
    "Mercado Livre": "http://mercadolivre.plugg.to/mercadolivre/getOneOrder/{user_id}/{order_id}/force_payments"
}


class OrderSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OrderSync")
        self.geometry("720x680")
        self.resizable(False, False)
        self.configure(fg_color="#101010")

        ctk.CTkLabel(self, text="OrderSync", font=("Segoe UI", 20, "bold"), text_color="#FFFFFF").pack(pady=(20, 5))

        self.graph_canvas = tk.Canvas(self, height=30, bg="#151515", highlightthickness=0)
        self.graph_canvas.pack(padx=30, fill="x", pady=(0, 15))

        self.bar_count = 50
        self.bar_width = 6
        self.bar_spacing = 4
        self.bars = []

        self.after(100, self.draw_bars)

        self.user_id_var = ctk.StringVar()
        frame_user = ctk.CTkFrame(self, fg_color="transparent")
        frame_user.pack(pady=5, padx=30, fill="x")
        ctk.CTkLabel(frame_user, text="User ID:", font=("Segoe UI", 15), text_color="white").pack(side="left", padx=10)
        self.entry_user_id = ctk.CTkEntry(frame_user, textvariable=self.user_id_var, font=("Segoe UI", 15),
                                          border_color="#00c9ff", fg_color="#1a1a1a", text_color="white")
        self.entry_user_id.pack(side="left", fill="x", expand=True, padx=10)

        self.canal_var = ctk.StringVar(value="Shein")
        frame_canal = ctk.CTkFrame(self, fg_color="transparent")
        frame_canal.pack(pady=5, padx=30, fill="x")
        ctk.CTkLabel(frame_canal, text="Canal:", font=("Segoe UI", 15), text_color="white").pack(side="left", padx=10)
        self.combo_canal = ctk.CTkComboBox(frame_canal, variable=self.canal_var, values=list(URLS.keys()),
                                           font=("Segoe UI", 15), fg_color="#1a1a1a", button_color="#00c9ff",
                                           text_color="white", border_color="#00c9ff")
        self.combo_canal.pack(side="left", fill="x", expand=True, padx=10)

        pedidos_frame = ctk.CTkFrame(self, fg_color="transparent")
        pedidos_frame.pack(pady=(20, 5), padx=30, fill="both")

        label_frame = ctk.CTkFrame(pedidos_frame, fg_color="transparent")
        label_frame.pack(anchor="w")

        ctk.CTkLabel(label_frame, text="Pedidos:", font=("Segoe UI", 15), text_color="white").pack(side="left")
        ctk.CTkLabel(label_frame, text="(máximo 200 pedidos)", font=("Segoe UI", 12),
                     text_color="#888888").pack(side="left", padx=10)

        self.text_pedidos = ctk.CTkTextbox(pedidos_frame, width=660, height=200, font=("Consolas", 14),
                                           fg_color="#1a1a1a", text_color="white", border_color="#00c9ff")
        self.text_pedidos.pack(pady=8)
        self.placeholder = "Exemplo: 12345 67890 112233"
        self.text_pedidos.insert("0.0", self.placeholder)
        self.text_pedidos.bind("<FocusIn>", self.clear_placeholder)
        self.text_pedidos.bind("<FocusOut>", self.restore_placeholder)

        ctk.CTkButton(self, text="  Sincronizar Pedidos  ", command=self.abrir_rotas,
                      font=("Segoe UI", 15), fg_color="#88dff7", hover_color="#009bcc", text_color="black").pack(pady=25)

        self.footer_canvas = tk.Canvas(self, height=20, bg="#121212", highlightthickness=0)
        self.footer_canvas.pack(padx=10, pady=(10, 15), fill="x")

        self.footer_bars = []
        self.footer_bar_count = 80
        self.footer_bar_width = 4
        self.footer_bar_spacing = 3

        self.after(100, self.draw_footer_bars)

    def draw_bars(self):
        canvas_width = self.graph_canvas.winfo_width()
        total_width = self.bar_count * (self.bar_width + self.bar_spacing) - self.bar_spacing
        x_offset = (canvas_width - total_width) // 2

        for i in range(self.bar_count):
            x0 = x_offset + i * (self.bar_width + self.bar_spacing)
            y0 = 20
            x1 = x0 + self.bar_width
            y1 = 25
            bar = self.graph_canvas.create_rectangle(x0, y0, x1, y1, fill="#22ffed", width=0)
            self.bars.append(bar)

        self.animate_graph(self.bars, self.graph_canvas, top=True)

    def draw_footer_bars(self):
        canvas_width = self.footer_canvas.winfo_width()
        total_width = self.footer_bar_count * (self.footer_bar_width + self.footer_bar_spacing) - self.footer_bar_spacing
        x_offset = (canvas_width - total_width) // 2

        for i in range(self.footer_bar_count):
            x0 = x_offset + i * (self.footer_bar_width + self.footer_bar_spacing)
            y0 = 15
            x1 = x0 + self.footer_bar_width
            y1 = 20
            bar = self.footer_canvas.create_rectangle(x0, y0, x1, y1, fill="#1ed6cb", width=0)
            self.footer_bars.append(bar)

        self.animate_graph(self.footer_bars, self.footer_canvas, top=False)

    def animate_graph(self, bars, canvas, top=True):
        def pulse():
            while True:
                for i, bar in enumerate(bars):
                    height = random.randint(2, 15) if top else random.randint(1, 8)
                    x0, y0, x1, _ = canvas.coords(bar)
                    new_y0 = 25 - height if top else 20 - height
                    canvas.coords(bar, x0, new_y0, x1, 25 if top else 20)
                time.sleep(0.1)

        threading.Thread(target=pulse, daemon=True).start()

    def clear_placeholder(self, event=None):
        if self.text_pedidos.get("1.0", "end-1c").strip() == self.placeholder:
            self.text_pedidos.delete("1.0", "end")

    def restore_placeholder(self, event=None):
        if self.text_pedidos.get("1.0", "end-1c").strip() == "":
            self.text_pedidos.insert("1.0", self.placeholder)

    def abrir_rotas(self):
        canal = self.canal_var.get()
        user_id = self.user_id_var.get().strip()
        pedidos_texto = self.text_pedidos.get("1.0", "end").strip()

        pedidos = [pedido.strip() for pedido in pedidos_texto.replace(",", " ").replace(";", " ").split()]
        pedidos = pedidos[:200]
        url_base = URLS[canal]

        for pedido in pedidos:
            url_final = url_base.replace("{order_id}", pedido).replace("{user_id}", user_id)
            url_final = url_final.replace("EXTERNALUSER", "0000000000000000")
            webbrowser.open_new_tab(url_final)

if __name__ == "__main__":
    app = OrderSyncApp()
    app.mainloop()
    # Desenvolvido por: Lucas Phillip Pantaleão