import os
import threading
import time
import tempfile
import requests
import json
import random
from tkinter import *
from tkinter import messagebox
from tkinter import simpledialog
from PIL import Image, ImageTk
from pygame import mixer
from io import BytesIO
import webbrowser

# Inicializa mixer
mixer.init()

# ---------------- CONFIG ----------------
APP_TITLE = "Music Player - Spotify Style (com recursos extras)"
PLAYLIST_FILE = "playlist.json"  # arquivo para salvar/carregar playlist
# ----------------------------------------

root = Tk()
root.title(APP_TITLE)
root.geometry('900x780')  # mais espaço p/ labels e botões
root.resizable(False, False)
root.configure(bg="#121212")

# estilos
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

# variáveis de estado
temp_file_path = None
deezer_results = []     # lista de URLs (preview ou caminhos)
deezer_covers = []
playlist_songs = []
playlist_covers = []
current_song_path = None
current_song_index = None
current_list_source = 'main'  # 'main' ou 'playlist'

shuffle_enabled = False
repeat_enabled = False

# ------------------- FUNÇÕES AUXILIARES -------------------
def get_total_length(path_or_url):
    """
    Tenta obter duração total em segundos.
    Para preview do Deezer (http) assume 30s (padrão).
    Para arquivos locais tenta usar mixer.Sound().get_length().
    """
    try:
        if isinstance(path_or_url, str) and path_or_url.startswith("http"):
            # previews do Deezer geralmente têm 30s
            return 30.0
        else:
            # tenta carregar como Sound (pode falhar para arquivos longos, mas tenta)
            sound = mixer.Sound(path_or_url)
            return sound.get_length()
    except Exception:
        # fallback
        return 30.0

def sec_to_mmss(sec):
    sec = int(sec)
    m = sec // 60
    s = sec % 60
    return f"{m}:{s:02d}"

# ------------------- FUNÇÕES DE PLAYER -------------------
def search_deezer():
    query = search_entry.get().strip()
    if not query:
        messagebox.showwarning("Busca vazia", "Digite o nome de uma música.")
        return

    url = f"https://api.deezer.com/search?q={query}"
    try:
        response = requests.get(url, timeout=10)
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

