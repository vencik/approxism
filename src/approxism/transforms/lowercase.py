from typing import Iterator

from approxism.tokeniser import Tokeniser
from approxism.matcher import Matcher


class Lowercase(Matcher.TokenTransform):
    """
    Lowercase words

    One may set minimal length the word must have in order to lowercase it and/or only
    do that if any characters are already in lower case.
    This may be handy to eliminate lowercasing short acronyms, which may then easily
    be mistaken for common words.

    By default, everything is lowercased.
    """
    def __init__(self, min_len: int = 0, except_caps: bool = False):
        """
        :param min_len: Minimal length the word must have to be lowercased
        :param except_caps: If `True` then even words shorter than `min_len`
                            are lowercased unless in all CAPS (in that case,
                            the word is kept as is)
        """
        self.min_len = min_len
        self.except_caps = except_caps

    def transform(
        self,
        sequence: str,
        tokens: Iterator[Tokeniser.Token],
    ) -> Iterator[Tokeniser.Token]:
        """
        :param sequence: Original sequence (not used)
        :param tokens: Sequence tokens
        :return: Tokens (all words lowercased)
        """
        for token in tokens:
            while True:  # pragmatic loop allowing for breaks
                if token.tag != Tokeniser.word: break  # don't lowercase non-words

                if len(token.string) < self.min_len:  # short word
                    if not self.except_caps: break  # keep as is

                    if token.string.upper() == token.string:
                        break  # all CAPS, keep as is

                token.string = token.string.lower()  # lowercase
                break  # end of pragmatic loop

            yield token
