"""extras.py - languages, voice, read-aloud and camera gestures. No grading happens here."""
import io
import os
import re
import urllib.request

from dotenv import load_dotenv

load_dotenv()

# display name -> (language name for the AI, language code)
LANGS = {
    "English": ("English", "en"),
    "हिन्दी": ("Hindi", "hi"),
    "العربية": ("Arabic", "ar"),
    "Français": ("French", "fr"),
}
AUTO = "🌐 Auto-detect"
CODE = {v[0]: v[1] for v in LANGS.values()}
WHISPER_NAMES = {"english": "English", "hindi": "Hindi", "arabic": "Arabic", "french": "French"}

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩०१२३४५६७८९", "01234567890123456789")


def normalize_digits(s: str) -> str:
    """Arabic-Indic and Devanagari digits -> 0-9, so SymPy can read them."""
    return s.translate(_DIGITS)


_FR_WORDS = (" le ", " la ", " les ", " un ", " une ", " des ", " est ", " quelle ", " quel ",
             " comment ", " pourquoi ", " donne ", " calcule ", " et ", " je ", " mon ",
             " ma ", " que ", " du ", " de ", " équilibre ", " dérivée ")


def detect_language(text: str):
    """Returns 'Hindi', 'Arabic', 'French', 'English', or None when it can't tell
    (for example a bare equation), so the app keeps the current language."""
    t = text or ""
    dev = len(re.findall(r"[\u0900-\u097F]", t))
    arb = len(re.findall(r"[\u0600-\u06FF]", t))
    if dev and dev >= arb:
        return "Hindi"
    if arb:
        return "Arabic"
    low = " " + t.lower() + " "
    if re.search(r"[àâçéèêëîïôûùüÿœ]", low):
        return "French"
    if sum(w in low for w in _FR_WORDS) >= 2:
        return "French"
    if len(re.findall(r"[A-Za-z]{3,}", t)) >= 2:
        return "English"
    return None


