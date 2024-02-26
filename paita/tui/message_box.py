from pathlib import PurePath

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.timer import Timer
from textual.widgets import Label, Markdown

ROLE_ABBREVIATIONS = {"question": "Q", "answer": "A", "info": "i", "error": "!"}


class FocusableContainer(Container, can_focus=True):
    ...


class MessageBox(Horizontal, can_focus=True):
    CSS_PATH = PurePath(__file__).parent / "styles" / "message_box.tcss"

    def __init__(self, data: str, *, role: str) -> None:
        super().__init__(classes=f"message {role}")
        self._data: str = data
        self._role: str = role
        self._markdown: Markdown = None
        self._update_timer: Timer = None

    def compose(self) -> ComposeResult:
        role_label = ROLE_ABBREVIATIONS[self._role]
        yield Label(role_label, classes=f"{self._role}_label")
        self._markdown = Markdown(self._data, classes="markdown")
        yield self._markdown

    def on_mount(self) -> None:
        self._update_timer = self.set_interval(1 / 2, self._markdown_update, pause=True)

    def append(self, data: str):
        # log.debug(f"append {data=}")
        self._data += data
        self._update_timer.resume()

    def flush(self):
        self._update_timer.pause()
        self._markdown_update()

    def _markdown_update(self):
        # log.debug(f"_markdown_update {self._data=}")
        self._markdown.update(self._data)
        self.parent.scroll_end(animate=False)