def prepare_and_load_url(url):
    """
    Se url for http, baixa para arquivo temporário e retorna caminho local.
    Se for caminho local, retorna diretamente.
    """
    global temp_file_path
    if url.startswith("http"):
        temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        try:
            with requests.get(url, stream=True, timeout=15) as r:
                r.raise_for_status()
                with open(temp_file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            return temp_file_path
        except Exception:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass
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
            cover_url = playlist_covers[index]
            selected_list = 'playlist'
        else:
            selected = songs_list.curselection()
            if not selected:
                # se nada selecionado, tenta tocar a primeira da playlist se houver
                if playlist_songs and not songs_list.size():
                    playlist_listbox.selection_set(0)
                    playlist_listbox.activate(0)
                    play_song()
                return
            index = selected[0]
            url = deezer_results[index]
            cover_url = deezer_covers[index]
            selected_list = 'main'

        # prepara arquivo local
        path = prepare_and_load_url(url)
        current_song_path = path
        current_song_index = index
        current_list_source = selected_list

        mixer.music.load(path)
        mixer.music.set_volume(volume_bar.get() / 100)
        mixer.music.play()

        # ajusta progress bar para total correto
        total = get_total_length(path)
        progress_bar.config(to=total)
        progress_time_label.config(text=f"0:00 / {sec_to_mmss(total)}")
        update_progress_bar()
        update_cover(selected_list, index)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao tocar a música:\n{e}")

def pause_or_resume():
    if mixer.music.get_busy():
        mixer.music.pause()
    else:
        mixer.music.unpause()

def pause_song():
    mixer.music.pause()

def resume_song():
    mixer.music.unpause()

def stop_song():
    global temp_file_path, current_song_path
    mixer.music.stop()
    progress_bar.set(0)
    progress_time_label.config(text="0:00 / 0:00")
    cover_label.config(image='')
    if temp_file_path and os.path.exists(temp_file_path):
        try:
            os.remove(temp_file_path)
        except Exception:
            pass
        temp_file_path = None
    current_song_path = None

def next_song():
    try:
        # se shuffle ativado, escolhe aleatório da lista correspondente
        if shuffle_enabled:
            if playlist_songs and playlist_listbox.size() > 0:
                idx = random.randrange(playlist_listbox.size())
                playlist_listbox.selection_clear(0, END)
                playlist_listbox.selection_set(idx)
                playlist_listbox.activate(idx)
            elif deezer_results and songs_list.size() > 0:
                idx = random.randrange(songs_list.size())
                songs_list.selection_clear(0, END)
                songs_list.selection_set(idx)
                songs_list.activate(idx)
            play_song()
            return

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
            selected = songs_list.curselection()
            if not selected:
                return
            next_index = selected[0] + 1
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
            selected = songs_list.curselection()
            if not selected:
                return
            prev_index = selected[0] - 1
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
    """
    Atualiza a barra de progresso e o label de tempo.
    Roda em thread separada para não travar UI.
    """
    def progress_thread():
        while True:
            try:
                if mixer.music.get_busy():
                    current_time_ms = mixer.music.get_pos()
                    # get_pos pode retornar -1 quando não reproduz; cuidado
                    if current_time_ms < 0:
                        current_time_ms = 0
                    current_time = current_time_ms / 1000.0
                    # pega total do scale "to"
                    total = float(progress_bar.cget('to'))
                    # evita overflow
                    if current_time > total:
                        current_time = total
                    progress_bar.set(current_time)
                    progress_time_label.config(text=f"{sec_to_mmss(current_time)} / {sec_to_mmss(total)}")
                time.sleep(0.5)
            except Exception:
                time.sleep(0.5)
    # rode como daemon
    threading.Thread(target=progress_thread, daemon=True).start()

def update_cover(source='main', index=0):
    try:
        if source == 'main':
            cover_url = deezer_covers[index]
        else:
            cover_url = playlist_covers[index]

        response = requests.get(cover_url, timeout=10)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img.thumbnail((220, 220), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        cover_label.image = img_tk
        cover_label.config(image=img_tk)
    except Exception:
        cover_label.config(image='')

# ------------------- PLAYLIST (ADD/REMOVE/SAVE/LOAD) -------------------
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

def save_playlist_to_file():
    try:
        data = []
        for i in range(playlist_listbox.size()):
            data.append({
                "title": playlist_listbox.get(i),
                "url": playlist_songs[i],
                "cover": playlist_covers[i]
            })
        with open(PLAYLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Salvo", f"Playlist salva em {PLAYLIST_FILE}.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar playlist:\n{e}")

def load_playlist_from_file():
    try:
        if not os.path.exists(PLAYLIST_FILE):
            messagebox.showinfo("Arquivo não encontrado", f"Nenhum arquivo {PLAYLIST_FILE} encontrado.")
            return
        with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        playlist_listbox.delete(0, END)
        playlist_songs.clear()
        playlist_covers.clear()
        for item in data:
            playlist_listbox.insert(END, item.get("title", "Sem título"))
            playlist_songs.append(item.get("url", ""))
            playlist_covers.append(item.get("cover", ""))
        messagebox.showinfo("Carregado", "Playlist carregada com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar playlist:\n{e}")

# ------------------- SHUFFLE / REPEAT -------------------
def toggle_shuffle():
    global shuffle_enabled
    shuffle_enabled = not shuffle_enabled
    btn_shuffle.config(bg='#3ac260' if shuffle_enabled else button_style['bg'])
    msg = "Shuffle ativado" if shuffle_enabled else "Shuffle desativado"
    # messagebox.showinfo("Shuffle", msg)

def toggle_repeat():
    global repeat_enabled
    repeat_enabled = not repeat_enabled
    btn_repeat.config(bg='#3ac260' if repeat_enabled else button_style['bg'])
    msg = "Repetir ativado" if repeat_enabled else "Repetir desativado"
    # messagebox.showinfo("Repeat", msg)

# ------------------- LYRICS -------------------
def show_lyrics():
    """
    Tenta obter letra usando lyrics.ovh. Requer artist e title da seleção atual.
    """
    try:
        # determina seleção (main ou playlist)
        if playlist_listbox.curselection():
            idx = playlist_listbox.curselection()[0]
            title_text = playlist_listbox.get(idx)
        else:
            sel = songs_list.curselection()
            if not sel:
                messagebox.showwarning("Atenção", "Selecione uma música para ver a letra.")
                return
            idx = sel[0]
            title_text = songs_list.get(idx)

        # tenta separar "Artista - Título"
        if " - " in title_text:
            artist, title = title_text.split(" - ", 1)
        else:
            # se não estiver no formato, pede ao usuário
            artist = simpledialog.askstring("Artista", "Informe o artista (ou deixe em branco):", parent=root) or ""
            title = simpledialog.askstring("Título", "Informe o título da música:", parent=root) or ""
            if not title:
                return

        # chama API
        api_url = f"https://api.lyrics.ovh/v1/{artist.strip()}/{title.strip()}"
        resp = requests.get(api_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            lyrics = data.get('lyrics', None)
            if not lyrics:
                messagebox.showinfo("Letra não encontrada", "Não foi possível encontrar a letra.")
                return
            # abre janela com letra
            win = Toplevel(root)
            win.title(f"Letra — {artist} - {title}")
            win.geometry("600x500")
            win.configure(bg="#121212")
            text = Text(win, bg="#111111", fg="white", wrap=WORD, font=('Segoe UI', 11))
            text.pack(expand=True, fill=BOTH, padx=10, pady=10)
            text.insert(END, lyrics)
            text.config(state=DISABLED)
        else:
            messagebox.showinfo("Não encontrado", "Letra não encontrada na API.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar letra:\n{e}")

# ------------------- MONITORAMENTO DE FIM -------------------
def monitor_end():
    """
    Observa quando a música termina para decidir o que fazer:
    - se repeat_enabled: toca novamente a mesma música
    - else se shuffle_enabled: toca aleatoriamente
    - else avança para próxima automaticamente (se houver)
    """
    while True:
        time.sleep(1)
        try:
            if not mixer.music.get_busy() and current_song_path:
                # pequena espera para evitar disparos múltiplos
                time.sleep(0.5)
                # se a música realmente encerrou (get_busy() ainda falso)
                if mixer.music.get_busy():
                    continue

                if repeat_enabled:
                    try:
                        mixer.music.load(current_song_path)
                        mixer.music.play()
                    except Exception:
                        pass
                else:
                    # se shuffle: escolher aleatório da lista atual
                    if shuffle_enabled:
                        try:
                            if current_list_source == 'playlist' and playlist_listbox.size() > 0:
                                idx = random.randrange(playlist_listbox.size())
                                playlist_listbox.selection_clear(0, END)
                                playlist_listbox.selection_set(idx)
                                playlist_listbox.activate(idx)
                            elif current_list_source == 'main' and songs_list.size() > 0:
                                idx = random.randrange(songs_list.size())
                                songs_list.selection_clear(0, END)
                                songs_list.selection_set(idx)
                                songs_list.activate(idx)
                            play_song()
                        except Exception:
                            pass
                    else:
                        # tenta ir para próxima automaticamente
                        root.event_generate("<<NextSongEvent>>")
        except Exception:
            pass

# evento custom para next
def on_next_event(e=None):
    # tenta avançar sem mensagens redundantes
    try:
        if playlist_listbox.curselection():
            next_index = playlist_listbox.curselection()[0] + 1
            if next_index < playlist_listbox.size():
                playlist_listbox.selection_clear(0, END)
                playlist_listbox.selection_set(next_index)
                playlist_listbox.activate(next_index)
                play_song()
            else:
                # fim da playlist -> para
                stop_song()
        else:
            selected = songs_list.curselection()
            if not selected:
                return
            next_index = selected[0] + 1
            if next_index < songs_list.size():
                songs_list.selection_clear(0, END)
                songs_list.selection_set(next_index)
                songs_list.activate(next_index)
                play_song()
            else:
                stop_song()
    except Exception:
        stop_song()

# registra evento
root.bind("<<NextSongEvent>>", on_next_event)

# inicializa thread de monitoramento
threading.Thread(target=monitor_end, daemon=True).start()

# ------------------- INTERFACE -------------------
root.grid_columnconfigure(0, weight=3)
root.grid_columnconfigure(1, weight=0)
root.grid_columnconfigure(2, weight=3)
root.grid_columnconfigure(3, weight=2)
root.grid_rowconfigure(1, weight=1)

# linha de busca
search_entry = Entry(root, font=('Segoe UI', 12), bg='#282828', fg='white', bd=0, insertbackground='white')
search_entry.grid(row=0, column=0, columnspan=2, padx=(15,5), pady=15, sticky="ew")

btn_search = Button(root, text="Buscar", command=search_deezer, **button_style)
btn_search.grid(row=0, column=2, padx=5, pady=15, sticky="ew")

btn_search_play = Button(root, text="Buscar e Tocar", command=search_and_play_deezer, **button_style)
btn_search_play.grid(row=0, column=3, padx=(5,15), pady=15, sticky="ew")

# lista de músicas (resultado)
songs_frame = Frame(root, bg="#282828")
songs_frame.grid(row=1, column=0, padx=(15,5), pady=5, sticky="nsew")
songs_frame.grid_rowconfigure(0, weight=1)
songs_frame.grid_columnconfigure(0, weight=1)

songs_list = Listbox(songs_frame, selectmode=SINGLE, **listbox_style)
songs_list.grid(row=0, column=0, sticky="nsew")

scrollbar_songs = Scrollbar(songs_frame, command=songs_list.yview)
scrollbar_songs.grid(row=0, column=1, sticky="ns")
songs_list.config(yscrollcommand=scrollbar_songs.set)

# playlist
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

btn_save_playlist = Button(playlist_buttons_frame, text="Salvar", command=save_playlist_to_file, **button_style)
btn_save_playlist.pack(side=LEFT, padx=5)

btn_load_playlist = Button(playlist_buttons_frame, text="Carregar", command=load_playlist_from_file, **button_style)
btn_load_playlist.pack(side=LEFT, padx=5)

# capa / anúncios / cover
cover_frame = Frame(root, bg="#121212")
cover_frame.grid(row=1, column=3, padx=(5,15), pady=5, sticky="n")
cover_label = Label(cover_frame, bg="#121212")
cover_label.pack(pady=10)

# barra de progresso + label de tempo
progress_bar = Scale(
    root, from_=0, to=30, orient=HORIZONTAL, length=760,
    bg="#121212", fg="#1DB954", troughcolor="#44475a",
    highlightthickness=0, sliderlength=15, showvalue=0
)
progress_bar.grid(row=2, column=0, columnspan=4, pady=(0,5), padx=15, sticky="ew")

progress_time_label = Label(root, text="0:00 / 0:00", bg="#121212", fg="white", font=('Segoe UI', 10))
progress_time_label.grid(row=2, column=3, sticky="e", padx=(0,25))

# botões principais
button_frame = Frame(root, bg="#121212")
button_frame.grid(row=3, column=0, columnspan=4, pady=(5,10))

Button(button_frame, text="⏮", command=prev_song, **button_style).pack(side=LEFT, padx=8)
Button(button_frame, text="▶️", command=play_song, **button_style).pack(side=LEFT, padx=8)
Button(button_frame, text="⏸", command=pause_song, **button_style).pack(side=LEFT, padx=8)
Button(button_frame, text="⏹", command=stop_song, **button_style).pack(side=LEFT, padx=8)
Button(button_frame, text="⏭", command=next_song, **button_style).pack(side=LEFT, padx=8)

# controles extras: shuffle / repeat / lyrics
extras_frame = Frame(root, bg="#121212")
extras_frame.grid(row=4, column=0, columnspan=4, pady=(0,10))

btn_shuffle = Button(extras_frame, text="Shuffle", command=toggle_shuffle, **button_style)
btn_shuffle.pack(side=LEFT, padx=6)

btn_repeat = Button(extras_frame, text="Repetir", command=toggle_repeat, **button_style)
btn_repeat.pack(side=LEFT, padx=6)

btn_lyrics = Button(extras_frame, text="Letra", command=show_lyrics, **button_style)
btn_lyrics.pack(side=LEFT, padx=6)

# volume
volume_bar = Scale(
    root, from_=0, to=100, orient=HORIZONTAL, length=240,
    bg="#121212", fg="#1DB954", troughcolor="#44475a",
    highlightthickness=0, sliderlength=15, label="Volume", font=('Segoe UI', 9),
    command=lambda v: mixer.music.set_volume(int(v)/100)
)
volume_bar.set(70)
volume_bar.grid(row=3, column=3, padx=(5,15), sticky="e")

# anúncios rotativos (mantive sua ideia)
ads_data = [
    {"img": "https://dummyimage.com/600x100/1db954/ffffff&text=Promoção+de+Fones", "url": "https://www.exemplo.com/fones"},
    {"img": "https://dummyimage.com/600x100/ff4757/ffffff&text=Baixe+nosso+App", "url": "https://www.exemplo.com/app"},
    {"img": "https://dummyimage.com/600x100/3742fa/ffffff&text=Curso+de+Python+com+Desconto", "url": "https://www.exemplo.com/python"}
]

ad_index = 0
ad_label = Label(root, bg="#121212", cursor="hand2")
ad_label.grid(row=5, column=0, columnspan=4, pady=(0,15))

def trocar_anuncio():
    global ad_index
    ad = ads_data[ad_index]

    try:
        response = requests.get(ad["img"], timeout=10)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img.thumbnail((760, 100), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        ad_label.image = img_tk
        ad_label.config(image=img_tk)
        ad_label.bind("<Button-1>", lambda e, url=ad["url"]: webbrowser.open(url))
    except Exception:
        ad_label.config(text="Erro ao carregar anúncio", fg="red")

    ad_index = (ad_index + 1) % len(ads_data)
    root.after(10000, trocar_anuncio)

trocar_anuncio()

# ------------------- FECHAR APP -------------------
def fechar_app():
    stop_song()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", fechar_app)

# ------------------- ATALHOS DE TECLADO -------------------
def on_space(e):
    # play/pause
    try:
        if mixer.music.get_busy():
            mixer.music.pause()
        else:
            mixer.music.unpause()
    except Exception:
        pass

def on_right(e):
    next_song()

def on_left(e):
    prev_song()

root.bind("<space>", on_space)
root.bind("<Right>", on_right)
root.bind("<Left>", on_left)

# ------------------- INSTRUÇÕES INICIAIS -------------------
# Tenta carregar playlist salva automaticamente (se existir)
if os.path.exists(PLAYLIST_FILE):
    try:
        with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            playlist_listbox.insert(END, item.get("title", "Sem título"))
            playlist_songs.append(item.get("url", ""))
            playlist_covers.append(item.get("cover", ""))
    except Exception:
        pass

# inicia loop da GUI
root.mainloop()
