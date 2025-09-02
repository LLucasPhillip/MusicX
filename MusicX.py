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

mixer.init()

root = Tk()
root.title('Music Player - Spotify Style')
root.geometry('800x550')
root.resizable(False, False)
root.configure(bg="#121212")

button_style = {
    'bg': '#1DB954',
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

temp_file_path = None
deezer_results = []
deezer_covers = []
playlist_songs = []
playlist_covers = []

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
            deezer_covers.append(track['album']['cover_medium'])

        cover_label.config(image='')

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar músicas:\n{e}")

def search_and_play_deezer():
    search_deezer()
    if deezer_results:
        songs_list.selection_clear(0, END)
        songs_list.selection_set(0)
        songs_list.activate(0)
        play_song()

def play_song():
    global temp_file_path
    try:
        if playlist_listbox.curselection():
            index = playlist_listbox.curselection()[0]
            url = playlist_songs[index]
            cover_url = playlist_covers[index]
            selected_list = 'playlist'
        else:
            selected = songs_list.curselection()
            if not selected:
                return
            index = selected[0]
            url = deezer_results[index]
            cover_url = deezer_covers[index]
            selected_list = 'main'

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
        update_cover(selected_list, index)

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
    cover_label.config(image='')
    if temp_file_path and os.path.exists(temp_file_path):
        os.remove(temp_file_path)
        temp_file_path = None

def next_song():
    try:
        if playlist_listbox.curselection():
            next_index = playlist_listbox.curselection()[0] + 1
            if next_index < playlist_listbox.size():
                playlist_listbox.selection_clear(0, END)
                playlist_listbox.selection_set(next_index)
                playlist_listbox.activate(next_index)
                play_song()
            else:
                messagebox.showinfo("Fim", "Não há mais músicas na playlist.")
        else:
            next_index = songs_list.curselection()[0] + 1
            if next_index < songs_list.size():
                songs_list.selection_clear(0, END)
                songs_list.selection_set(next_index)
                songs_list.activate(next_index)
                play_song()
            else:
                messagebox.showinfo("Fim", "Não há mais músicas na lista.")
    except IndexError:
        messagebox.showinfo("Fim", "Não há mais músicas.")

def prev_song():
    try:
        if playlist_listbox.curselection():
            prev_index = playlist_listbox.curselection()[0] - 1
            if prev_index >= 0:
                playlist_listbox.selection_clear(0, END)
                playlist_listbox.selection_set(prev_index)
                playlist_listbox.activate(prev_index)
                play_song()
            else:
                messagebox.showinfo("Início", "Essa é a primeira música da playlist.")
        else:
            prev_index = songs_list.curselection()[0] - 1
            if prev_index >= 0:
                songs_list.selection_clear(0, END)
                songs_list.selection_set(prev_index)
                songs_list.activate(prev_index)
                play_song()
            else:
                messagebox.showinfo("Início", "Essa é a primeira música da lista.")
    except IndexError:
        messagebox.showinfo("Início", "Essa é a primeira música.")

def update_progress_bar():
    def progress_thread():
        while mixer.music.get_busy():
            time.sleep(1)
            current_time = mixer.music.get_pos() / 1000
            progress_bar.set(current_time)
    threading.Thread(target=progress_thread, daemon=True).start()

def update_cover(source='main', index=0):
    try:
        if source == 'main':
            cover_url = deezer_covers[index]
        else:
            cover_url = playlist_covers[index]

        response = requests.get(cover_url)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img.thumbnail((200, 200), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        cover_label.image = img_tk
        cover_label.config(image=img_tk)
    except Exception:
        cover_label.config(image='')

def add_to_playlist():
    selected = songs_list.curselection()
    if not selected:
        messagebox.showwarning("Atenção", "Selecione uma música para adicionar à playlist.")
        return
    index = selected[0]
    title = songs_list.get(index)
    url = deezer_results[index]
    cover = deezer_covers[index]

    if title in playlist_listbox.get(0, END):
        messagebox.showinfo("Info", "Esta música já está na playlist.")
        return

    playlist_listbox.insert(END, title)
    playlist_songs.append(url)
    playlist_covers.append(cover)

def remove_from_playlist():
    selected = playlist_listbox.curselection()
    if not selected:
        messagebox.showwarning("Atenção", "Selecione uma música para remover da playlist.")
        return
    index = selected[0]
    playlist_listbox.delete(index)
    playlist_songs.pop(index)
    playlist_covers.pop(index)

def fechar_app():
    stop_song()
    root.destroy()


root.grid_columnconfigure(0, weight=3)
root.grid_columnconfigure(1, weight=0)
root.grid_columnconfigure(2, weight=3)
root.grid_columnconfigure(3, weight=2)
root.grid_rowconfigure(1, weight=1)

search_entry = Entry(root, font=('Segoe UI', 12), bg='#282828', fg='white', bd=0, insertbackground='white')
search_entry.grid(row=0, column=0, columnspan=2, padx=(15,5), pady=15, sticky="ew")

btn_search = Button(root, text="Buscar", command=search_deezer, **button_style)
btn_search.grid(row=0, column=2, padx=5, pady=15, sticky="ew")

btn_search_play = Button(root, text="Buscar e Tocar", command=search_and_play_deezer, **button_style)
btn_search_play.grid(row=0, column=3, padx=(5,15), pady=15, sticky="ew")

songs_frame = Frame(root, bg="#282828")
songs_frame.grid(row=1, column=0, padx=(15,5), pady=5, sticky="nsew")
songs_frame.grid_rowconfigure(0, weight=1)
songs_frame.grid_columnconfigure(0, weight=1)

songs_list = Listbox(songs_frame, selectmode=SINGLE, **listbox_style)
songs_list.grid(row=0, column=0, sticky="nsew")

scrollbar_songs = Scrollbar(songs_frame, command=songs_list.yview)
scrollbar_songs.grid(row=0, column=1, sticky="ns")
songs_list.config(yscrollcommand=scrollbar_songs.set)

playlist_frame = Frame(root, bg="#282828")
playlist_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
playlist_frame.grid_rowconfigure(1, weight=1)
playlist_frame.grid_columnconfigure(0, weight=1)

Label(playlist_frame, text="Playlist", bg="#282828", fg="#1DB954", font=('Segoe UI', 14, 'bold')).grid(row=0, column=0, sticky="w", padx=5, pady=(5,0))

playlist_listbox = Listbox(playlist_frame, selectmode=SINGLE, **listbox_style)
playlist_listbox.grid(row=1, column=0, sticky="nsew", padx=5)

scrollbar_playlist = Scrollbar(playlist_frame, command=playlist_listbox.yview)
scrollbar_playlist.grid(row=1, column=1, sticky="ns")
playlist_listbox.config(yscrollcommand=scrollbar_playlist.set)

playlist_buttons_frame = Frame(playlist_frame, bg="#282828")
playlist_buttons_frame.grid(row=2, column=0, pady=10)

btn_add_playlist = Button(playlist_buttons_frame, text="Adicionar", command=add_to_playlist, **button_style)
btn_add_playlist.pack(side=LEFT, padx=5)

btn_remove_playlist = Button(playlist_buttons_frame, text="Remover", command=remove_from_playlist, **button_style)
btn_remove_playlist.pack(side=LEFT, padx=5)

cover_frame = Frame(root, bg="#121212")
cover_frame.grid(row=1, column=3, padx=(5,15), pady=5, sticky="n")
cover_label = Label(cover_frame, bg="#121212")
cover_label.pack(pady=10)

progress_bar = Scale(
    root, from_=0, to=30, orient=HORIZONTAL, length=750,
    bg="#121212", fg="#1DB954", troughcolor="#44475a",
    highlightthickness=0, sliderlength=15, showvalue=0
)
progress_bar.grid(row=2, column=0, columnspan=4, pady=(0,15), padx=15, sticky="ew")

button_frame = Frame(root, bg="#121212")
button_frame.grid(row=3, column=0, columnspan=4, pady=(0,15))

Button(button_frame, text="⏮", command=prev_song, **button_style).pack(side=LEFT, padx=12)
Button(button_frame, text="▶️", command=play_song, **button_style).pack(side=LEFT, padx=12)
Button(button_frame, text="⏸", command=pause_song, **button_style).pack(side=LEFT, padx=12)
Button(button_frame, text="⏹", command=stop_song, **button_style).pack(side=LEFT, padx=12)
Button(button_frame, text="⏭", command=next_song, **button_style).pack(side=LEFT, padx=12)

root.protocol("WM_DELETE_WINDOW", fechar_app)

root.mainloop()