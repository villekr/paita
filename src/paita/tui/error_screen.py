from pathlib import PurePath

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ErrorScreen(ModalScreen[bool]):
    CSS_PATH = PurePath(__file__).parent / "styles" / "error_screen.tcss"

    def __init__(self, error: str, button_text: str = "Ok"):
        super().__init__()
        self._error: str = error
        self._button_text: str = button_text

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="error_screen_vertical"):
            yield Label(self._error, id="error_screen_label")
            with Horizontal(id="error_screen_button_block"):
                yield Button(self._button_text, variant="primary", id="error_screen_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "error_screen_button":
            self.dismiss(False)
