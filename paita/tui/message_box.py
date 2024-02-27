from pathlib import PurePath

import pyperclip
from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.timer import Timer
from textual.widgets import Label, Markdown

# from paita.utils.logger import log


ROLE_ABBREVIATIONS = {"question": "Q", "answer": "A", "info": "i", "error": "!"}


class MessageContent(Markdown):
    can_focus = True

    def on_key(self, event: events.Key) -> None:
        if event.key == "c":
            pyperclip.copy(self.parent.data)
        # TODO: Implement toggle with enter/esc so that child widgets can be
        # focused and their content can also be copied
        # elif event.key == "enter":
        #     self.can_focus_children = True
        #     log.debug(f"{self.children=}")
        #     first_child = self.children[0]
        #     log.debug(f"{first_child=}")
        #     first_child.can_focus = True
        #     first_child.focus(scroll_visible=True)
        # elif event.key == "escape":
        #     self.can_focus_children = False
        #     self.focus(scroll_visible=True)


class MessageBox(Horizontal, can_focus=True):
    CSS_PATH = PurePath(__file__).parent / "styles" / "message_box.tcss"

    def __init__(self, data: str, *, role: str) -> None:
        super().__init__(classes=f"message {role}")
        self.can_focus = False
        self.data: str = data
        self._role: str = role
        self._message_content: MessageContent = None
        self._update_timer: Timer = None

    def compose(self) -> ComposeResult:
        role_label = ROLE_ABBREVIATIONS[self._role]
        yield Label(role_label, classes=f"{self._role}_label")
        self._message_content = MessageContent(self.data, classes="markdown")
        yield self._message_content

    def on_mount(self) -> None:
        self._update_timer = self.set_interval(1 / 2, self._markdown_update, pause=True)

    def append(self, data: str):
        self.data += data
        self._update_timer.resume()

    def flush(self):
        self._update_timer.pause()
        self._markdown_update()

    def _markdown_update(self):
        self._message_content.update(self.data)
        self.parent.scroll_end(animate=False)
