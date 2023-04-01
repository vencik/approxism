from approxism import Tokeniser
from approxism.transforms import Lowercase


def check(constructor_args, src, dest):
    def token(token_tag) -> str:
        return token_tag[0] if isinstance(token_tag, tuple) else token_tag

    def tag(token_tag) -> str:
        return token_tag[1] if isinstance(token_tag, tuple) else "word"

    assert list(Lowercase(**constructor_args).transform("NOT USED", (
        Tokeniser.Token(token(token_tag), begin=0, end=0, tag=tag(token_tag))
        for token_tag in src
    ))) == [
        Tokeniser.Token(token(token_tag), begin=0, end=0, tag=tag(token_tag))
        for token_tag in dest
    ]


def test_default():
    check({}, [
        ("Hello", "word"), ("world", "word"), ("!", "punct"), (" ", "WS"),
        ("THIS", "word"), ("WILL", "word"), ("lowerCase", "word"),
        ("BUT", "wrd"), ("tHiS", "..."), ("WON'T", "???"),
    ], [
        ("hello", "word"), ("world", "word"), ("!", "punct"), (" ", "WS"),
        ("this", "word"), ("will", "word"), ("lowercase", "word"),
        ("BUT", "wrd"), ("tHiS", "..."), ("WON'T", "???"),
    ])


def test_min_len():
    check({"min_len": 4}, [
        "ABCDEF", "ABCDE", "ABCD", "ABC", "AB", "A",
    ], [
        "abcdef", "abcde", "abcd", "ABC", "AB", "A",
    ])


def test_except_caps():
    check({"min_len": 4, "except_caps": True}, [
        "ABCDEF", "ABCDE", "ABCD", "ABC", "AB", "A",
        "ABcdEF", "ABCde", "ABCd", "Abc", "Ab",
    ], [
        "abcdef", "abcde", "abcd", "ABC", "AB", "A",
        "abcdef", "abcde", "abcd", "abc", "ab",
    ])