# ---------------- all on-screen text, in every language ----------------
T = {
    "English": {
        "tagline": "Learn from your mistakes. Ask in any language.",
        "welcome": "👋 Hi! Ask me a question, send your working, upload a photo, or use your voice. "
                   "I'll find exactly where the mistake happened and help you fix it.",
        "try": "Try one of these:",
        "examples": ["What is the derivative of x^3 + 2x?", "Balance H2 + O2 -> H2O",
                     "2x + 3 = 11\n2x = 14\nx = 7", "Calculate 20 m / (4 s)"],
        "placeholder": "Ask a question, or send your working (type it or upload a photo).",
        "mic": "🎤 Ask by voice", "cam": "📷 Show a hand gesture",
        "name": "Your name",
        "read": "What I read (check it is right!)",
        "correct": "All correct! ✅",
        "mistake": "Verified mistake", "your_line": "Your line",
        "answer": "Answer (computed by software)",
        "try_similar": "Try a similar one",
        "check_btn": "Check",
        "fixed": "Well done! You've got it now. 🎉",
        "same": "Same trouble. We'll review this again later.",
        "cant_read_twin": "I couldn't read your answer.",
        "map": "Mistake map", "due": "Ready to review", "level": "level", "errors": "errors",
        "none": "No mistakes recorded yet.",
        "no_gesture": "No hand gesture found. Hold your hand up clearly.",
        "cant_hear": "I couldn't hear that. Try again, or type your question.",
        "cant_read": "I couldn't read the maths. Open 'What I read': if it is wrong, type the problem.",
        "sorry": "Sorry, I couldn't reach the AI just now. Please try again.",
        "read_aloud": "🔊 Listen to the last answer", "clear": "🗑️ Clear chat",
        "no_audio": "Couldn't make audio right now.",
        "tasks": {
            "algebra": ("Solve step by step", "Your working, one equation per line"),
            "derivative": ("Differentiate", "Your final answer"),
            "integral": ("Integrate", "Your final answer (include + C)"),
            "chemistry_balance": ("Balance this equation", "Your balanced equation, like 2H2 + O2 -> 2H2O"),
            "physics_calc": ("Calculate (include units)", "Your answer with units, like 5 m/s")},
    },
    "Hindi": {
        "tagline": "अपनी गलतियों से सीखें। किसी भी भाषा में पूछें।",
        "welcome": "👋 नमस्ते! कोई सवाल पूछें, अपना हल भेजें, फ़ोटो अपलोड करें या बोलकर पूछें। "
                   "मैं ठीक वहीं गलती ढूँढूँगा जहाँ हुई है और उसे सुधारने में मदद करूँगा।",
        "try": "इनमें से कोई आज़माएँ:",
        "examples": ["x^3 + 2x का अवकलज क्या है?", "H2 + O2 -> H2O को संतुलित करो",
                     "2x + 3 = 11\n2x = 14\nx = 7", "20 m / (4 s) की गणना करो"],
        "placeholder": "सवाल पूछें या अपना हल भेजें (लिखें या फ़ोटो डालें)।",
        "mic": "🎤 बोलकर पूछें", "cam": "📷 हाथ का इशारा दिखाएँ",
        "name": "आपका नाम",
        "read": "मैंने क्या पढ़ा (जाँच लें कि सही है!)",
        "correct": "बिल्कुल सही! ✅",
        "mistake": "पुष्टि की गई गलती", "your_line": "आपकी पंक्ति",
        "answer": "उत्तर (सॉफ़्टवेयर से गणना)",
        "try_similar": "ऐसा ही एक और हल करें",
        "check_btn": "जाँचें",
        "fixed": "बहुत बढ़िया! अब आपको समझ आ गया है। 🎉",
        "same": "अभी भी वही दिक्कत है। हम इसे बाद में फिर दोहराएँगे।",
        "cant_read_twin": "मैं आपका उत्तर पढ़ नहीं पाया।",
        "map": "गलतियों का नक्शा", "due": "दोहराने के लिए तैयार", "level": "स्तर", "errors": "गलतियाँ",
        "none": "अभी कोई गलती दर्ज नहीं।",
        "no_gesture": "कोई इशारा नहीं मिला। हाथ साफ़ दिखाएँ।",
        "cant_hear": "मैं सुन नहीं पाया। दोबारा कोशिश करें या टाइप करें।",
        "cant_read": "मैं यह गणित पढ़ नहीं पाया। 'मैंने क्या पढ़ा' देखें; गलत हो तो सवाल टाइप करें।",
        "sorry": "माफ़ कीजिए, अभी AI से संपर्क नहीं हो पाया। कृपया फिर कोशिश करें।",
        "read_aloud": "🔊 आखिरी जवाब सुनें", "clear": "🗑️ चैट साफ़ करें",
        "no_audio": "अभी आवाज़ नहीं बन पाई।",
        "tasks": {
            "algebra": ("चरण-दर-चरण हल करें", "आपका हल, हर पंक्ति में एक समीकरण"),
            "derivative": ("अवकलन करें", "आपका अंतिम उत्तर"),
            "integral": ("समाकलन करें", "आपका अंतिम उत्तर (+ C लिखें)"),
            "chemistry_balance": ("इस समीकरण को संतुलित करें", "आपका संतुलित समीकरण, जैसे 2H2 + O2 -> 2H2O"),
            "physics_calc": ("गणना करें (इकाई लिखें)", "इकाई सहित उत्तर, जैसे 5 m/s")},
    },
    "Arabic": {
        "tagline": "تعلّم من أخطائك. اسأل بأي لغة.",
        "welcome": "👋 مرحباً! اطرح سؤالاً أو أرسل حلّك أو ارفع صورة أو تحدّث بصوتك. "
                   "سأجد الخطأ بالضبط وأساعدك على تصحيحه.",
        "try": "جرّب أحد هذه الأمثلة:",
        "examples": ["ما مشتقة x^3 + 2x؟", "وازن المعادلة H2 + O2 -> H2O",
                     "2x + 3 = 11\n2x = 14\nx = 7", "احسب 20 m / (4 s)"],
        "placeholder": "اطرح سؤالاً أو أرسل حلّك (اكتب أو ارفع صورة).",
        "mic": "🎤 اسأل بالصوت", "cam": "📷 أظهر إشارة بيدك",
        "name": "اسمك",
        "read": "ما قرأته (تأكد أنه صحيح!)",
        "correct": "كل شيء صحيح! ✅",
        "mistake": "خطأ مؤكَّد", "your_line": "سطرك",
        "answer": "الجواب (محسوب بالبرنامج)",
        "try_similar": "جرّب مسألة مشابهة",
        "check_btn": "تحقق",
        "fixed": "رائع! يبدو أنك فهمت الآن. 🎉",
        "same": "ما زالت المشكلة نفسها. سنراجعها لاحقاً.",
        "cant_read_twin": "لم أستطع قراءة إجابتك.",
        "map": "خريطة الأخطاء", "due": "جاهز للمراجعة", "level": "المستوى", "errors": "أخطاء",
        "none": "لا توجد أخطاء مسجلة بعد.",
        "no_gesture": "لم أجد إشارة. ارفع يدك بوضوح.",
        "cant_hear": "لم أسمع جيداً. حاول مرة أخرى أو اكتب سؤالك.",
        "cant_read": "لم أستطع قراءة المسألة. افتح «ما قرأته»؛ إن كان خاطئاً فاكتب المسألة.",
        "sorry": "عذراً، لا أستطيع الوصول إلى الذكاء الاصطناعي الآن. حاول مرة أخرى.",
        "read_aloud": "🔊 استمع لآخر إجابة", "clear": "🗑️ مسح المحادثة",
        "no_audio": "تعذّر إنشاء الصوت الآن.",
        "tasks": {
            "algebra": ("حلّ خطوة بخطوة", "حلّك، معادلة واحدة في كل سطر"),
            "derivative": ("اشتقّ", "جوابك النهائي"),
            "integral": ("أوجد التكامل", "جوابك النهائي (أضف + C)"),
            "chemistry_balance": ("وازن هذه المعادلة", "معادلتك الموزونة، مثل 2H2 + O2 -> 2H2O"),
            "physics_calc": ("احسب (مع الوحدات)", "جوابك مع الوحدة، مثل 5 m/s")},
    },
    "French": {
        "tagline": "Apprenez de vos erreurs. Posez vos questions dans n'importe quelle langue.",
        "welcome": "👋 Bonjour ! Posez une question, envoyez votre travail, ajoutez une photo ou parlez. "
                   "Je trouve l'endroit exact de l'erreur et je vous aide à la corriger.",
        "try": "Essayez l'un de ces exemples :",
        "examples": ["Quelle est la dérivée de x^3 + 2x ?", "Équilibre H2 + O2 -> H2O",
                     "2x + 3 = 11\n2x = 14\nx = 7", "Calcule 20 m / (4 s)"],
        "placeholder": "Posez une question ou envoyez votre travail (texte ou photo).",
        "mic": "🎤 Poser une question à voix haute", "cam": "📷 Montrez un geste de la main",
        "name": "Votre nom",
        "read": "Ce que j'ai lu (vérifiez que c'est correct !)",
        "correct": "Tout est correct ! ✅",
        "mistake": "Erreur vérifiée", "your_line": "Votre ligne",
        "answer": "Réponse (calculée par le logiciel)",
        "try_similar": "Essayez un exercice similaire",
        "check_btn": "Vérifier",
        "fixed": "Bravo ! Vous avez compris. 🎉",
        "same": "Même difficulté. Nous le reverrons plus tard.",
        "cant_read_twin": "Je n'ai pas pu lire votre réponse.",
        "map": "Carte des erreurs", "due": "À réviser", "level": "niveau", "errors": "erreurs",
        "none": "Aucune erreur enregistrée.",
        "no_gesture": "Aucun geste trouvé. Montrez bien votre main.",
        "cant_hear": "Je n'ai pas entendu. Réessayez ou écrivez votre question.",
        "cant_read": "Je n'ai pas pu lire les maths. Ouvrez « Ce que j'ai lu » ; si c'est faux, tapez le problème.",
        "sorry": "Désolé, impossible de joindre l'IA pour le moment. Réessayez.",
        "read_aloud": "🔊 Écouter la dernière réponse", "clear": "🗑️ Effacer la conversation",
        "no_audio": "Impossible de créer l'audio pour le moment.",
        "tasks": {
            "algebra": ("Résolvez étape par étape", "Votre résolution, une équation par ligne"),
            "derivative": ("Dérivez", "Votre réponse finale"),
            "integral": ("Intégrez", "Votre réponse finale (ajoutez + C)"),
            "chemistry_balance": ("Équilibrez cette équation", "Votre équation équilibrée, ex. 2H2 + O2 -> 2H2O"),
            "physics_calc": ("Calculez (avec les unités)", "Votre réponse avec unités, ex. 5 m/s")},
    },
}

