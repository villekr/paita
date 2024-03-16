from pathlib import PurePath

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator


class WaitScreen(ModalScreen[bool]):
    CSS_PATH = PurePath(__file__).parent / "styles" / "wait_screen.tcss"

    def __init__(self, text):
        super().__init__()
        self._text = text

    def compose(self) -> ComposeResult:
        with Vertical(id="wait_screen_vertical"):
            yield Label(self._text, id="wait_screen_label")
            yield LoadingIndicator()
