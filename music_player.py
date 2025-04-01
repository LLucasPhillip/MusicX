import os
import threading
import time
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter import ttk
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
label_style = {
    'bg': '#282c34',
    'fg': '#61dafb',
    'font': ('Courier', 10, 'bold')
}
listbox_style = {
    'bg': '#1C1C1C',
    'fg': 'green',
    'font': ('Courier', 12),
    'selectbackground': '#696969',
    'selectforeground': 'black'
}

style = ttk.Style()
style.configure("TButton",
                font=('Courier', 12, 'bold'),
                background='#282c34',
                foreground='#61dafb',
                borderwidth=3,
                relief='raised')
style.map("TButton",
          background=[('active', '#444b58')],
          foreground=[('active', '#61dafb')],
          relief=[('pressed', 'sunken'), ('!pressed', 'raised')])

style.configure("TScale",
                background="#282c34",
                troughcolor='#444b58',
                sliderrelief='raised')

listbox_frame = Frame(canvas, bg="black", bd=2, relief=SUNKEN)
listbox_frame.place(relx=0.1, rely=0.15, relwidth=0.8, relheight=0.4)
scrollbar = Scrollbar(listbox_frame, orient=VERTICAL)
songs_list = Listbox(listbox_frame, selectmode=SINGLE, yscrollcommand=scrollbar.set, **listbox_style)
scrollbar.config(command=songs_list.yview)
scrollbar.pack(side=RIGHT, fill=Y)
songs_list.pack(side=LEFT, fill=BOTH, expand=True)

def show_info():
    messagebox.showinfo("Developer Info", "Name: Rafi Ahamed\nEmail: fidaahamed15@gmail.com\nMusic Player App")

def add_songs():
    temp_song = filedialog.askopenfilenames(initialdir=music_dir, title="Choose a song",
                                            filetypes=[("mp3 Files", "*.mp3")])
    for s in temp_song:
        if s not in songs_list.get(0, END):
            songs_list.insert(END, s)

def delete_song():
    try:
        selected_song_index = songs_list.curselection()[0]
        songs_list.delete(selected_song_index)
    except IndexError:
        messagebox.showerror("Error", "No song selected to delete!")

def play_song():
    try:
        selected_song = songs_list.get(ACTIVE)
        mixer.music.load(selected_song)
        mixer.music.play()
        update_song_details()
    except Exception as e:
        messagebox.showerror("Error", f"Unable to play the song: {e}")

def control_playback(action):
    if action == 'pause':
        mixer.music.pause()
    elif action == 'resume':
        mixer.music.unpause()
    elif action == 'stop':
        mixer.music.stop()
        reset_progress()

def update_song_details():
    def update_thread():
        try:
            song_length = mixer.Sound(songs_list.get(ACTIVE)).get_length()
            progress_slider.config(to=song_length)
            total_time_label.config(text=f"Total Duration: {time.strftime('%M:%S', time.gmtime(song_length))}")

            while mixer.music.get_busy():
                if not progress_slider_clicked:
                    current_time = mixer.music.get_pos() / 1000
                    progress_slider.set(current_time)
                    selected_time_label.config(
                        text=f"Selected Time: {time.strftime('%M:%S', time.gmtime(current_time))}")
                time.sleep(0.5)
        except Exception as e:
            print(f"Error: {e}")

    threading.Thread(target=update_thread, daemon=True).start()

def reset_progress():
    progress_slider.set(0)
    selected_time_label.config(text="Selected Time: 00:00")
    total_time_label.config(text="Total Duration: 00:00")

root.protocol("WM_DELETE_WINDOW", lambda: root.destroy())
root.mainloop()