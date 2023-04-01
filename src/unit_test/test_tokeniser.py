from string import punctuation

from approxism import Tokeniser
from approxism.tokeniser import punctuation_chars


def test_punctuation_chars():
    punct_chars = punctuation_chars()

    # All ASCII punct chars are there, except apostrophe
    assert all(ch in punct_chars for ch in set(punctuation) - set("'’"))

    # Check a few UNICODE punct. chars...
    assert all(ch in punct_chars for ch in "“”¿¡")


def test_available():
    available = Tokeniser.available()
    assert all(lang in available for lang in ["english", "czech", "german", "french"])


def test_sentences():
    text =  "Hello world!  This is a test text, it should be split. All done, good bye!"
    assert list(Tokeniser().sentences(text)) == [
        "Hello world!",
        "  This is a test text, it should be split.",
        " All done, good bye!",
    ]


def test_tokenise():
    #                                 0         1         2         3
    #                                 0123456789012345678901234567890123456789
    assert list(Tokeniser().tokenise("I'm sorry, I haven't a clue.")) == [
        Tokeniser.Token("I'm",       0,  3, Tokeniser.word),
        Tokeniser.Token(" ",         3,  4, Tokeniser.ws),
        Tokeniser.Token("sorry",     4,  9, Tokeniser.word),
        Tokeniser.Token(", ",        9, 11, Tokeniser.punct),
        Tokeniser.Token("I",        11, 12, Tokeniser.word),
        Tokeniser.Token(" ",        12, 13, Tokeniser.ws),
        Tokeniser.Token("haven't",  13, 20, Tokeniser.word),
        Tokeniser.Token(" ",        20, 21, Tokeniser.ws),
        Tokeniser.Token("a",        21, 22, Tokeniser.word),
        Tokeniser.Token(" ",        22, 23, Tokeniser.ws),
        Tokeniser.Token("clue",     23, 27, Tokeniser.word),
        Tokeniser.Token(".",        27, 28, Tokeniser.punct),
    ]
