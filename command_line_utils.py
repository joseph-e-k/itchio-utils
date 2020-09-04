import dataclasses
from typing import Any


def english_list(things, conjunction="and"):
    if len(things) == 0:
        raise ValueError("English doesn't allow empty lists")

    if len(things) == 1:
        return str(things[0])

    if len(things) == 2:
        return f"{things[0]} {conjunction} {things[1]}"

    prefix = ", ".join(str(thing) for thing in things[:-1])
    return f"{prefix}, {conjunction} {things[-1]}"


@dataclasses.dataclass(frozen=True)
class PromptChoice:
    description: str
    value: Any

    def __iter__(self):
        return iter(dataclasses.astuple(self))


def prompt_user_choice(message, choices):
    choices = {
        key: PromptChoice(description, value)
        for (key, (description, value)) in dict(choices).items()
    }

    print(message)
    english_choices = english_list(
        [f"'{key}' to {choice.description}" for (key, choice) in choices.items()],
        conjunction="or"
    )
    user_entered = input(f"Enter {english_choices}: ")

    while user_entered not in choices:
        user_entered = input(f"Invalid choice. Enter {english_choices}: ")

    return choices[user_entered].value
