#!/usr/bin/env python3

from dataclasses import dataclass
import json

from approxism import Extractor
from approxism.transforms import Lowercase


@dataclass
class MyRecord(Extractor.Dictionary.Record):
    whatever: str
    etc: str


def main(argv) -> int:
    if len(argv) != 3:
        print(f"Usage: {__file__} dictionary.json text.txt")
        return 1

    dictionary_json, text_txt = argv[1:]

    with open(dictionary_json, "r", encoding="utf-8") as json_fd:
        dictionary = {
            term: MyRecord(**record)
            for term, record in json.load(json_fd).items()
        }

    extractor = Extractor(
        dictionary,
        default_threshold=0.7,
        language="english",
        strip_stopwords=False,  # matches may start/end at a stop word
        token_transform=[Lowercase(min_len=4, except_caps=True)],
    )

    with open(text_txt, "r", encoding="utf-8") as text_fd:
        my_text = text_fd.read()

    for match in extractor.extract(my_text):
        print(match)

    return 0

if __name__ == "__main__":
    from sys import argv, exit
    exit(main(argv))
