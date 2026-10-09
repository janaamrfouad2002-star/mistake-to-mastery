"""presenter.py - live presentation bot: talk, answer, translate."""
from dotenv import load_dotenv
from app.llm import _get_model, _text
from app.extras import transcribe, speak, detect_language

load_dotenv()

# Full language name -> gTTS code. This is the ONLY place we map it now.
LANG_TO_GTTS = {
    "English": "en",
    "Hindi": "hi",
    "Arabic": "ar",
    "French": "fr",
}

SCRIPT = {
    "English": {
        "intro": ("Hello everyone! I'm the Mistake-to-Mastery assistant. "
                  "I don't just give answers — I find the exact step where a student went wrong, "
                  "name the misconception, and give them a similar problem to practise."),
        "beats": [
            ("The problem", "Most tutors give the final answer. The student never learns where they slipped."),
            ("The idea", "We compare each line with the previous one. The first line that changes the answer is the mistake."),
            ("The diagnosis", "A library of known misconceptions names it."),
            ("The fix", "A new twin problem on the same misconception."),
            ("The proof", "100 auto-generated cases per mistake type measure accuracy."),
            ("The reach", "Ask in English, Hindi, Arabic or French."),
        ],
        "outro": "That's Mistake-to-Mastery. Ask me anything — in any language.",
        "not_understood": "I didn't catch that. Try again, or say 'translate'.",
        "demo_offer": "Want to see it live? Ask me a maths question.",
    },
    "Hindi": {
        "intro": "नमस्ते! मैं Mistake-to-Mastery सहायक हूँ। मैं ठीक वह चरण ढूँढती हूँ जहाँ गलती हुई।",
        "beats": [("समस्या", "ज़्यादातर ट्यूटर सिर्फ अंतिम उत्तर देते हैं।"),
                  ("विचार", "हम हर पंक्ति की तुलना करते हैं।"),
                  ("निदान", "गलतफहमियों की लाइब्रेरी नाम बताती है।"),
                  ("सुधार", "उसी गलतफहमी पर नया सवाल।"),
                  ("प्रमाण", "100 केस से सटीकता मापी जाती है।"),
                  ("पहुँच", "अंग्रेज़ी, हिन्दी, अरबी या फ़्रेंच में।")],
        "outro": "यही है Mistake-to-Mastery।",
        "not_understood": "मैं समझ नहीं पायी।",
        "demo_offer": "कोई गणित सवाल पूछें।",
    },
    "Arabic": {
        "intro": "مرحباً! أنا مساعدة Mistake-to-Mastery. أجد الخطوة التي أخطأ فيها الطالب.",
        "beats": [("المشكلة", "معظم المدرّسين يعطون الجواب النهائي فقط."),
                  ("الفكرة", "نقارن كل سطر بالسطر السابق."),
                  ("التشخيص", "مكتبة المفاهيم الخاطئة تسمّي الخطأ."),
                  ("الحل", "مسألة جديدة على نفس المفهوم."),
                  ("الدليل", "نقيس الدقة على 100 حالة."),
                  ("الانتشار", "بالإنجليزية أو الهندية أو العربية أو الفرنسية.")],
        "outro": "هذا هو Mistake-to-Mastery.",
        "not_understood": "لم أفهم.",
        "demo_offer": "اطرح سؤالاً في الرياضيات.",
    },
    "French": {
        "intro": "Bonjour ! Je suis l'assistante Mistake-to-Mastery. Je trouve l'étape exacte où l'élève s'est trompé.",
        "beats": [("Le problème", "La plupart des tuteurs donnent la réponse finale."),
                  ("L'idée", "On compare chaque ligne avec la précédente."),
                  ("Le diagnostic", "Une bibliothèque d'erreurs connues la nomme."),
                  ("Le remède", "Un nouvel exercice sur la même erreur."),
                  ("La preuve", "100 cas mesurent la précision."),
                  ("La portée", "Anglais, hindi, arabe ou français.")],
        "outro": "Voilà Mistake-to-Mastery.",
        "not_understood": "Je n'ai pas compris.",
        "demo_offer": "Posez une question de maths.",
    },
}


def _t(lang: str) -> dict:
    return SCRIPT.get(lang) or SCRIPT["English"]


def intro(lang: str = "English") -> str:
    return _t(lang)["intro"]


def outro(lang: str = "English") -> str:
    return _t(lang)["outro"]


def beats(lang: str = "English") -> list:
    return _t(lang)["beats"]


def demo_offer(lang: str = "English") -> str:
    return _t(lang)["demo_offer"]


def translate(text: str, target_lang: str) -> str:
    if not text or target_lang == "English":
        return text
    model = _get_model()
    if model is None:
        return text
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        msgs = [
            SystemMessage(content=f"Translate into {target_lang}. Keep maths and numbers unchanged. Reply with translation only."),
            HumanMessage(content=text),
        ]
        return _text(model.invoke(msgs)).strip() or text
    except Exception as e:
        print("TRANSLATE ERROR:", e)
        return text


PRESENTER_SYSTEM = (
    "You are a friendly presenter bot for a school project called Mistake-to-Mastery. "
    "Answer the audience's question in 2 to 4 short sentences. "
    "Explain the project, its features, or the maths behind the demo. "
    "Be warm, confident and concise. Always reply in {lang}."
)


def respond(text: str, lang: str = "English", context: str = "") -> str:
    model = _get_model()
    if model is None:
        return _t(lang)["not_understood"]
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        user = text if not context else f"Context:\n{context}\n\nQuestion: {text}"
        reply = _text(model.invoke([SystemMessage(content=PRESENTER_SYSTEM.format(lang=lang)),
                                    HumanMessage(content=user)]))
        return reply.strip() or _t(lang)["not_understood"]
    except Exception as e:
        print("RESPOND ERROR:", e)
        return _t(lang)["not_understood"]


def listen(audio_bytes: bytes, language_code=None):
    return transcribe(audio_bytes, language_code)


def say(text: str, lang: str = "English"):
    """Generate speech. Prints the code it's using so you can verify in the terminal."""
    code = LANG_TO_GTTS.get(lang, "en")
    print(f"[presenter.say] lang={lang!r} -> gTTS code={code!r} text={text[:40]!r}")
    mp3 = speak(text, code)
    if mp3 is None:
        print(f"[presenter.say] speak() returned None for code={code!r}")
    return mp3