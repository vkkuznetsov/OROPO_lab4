from dataclasses import dataclass, field


@dataclass
class User:
    id: int
    screen_name: str
    _first_name: str = field(repr=False)
    _last_name: str = field(repr=False)

    def __post_init__(self):
        self._name = f"{self._first_name} {self._last_name}"
        return self._name

    def __repr__(self):
        return f"User(id={self.id}, screen_name='{self.screen_name}', name='{self._name}')"

    @property
    def name(self):
        return self._name


user = User(id=1, screen_name="soeransy", _first_name="Кирилл", _last_name="Евстафьев")
print(user.name)
