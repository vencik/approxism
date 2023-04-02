from __future__ import annotations
from typing import Set, ClassVar, Iterator
from dataclasses import dataclass
from string import whitespace, punctuation
from unicodedata import category as unicode_category
from sys import maxunicode
import re
from glob import glob
from pathlib import Path
from os import environ

from nltk.data import load as nltk_load
from nltk import download as nltk_download
from nltk.tokenize.punkt import PunktSentenceTokenizer
from filelock import FileLock


def punctuation_chars() -> Set[str]:
    """
    :return: Punctuation characters
    """
    chars = {
        char for char_code in range(maxunicode + 1)
        if unicode_category(char := chr(char_code))[0] == 'P'
    }
    chars.update(set(punctuation))
    chars -= set("'’")
    return chars


class Tokeniser:
    """
    String tokeniser

    The tokeniser uses NLTK punkt to split text into sentences.
    Sentences are tokenised by splitting text by split characters,
    which are white spaces and punctuation characters (or character sequences).

    Unfortunately, many NLTK models (including punkt tokenisers) are't explicit about
    copyright statement and/or license (see https://www.nltk.org/nltk_data/).
    Hence, re-packaging the models could easily be a breach of copyright law.
    Therefore, download of the models is left to the user; I don't dare include them
    in the distribution.
    You have been warned...

    You may either download them manually; in that case, set the path to the top-level
    NLTK data directory (containing `tokenizers/punkt/PY3/*.pickle`) in `NLTK_DATA`
    environment variable.
    You may also only set that variable without downloading the data; if the models
    don't exist yet, the tokeniser will download them on-demand.

    If the `NLTK_DATA` environment variable isn't set, the tokeniser shall use
    `/var/tmp/approxism/nltk_data` default.

    NOTE: During download, the NLTK data directory is locked (using an advisory
    file lock).
    Therefore, even parallel usage of the library should be safe and correct.
    """

    @dataclass
    class Token:
        """
        Token
        """
        string: str
        begin: int
        end: int
        tag: str

    _punctuation = punctuation_chars()
    _whitespaces = set(whitespace)
    _split_chars = "".join(_punctuation) + "".join(_whitespaces)
    _word_re = re.compile(rf"[^{re.escape(_split_chars)}]+")

    # Tags
    word = "word"
    ws = "WS"
    punct = "punct"

    nltk_data_dir = environ.get("NLTK_DATA", "/var/tmp/approxism/nltk_data")
    punkt_data_dir = f"{nltk_data_dir}/tokenizers/punkt/PY3"

    @staticmethod
    def assert_punkt_models():
        """
        Make sure NLTK.punkt models are available
        """
        Path(Tokeniser.nltk_data_dir).mkdir(parents=True, exist_ok=True)
        punkt_data_dir = Path(Tokeniser.punkt_data_dir)

        with FileLock(f"{Tokeniser.nltk_data_dir}/.lock"):
            if not punkt_data_dir.is_dir():  # download NLTK.punkt
                nltk_download("punkt", download_dir=Tokeniser.nltk_data_dir)

        assert punkt_data_dir.is_dir()

    def __init__(self, language: str = "english"):
        """
        :param language: Language
        :param default: Default language to use if requested language is not available
        """
        Tokeniser.assert_punkt_models()
        self._punkt = nltk_load(f"{Tokeniser.punkt_data_dir}/{language}.pickle")

    def sentences(self, text: str) -> Iterator[str]:
        """
        :param text: Text string
        :return: Sentences in the text
        """
        begin = 0
        for sentence in self._punkt.tokenize(text):
            end = text.index(sentence, begin) + len(sentence)
            yield text[begin:end]
            begin = end

    def tokenise(self, string: str) -> Iterator[Tokeniser.Token]:
        """
        :param string: String of tokens
        :return: Iterator of [token, begin, end, tag]
        """
        def split_tag(token: str) -> str:
            for char in token:
                if char in Tokeniser._punctuation:
                    return Tokeniser.punct
            return Tokeniser.ws

        offset = 0
        for match in re.finditer(Tokeniser._word_re, string):
            begin, end = match.span()

            if offset < begin:   # split token
                token = string[offset:begin]
                yield Tokeniser.Token(
                    token, begin=offset, end=begin, tag=split_tag(token))

            yield Tokeniser.Token(match.group(), begin, end, tag=Tokeniser.word)
            offset = end

        if offset < len(string):  # trailing split token
            token = string[offset:]
            yield Tokeniser.Token(
                token, begin=offset, end=len(string), tag=split_tag(token))

    @staticmethod
    def available() -> List[str]:
        """
        :return: List of available languages
        """
        Tokeniser.assert_punkt_models()
        return [
            Path(pickle).stem
            for pickle in glob(f"{Tokeniser.punkt_data_dir}/*.pickle")
        ]
