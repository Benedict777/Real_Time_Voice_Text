# -*- coding: utf-8 -*-
"""
Real-Time Speech Transcription & Translation
Ovozni real vaqtda eshitib, matnga aylantiradi va o'zbek tiliga tarjima qiladi.
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

import requests
import speech_recognition as sr
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# .env fayldan sozlamalarni o'qish (API kalit kodda saqlanmaydi)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Ranglar
BG = "#1e1e2e"
PANEL = "#2a2a3e"
ACCENT = "#7c6af7"
TEXT_PRI = "#e8e6f0"
TEXT_MUT = "#8884a8"
SUCCESS = "#4caf88"
DANGER = "#e05c5c"
YELLOW = "#f0c060"
FONT_MONO = ("Consolas", 11)

# Tillar: nomi -> (ovoz tanish kodi, tarjima kodi)
LANGUAGES = {
    "Yapon (ja)": ("ja-JP", "ja"),
    "Ingliz (en)": ("en-US", "en"),
    "Rus (ru)": ("ru-RU", "ru"),
    "Koreys (ko)": ("ko-KR", "ko"),
    "Xitoy (zh)": ("zh-CN", "zh-CN"),
}

LABEL_GOOGLE = "O'zbekcha tarjima (Google Translate)"
STATUS_STOPPED = "To'xtatilgan"
STATUS_LISTENING = "Gapiring / Video ovozi..."


def find_vbcable_index():
    """VB-Cable qurilmasining indeksini topadi, topilmasa None qaytaradi."""
    try:
        names = sr.Microphone.list_microphone_names()
    except Exception:
        return None
    for i, name in enumerate(names):
        low = name.lower()
        if "cable" in low or "vb-audio" in low:
            return i
    return None


def google_translate(text, src):
    """Tez tarjima (Google Translate, kalit shart emas)."""
    try:
        return GoogleTranslator(source=src, target="uz").translate(text)
    except Exception:
        return ""


def gemini_translate(full_text, src_lang, api_key):
    """Butun matnni Gemini AI bilan sifatli tarjima qiladi.

    Qaytaradi: (tarjima, xato). Muvaffaqiyatli bo'lsa xato None bo'ladi.
    """
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + GEMINI_MODEL
        + ":generateContent"
    )
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    prompt = (
        "Quyidagi %s tilidagi matnni o'zbek tiliga tabiiy va tushunarli qilib "
        "tarjima qil. Faqat tarjimani yoz, boshqa hech narsa yozma:\n\n%s"
        % (src_lang, full_text)
    )
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        if resp.status_code != 200:
            return None, "API xatosi: %s\n%s" % (resp.status_code, resp.text[:300])
        data = resp.json()
        candidates = data.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"].strip(), None
        return None, "Noaniq javob"
    except Exception as e:
        return None, str(e)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Transkripsiya va Tarjima")
        self.geometry("660x720")
        self.resizable(True, True)
        self.configure(bg=BG)

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 100
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.7

        self.is_listening = False
        self.stop_event = threading.Event()
        self.audio_queue = queue.Queue()
        self.vbcable_index = find_vbcable_index()
        self.speech_lang = "ja-JP"
        self.src_lang = "ja"

        self._record_thread = None
        self._process_thread = None

        self._build_ui()

    # ------------------------------------------------------------------
    # Interfeys
    # ------------------------------------------------------------------
    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=20, pady=(18, 4))
        tk.Label(
            hdr,
            text="Transkripsiya va Tarjima",
            font=("Segoe UI", 13, "bold"),
            bg=BG,
            fg=TEXT_PRI,
        ).pack(side="left")

        if self.vbcable_index is not None:
            tk.Label(
                self,
                text="VB-Cable topildi (indeks: %d)" % self.vbcable_index,
                font=("Segoe UI", 9),
                bg=BG,
                fg=SUCCESS,
            ).pack(anchor="w", padx=22)
        else:
            tk.Label(
                self,
                text="VB-Cable topilmadi - oddiy mikrofon ishlatiladi",
                font=("Segoe UI", 9),
                bg=BG,
                fg=YELLOW,
            ).pack(anchor="w", padx=22)

        self.lbl_status = tk.Label(
            self, text=STATUS_STOPPED, font=("Segoe UI", 10), bg=BG, fg=TEXT_MUT
        )
        self.lbl_status.pack(anchor="w", padx=22, pady=(2, 0))

        # Tugmalar
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill="x", padx=20, pady=(10, 4))
        self.btn_start = self._btn(btn_row, "Boshlash", SUCCESS, self.start_listening)
        self.btn_stop = self._btn(
            btn_row, "To'xtatish", DANGER, self.stop_listening, state="disabled"
        )
        self._btn(btn_row, "Tozalash", "#555566", self.clear_all)
        self._btn(btn_row, "Nusxa", "#555566", self.copy_all)
        self._btn(btn_row, "Qurilmalar", "#444455", self.show_devices)

        # Gemini tugmasi
        btn_row2 = tk.Frame(self, bg=BG)
        btn_row2.pack(fill="x", padx=20, pady=(0, 6))
        self.btn_gemini = self._btn(
            btn_row2,
            "Gemini bilan qayta tarjima qil",
            ACCENT,
            self.retranslate_gemini,
        )
        tk.Label(
            btn_row2,
            text="(butun matn AI bilan sifatli tarjima)",
            font=("Segoe UI", 9),
            bg=BG,
            fg=TEXT_MUT,
        ).pack(side="left", padx=8)

        # Til tanlash
        lang_row = tk.Frame(self, bg=BG)
        lang_row.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(
            lang_row, text="Til:", font=("Segoe UI", 10), bg=BG, fg=TEXT_MUT
        ).pack(side="left", padx=(0, 8))
        self.lang_var = tk.StringVar(value="Yapon (ja)")
        lang_menu = tk.OptionMenu(
            lang_row, self.lang_var, *LANGUAGES.keys(), command=self.change_lang
        )
        lang_menu.config(
            font=("Segoe UI", 10),
            bg=PANEL,
            fg=TEXT_PRI,
            activebackground=ACCENT,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=8,
            pady=4,
            highlightthickness=0,
        )
        lang_menu["menu"].config(bg=PANEL, fg=TEXT_PRI, font=("Segoe UI", 10))
        lang_menu.pack(side="left")

        # Manba matni
        self.lbl_src = tk.Label(
            self,
            text="Yapon (ja) matni",
            font=("Segoe UI", 9, "bold"),
            bg=BG,
            fg=TEXT_MUT,
        )
        self.lbl_src.pack(anchor="w", padx=22, pady=(4, 2))
        self.txt_src = scrolledtext.ScrolledText(
            self,
            font=FONT_MONO,
            bg=PANEL,
            fg=TEXT_PRI,
            insertbackground=TEXT_PRI,
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            height=10,
            wrap="word",
            selectbackground=ACCENT,
        )
        self.txt_src.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        # Tarjima
        self.lbl_uz = tk.Label(
            self,
            text=LABEL_GOOGLE,
            font=("Segoe UI", 9, "bold"),
            bg=BG,
            fg=TEXT_MUT,
        )
        self.lbl_uz.pack(anchor="w", padx=22, pady=(4, 2))
        self.txt_uz = scrolledtext.ScrolledText(
            self,
            font=FONT_MONO,
            bg=PANEL,
            fg="#a8e6c8",
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            height=10,
            wrap="word",
            state="disabled",
            selectbackground=ACCENT,
        )
        self.txt_uz.pack(fill="both", expand=True, padx=20, pady=(0, 18))

    def _btn(self, parent, label, color, cmd, state="normal"):
        b = tk.Button(
            parent,
            text=label,
            font=("Segoe UI", 10),
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=cmd,
            state=state,
        )
        b.pack(side="left", padx=(0, 8))
        return b

    # ------------------------------------------------------------------
    # Boshqaruv
    # ------------------------------------------------------------------
    def change_lang(self, selection):
        self.speech_lang, self.src_lang = LANGUAGES[selection]
        self.lbl_src.config(text=selection + " matni")
        if self.is_listening:
            self.stop_listening()

    def show_devices(self):
        try:
            names = sr.Microphone.list_microphone_names()
        except Exception as e:
            messagebox.showerror("Xato", "Qurilmalarni o'qib bo'lmadi:\n" + str(e))
            return
        msg = "Mavjud audio qurilmalar:\n\n"
        for i, name in enumerate(names):
            marker = " <-- VB-Cable" if i == self.vbcable_index else ""
            msg += "%d: %s%s\n" % (i, name, marker)
        messagebox.showinfo("Audio qurilmalar", msg)

    def start_listening(self):
        if self.is_listening:
            return

        # Eski threadlar to'liq to'xtashini kutish
        self.stop_event.set()
        if self._record_thread and self._record_thread.is_alive():
            self._record_thread.join(timeout=2)
        if self._process_thread and self._process_thread.is_alive():
            self._process_thread.join(timeout=2)

        # Yangi sessiya
        self.is_listening = True
        self.stop_event.clear()
        self.audio_queue = queue.Queue()

        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(text=STATUS_LISTENING, fg=SUCCESS)

        self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._record_thread.start()
        self._process_thread.start()

    def stop_listening(self):
        self.is_listening = False
        self.stop_event.set()
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.lbl_status.config(text=STATUS_STOPPED, fg=TEXT_MUT)

    # ------------------------------------------------------------------
    # Ovoz yozish va tanish
    # ------------------------------------------------------------------
    def _record_loop(self):
        try:
            mic = sr.Microphone(device_index=self.vbcable_index)
            with mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                while not self.stop_event.is_set():
                    try:
                        audio = self.recognizer.listen(
                            source, timeout=1, phrase_time_limit=10
                        )
                        if not self.stop_event.is_set():
                            self.audio_queue.put(
                                (audio, self.speech_lang, self.src_lang)
                            )
                    except sr.WaitTimeoutError:
                        pass
                    except Exception:
                        pass
        except Exception as e:
            err = str(e)
            self.after(0, lambda: self._mic_error(err))

    def _mic_error(self, err):
        self.stop_listening()
        messagebox.showerror(
            "Mikrofon xatosi",
            "Audio qurilmani ochib bo'lmadi:\n" + err,
        )

    def _process_loop(self):
        while not self.stop_event.is_set() or not self.audio_queue.empty():
            try:
                item = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue
            threading.Thread(
                target=self._recognize_one, args=(item,), daemon=True
            ).start()

    def _recognize_one(self, item):
        audio, speech_lang, src_lang = item
        try:
            text = self.recognizer.recognize_google(audio, language=speech_lang)
            if text.strip():
                self.after(0, lambda t=text: self._append_src(t))
                self._quick_translate(text, src_lang)
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            err = str(e)
            self.after(
                0,
                lambda: messagebox.showerror(
                    "Tarmoq xatosi", "Google API ga ulanib bo'lmadi:\n" + err
                ),
            )

    def _append_src(self, text):
        self.txt_src.insert("end", text + "\n")
        self.txt_src.see("end")

    def _quick_translate(self, text, src_lang):
        def _run():
            uz = google_translate(text, src_lang)
            if uz:

                def _do():
                    self.txt_uz.config(state="normal")
                    self.txt_uz.insert("end", uz + "\n")
                    self.txt_uz.see("end")
                    self.txt_uz.config(state="disabled")

                self.after(0, _do)

        threading.Thread(target=_run, daemon=True).start()

    # ------------------------------------------------------------------
    # Gemini bilan qayta tarjima
    # ------------------------------------------------------------------
    def retranslate_gemini(self):
        if not GEMINI_API_KEY:
            messagebox.showerror(
                "API kalit yo'q",
                ".env faylida GEMINI_API_KEY ni kiriting.\n"
                "Namuna: .env.example faylida.",
            )
            return

        src_full = self.txt_src.get("1.0", "end").strip()
        if not src_full:
            messagebox.showinfo("Bo'sh", "Matn yo'q.")
            return

        self.btn_gemini.config(state="disabled", text="Tarjima qilinmoqda...")
        self.lbl_uz.config(
            text="O'zbekcha tarjima (Gemini AI ishlamoqda...)", fg=YELLOW
        )

        src = self.src_lang

        def _run():
            uz, err = gemini_translate(src_full, src, GEMINI_API_KEY)

            def _do():
                self.btn_gemini.config(
                    state="normal", text="Gemini bilan qayta tarjima qil"
                )
                if err:
                    messagebox.showerror("Gemini xatosi", err)
                    self.lbl_uz.config(text=LABEL_GOOGLE, fg=TEXT_MUT)
                else:
                    self.txt_uz.config(state="normal")
                    self.txt_uz.delete("1.0", "end")
                    self.txt_uz.insert("end", uz)
                    self.txt_uz.config(state="disabled")
                    self.lbl_uz.config(text="O'zbekcha tarjima (Gemini AI)", fg=SUCCESS)

            self.after(0, _do)

        threading.Thread(target=_run, daemon=True).start()

    # ------------------------------------------------------------------
    # Yordamchi tugmalar
    # ------------------------------------------------------------------
    def clear_all(self):
        self.txt_src.delete("1.0", "end")
        self.txt_uz.config(state="normal")
        self.txt_uz.delete("1.0", "end")
        self.txt_uz.config(state="disabled")
        self.lbl_uz.config(text=LABEL_GOOGLE, fg=TEXT_MUT)

    def copy_all(self):
        src = self.txt_src.get("1.0", "end").strip()
        uz = self.txt_uz.get("1.0", "end").strip()
        combined = ""
        if src:
            combined += "[Manba]\n" + src
        if uz:
            combined += "\n\n[O'zbek]\n" + uz
        if combined:
            self.clipboard_clear()
            self.clipboard_append(combined)
            self.lbl_status.config(text="Nusxalandi!", fg=ACCENT)
            self.after(
                2000,
                lambda: self.lbl_status.config(
                    text=STATUS_LISTENING if self.is_listening else STATUS_STOPPED,
                    fg=SUCCESS if self.is_listening else TEXT_MUT,
                ),
            )


if __name__ == "__main__":
    app = App()
    app.mainloop()
