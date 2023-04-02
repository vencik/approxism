from typing import List
from pathlib import Path
from glob import glob


class Stopwords(set):
    """
    Stopwords set
    """

    data_dir = f"{Path(__file__).parent}/stopwords"

    def __init__(self, language: str = "english"):
        """
        :param language: Language
        """
        stopwords_txt = f"{Stopwords.data_dir}/{language}.txt"
        with open(stopwords_txt, "r", encoding="utf-8") as stopwords_fd:
            super().__init__(word.strip() for word in stopwords_fd)

    @staticmethod
    def available() -> List[str]:
        """
        :return: List of available languages
        """
        return [
            Path(stopwords).stem
            for stopwords in glob(f"{Stopwords.data_dir}/*.txt")
        ]


class NoStopwords(set):
    """
    Empty set of stopwords
    """
