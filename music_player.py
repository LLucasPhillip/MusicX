import os
import threading
import time
import tempfile
import requests
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
from pygame import mixer
from io import BytesIO

# Inicializar mixer
mixer.init()

# Janela principal
root = Tk()
root.title('Music Player - Spotify Style')
root.geometry('700x550')
root.resizable(False, False)
root.configure(bg="#121212")  # fundo escuro típico do Spotify

# Estilos
button_style = {
    'bg': '#1DB954',  # verde Spotify
    'fg': '#FFFFFF',
    'font': ('Segoe UI', 10, 'bold'),
    'relief': FLAT,
    'bd': 0,
    'activebackground': '#1ED760',
    'activeforeground': '#ffffff',
    'highlightthickness': 0,
    'cursor': 'hand2'
}

listbox_style = {
    'bg': '#282828',
    'fg': '#FFFFFF',
    'font': ('Segoe UI', 11),
    'selectbackground': '#1DB954',
    'selectforeground': '#000000'
}

# Lista de músicas frame
listbox_frame = Frame(root, bg="#282828", bd=0)
listbox_frame.place(relx=0.1, rely=0.15, relwidth=0.5, relheight=0.5)

songs_list = Listbox(listbox_frame, selectmode=SINGLE, **listbox_style)
songs_list.pack(side=LEFT, fill=BOTH, expand=True)

scrollbar = Scrollbar(listbox_frame)
scrollbar.pack(side=RIGHT, fill=Y)
songs_list.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=songs_list.yview)

# Área para capa da música
cover_frame = Frame(root, bg="#121212", bd=0)
cover_frame.place(relx=0.65, rely=0.15, relwidth=0.25, relheight=0.5)

cover_label = Label(cover_frame, bg="#121212")
cover_label.pack(fill=BOTH, expand=True)

# Entrada para busca
search_entry = Entry(root, font=('Segoe UI', 12), width=40, bg='#282828', fg='white', bd=0, insertbackground='white')
search_entry.place(relx=0.1, rely=0.05)

# Botões de busca
Button(root, text="Buscar", command=lambda: search_deezer(), **button_style).place(relx=0.7, rely=0.045, width=100, height=30)
Button(root, text="Buscar e Tocar", command=lambda: search_and_play_deezer(), **button_style).place(relx=0.8, rely=0.045, width=150, height=30)

# Barra de progresso
progress_bar = Scale(
    root, from_=0, to=30, orient=HORIZONTAL, length=500,
    bg="#121212", fg="#1DB954", troughcolor="#44475a",
    highlightthickness=0, sliderlength=15, showvalue=0
)
progress_bar.place(relx=0.1, rely=0.72)

# Botões de controle
button_frame = Frame(root, bg="#121212")
button_frame.place(relx=0.1, rely=0.78, relwidth=0.8, height=50)

Button(button_frame, text="⏮", command=lambda: prev_song(), **button_style).pack(side=LEFT, padx=10)
Button(button_frame, text="▶️", command=lambda: play_song(), **button_style).pack(side=LEFT, padx=10)
Button(button_frame, text="⏸", command=lambda: pause_song(), **button_style).pack(side=LEFT, padx=10)
Button(button_frame, text="⏹", command=lambda: stop_song(), **button_style).pack(side=LEFT, padx=10)
Button(button_frame, text="⏭", command=lambda: next_song(), **button_style).pack(side=LEFT, padx=10)

# Variáveis globais
temp_file_path = None
deezer_results = []
deezer_covers = []  # URLs das capas

# Funções
def search_deezer():
    query = search_entry.get().strip()
    if not query:
        messagebox.showwarning("Busca vazia", "Digite o nome de uma música.")
        return

    url = f"https://api.deezer.com/search?q={query}"
    try:
        response = requests.get(url)
        data = response.json()

        if 'data' not in data or not data['data']:
            messagebox.showinfo("Nada encontrado", "Nenhuma música encontrada.")
            return

        songs_list.delete(0, END)
        deezer_results.clear()
        deezer_covers.clear()

        for track in data['data']:
            title = f"{track['artist']['name']} - {track['title']}"
            songs_list.insert(END, title)
            deezer_results.append(track['preview'])
            deezer_covers.append(track['album']['cover_medium'])  # capa média

        cover_label.config(image='')  # Limpa capa ao buscar

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar músicas:\n{e}")

def search_and_play_deezer():
    search_deezer()
    if deezer_results:
        songs_list.selection_clear(0, END)
        songs_list.selection_set(0)
        songs_list.activate(0)
        play_song()

def play_url_audio(url):
    global temp_file_path
    try:
        temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        with requests.get(url, stream=True) as r:
            with open(temp_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        mixer.music.load(temp_file_path)
        mixer.music.play()
        update_progress_bar()
        update_cover()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao tocar a música:\n{e}")

def play_song():
    global temp_file_path
    try:
        selected = songs_list.curselection()
        if not selected:
            return
        index = selected[0]
        url = deezer_results[index]

        if url.startswith("http"):
            temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            with requests.get(url, stream=True) as r:
                with open(temp_file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            path = temp_file_path
        else:
            path = url

        mixer.music.load(path)
        mixer.music.play()
        update_progress_bar()
        update_cover()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao tocar a música:\n{e}")

def pause_song():
    mixer.music.pause()

def resume_song():
    mixer.music.unpause()

def stop_song():
    global temp_file_path
    mixer.music.stop()
    progress_bar.set(0)
    cover_label.config(image='')  # Limpa capa
    if temp_file_path and os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        temp_file_path = None

def next_song():
    try:
        next_index = songs_list.curselection()[0] + 1
        if next_index < songs_list.size():
            songs_list.selection_clear(0, END)
            songs_list.selection_set(next_index)
            songs_list.activate(next_index)
            play_song()
    except IndexError:
        messagebox.showinfo("Fim", "Não há mais músicas na lista.")

def prev_song():
    try:
        prev_index = songs_list.curselection()[0] - 1
        if prev_index >= 0:
            songs_list.selection_clear(0, END)
            songs_list.selection_set(prev_index)
            songs_list.activate(prev_index)
            play_song()
    except IndexError:
        messagebox.showinfo("Início", "Essa é a primeira música.")

def update_progress_bar():
    def progress_thread():
        while mixer.music.get_busy():
            time.sleep(1)
            current_time = mixer.music.get_pos() / 1000
            progress_bar.set(current_time)
    threading.Thread(target=progress_thread, daemon=True).start()

def update_cover():
    selected = songs_list.curselection()
    if not selected:
        cover_label.config(image='')
        return
    index = selected[0]
    try:
        cover_url = deezer_covers[index]
        response = requests.get(cover_url)
        img_data = response.content
        img = Image.open(BytesIO(img_data)).resize((200, 200), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        cover_label.image = img_tk
        cover_label.config(image=img_tk)
    except Exception:
        cover_label.config(image='')

# Fechar app corretamente (DANDO ERRO)
def fechar_app():
    stop_song()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", fechar_app)
root.mainloop()