GESTURE_REPLY = {
    "English": {"Thumb_Up": "Got it! ✅", "Pointing_Up": "Go ahead, ask your question (type or use the microphone).",
                "Open_Palm": "Okay, I'll wait. ✋"},
    "Hindi": {"Thumb_Up": "बढ़िया, समझ आ गया! ✅", "Pointing_Up": "पूछिए, अपना सवाल लिखें या माइक्रोफ़ोन इस्तेमाल करें।",
              "Open_Palm": "ठीक है, मैं रुकता हूँ। ✋"},
    "Arabic": {"Thumb_Up": "رائع، فهمت! ✅", "Pointing_Up": "تفضّل، اطرح سؤالك (اكتب أو استخدم الميكروفون).",
               "Open_Palm": "حسناً، سأنتظر. ✋"},
    "French": {"Thumb_Up": "Super, c'est compris ! ✅", "Pointing_Up": "Allez-y, posez votre question (texte ou micro).",
               "Open_Palm": "D'accord, j'attends. ✋"},
}


# ---------------- voice in ----------------
def transcribe(audio_bytes: bytes, language_code=None):
    """Speech to text with Whisper on Groq. Returns (text, language name or None)."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return "", None
    try:
        from groq import Groq
        kwargs = dict(file=("question.wav", audio_bytes), model="whisper-large-v3-turbo",
                      response_format="verbose_json")
        if language_code:
            kwargs["language"] = language_code
        r = Groq(api_key=key).audio.transcriptions.create(**kwargs)
        lang = WHISPER_NAMES.get(str(getattr(r, "language", "") or "").lower())
        return (r.text or "").strip(), lang
    except Exception as e:
        print("VOICE ERROR:", e)
        return "", None


# ---------------- voice out ----------------
# Maps both short codes and full names to a valid gTTS language tag.
_GTTS_LANG = {
    "en": "en", "english": "en",
    "hi": "hi", "hindi": "hi",
    "ar": "ar", "arabic": "ar",
    "fr": "fr", "french": "fr",
    # common regional aliases in case some code passes these
    "en-us": "en", "en-gb": "en",
    "hi-in": "hi",
    "ar-sa": "ar", "ar-eg": "ar",
    "fr-fr": "fr", "fr-ca": "fr",
}


def speak(text: str, code: str):
    """Text to speech with gTTS. Accepts 'en'/'hi'/'ar'/'fr' or full language names.
    Falls back to English if the requested language fails."""
    clean = re.sub(r"[`*#_>]", "", text or "")
    clean = re.sub(r"\s+", " ", clean).strip()[:1000]
    if not clean:
        return None

    target = _GTTS_LANG.get((code or "").lower(), "en")

    def _synth(lang_tag: str):
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(clean, lang=lang_tag).write_to_fp(buf)
        return buf.getvalue()

    try:
        return _synth(target)
    except Exception as e:
        print("SPEAK ERROR:", e)
        # If the target language failed (e.g. no internet, bad text), try English.
        if target != "en":
            try:
                return _synth("en")
            except Exception as e2:
                print("SPEAK FALLBACK ERROR:", e2)
        return None


# ---------------- camera gestures ----------------
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
             "gesture_recognizer/float16/1/gesture_recognizer.task")
MODEL_PATH = "gesture_recognizer.task"


def _gesture_with_gemini(image_bytes: bytes):
    """Fallback when mediapipe is not installed. Returns (list, error or None)."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from app.llm import _get_model, _content, _text
    model = _get_model(vision=True)
    if model is None:
        return None, "Add GOOGLE_API_KEY to .env, or install mediapipe."
    allowed = ["Thumb_Up", "Thumb_Down", "Pointing_Up", "Open_Palm"]
    try:
        msgs = [SystemMessage(content=(
                    "You look at one photo of a person's hand. Reply with exactly one word "
                    "from this list and nothing else: Thumb_Up, Thumb_Down, Pointing_Up, "
                    "Open_Palm, None. Use None if no clear gesture is visible.")),
                HumanMessage(content=_content("Which gesture is this?", image_bytes, "image/jpeg"))]
        words = _text(model.invoke(msgs)).strip().split()
        word = words[0].strip(".,'\"") if words else "None"
        return ([(word, 0.0)] if word in allowed else []), None
    except Exception as e:
        print("GESTURE ERROR:", e)
        return None, "I couldn't reach the AI to read the gesture."


def recognise_gesture(image_bytes: bytes):
    """Returns (list of (gesture, confidence), error message or None)."""
    try:
        import mediapipe as mp
        import numpy as np
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
        from PIL import Image
    except ImportError:
        return _gesture_with_gemini(image_bytes)
    try:
        if not os.path.exists(MODEL_PATH):
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        img = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
        opts = vision.GestureRecognizerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH), num_hands=2)
        rec = vision.GestureRecognizer.create_from_options(opts)
        res = rec.recognize(mp.Image(image_format=mp.ImageFormat.SRGB, data=img))
        found = [(g[0].category_name, g[0].score) for g in res.gestures
                 if g and g[0].category_name != "None"]
        return found, None
    except Exception as e:
        print("GESTURE ERROR:", e)
        return None, "I couldn't process the camera image."