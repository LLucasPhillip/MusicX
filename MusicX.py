import os
import threading
import time
import tempfile
import requests
import json
import random
from tkinter import *
from tkinter import messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
from pygame import mixer
from io import BytesIO
import webbrowser

mixer.init()
APP_TITLE = "Music Player"
PLAYLIST_FILE = "playlist.json"

root = Tk()
root.title(APP_TITLE)
root.geometry('980x680')
root.minsize(900,640)
root.configure(bg="#0f1720")
root.grid_columnconfigure(0, weight=3)
root.grid_columnconfigure(1, weight=2)
root.grid_columnconfigure(2, weight=3)
root.grid_rowconfigure(2, weight=1)

theme = {
    "dark": {"bg":"#0f1720","panel":"#0b1220","muted":"#111318","accent":"#1DB954","text":"#E6EEF3","muted_text":"#9aa6b2","track":"#263238"},
    "light":{"bg":"#f3f4f6","panel":"#ffffff","muted":"#f7fafc","accent":"#0ea5a4","text":"#0f172a","muted_text":"#546e7a","track":"#e6eef3"}
}
current_theme = "dark"
colors = theme[current_theme]

FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_STD = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)

button_cfg = {"font":("Segoe UI",10,"bold"), "bd":0, "relief":FLAT, "activeforeground":colors["text"], "cursor":"hand2"}

temp_file_path = None
deezer_results = []
deezer_covers = []
playlist_songs = []
playlist_covers = []
current_song_path = None
current_song_index = None
current_list_source = "main"
shuffle_enabled = False
repeat_enabled = False

def get_total_length(path_or_url):
    try:
        if isinstance(path_or_url,str) and path_or_url.startswith("http"):
            return 30.0
        else:
            sound = mixer.Sound(path_or_url)
            return sound.get_length()
    except Exception:
        return 30.0

def sec_to_mmss(sec):
    sec = int(sec)
    m = sec // 60
    s = sec % 60
    return f"{m}:{s:02d}"

def search_deezer():
    query = search_entry.get().strip()
    if not query:
        messagebox.showwarning("Busca vazia","Digite o nome de uma música")
        return
    url = f"https://api.deezer.com/search?q={query}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "data" not in data or not data["data"]:
            messagebox.showinfo("Nada encontrado","Nenhuma música encontrada")
            return
        songs_list.delete(0,END)
        deezer_results.clear()
        deezer_covers.clear()
        for track in data["data"]:
            title = f"{track['artist']['name']} - {track['title']}"
            songs_list.insert(END,title)
            deezer_results.append(track.get("preview",""))
            deezer_covers.append(track.get("album",{}).get("cover_medium",""))
        cover_label.config(image="")
    except Exception as e:
        messagebox.showerror("Erro",f"Erro ao buscar músicas:\n{e}")

def search_and_play_deezer():
    search_deezer()
    if deezer_results:
        songs_list.selection_clear(0,END)
        songs_list.selection_set(0)
        songs_list.activate(0)
        play_song()

