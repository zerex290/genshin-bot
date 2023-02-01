from dataclasses import dataclass


@dataclass(frozen=True)
class GenshinAccount:
    user_id: int
    uid: int
    ltuid: int
    ltoken: str
    cookie_token: str

    @property
    def account_id(self) -> int:
        return self.ltuid
