from googletrans import Translator, LANGUAGES

from flask import redirect, render_template, request, session
from functools import wraps


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Translates the lyrics inputted into the text box with Google API package


def translate_lyrics(lyrics, source_lang, dest_lang):
    trans = Translator()
    text = trans.translate(lyrics, src=source_lang, dest=dest_lang)
    return text.text

# Returns codes of languages to use with the .translate() method BY REVERSING dictionary


def get_language_codes():
    lang_dict = {val.title(): key for key, val in LANGUAGES.items()}
    return lang_dict


# Returns list of all supported languages that will be displayed in the dropdown menus
def get_language_list():
    return [LANGUAGES[lang].title() for lang in LANGUAGES]

