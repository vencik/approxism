from __future__ import annotations
from typing import Set, ClassVar, Iterator
from string import whitespace, punctuation
from unicodedata import category as unicode_category
from sys import maxunicode
import re

from nltkdata import load as nltk_load
from nltk.tokenize.punkt import PunktSentenceTokenizer


class Tokeniser:
    """
    String tokeniser

    The tokeniser uses NLTK punkt to split text into sentences.
    Sentences are tokenised by splitting text by split characters,
    which are white spaces and punctuation characters (or character sequences).
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

    @staticmethod
    def _punct() -> Set[str]:
        """
        :return: Punctuation characters
        """
        chars = {
            char for char_code in range(maxunicode + 1)
            if unicode_category(char := chr(char_code))[0] == 'P'
        }
        chars.update(set(punctuation) - set("'"))
        return chars

    @staticmethod
    def _ws() -> Set[str]:
        """
        :return: White space characters
        """
        return set(whitespace)

    _punctuation = Tokeniser._punct()
    _whitespaces = Tokeniser._ws()
    _split_chars = "".join(Tokeniser._punctuation) + "".join(Tokeniser._whitespaces)
    _splitter = re.compile(rf"[^{Tokeniser._split_chars}]+")

    word = "word"
    whitespace = "WS"
    punctuation = "punct"

    def __init__(self, language: str = "english"):
        """
        :param language: Language
        """
        punkt_pickle = f"./punkt/PY3/{language}.pickle"
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
                    return Tokeniser.punctuation
            return Tokeniser.whitespace

        offset = 0
        for match in re.finditer(Tokeniser._splitter, string):
            begin, end = match.span()

            if offset < begin:   # split token
                token = string[offset:begin]
                yield Tokeniser.Token(
                    token, begin=offset, end=begin, tag=split_tag(token))

            yield TokeniserToken(match.group(), begin, end, tag=Tokenise.word)
            offset = end

        if offset < len(string):  # trailing split token
            token = string[offset:]
            yield Tokeniser.Token(
                token, begin=offset, end=len(string), tag=split_tag(token))
