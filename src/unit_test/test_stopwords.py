from approxism import Stopwords
from approxism.stopwords import NoStopwords


def test_default():
    sws = Stopwords()
    assert "is" in sws
    assert sws == Stopwords("english")


def test_czech():
    sws = Stopwords("czech")
    assert "ještě" in sws


def test_available():
    avail = Stopwords.available()
    assert all(lang in avail for lang in ["german", "french", "dutch", "ukrainian"])


def test_no_stopwords():
    assert len(NoStopwords()) == 0
