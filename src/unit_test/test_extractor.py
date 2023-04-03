from typing import Optional
from dataclasses import dataclass
from io import StringIO
import json

from approxism import Extractor
from approxism.transforms import Lowercase


@dataclass
class Person(Extractor.Dictionary.Record):
    birth: Optional[str] = None
    nationality: Optional[str] = None
    death: Optional[str] = None
    fictional: Optional[bool] = None

dictionary = {
    "Barrie, Chris" : Person(
        birth="28 March 1960",
        nationality="British",
    ),
    "Rimmer, Arnold" : Person(
        fictional=True,
    ),
    "Charles, Craig" : Person(
        birth="11 July 1964",
    ),
    "Lister, David" : Person(
        _matching_threshold=0.75,  # called Dave, let's lower the score threshold a bit
        birth="unknown",
        fictional=True,
    ),
    "John-Jules, Danny" : Person(
        birth="16 September 1960",
    ),
    "Cat" : Person(
        fictional=True,
        death="9 to go"
    ),
    "Llewellyn, Robert" : Person(
        birth="10 March 1956",
    ),
    "Kryten" : Person(
        birth="none, manufactured",
        fictional=True,
        nationality="N/A",
    ),
    "Lovett, Norman" : Person(
        birth="31 October 1946",
        nationality="British",
    ),
    "Holly" : Person(
        birth="none, manufactured",
        fictional=True,
    ),
    "Grant, Rob" : Person(
    ),
    "Naylor, Doug" : Person(
        birth="31 December 1955",
    ),
}

text = """
Red Dwarf is a British science fiction comedy franchise created by Rob Grant and Doug Naylor, which primarily consists of a television sitcom that aired on BBC Two between 1988 and 1999, and on Dave since 2009, gaining a cult following.[1] The series follows low-ranking technician Dave Lister, who awakens after being in suspended animation for three million years to find that he is the last living human, and that he is alone on the mining spacecraft Red Dwarf—save for a hologram of his deceased bunkmate Arnold Rimmer and "Cat", a life form which evolved from Lister's pregnant cat.

As of 2020, the cast includes Chris Barrie as Rimmer, Craig Charles as Lister, Danny John-Jules as Cat, Robert Llewellyn as the sanitation droid Kryten, and Norman Lovett as the ship's computer, Holly.
"""


def test_dictionary():
    extractor = Extractor(dictionary)
    assert dict(extractor.dictionary()) == dictionary


def test_extraction():
    extractor = Extractor(dictionary, default_threshold=0.8)

    # Note that the detection order (in the list below) follows the matching order
    # (is in the dictionary above), NOT the match position order
    expected = [
        # 1st sentence
        Extractor.Match(
            term="Grant, Rob",
            begin=68,
            end=77,
            score=2*6/(7+6),
            record=dictionary["Grant, Rob"],
            token="Rob Grant",
        ),
        Extractor.Match(
            term="Naylor, Doug",
            begin=82,
            end=93,
            score=2*8/(9+8),
            record=dictionary["Naylor, Doug"],
            token="Doug Naylor",
        ),

        # 2nd sentence
        Extractor.Match(
            term="Rimmer, Arnold",
            begin=510,
            end=523,
            score=2*10/(11+10),
            record=dictionary["Rimmer, Arnold"],
            token="Arnold Rimmer",
        ),
        Extractor.Match(
            term="Lister, David",
            begin=283,
            end=294,
            score=2*7/(10+8),  # == ~0.778, note that the default threshold is 0.8
            record=dictionary["Lister, David"],
            token="Dave Lister",
        ),
        Extractor.Match(
            term="Cat",
            begin=529,
            end=532,
            score=1.0,
            record=dictionary["Cat"],
            token="Cat",
        ),

        # 3rd sentence
        Extractor.Match(
            term="Barrie, Chris",
            begin=620,
            end=632,
            score=2*9/(10+9),
            record=dictionary["Barrie, Chris"],
            token="Chris Barrie",
        ),
        Extractor.Match(
            term="Charles, Craig",
            begin=644,
            end=657,
            score=2*10/(11+10),
            record=dictionary["Charles, Craig"],
            token="Craig Charles",
        ),
        Extractor.Match(
            term="John-Jules, Danny",
            begin=669,
            end=685,
            score=2*12/(13+12),
            record=dictionary["John-Jules, Danny"],
            token="Danny John-Jules",
        ),
        Extractor.Match(
            term="Cat",
            begin=689,
            end=692,
            score=1.0,
            record=dictionary["Cat"],
            token="Cat",
        ),
        Extractor.Match(
            term="Llewellyn, Robert",
            begin=694,
            end=710,
            score=2*13/(14+13),
            record=dictionary["Llewellyn, Robert"],
            token="Robert Llewellyn",
        ),
        Extractor.Match(
            term="Kryten",
            begin=735,
            end=741,
            score=1.0,
            record=dictionary["Kryten"],
            token="Kryten",
        ),
        Extractor.Match(
            term="Lovett, Norman",
            begin=747,
            end=760,
            score=2*10/(11+10),
            record=dictionary["Lovett, Norman"],
            token="Norman Lovett",
        ),
        Extractor.Match(
            term="Holly",
            begin=785,
            end=790,
            score=1.0,
            record=dictionary["Holly"],
            token="Holly",
        ),
    ]

    matches = list(extractor.extract(text))
    assert matches == expected
    assert all(text[match.begin:match.end] == match.token for match in matches)


def test_serialisation(tmpdir):
    extractor = Extractor(
        dictionary,
        default_threshold=0.9,
        language="german",
        strict_language=False,
        token_transform=[Lowercase(min_len=4)])

    dump_json = str(tmpdir/"dump.json")
    extractor.serialise(dump_json)

    with open(dump_json, "r", encoding="utf-8") as dump_fd:
        dump = json.load(dump_fd)
    assert dump == {
        "default_threshold" : 0.9,
        "matcher_arguments" : {
            "language" : "german",
            "strict_language" : False,
            "token_transform" : [{
                "_class" : "approxism.transforms.lowercase::Lowercase",
                "min_len" : 4,
                "except_caps" : False,
            }],
        },
        "dictionary" : {
            name : {
                key : value
                for key, value in list(person.__dict__.items()) + [
                    ("_class", "test_extractor::Person"),
                ]
                if value is not None
            }
            for name, person in dictionary.items()
        }
    }

    extractor = Extractor.deserialise(dump_json)
    assert isinstance(extractor, Extractor)
    assert extractor.default_threshold == 0.9
    assert extractor._dictionary == dictionary
    assert len(extractor._matcher_kwargs) == 3
    assert extractor._matcher_kwargs["language"] == "german"
    assert extractor._matcher_kwargs["strict_language"] == False
    assert isinstance(extractor._matcher_kwargs["token_transform"], list)
    assert len(extractor._matcher_kwargs["token_transform"]) == 1
    assert isinstance(extractor._matcher_kwargs["token_transform"][0], Lowercase)
    assert extractor._matcher_kwargs["token_transform"][0].min_len == 4
    assert extractor._matcher_kwargs["token_transform"][0].except_caps == False
