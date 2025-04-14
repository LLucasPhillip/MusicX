import os
import threading
import time
import tempfile
import subprocess
from tkinter import *
from tkinter import messagebox, filedialog
from pygame import mixer
from PIL import Image, ImageTk  
import yt_dlp

mixer.init()

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
    if url:
        path = baixar_youtube_para_mp3(url)
        if path:
            songs_list.insert(END, path)
        url_entry.delete(0, END)

def add_file():
    filepaths = filedialog.askopenfilenames(
        title="Escolha músicas",
        filetypes=[("Arquivos de áudio", "*.mp3 *.mp4")]
    )
    for path in filepaths:
        if path.endswith(".mp4"):
            path = extrair_audio_mp4(path)
        if path:
            songs_list.insert(END, path)

def extrair_audio_mp4(path_mp4):
    try:
        output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        subprocess.run([
            'ffmpeg', '-i', path_mp4,
            '-vn', '-acodec', 'libmp3lame', '-ab', '192k', '-y',
            output
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao extrair áudio do .mp4:\n{e}")
        return None

def play_song():
    global temp_file_path
    try:
        selected = songs_list.curselection()
        if not selected:
            return
        path = songs_list.get(selected[0])
        mixer.music.load(path)
        mixer.music.play()
        temp_file_path = path
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
    if temp_file_path and os.path.exists(temp_file_path) and "temp" in temp_file_path:
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

progress_bar = Scale(root, from_=0, to=100, orient=HORIZONTAL, length=500, **button_style)
progress_bar.place(relx=0.15, rely=0.85)

Button(root, text="➕ URL", command=add_url, **button_style).place(relx=0.8, rely=0.595, width=80, height=30)
Button(root, text="📁 Arquivo", command=add_file, **button_style).place(relx=0.65, rely=0.595, width=100, height=30)
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