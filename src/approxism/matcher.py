from __future__ import annotations
from typing import List, ClassVar, Union, Optional, Iterator, Iterable
from abc import ABC, abstractmethod
from dataclasses import dataclass

from pysdcxx import Bigrams, SequenceMatcher

from .tokeniser import Tokeniser
from .stopwords import Stopwords, NoStopwords


class Matcher:
    """
    Approximate string matcher based on `pysdcxx.SequenceMatcher`,
    i.e. Sørensen–Dice coefficient of token sequence bigrams.

    The matcher simplifies text & dictionary preparation for the matching;
    namely, it facilitates tokenisation and selection of best-fitting match.
    """

    @dataclass
    class Match:
        """
        Approximate match
        """
        begin: int
        end: int
        score: float

    @dataclass
    class TokenSequence:
        """
        Sequence of tokens
        """
        tokens: List[Tokeniser.Token]
        matcher: SequenceMatcher

    class TokenTransform(ABC):
        """
        Token sequence transform interface
        The user may inject transformation of sequence of tokens (sentences or match
        patterns), like e.g. lowercasing (to improve pre-processing).
        """
        @abstractmethod
        def transform(
            self,
            sequence: str,
            tokens: Iterable[Tokeniser.Token],
        ) -> Iterator[Tokeniser.Token]:
            """
            :param sequence: Original sequence
            :param tokens: Sequence tokens
            :return: Transformed tokens
            """

    class Text:
        """
        Pre-processed text
        """
        def __init__(self, matcher: Matcher, text: str, split_sentences: bool):
            """
            :param matcher: Matcher
            :param text: Text
            :param split_sentences: Do sentence splitting
            """
            self._matcher = matcher
            self._sentences : List[Matcher.TokenSequence] = []

            sentences = self._matcher.sentences(text) if split_sentences else (text,)

            offset = 0
            for sentence in sentences:
                token_seq = Matcher.TokenSequence(tokens=[], matcher=SequenceMatcher())

                for token in self._matcher.tokenise(sentence):
                    token.begin += offset
                    token.end += offset
                    token_seq.tokens.append(token)
                    token_seq.matcher.append(
                        self._matcher.token_bigrams(token),
                        strip=self._matcher.is_strip_token(token),
                    )

                self._sentences.append(token_seq)
                offset += len(sentence)

        def match(
            self,
            string: Union[str, Bigrams],
            threshold: float,
        ) -> Iterator[Matcher.Match]:
            """
            Match `string` (bigrams) in text
            :param string: Matched string
            :param threshold: Matching score threshold in (0 to 1)
            :return: Matches found
            """
            bigrams = self._matcher.sequence_bigrams(string) \
                if isinstance(string, str) else string
            assert isinstance(bigrams, Bigrams)

            for sentence in self._sentences:
                def make_match(match: SequenceMatcher.Match) -> Matcher.Match:
                    return Matcher.Match(
                        begin=sentence.tokens[match.begin].begin,
                        end=sentence.tokens[match.end - 1].end,
                        score=match.score,
                    )

                best_match: Optional[SequenceMatcher.Match] = None  # best overlap

                for match in sentence.matcher.match(bigrams, threshold):
                    if not best_match:  # no match so far...
                        pass  # ... we shall register this one as the best for now

                    elif not match.begin < best_match.end:  # past last match overlaps
                        yield make_match(best_match)

                    elif match.score <= best_match.score:  # worse overlap found...
                        continue  # ... keep the better one

                    best_match = match  # found (better) overlaping match

                if best_match:  # produce last best match
                    yield make_match(best_match)

    default_language = "english"

    def __init__(
        self,
        language: str = default_language,
        strict_language: bool = True,
        strip_stopwords: bool = True,
        omit_whitespaces: bool = True,
        token_transform: Optional[List[Matcher.TokenTransform]] = None,
    ):
        """
        :param language: Language (for tokenisation)
        :param strict_language: Throw if language unavailable (otherwise use fallbacks)
        :param strip_stopwords: Matches are NOT allowed to begin/end by a stop word
        :param omit_whitespaces: Whitespaces don't contribute to bigram multi-sets
        :param token_transform: Token sequence transform
        """
        self._tokeniser = Tokeniser(
            language if strict_language or language in Tokeniser.available() \
            else Matcher.default_language)

        self._stopwords = (
            Stopwords(language) if strict_language or language in Stopwords.available() \
            else NoStopwords()) if strip_stopwords else NoStopwords()

        self._omit_whitespaces = omit_whitespaces
        self._transform = token_transform or []

    def text(self, string: str) -> Matcher.Text:
        """
        :param string: Text in which to search (in string form)
        :return: Pre-processed text (split into tokenised sentences, bigrams computed)
        """
        return Matcher.Text(self, string, split_sentences=True)

    def sentence(self, string: str) -> Matcher.Text:
        """
        :param string: Sentence in hich to search (in string form)
        :return: Pre-processed sentence (tokenised, bigrams computed)
        """
        return Matcher.Text(self, string, split_sentences=False)

    def sentences(self, text: str) -> Iterator[str]:
        """
        :param text: Text string
        :return: Sentences in the text
        """
        return self._tokeniser.sentences(text)

    def tokenise(self, string: str) -> Iterator[Tokeniser.Token]:
        """
        :param string: String of tokens
        :return: Iterator of [token, begin, end, tag]
        """
        tokens = self._tokeniser.tokenise(string)
        for transform in self._transform:
            tokens = transform.transform(string, tokens)
        return tokens

    def is_strip_token(self, token: Tokeniser.Token) -> bool:
        """
        :param token: Token
        :return: `True` iff token is a whitespace, punctuation or (optionally) stop word
        """
        return token.tag != Tokeniser.word or token.string in self._stopwords

    def token_bigrams(self, token: Tokeniser.Token) -> Bigrams:
        """
        :param token: Token
        :return: Token bigrams
        """
        if token.tag == Tokeniser.ws and self._omit_whitespaces:
            return Bigrams()

        token_string = token.string
        if len(token_string) == 1:  # don't drop single char tokens
            token_string = f"{token_string} "

        return Bigrams(token_string)

    def sequence_bigrams(self, string: str) -> Bigrams:
        """
        :param string: String of tokens
        :return: Token sequence bigrams
        """
        tokens = list(self.tokenise(string))
        while len(tokens) and self.is_strip_token(tokens[0]):
            tokens.pop(0)
        while len(tokens) and self.is_strip_token(tokens[-1]):
            tokens.pop(-1)

        return sum(
            (self.token_bigrams(token) for token in tokens),
            start=Bigrams(),
        )