def prepare_and_load_url(url):
    global temp_file_path
    if not url:
        raise Exception("URL inválida")
    if isinstance(url,str) and url.startswith("http"):
        temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        try:
            with requests.get(url, stream=True, timeout=15) as r:
                r.raise_for_status()
                with open(temp_file_path,"wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            return temp_file_path
        except Exception:
            if temp_file_path and os.path.exists(temp_file_path):
                try: os.remove(temp_file_path)
                except Exception: pass
            temp_file_path = None
            raise
    else:
        return url

def play_song():
    global temp_file_path, current_song_path, current_song_index, current_list_source
    try:
        selected_list = None
        if playlist_listbox.curselection():
            index = playlist_listbox.curselection()[0]
            url = playlist_songs[index]
            selected_list = "playlist"
        else:
            selected = songs_list.curselection()
            if not selected:
                if playlist_songs and not songs_list.size():
                    playlist_listbox.selection_set(0)
                    playlist_listbox.activate(0)
                    play_song()
                return
            index = selected[0]
            url = deezer_results[index] if index < len(deezer_results) else ""
            selected_list = "main"
        path = prepare_and_load_url(url)
        current_song_path = path
        current_song_index = index
        current_list_source = selected_list
        mixer.music.load(path)
        mixer.music.set_volume(volume_bar.get()/100)
        mixer.music.play()
        total = get_total_length(path)
        progress_scale.config(to=total)
        progress_time_label.config(text=f"0:00 / {sec_to_mmss(total)}")
        update_progress_bar()
        update_cover(selected_list,index)
    except Exception as e:
        messagebox.showerror("Erro",f"Erro ao tocar a música:\n{e}")

def pause_song():
    try:
        if mixer.music.get_busy():
            mixer.music.pause()
        else:
            mixer.music.unpause()
    except Exception:
        pass

def stop_song():
    global temp_file_path, current_song_path
    try: mixer.music.stop()
    except Exception: pass
    progress_scale.set(0)
    progress_time_label.config(text="0:00 / 0:00")
    cover_label.config(image="")
    if temp_file_path and os.path.exists(temp_file_path):
        try: os.remove(temp_file_path)
        except Exception: pass
        temp_file_path = None
    current_song_path = None

def next_song():
    try:
        if shuffle_enabled:
            if playlist_songs and playlist_listbox.size()>0:
                idx = random.randrange(playlist_listbox.size())
                playlist_listbox.selection_clear(0,END)
                playlist_listbox.selection_set(idx)
                playlist_listbox.activate(idx)
            elif deezer_results and songs_list.size()>0:
                idx = random.randrange(songs_list.size())
                songs_list.selection_clear(0,END)
                songs_list.selection_set(idx)
                songs_list.activate(idx)
            play_song()
            return
        if playlist_listbox.curselection():
            next_index = playlist_listbox.curselection()[0]+1
            if next_index < playlist_listbox.size():
                playlist_listbox.selection_clear(0,END)
                playlist_listbox.selection_set(next_index)
                playlist_listbox.activate(next_index)
                play_song()
            else:
                stop_song()
        else:
            selected = songs_list.curselection()
            if not selected: return
            next_index = selected[0]+1
            if next_index < songs_list.size():
                songs_list.selection_clear(0,END)
                songs_list.selection_set(next_index)
                songs_list.activate(next_index)
                play_song()
            else:
                stop_song()
    except Exception:
        stop_song()

def prev_song():
    try:
        if playlist_listbox.curselection():
            prev_index = playlist_listbox.curselection()[0]-1
            if prev_index>=0:
                playlist_listbox.selection_clear(0,END)
                playlist_listbox.selection_set(prev_index)
                playlist_listbox.activate(prev_index)
                play_song()
            else:
                stop_song()
        else:
            selected = songs_list.curselection()
            if not selected: return
            prev_index = selected[0]-1
            if prev_index>=0:
                songs_list.selection_clear(0,END)
                songs_list.selection_set(prev_index)
                songs_list.activate(prev_index)
                play_song()
            else:
                stop_song()
    except Exception:
        stop_song()

def update_progress_bar():
    def thread_fn():
        while True:
            try:
                if mixer.music.get_busy():
                    pos_ms = mixer.music.get_pos()
                    if pos_ms < 0: pos_ms = 0
                    cur = pos_ms/1000.0
                    total = float(progress_scale.cget("to"))
                    if cur>total: cur=total
                    progress_scale.set(cur)
                    progress_time_label.config(text=f"{sec_to_mmss(cur)} / {sec_to_mmss(total)}")
                time.sleep(0.5)
            except Exception:
                time.sleep(0.5)
    threading.Thread(target=thread_fn,daemon=True).start()

def update_cover(source,index):
    try:
        if source=="main":
            cover_url = deezer_covers[index] if index < len(deezer_covers) else ""
        else:
            cover_url = playlist_covers[index] if index < len(playlist_covers) else ""
        if not cover_url:
            cover_label.config(image="")
            return
        resp = requests.get(cover_url, timeout=10)
        img = Image.open(BytesIO(resp.content)).convert("RGBA")
        img.thumbnail((260,260),Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(img)
        cover_label.image = imgtk
        cover_label.config(image=imgtk)
    except Exception:
        cover_label.config(image="")

def add_to_playlist():
    sel = songs_list.curselection()
    if not sel:
        messagebox.showwarning("Atenção","Selecione uma música para adicionar")
        return
    i = sel[0]
    title = songs_list.get(i)
    url = deezer_results[i] if i < len(deezer_results) else ""
    cover = deezer_covers[i] if i < len(deezer_covers) else ""
    if title in playlist_listbox.get(0,END):
        messagebox.showinfo("Info","Já está na playlist")
        return
    playlist_listbox.insert(END,title)
    playlist_songs.append(url)
    playlist_covers.append(cover)

def remove_from_playlist():
    sel = playlist_listbox.curselection()
    if not sel:
        messagebox.showwarning("Atenção","Selecione uma música para remover")
        return
    i = sel[0]
    playlist_listbox.delete(i)
    if i < len(playlist_songs): playlist_songs.pop(i)
    if i < len(playlist_covers): playlist_covers.pop(i)

def add_local_file():
    try:
        filetypes = [("Áudio","*.mp3 *.wav *.ogg"),("All","*.*")]
        path = filedialog.askopenfilename(title="Selecione arquivo de áudio", filetypes=filetypes)
        if not path: return
        name = os.path.basename(path)
        display = f"Arquivo: {name}"
        if display in playlist_listbox.get(0,END):
            messagebox.showinfo("Info","Arquivo já na playlist")
            return
        playlist_listbox.insert(END,display)
        playlist_songs.append(path)
        playlist_covers.append("")
    except Exception as e:
        messagebox.showerror("Erro",f"Erro ao adicionar arquivo:\n{e}")

def clear_playlist():
    if messagebox.askyesno("Confirmar","Limpar toda a playlist?"):
        playlist_listbox.delete(0,END)
        playlist_songs.clear()
        playlist_covers.clear()

def save_playlist_to_file():
    try:
        data=[]
        for i in range(playlist_listbox.size()):
            data.append({"title":playlist_listbox.get(i),"url":playlist_songs[i] if i < len(playlist_songs) else "","cover":playlist_covers[i] if i < len(playlist_covers) else ""})
        with open(PLAYLIST_FILE,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
        messagebox.showinfo("Salvo","Playlist salva")
    except Exception as e:
        messagebox.showerror("Erro",f"Erro ao salvar:\n{e}")

def load_playlist_from_file():
    try:
        if not os.path.exists(PLAYLIST_FILE):
            messagebox.showinfo("Info","Nenhum arquivo de playlist encontrado")
            return
        with open(PLAYLIST_FILE,"r",encoding="utf-8") as f:
            data = json.load(f)
        playlist_listbox.delete(0,END)
        playlist_songs.clear()
        playlist_covers.clear()
        for it in data:
            playlist_listbox.insert(END,it.get("title","Sem título"))
            playlist_songs.append(it.get("url",""))
            playlist_covers.append(it.get("cover",""))
        messagebox.showinfo("Carregado","Playlist carregada")
    except Exception as e:
        messagebox.showerror("Erro",f"Erro ao carregar:\n{e}")

def toggle_shuffle():
    global shuffle_enabled
    shuffle_enabled = not shuffle_enabled
    btn_shuffle.config(bg=colors["accent"] if shuffle_enabled else colors["panel"])

def toggle_repeat():
    global repeat_enabled
    repeat_enabled = not repeat_enabled
    btn_repeat.config(bg=colors["accent"] if repeat_enabled else colors["panel"])

def show_lyrics():
    try:
        if playlist_listbox.curselection():
            idx = playlist_listbox.curselection()[0]
            title = playlist_listbox.get(idx)
        else:
            sel = songs_list.curselection()
            if not sel:
                messagebox.showwarning("Atenção","Selecione uma música")
                return
            idx = sel[0]
            title = songs_list.get(idx)
        if " - " in title:
            artist,track = title.split(" - ",1)
        else:
            artist = simpledialog.askstring("Artista","Informe o artista:",parent=root) or ""
            track = simpledialog.askstring("Título","Informe o título:",parent=root) or ""
            if not track: return
        api = f"https://api.lyrics.ovh/v1/{artist.strip()}/{track.strip()}"
        r = requests.get(api,timeout=10)
        if r.status_code==200:
            data = r.json()
            lyrics = data.get("lyrics",None)
            if not lyrics:
                messagebox.showinfo("Não encontrado","Letra não encontrada")
                return
            win = Toplevel(root)
            win.title(f"Letra — {artist} - {track}")
            win.geometry("620x520")
            text = Text(win,bg=colors["panel"],fg=colors["text"],wrap=WORD,font=FONT_STD,bd=0)
            text.pack(expand=True,fill=BOTH,padx=10,pady=10)
            text.insert(END,lyrics)
            text.config(state=DISABLED)
        else:
            messagebox.showinfo("Não encontrado","Letra não encontrada")
    except Exception as e:
        messagebox.showerror("Erro",f"Erro ao buscar letra:\n{e}")

def monitor_end():
    while True:
        time.sleep(1)
        try:
            if not mixer.music.get_busy() and current_song_path:
                time.sleep(0.5)
                if mixer.music.get_busy(): continue
                if repeat_enabled:
                    try:
                        mixer.music.load(current_song_path)
                        mixer.music.play()
                    except Exception:
                        pass
                else:
                    if shuffle_enabled:
                        try:
                            if current_list_source=="playlist" and playlist_listbox.size()>0:
                                idx = random.randrange(playlist_listbox.size())
                                playlist_listbox.selection_clear(0,END)
                                playlist_listbox.selection_set(idx)
                                playlist_listbox.activate(idx)
                            elif current_list_source=="main" and songs_list.size()>0:
                                idx = random.randrange(songs_list.size())
                                songs_list.selection_clear(0,END)
                                songs_list.selection_set(idx)
                                songs_list.activate(idx)
                            play_song()
                        except Exception:
                            pass
                    else:
                        root.event_generate("<<NextSongEvent>>")
        except Exception:
            pass

def on_next_event(e=None):
    try:
        if playlist_listbox.curselection():
            next_index = playlist_listbox.curselection()[0]+1
            if next_index < playlist_listbox.size():
                playlist_listbox.selection_clear(0,END)
                playlist_listbox.selection_set(next_index)
                playlist_listbox.activate(next_index)
                play_song()
            else:
                stop_song()
        else:
            sel = songs_list.curselection()
            if not sel: return
            next_index = sel[0]+1
            if next_index < songs_list.size():
                songs_list.selection_clear(0,END)
                songs_list.selection_set(next_index)
                songs_list.activate(next_index)
                play_song()
            else:
                stop_song()
    except Exception:
        stop_song()

root.bind("<<NextSongEvent>>",on_next_event)
threading.Thread(target=monitor_end,daemon=True).start()

header = Frame(root,bg=colors["bg"])
header.grid(row=0,column=0,columnspan=3,sticky="ew",padx=14,pady=(12,6))
header.grid_columnconfigure(0,weight=1)
title = Label(header,text=APP_TITLE,font=FONT_TITLE,bg=colors["bg"],fg=colors["accent"])
title.grid(row=0,column=0,sticky="w")
controls_right = Frame(header,bg=colors["bg"])
controls_right.grid(row=0,column=1,sticky="e")

search_entry = Entry(controls_right,font=FONT_STD,bg=colors["muted"],fg=colors["text"],bd=0,insertbackground=colors["text"],width=30)
search_entry.grid(row=0,column=0,padx=(0,8))
btn_search = Button(controls_right,text="Buscar",command=search_deezer,bg=colors["accent"],fg="#fff",**button_cfg)
btn_search.grid(row=0,column=1,padx=6)
btn_search_play = Button(controls_right,text="Buscar e Tocar",command=search_and_play_deezer,bg=colors["accent"],fg="#fff",**button_cfg)
btn_search_play.grid(row=0,column=2,padx=6)
def toggle_theme():
    global current_theme,colors
    current_theme = "light" if current_theme=="dark" else "dark"
    colors = theme[current_theme]
    root.configure(bg=colors["bg"])
    header.config(bg=colors["bg"])
    title.config(bg=colors["bg"],fg=colors["accent"])
    left_frame.config(bg=colors["muted"])
    center_frame.config(bg=colors["panel"])
    right_frame.config(bg=colors["muted"])
    for w in [search_entry,progress_frame,ads_frame]:
        try: w.config(bg=colors["muted"])
        except Exception: pass
    for lb in [songs_list,playlist_listbox]:
        try: lb.config(bg=colors["muted"],fg=colors["text"],selectbackground=colors["accent"])
        except Exception: pass
    for btn in [btn_search,btn_search_play,btn_add,btn_add_file,btn_remove,btn_clear,btn_save,btn_load,btn_shuffle,btn_repeat,btn_lyrics,btn_theme]:
        try: btn.config(bg=colors["panel"],fg=colors["text"])
        except Exception: pass
btn_theme = Button(controls_right,text="Tema",command=toggle_theme,bg=colors["panel"],fg=colors["text"],**button_cfg)
btn_theme.grid(row=0,column=3,padx=6)

left_frame = Frame(root,bg=colors["muted"],bd=0)
left_frame.grid(row=1,column=0,sticky="nsew",padx=(14,8),pady=6)
left_frame.grid_rowconfigure(1,weight=1)
Label(left_frame,text="Resultados",bg=colors["muted"],fg=colors["text"],font=FONT_STD).grid(row=0,column=0,sticky="w",padx=8,pady=(8,4))
songs_list = Listbox(left_frame,selectmode=SINGLE,bg=colors["muted"],fg=colors["text"],font=FONT_STD,bd=0,highlightthickness=0,selectbackground=colors["accent"],activestyle="none")
songs_list.grid(row=1,column=0,sticky="nsew",padx=8,pady=(0,8))
sb_songs = Scrollbar(left_frame,command=songs_list.yview)
sb_songs.grid(row=1,column=1,sticky="ns",pady=(0,8))
songs_list.config(yscrollcommand=sb_songs.set)
left_buttons = Frame(left_frame,bg=colors["muted"])
left_buttons.grid(row=2,column=0,sticky="w",padx=8,pady=(0,12))
btn_add = Button(left_buttons,text="Adicionar →",command=add_to_playlist,bg=colors["panel"],fg=colors["text"],**button_cfg,width=12)
btn_add.grid(row=0,column=0,padx=4)
btn_add_file = Button(left_buttons,text="Adicionar Arquivo",command=add_local_file,bg=colors["panel"],fg=colors["text"],**button_cfg,width=14)
btn_add_file.grid(row=0,column=1,padx=4)

center_frame = Frame(root,bg=colors["panel"])
center_frame.grid(row=1,column=1,sticky="nsew",padx=8,pady=6)
center_frame.grid_rowconfigure(1,weight=1)
Label(center_frame,text="Player",bg=colors["panel"],fg=colors["text"],font=FONT_STD).grid(row=0,column=0,sticky="w",padx=8,pady=(8,6))
cover_holder = Frame(center_frame,bg=colors["panel"])
cover_holder.grid(row=1,column=0,sticky="n",pady=(6,4))
cover_label = Label(cover_holder,bg=colors["panel"])
cover_label.pack()
controls_panel = Frame(center_frame,bg=colors["panel"])
controls_panel.grid(row=2,column=0,pady=(8,6))
btn_prev = Button(controls_panel,text="⏮",command=prev_song,bg=colors["panel"],fg=colors["text"],**button_cfg,width=6)
btn_prev.grid(row=0,column=0,padx=6)
btn_play = Button(controls_panel,text="▶️",command=play_song,bg=colors["panel"],fg=colors["text"],**button_cfg,width=8)
btn_play.grid(row=0,column=1,padx=6)
btn_pause = Button(controls_panel,text="⏸",command=pause_song,bg=colors["panel"],fg=colors["text"],**button_cfg,width=6)
btn_pause.grid(row=0,column=2,padx=6)
btn_next = Button(controls_panel,text="⏭",command=next_song,bg=colors["panel"],fg=colors["text"],**button_cfg,width=6)
btn_next.grid(row=0,column=3,padx=6)
progress_frame = Frame(center_frame,bg=colors["panel"])
progress_frame.grid(row=3,column=0,pady=(8,0),sticky="ew",padx=6)
progress_scale = Scale(progress_frame,from_=0,to=30,orient=HORIZONTAL,length=420,bg=colors["panel"],fg=colors["accent"],troughcolor=colors["track"],highlightthickness=0,sliderlength=15,showvalue=0)
progress_scale.grid(row=0,column=0,sticky="ew")
progress_time_label = Label(progress_frame,text="0:00 / 0:00",bg=colors["panel"],fg=colors["muted_text"],font=FONT_SMALL)
progress_time_label.grid(row=0,column=1,padx=(8,0))

right_frame = Frame(root,bg=colors["muted"])
right_frame.grid(row=1,column=2,sticky="nsew",padx=(8,14),pady=6)
right_frame.grid_rowconfigure(1,weight=1)
Label(right_frame,text="Playlist",bg=colors["muted"],fg=colors["text"],font=FONT_STD).grid(row=0,column=0,sticky="w",padx=8,pady=(8,4))
playlist_listbox = Listbox(right_frame,selectmode=SINGLE,bg=colors["muted"],fg=colors["text"],font=FONT_STD,bd=0,highlightthickness=0,selectbackground=colors["accent"],activestyle="none")
playlist_listbox.grid(row=1,column=0,sticky="nsew",padx=8,pady=(0,8))
sb_playlist = Scrollbar(right_frame,command=playlist_listbox.yview)
sb_playlist.grid(row=1,column=1,sticky="ns",pady=(0,8))
playlist_listbox.config(yscrollcommand=sb_playlist.set)
right_buttons = Frame(right_frame,bg=colors["muted"])
right_buttons.grid(row=2,column=0,sticky="w",padx=8,pady=(0,12))
btn_remove = Button(right_buttons,text="Remover",command=remove_from_playlist,bg=colors["panel"],fg=colors["text"],**button_cfg,width=12)
btn_remove.grid(row=0,column=0,padx=4,pady=4)
btn_clear = Button(right_buttons,text="Limpar",command=clear_playlist,bg=colors["panel"],fg=colors["text"],**button_cfg,width=12)
btn_clear.grid(row=1,column=0,padx=4,pady=4)
btn_save = Button(right_buttons,text="Salvar",command=save_playlist_to_file,bg=colors["panel"],fg=colors["text"],**button_cfg,width=12)
btn_save.grid(row=0,column=1,padx=4,pady=4)
btn_load = Button(right_buttons,text="Carregar",command=load_playlist_from_file,bg=colors["panel"],fg=colors["text"],**button_cfg,width=12)
btn_load.grid(row=1,column=1,padx=4,pady=4)
extras_bottom = Frame(root,bg=colors["bg"])
extras_bottom.grid(row=4,column=0,columnspan=3,sticky="ew",padx=14,pady=(6,12))
extras_bottom.grid_columnconfigure(0,weight=1)
left_extras = Frame(extras_bottom,bg=colors["bg"])
left_extras.grid(row=0,column=0,sticky="w")
btn_shuffle = Button(left_extras,text="Shuffle",command=toggle_shuffle,bg=colors["panel"],fg=colors["text"],**button_cfg,width=10)
btn_shuffle.grid(row=0,column=0,padx=6)
btn_repeat = Button(left_extras,text="Repetir",command=toggle_repeat,bg=colors["panel"],fg=colors["text"],**button_cfg,width=10)
btn_repeat.grid(row=0,column=1,padx=6)
btn_lyrics = Button(left_extras,text="Letra",command=show_lyrics,bg=colors["panel"],fg=colors["text"],**button_cfg,width=10)
btn_lyrics.grid(row=0,column=2,padx=6)
volume_frame = Frame(extras_bottom,bg=colors["bg"])
volume_frame.grid(row=0,column=1,sticky="e")
volume_bar = Scale(volume_frame,from_=0,to=100,orient=HORIZONTAL,length=180,bg=colors["bg"],fg=colors["accent"],troughcolor=colors["track"],highlightthickness=0,sliderlength=12,label="Volume",font=FONT_SMALL,command=lambda v: mixer.music.set_volume(int(v)/100))
volume_bar.set(70)
volume_bar.grid(row=0,column=0,padx=(0,6))
ads_frame = Frame(root,bg=colors["bg"])
ads_frame.grid(row=3,column=0,columnspan=3,sticky="ew",padx=14,pady=(6,0))
ads_label = Label(ads_frame,bg=colors["bg"])
ads_label.pack(fill=X)
ads_data = [
    {"img":"https://dummyimage.com/760x80/1db954/ffffff&text=Promoção+de+Fones","url":"https://www.exemplo.com/fones"},
    {"img":"https://dummyimage.com/760x80/ff4757/ffffff&text=Baixe+nosso+App","url":"https://www.exemplo.com/app"},
    {"img":"https://dummyimage.com/760x80/3742fa/ffffff&text=Curso+de+Python+com+Desconto","url":"https://www.exemplo.com/python"}
]
ad_index = 0
def rotate_ads():
    global ad_index
    ad = ads_data[ad_index]
    try:
        r = requests.get(ad["img"],timeout=10)
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        img.thumbnail((900,80),Image.LANCZOS)
        it = ImageTk.PhotoImage(img)
        ads_label.image = it
        ads_label.config(image=it)
        ads_label.bind("<Button-1>",lambda e,url=ad["url"]: webbrowser.open(url))
    except Exception:
        ads_label.config(text="Promo indisponível",fg=colors["muted_text"],bg=colors["bg"])
    ad_index = (ad_index+1) % len(ads_data)
    root.after(10000,rotate_ads)
rotate_ads()

def fechar():
    stop_song()
    root.destroy()
root.protocol("WM_DELETE_WINDOW",fechar)

def on_space(e):
    pause_song()
root.bind("<space>",on_space)
root.bind("<Right>",lambda e: next_song())
root.bind("<Left>",lambda e: prev_song())

if os.path.exists(PLAYLIST_FILE):
    try:
        with open(PLAYLIST_FILE,"r",encoding="utf-8") as f:
            data = json.load(f)
        for it in data:
            playlist_listbox.insert(END,it.get("title","Sem título"))
            playlist_songs.append(it.get("url",""))
            playlist_covers.append(it.get("cover",""))
    except Exception:
        pass

root.mainloop()
