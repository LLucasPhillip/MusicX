import os
import threading
import time
import tempfile
from tkinter import *
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from pygame import mixer
import yt_dlp

mixer.init()

root = Tk()
root.title('Music Player App')
root.geometry('700x500')
root.resizable(False, False)

# Fundo
bg_image = Image.open("bg.jpeg")
bg_image = bg_image.resize((700, 500), Image.LANCZOS)
bg_photo = ImageTk.PhotoImage(bg_image)

canvas = Canvas(root, width=700, height=500)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_photo, anchor="nw")

button_style = {
    'bg': '#282c34',
    'fg': '#61dafb',
    'font': ('Courier', 12, 'bold'),
    'relief': RAISED,
    'bd': 3
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

# Arquivo temporário
temp_file_path = None

def baixar_youtube_para_mp3(url):
    try:
        saida = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': saida,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return saida
    except Exception as e:
        messagebox.showerror("Download Error", f"Erro ao baixar do YouTube:\n{e}")
        return None

def add_url():
    url = url_entry.get()
    if url and url not in songs_list.get(0, END):
        songs_list.insert(END, url)
        url_entry.delete(0, END)

# ✅ NOVA FUNÇÃO: Adicionar arquivos locais
def add_file():
    filepaths = filedialog.askopenfilenames(title="Escolha músicas", filetypes=[("MP3 Files", "*.mp3")])
    for path in filepaths:
        if path not in songs_list.get(0, END):
            songs_list.insert(END, path)

def play_song():
    global temp_file_path
    try:
        selected_song = songs_list.get(ACTIVE)

        # Parar música anterior e limpar arquivo temporário
        stop_song()

        if selected_song.startswith('http'):
            messagebox.showinfo("Baixando", "Baixando música do YouTube, aguarde...")
            path = baixar_youtube_para_mp3(selected_song)
            if not path:
                return
            temp_file_path = path
            mixer.music.load(temp_file_path)
        else:
            mixer.music.load(selected_song)

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
        songs_list.selection_clear(0, END)
        songs_list.selection_set(next_index)
        songs_list.activate(next_index)
        play_song()
    except IndexError:
        messagebox.showinfo("Fim", "Não há mais músicas na lista.")

def prev_song():
    try:
        prev_index = songs_list.curselection()[0] - 1
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

progress_bar = Scale(root, from_=0, to=100, orient=HORIZONTAL, length=500, **button_style)
progress_bar.place(relx=0.15, rely=0.85)

# Botões
Button(root, text="➕ URL", command=add_url, **button_style).place(relx=0.8, rely=0.595, width=80, height=30)
Button(root, text="📁 Arquivo", command=add_file, **button_style).place(relx=0.65, rely=0.595, width=100, height=30)

Button(root, text=" ▶ Play ", command=play_song, **button_style).place(relx=0.25, rely=0.75, width=80, height=40)
Button(root, text=" ⏸ Pause ", command=pause_song, **button_style).place(relx=0.4, rely=0.75, width=80, height=40)
Button(root, text=" ▶ Resume ", command=resume_song, **button_style).place(relx=0.55, rely=0.75, width=80, height=40)
Button(root, text=" ⏹ Stop ", command=stop_song, **button_style).place(relx=0.7, rely=0.75, width=80, height=40)
Button(root, text=" ⏮ Prev ", command=prev_song, **button_style).place(relx=0.1, rely=0.75, width=80, height=40)
Button(root, text=" ⏭ Next ", command=next_song, **button_style).place(relx=0.85, rely=0.75, width=80, height=40)

root.protocol("WM_DELETE_WINDOW", lambda: (stop_song(), root.destroy()))
root.mainloop()
