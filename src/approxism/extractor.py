from __future__ import annotations
from typing import Iterator, Tuple, Any, Optional, Union, IO, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass, is_dataclass
import json
from importlib import import_module
from copy import copy

from pysdcxx import Bigrams

from .matcher import Matcher


class Extractor:
    """
    Identifies dictionary terms in text (using approximate string matching)

    The class simplifies implementation of the (probably most typical) use case
    of the approximate string matching: identification of given dictionary terms
    in a free text (of potentially substantial length).

    Dictionary is obtained from an object which implements the `Extractor.Dictionary`
    interface.
    (E.g. common Python `dict` implements it; but it may be implemented on top of a DB
    connector and so on...)
    The dictionary consists of the (multi-word) terms mapped to customisable records.
    Matches provide access to the records back.
    The resulting system may therefore be used pretty straightforwardly as dictionary
    based named-entity recognition (NER) solution, see
    https://en.wikipedia.org/wiki/Named-entity_recognition

    Each term record may specify custom matching threshold for the particular term
    using `_matching_threshold` record (reserved) field.
    If term-specific matching threshold isn't set, a default threshold shall apply.
    (Different terms, especially terms of substantially different sizes, may indeed
    require more or less lenient matching---the decision is left to the user for
    their convenience.)

    Extractor JSON (de)serialisation is available as long as the dictionary records
    and used token transforms are JSON-serialisable.

    Binary serialisation (e.g. using `pickle`) isn't supported.
    The reason is that the underlying libsdcxx implementation doesn't support binary
    serialisation (at least so far).
    In any case, the only significant time savings achievable by binary serialisation
    would be in speeding up dictionary terms' bigrams creation.
    Since these are computed from the terms in linear time already, binary serialisation
    would probably not be fundamentally faster than reconstruction of the bigram
    multisets from the terms, anyway.
    """

    class Dictionary(ABC):
        """
        Term dictionary interface
        """

        @dataclass
        class Record:
            """
            Dictionary record (base class)
            """
            _matching_threshold: Optional[float] = None

        @abstractmethod
        def items(self) -> Iterator[Tuple[str, Extractor.Dictionary.Record]]:
            """
            Iterate dictionary items
            :return: [term, record] tuples of the dictionary items
            """

    @dataclass
    class Match:
        """
        Match of a term in text

        Fields:
        * `term`    : dictionary term
        * `begin`   : match begin (in Python slice semantics)
        * `end`     : match end (in Python slice semantics)
        * `score`   : match score (Sørensen–Dice coefficient on bigram mutlisets)
        * `record`  : dictionary record (customisable, term-related info)
        * `token`   : matching token in the text (`token == text[begin:end]`)
        """
        term: str
        begin: int
        end: int
        score: float
        record: Extractor.Dictionary.Record
        token: str

    @dataclass
    class _TermRecordBigrams:
        """
        Term record and bigrams
        """
        record: Extractor.Dictionary.Record
        bigrams: Bigrams

    class _JSONEncoder(json.JSONEncoder):
        def default(self, obj: Any) -> Dict[str, Any]:
            result = {
                "_class" : f"{obj.__module__}::{obj.__class__.__name__}",
            }

            obj_dict = copy(obj.__dict__) if not is_dataclass(obj.__class__) else {
                member: value
                for member, value in obj.__dict__.items()
                if value is not None  # no need to serialise unset optional members
            }

            result.update(obj_dict)
            return result

    def __init__(
        self,
        dictionary: Extractor.Dictionary,
        default_threshold: float = 1.0,
        **kwargs: Dict[str, Any],
    ):
        """
        Note that the default matching score threshold is set to 1 (exact match).
        As the matching method time complexity is rather sensitive to the matching score
        threshold, such a conservative default is used in order to achieve fastest
        operation in cases where the user is too lazy to even RTFM.
        More inquisitive users shall be able to achieve much more interesting results
        (which doesn't necessarily mean _better_ results per se... ;-))

        :param dictionary: Term dictionary
        :param default_threshold: Matching threshold used if no term-specific one is set
        :param kwargs: Arguments passed to `Matcher` constructor
        """
        self.default_threshold = default_threshold

        self._dictionary = dictionary
        self._matcher_kwargs = kwargs

    def dictionary(self) -> Iterator[Tuple[str, Extractor.Dictionary.Record]]:
        """
        :return: [term, record] tuples of the dictionary items
        """
        return self._dictionary.items()

    def extract(self, text: str) -> Iterator[Extractor.Match]:
        """
        Extract dictionary term matches identified in text
        :param text: Text
        :return: Matches
        """
        matcher = Matcher(**self._matcher_kwargs)

        terms = {  # preprocess terms
            term : Extractor._TermRecordBigrams(record, matcher.sequence_bigrams(term))
            for term, record in self.dictionary()
        }

        offset = 0
        for sentence_str in matcher.sentences(text):    # split text into sentences
            sentence = matcher.sentence(sentence_str)   # preprocess sentence

            for term, rec_bgrms in terms.items():       # match terms
                record, bigrams = rec_bgrms.record, rec_bgrms.bigrams
                threshold = record._matching_threshold or self.default_threshold

                for match in sentence.match(bigrams, threshold):
                    yield Extractor.Match(
                        term,
                        match.begin + offset,
                        match.end + offset,
                        match.score,
                        record,
                        token=sentence_str[match.begin:match.end],
                    )

            offset += len(sentence_str)

    def serialise(self, dump: Union[str, IO]):
        """
        :param dump: File name or I/O object where the JSON serialisation shall be stored
        """
        with open(dump, "w", encoding="utf-8") if isinstance(dump, str) else dump as fd:
            json.dump({
                "default_threshold" : self.default_threshold,
                "matcher_arguments" : self._matcher_kwargs,
                "dictionary" : dict(self._dictionary.items()),
            }, fd, indent=4, cls=Extractor._JSONEncoder)

    @classmethod
    def deserialise(cls, dump: Union[str, IO]):
        """
        :param dump: File name or I/O object where the JSON serialisation is
        """
        def get_class(source: Any, class_name: str) -> Type:
            split = class_name.split('.', 1)
            c1ass = getattr(source, split[0])
            return c1ass if len(split) == 1 else get_class(c1ass, split[1])

        def reconstruct(obj: Any) -> Any:
            if isinstance(obj, dict):
                class_name = obj.get("_class")
                if class_name:  # the object supports deserialisation from data members
                    del obj["_class"]
                    module_name, class_name = class_name.split('::', 1)
                    return get_class(import_module(module_name), class_name)(**obj)

                # Otherwise reconstruct dict values to depth
                return {key: reconstruct(value) for key, value in obj.items()}

            elif isinstance(obj, list):  # reconstruct list to depth
                return [reconstruct(item) for item in obj]

            else:  # keep value as is
                return obj

        with open(dump, "r", encoding="utf-8") if isinstance(dump, str) else dump as fd:
             config = json.load(fd)

        return cls(
            dictionary=reconstruct(config["dictionary"]),
            default_threshold=config["default_threshold"],
            **reconstruct(config["matcher_arguments"]),
        )
