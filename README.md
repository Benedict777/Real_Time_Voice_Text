# 🎙️ Real-Time Speech Transcription & Translation

[English](#english) | [O'zbekcha](#ozbekcha)

---

<a name="english"></a>
## 🇬🇧 English

A desktop app that listens to audio in real time, transcribes it, and instantly translates it into Uzbek. When you are done, you can translate the whole transcript at once with Gemini AI for higher quality.

### Features
- Real-time speech recognition (Japanese, English, Russian, Korean, Chinese)
- Instant live translation into Uzbek (Google Translate)
- High-quality full-text translation with Gemini AI
- Captures system audio (videos, calls, streams) through VB-Cable
- Copy source text and translation to the clipboard in one click

### ⚠️ IMPORTANT: VB-Cable is required
To capture sound from your computer (videos, Zoom, YouTube, etc.), the app needs the **VB-Cable** virtual audio device. Without it, the app falls back to your regular microphone.

1. Download VB-Cable: https://vb-audio.com/Cable/
2. Extract the archive and run `VBCABLE_Setup_x64.exe` **as administrator**
3. Restart your computer
4. In Windows **Sound settings**, set the **Output** device to `CABLE Input`
5. The app will detect `CABLE Output` automatically (check with the "Devices" button)

> VB-Cable works on Windows only. To hear the audio yourself while it is routed to the cable, enable **"Listen to this device"** on `CABLE Output` in the Recording tab.

### Installation

```bash
git clone https://github.com/USERNAME/REPO_NAME.git
cd REPO_NAME

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration
Get a free API key at https://aistudio.google.com/apikey, then create a `.env` file in the project folder (see `.env.example`):

```
GEMINI_API_KEY=your_key_here
```

> Never commit your `.env` file or share your API key.

### Usage

```bash
python rtov.py
```

1. Choose the spoken language
2. Click **Start** and play audio or speak
3. Click **Stop** when finished
4. Click **Translate again with Gemini** for a high-quality translation of the full text

### Requirements
- Windows 10/11
- Python 3.9+
- Internet connection (Google Speech Recognition and translation)
- VB-Cable (for system audio)

### License
MIT

---

<a name="ozbekcha"></a>
## 🇺🇿 O'zbekcha

Ovozni real vaqtda eshitib, matnga aylantiradigan va o'sha zahoti o'zbek tiliga tarjima qiladigan dastur. Tugagach, butun matnni Gemini AI yordamida yuqori sifatda qayta tarjima qilish mumkin.

### Imkoniyatlar
- Ovozni real vaqtda tanish (yapon, ingliz, rus, koreys, xitoy tillari)
- O'zbek tiliga bir zumda tarjima (Google Translate)
- Gemini AI bilan butun matnning sifatli tarjimasi
- VB-Cable orqali kompyuter tovushini (video, qo'ng'iroq, efir) eshitish
- Manba matn va tarjimani bir tugma bilan nusxalash

### ⚠️ MUHIM: VB-Cable o'rnatish shart!
Kompyuterdagi tovushni (video, Zoom, YouTube va h.k.) eshitishi uchun dasturga **VB-Cable** virtual audio kabeli kerak. U bo'lmasa, dastur oddiy mikrofondan foydalanadi.

1. VB-Cable'ni yuklab oling: https://vb-audio.com/Cable/
2. Arxivni oching va `VBCABLE_Setup_x64.exe` ni **administrator sifatida** ishga tushiring
3. Kompyuterni qayta ishga tushiring
4. Windows **Sound settings** da **Output** qurilmasini `CABLE Input` ga o'rnating
5. Dastur `CABLE Output` ni o'zi topadi ("Qurilmalar" tugmasi bilan tekshiring)

> VB-Cable faqat Windows uchun. Tovushni o'zingiz ham eshitmoqchi bo'lsangiz, Recording bo'limida `CABLE Output` uchun **"Listen to this device"** ni yoqing.

### O'rnatish

```bash
git clone https://github.com/USERNAME/REPO_NAME.git
cd REPO_NAME

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

### Sozlash
https://aistudio.google.com/apikey saytidan bepul API kalit oling, so'ng loyiha papkasida `.env` fayl yarating (`.env.example` ga qarang):

```
GEMINI_API_KEY=sizning_kalitingiz
```

> `.env` faylni GitHub'ga yuklamang va kalitni hech kimga bermang.

### Ishlatish

```bash
python rtov.py
```

1. Gapirilayotgan tilni tanlang
2. **Boshlash** ni bosing va ovoz qo'ying yoki gapiring
3. Tugagach **Toxtatish** ni bosing
4. Butun matnni sifatli tarjima qilish uchun **Gemini bilan qayta tarjima qil** ni bosing

### Talablar
- Windows 10/11
- Python 3.9+
- Internet (Google ovoz tanish va tarjima uchun)
- VB-Cable (kompyuter tovushi uchun)

### Litsenziya
MIT