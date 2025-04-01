import os
import threading
import time
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pygame import mixer

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

music_dir = os.path.join(os.path.expanduser("~"), "Music")

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
songs_list.pack(side=LEFT, fill=BOTH, expand=True)  # Removendo Scrollbar

def add_songs():
    temp_song = filedialog.askopenfilenames(initialdir=music_dir, title="Choose a song",
                                            filetypes=[("mp3 Files", "*.mp3")])
    for s in temp_song:
        if s not in songs_list.get(0, END):
            songs_list.insert(END, s)

def play_song():
    try:
        selected_song = songs_list.get(ACTIVE)
        mixer.music.load(selected_song)
        mixer.music.play()
        update_progress_bar()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to play the song: {e}")

def pause_song():
    mixer.music.pause()

def resume_song():
    mixer.music.unpause()

def stop_song():
    mixer.music.stop()
    progress_bar.set(0)

def next_song():
    try:
        next_index = songs_list.curselection()[0] + 1
        songs_list.selection_clear(0, END)
        songs_list.selection_set(next_index)
        songs_list.activate(next_index)
        play_song()
    except IndexError:
        messagebox.showinfo("End", "No more songs in the list.")

def prev_song():
    try:
        prev_index = songs_list.curselection()[0] - 1
        songs_list.selection_clear(0, END)
        songs_list.selection_set(prev_index)
        songs_list.activate(prev_index)
        play_song()
    except IndexError:
        messagebox.showinfo("Start", "This is the first song.")

def update_progress_bar():
    def progress_thread():
        while mixer.music.get_busy():
            time.sleep(1)
            current_time = mixer.music.get_pos() / 1000
            progress_bar.set(current_time)
    threading.Thread(target=progress_thread, daemon=True).start()

progress_bar = Scale(root, from_=0, to=100, orient=HORIZONTAL, length=500, **button_style)
progress_bar.place(relx=0.15, rely=0.85)

play_button = Button(root, text="▶ Play", command=play_song, **button_style)
play_button.place(relx=0.25, rely=0.75, width=80, height=40)

pause_button = Button(root, text="⏸ Pause", command=pause_song, **button_style)
pause_button.place(relx=0.4, rely=0.75, width=80, height=40)

resume_button = Button(root, text="▶ Resume", command=resume_song, **button_style)
resume_button.place(relx=0.55, rely=0.75, width=80, height=40)

stop_button = Button(root, text="⏹ Stop", command=stop_song, **button_style)
stop_button.place(relx=0.7, rely=0.75, width=80, height=40)

prev_button = Button(root, text="⏮ Prev", command=prev_song, **button_style)
prev_button.place(relx=0.1, rely=0.75, width=80, height=40)

next_button = Button(root, text="⏭ Next", command=next_song, **button_style)
next_button.place(relx=0.85, rely=0.75, width=80, height=40)

root.protocol("WM_DELETE_WINDOW", lambda: root.destroy())
root.mainloop()