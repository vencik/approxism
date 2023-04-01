from __future__ import annotations
from typing import Set, ClassVar, Iterator
from dataclasses import dataclass
from string import whitespace, punctuation
from unicodedata import category as unicode_category
from sys import maxunicode
import re
from glob import glob
from os.path import basename

from nltk.data import load as nltk_load
from nltk.tokenize.punkt import PunktSentenceTokenizer


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
    """

    class Error(Exception):
        """
        Tokeniser error
        """

    @dataclass
    class Token:
        """
        Token
        """
        string: str
        begin: int
        end: int
        tag: string

    _punctuation = punctuation_chars()
    _whitespaces = set(whitespace)
    _split_chars = "".join(_punctuation) + "".join(_whitespaces)
    _splitter = re.compile(rf"[^{re.escape(_split_chars)}]+")

    # Tags
    word = "word"
    ws = "WS"
    punct = "punct"

    data_dir = "./nltk_data"
    punkt_data_dir = f"{data_dir}/punkt/PY3"

    def __init__(self, language: str = "english"):
        """
        :param language: Language
        :param default: Default language to use if requested language is not available
        """
        punkt_pickle = f"{Tokeniser.punkt_data_dir}/{language}.pickle"
        self._punkt = nltk_load(punkt_pickle)

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
        for match in re.finditer(Tokeniser._splitter, string):
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
        return [
            basename(pickle).split('.')[0]
            for pickle in glob(f"{Tokeniser.punkt_data_dir}/*.pickle")
        ]
