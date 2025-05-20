import os
import threading
import time
import tempfile
import requests
from tkinter import *
from tkinter import messagebox
from pygame import mixer
from PIL import Image, ImageTk

# Inicializar mixer
mixer.init()

# Interface principal
root = Tk()
root.title('Music Player App')
root.geometry('700x500')
root.resizable(False, False)

bg_image = Image.open("bg.jpeg")
bg_image = bg_image.resize((700, 500), Image.LANCZOS)
bg_photo = ImageTk.PhotoImage(bg_image)

canvas = Canvas(root, width=700, height=500)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_photo, anchor="nw")

# Estilos mais sutis
button_style = {
    'bg': '#3b3f4a',          # fundo escuro porém suave
    'fg': '#a9b1d6',          # texto em tom claro e frio
    'font': ('Courier', 11),  # fonte menor e simples
    'relief': FLAT,           # sem borda levantada
    'bd': 0,
    'activebackground': '#5c6270',  # fundo quando hover/click
    'activeforeground': '#d0d4e8',  # texto quando hover/click
    'highlightthickness': 0,
    'cursor': 'hand2'
}

listbox_style = {
    'bg': '#1C1C1C',
    'fg': 'green',
    'font': ('Courier', 12),
    'selectbackground': '#696969',
    'selectforeground': 'black'
}

listbox_frame = Frame(canvas, bg="black", bd=2, relief=SUNKEN)
listbox_frame.place(relx=0.1, rely=0.15, relwidth=0.8, relheight=0.4)

songs_list = Listbox(listbox_frame, selectmode=SINGLE, **listbox_style)
songs_list.pack(side=LEFT, fill=BOTH, expand=True)

url_entry = Entry(root, font=('Courier', 12), width=50)
url_entry.place(relx=0.1, rely=0.6)

search_entry = Entry(root, font=('Courier', 12), width=30)
search_entry.place(relx=0.1, rely=0.05)

temp_file_path = None
deezer_results = []  # Armazena URLs de preview da Deezer

def search_deezer():
    query = search_entry.get()
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

        for track in data['data']:
            title = f"{track['artist']['name']} - {track['title']}"
            songs_list.insert(END, title)
            deezer_results.append(track['preview'])

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar músicas:\n{e}")

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
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao tocar a música:\n{e}")

def search_and_play_deezer():
    query = search_entry.get()
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

        for track in data['data']:
            title = f"{track['artist']['name']} - {track['title']}"
            songs_list.insert(END, title)
            deezer_results.append(track['preview'])

        # Toca a primeira música direto
        first_preview_url = data['data'][0]['preview']
        play_url_audio(first_preview_url)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar músicas:\n{e}")

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

progress_bar = Scale(
    root, from_=0, to=30, orient=HORIZONTAL, length=500,
    bg="#282c34",
    fg="#61dafb",
    troughcolor="#44475a",
    highlightthickness=0,
    sliderlength=15,
    showvalue=0,
)
progress_bar.place(relx=0.15, rely=0.85)

Button(root, text="🔍 Buscar", command=search_deezer, **button_style).place(relx=0.7, rely=0.045, width=100, height=30)
Button(root, text="🔍 Buscar e Tocar", command=search_and_play_deezer, **button_style).place(relx=0.8, rely=0.045, width=150, height=30)
Button(root, text="▶️", command=play_song, **button_style).place(relx=0.25, rely=0.75, width=80, height=40)
Button(root, text="⏸", command=pause_song, **button_style).place(relx=0.4, rely=0.75, width=80, height=40)
Button(root, text="⏹", command=stop_song, **button_style).place(relx=0.7, rely=0.75, width=80, height=40)
Button(root, text="⏮", command=prev_song, **button_style).place(relx=0.1, rely=0.75, width=80, height=40)
Button(root, text="⏭", command=next_song, **button_style).place(relx=0.85, rely=0.75, width=80, height=40)

def fechar_app():
    stop_song()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", fechar_app)
root.mainloop()
