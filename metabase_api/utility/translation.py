import logging
import os
from enum import Enum, auto
from pathlib import Path

import yaml
from googletrans import Translator as GoogleTranslator

THIS_FILE_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
TRANSLATION_CONFIG_LOC = (THIS_FILE_PATH / ".." / "resources").resolve()

_logger = logging.getLogger(__name__)


class TranslationPolicyOnMiss(Enum):
    FAIL = auto()
    MIRROR = auto()
    FALLBACK_ON_GOOGLE_TRANSLATE = auto()


class Language(Enum):
    EN = auto()
    FR = auto()


class Translator:
    """Translator from English."""

    def __init__(
        self, to: Language, on_miss: TranslationPolicyOnMiss, case_sensitive: bool
    ):
        self.to_lang = to
        self.on_miss = on_miss
        self.case_sensitive = case_sensitive
        _logger.info("Firing up Google Translator")
        self._google_translator: GoogleTranslator = GoogleTranslator()
        # Reads procedure's definition from its YAML file
        with open(TRANSLATION_CONFIG_LOC / "translation_from_en.yml", "r") as stream:
            self._translation_dict = yaml.safe_load(stream)
        if not self.case_sensitive:
            self._translation_dict = {
                k.lower(): v for (k, v) in self._translation_dict.items()
            }

    def _use_google_translate(self, s: str) -> str:
        r = self._google_translator.translate(s, dest=self.to_lang.name)
        t = r.text
        _logger.debug(
            f"Using Google Translate to decipher '{s}' -> '{t}'; updating dictionary."
        )
        self._translation_dict[s] = {self.to_lang.name: t}
        return t

    def translate(self, sentence: str) -> str:
        """Translates a full expression. Handles pre/post white spaces."""
        if self.to_lang == Language.EN:
            # nothing to do - we assume the dashboard is originally in English
            return sentence
        # handle whitespaces
        # how many at the left? And at the right?
        lblanks = len(sentence) - len(sentence.lstrip())
        rblanks = len(sentence) - len(sentence.rstrip())
        sentence = sentence.strip()
        if len(sentence) == 0:
            return sentence
        case_sentence = sentence.lower() if not self.case_sensitive else sentence
        if case_sentence not in self._translation_dict:
            _err_msg = f"No translation found for '{sentence}'"
            if self.on_miss == TranslationPolicyOnMiss.FAIL:
                _logger.error(_err_msg)
                raise RuntimeError(_err_msg)
            elif self.on_miss == TranslationPolicyOnMiss.MIRROR:
                _logger.debug(f"{_err_msg}; returning it as policy is '{self.on_miss}'")
                t = sentence
            elif self.on_miss == TranslationPolicyOnMiss.FALLBACK_ON_GOOGLE_TRANSLATE:
                t = self._use_google_translate(sentence)
            else:
                raise RuntimeError(
                    f"Internal: I don't know what to do with translation policy {self.on_miss}"
                )
        else:
            if self.to_lang.name not in self._translation_dict[case_sentence]:
                raise ValueError(f"No {self.to_lang.name} translation for '{sentence}'")
            t = self._translation_dict[case_sentence][self.to_lang.name]
        # let's re-add the white spaces
        return " " * lblanks + t + " " * rblanks


Translators: dict[Language, Translator] = {
    lang: Translator(
        to=lang,
        on_miss=TranslationPolicyOnMiss.FALLBACK_ON_GOOGLE_TRANSLATE,
        case_sensitive=False,
    )
    for lang in Language
}

#
# Translators: dict[Language, Translator] = {
#     Language.FR: Translator(
#         to=Language.FR,
#         on_miss=TranslationPolicyOnMiss.FALLBACK_ON_GOOGLE_TRANSLATE,
#         case_sensitive=False,
#     ),
#     Language.EN: Translator(
#         to=Language.EN,
#         on_miss=TranslationPolicyOnMiss.FALLBACK_ON_GOOGLE_TRANSLATE,
#         case_sensitive=False,
#     )
#
# }
