from typing import List


class BaseManual:
    HELP = ''

    @classmethod
    def with_incorrect_options(cls, incorrect_options: List[str]) -> str:
        options = ', '.join(incorrect_options)
        return f"""Неверно указаны опции команды: ({options}).\nОзнакомьтесь со справкой:{cls.HELP}"""
