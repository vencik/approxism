from typing import List
from os.path import basename, dirname, realpath
from glob import glob


class Stopwords(set):
    """
    Stopwords set
    """

    data_dir = f"{dirname(realpath(__file__))}/stopwords"

    def __init__(self, language: str = "english"):
        """
        :param language: Language
        :param lang_dir
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
            basename(stopwords).split('.')[0]
            for stopwords in glob(f"{Stopwords.data_dir}/*.txt")
        ]


class NoStopwords(set):
    """
    Empty set of stopwords
    """
