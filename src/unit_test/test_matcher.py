import pytest

from approxism import Matcher
from approxism.transforms import Lowercase


def test_default():
    matcher = Matcher()
    #                         0123456789012
    assert list(matcher.text("Hello world!").match("worl", 0.85)) == [
        Matcher.Match(6, 11, 2*3/(4+3))  # 2 times intersection size over sum of sizes
    ]

    # Score threshold too high
    assert list(matcher.text("Hello world!").match("worl", 0.9)) == []

    text = matcher.text(
        #0         1         2         3         4         5         6         7
        #01234567890123456789012345678901234567890123456789012345678901234567890123456
        "First test sentence.  Second test sentence. Such great test sentences."
    )
    bgr = matcher.sequence_bigrams("test sentnece")  # 'cause I can't type properly...

    assert list(text.match(bgr, 0.65)) == [
        Matcher.Match( 6, 19, 2*8/(11+11)),     # 3 bigrams lost: te en nc
        Matcher.Match(29, 42, 2*8/(11+11)),     # ditto
        Matcher.Match(55, 69, 2*8/(12+11)),     # 4 bigrams lost: te en nc es
    ]


def test_lowercase():
    #      0         1         2         3         4         5         6         7
    #      01234567890123456789012345678901234567890123456789012345678901234567890123456
    txt = "Kniha Teoretické otázky neuronových sítí, autoři: Jiří Šíma a Roman Neruda."

    name1 = "šíma, jiří"
    name2 = "neruda, roman"

    matcher = Matcher("czech")
    text = matcher.sentence(txt)
    bgr1 = matcher.sequence_bigrams(name1)
    bgr2 = matcher.sequence_bigrams(name2)

    assert list(text.match(bgr1, 0.57)) == [
        Matcher.Match(50, 59, 2*4/(7+7)),       # 3 bigrams lost: Ji '  ' Ší
    ]
    assert list(text.match(bgr2, 0.6)) == [
        Matcher.Match(62, 74, 2*7/(10+10)),     # 3 bigrams lost: Ro '  ' Ne
    ]

    matcher = Matcher("czech", token_transform=[Lowercase()])
    text = matcher.sentence(txt)
    bgr1 = matcher.sequence_bigrams(name1)
    bgr2 = matcher.sequence_bigrams(name2)

    assert list(text.match(bgr1, 0.85)) == [
        Matcher.Match(50, 59, 2*6/(7+7)),       # 1 bigram lost only: '  '
    ]
    assert list(text.match(bgr2, 0.85)) == [
        Matcher.Match(62, 74, 2*9/(10+10)),     # ditto
    ]


def test_acronym_support():
    #      0         1         2         3         4
    #      01234567890123456789012345678901234567890123456
    txt = "Créez une nouvelle AMI pour l'instance EC2."     # technical stuff

    pattern = "nouvel ami"                                  # dating people or whatnot

    matcher = Matcher("french", token_transform=[Lowercase()])
    assert list(matcher.sentence(txt).match(pattern, 0.85)) == [
        Matcher.Match(10, 22, 2*8/(8+10)),  # AMI == AWS Machine Image, not a friend :-(
    ]

    matcher = Matcher("french", token_transform=[Lowercase(min_len=4, except_caps=True)])
    assert list(matcher.sentence(txt).match(pattern, 0.7)) == []  # matches no more :-)


def test_stopwords():
    #      0         1         2         3         4
    #      01234567890123456789012345678901234567890123456789
    txt = "How to tell which cat is dominant in the house?"

    pattern = "dominant man"

    assert list(Matcher(strip_stopwords=False).sentence(txt).match(pattern, 0.8)) == [
        Matcher.Match(22, 33, 2*8/(9+10)),  # maximises match by adding "is" (gains '  ')
    ]

    assert list(Matcher(strip_stopwords=True).sentence(txt).match(pattern, 0.8)) == [
        Matcher.Match(25, 33, 2*7/(7+10)),  # forced to drop the "is", that's better :-)
    ]


def test_strict_language():
    with pytest.raises(LookupError):  # alas, Martian isn't supported so far...
        Matcher("martian")

    assert Matcher("martian", strict_language=False)  # a fallback will do (Neptunian?)
