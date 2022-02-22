from flask import Flask, render_template  # These are all we need for our purposes
import json

import datetime
import glob

app = Flask(__name__)


###############################################################################
# DATA
###############################################################################

data_dir = "data/"
# if 'data/' not in glob.glob('*'):
if not glob.glob(data_dir):
    data_dir = "../data/"
if not glob.glob(data_dir):
    data_dir = "webapp/data/"

# load languages.json file
with open(f"{data_dir}languages.json", "r") as f:
    languages = json.load(f)

# load other_wordles.json file
with open(f"{data_dir}other_wordles.json", "r") as f:
    other_wordles = json.load(f)


def load_words(lang):
    _5words = []
    with open(f"{data_dir}/languages/{lang}/{lang}_5words.txt", "r") as f:
        for line in f:
            _5words.append(line.strip())
    # QA
    _5words = [word.lower() for word in _5words if len(word) == 5 and word.isalpha()]
    return _5words


def load_supplemental_words(lang):
    """loads the supplemental words file if it exists"""
    try:
        with open(f"{data_dir}languages/{lang}/{lang}_5words_supplement.txt", "r") as f:
            supplemental_words = [line.strip() for line in f]
    except FileNotFoundError:
        supplemental_words = []
    return supplemental_words


def load_language_config(lang):
    try:
        with open(f"{data_dir}languages/{lang}/language_config.json", "r") as f:
            language_config = json.load(f)
        return language_config
    except:
        # english is fallback (not ideal but better than empty...)
        with open(f"{data_dir}default_language_config.json", "r") as f:
            language_config = json.load(f)
        return language_config


def get_todays_idx():
    n_days = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).days
    idx = n_days - 18992 + 195
    return idx


todays_idx = get_todays_idx()

language_codes = [f.split("/")[-1] for f in glob.glob(f"{data_dir}/languages/*")]
language_codes_5words = {l_code: load_words(l_code) for l_code in language_codes}
language_codes_5words_supplements = {
    l_code: load_supplemental_words(l_code) for l_code in language_codes
}
language_configs = {l_code: load_language_config(l_code) for l_code in language_codes}

# drop not supported languages
languages = {k: v for k, v in languages.items() if k in language_codes}


# print stats about how many languages we have
print("\n***********************************************")
print(f"                    STATS")
print(f"- {len(languages)} languages")
print(f"- {len([k for (k, v) in language_codes_5words_supplements.items() if v !=[]])} languages with supplemental words")
print(f"- The language with least words is {min(language_codes_5words, key=lambda k: len(language_codes_5words[k]))}, with {len(language_codes_5words[min(language_codes_5words, key=lambda k: len(language_codes_5words[k]))])} words")
print(f"- The language with most words is {max(language_codes_5words, key=lambda k: len(language_codes_5words[k]))}, with {len(language_codes_5words[max(language_codes_5words, key=lambda k: len(language_codes_5words[k]))])} words")
print(f"- Average number of words per language is {sum(len(language_codes_5words[l_code]) for l_code in language_codes)/len(language_codes):.2f}")
print(f"- Average length of supplemental words per language is {sum(len(language_codes_5words_supplements[l_code]) for l_code in language_codes)/len(language_codes):.2f}")
print(f"- There are {len(other_wordles)} other wordles")
print(f"***********************************************\n")


###############################################################################
# CLASSES
###############################################################################


class Language:
    """Holds the attributes of a language"""

    def __init__(self, language_code, word_list):
        self.language_code = language_code
        self.word_list = word_list
        self.word_list_supplement = language_codes_5words_supplements[language_code]
        self.daily_word = word_list[todays_idx % len(word_list)]
        self.todays_idx = todays_idx
        self.config = language_configs[language_code]

        # possible characters
        self.characters = set()
        for word in word_list:
            for char in word:
                self.characters.add(char)
        self.characters = sorted(list(self.characters))

        # if we have a manually defined keyboard, use that. Else create one using the charset
        if self.config["keyboard"] != "":
            self.keyboard = self.config["keyboard"]
        else:
            # keyboard of ten characters per row
            self.keyboard = []
            for i, c in enumerate(self.characters):
                if i % 10 == 0:
                    self.keyboard.append([])
                self.keyboard[-1].append(c)
            self.keyboard[-1].insert(0, "⇨")
            self.keyboard[-1].append("⌫")

            # Deal with bottom row being too crammed:
            if len(self.keyboard[-1]) == 11:
                popped_c = self.keyboard[-1].pop(1)
                self.keyboard[-2].insert(-1, popped_c)
            if len(self.keyboard[-1]) == 12:
                popped_c = self.keyboard[-2].pop(0)
                self.keyboard[-3].insert(-1, popped_c)
                popped_c = self.keyboard[-1].pop(2)
                self.keyboard[-2].insert(-1, popped_c)
                popped_c = self.keyboard[-1].pop(2)
                self.keyboard[-2].insert(-1, popped_c)


###############################################################################
# ROUTES
###############################################################################


@app.route("/")
def index():
    return render_template(
        "index.html",
        languages=languages,
        language_codes=language_codes,
        todays_idx=todays_idx,
        other_wordles=other_wordles,
    )


# arbitrary app route
@app.route("/<lang_code>")
def language(lang_code):
    if lang_code not in language_codes:
        return "Language not found"
    word_list = language_codes_5words[lang_code]
    language = Language(lang_code, word_list)
    return render_template("game.html", language=language)


if __name__ == "__main__":
    app.run(debug=True)