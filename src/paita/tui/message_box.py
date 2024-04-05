from pathlib import PurePath
from typing import TYPE_CHECKING

import pyperclip
from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Label, Markdown, Static
from textual.widgets._markdown import MarkdownBlock, MarkdownBullet, MarkdownFence

if TYPE_CHECKING:
    from textual.timer import Timer

ROLE_ABBREVIATIONS = {"question": "Q", "answer": "A", "info": "i", "error": "!"}


class MessageContent(Markdown, can_focus=True, can_focus_children=False):
    BINDINGS = [
        Binding("enter", "enable_focus_children"),
        Binding("escape", "disable_focus_children"),
        Binding("tab,down,right", "focus_next", priority=True),
        Binding("shift+tab,up,left", "focus_previous", priority=True),
        Binding("c", "copy", "Copy", show=True, key_display="c", priority=True),
    ]

    def action_enable_focus_children(self) -> None:
        self.can_focus_children = True
        for child in self.children:
            child.can_focus = True
        self.children[0].focus()

    def action_disable_focus_children(self) -> None:
        if isinstance(self.screen.focused, MarkdownFence):
            self.update_fence_highlighting(
                fence=self.screen.focused,
                highlight=False,
            )

        self.can_focus_children = False
        for child in self.children:
            child.can_focus = False
        self.focus()

    def action_focus_next(self) -> None:
        if self.can_focus_children:
            if isinstance(self.screen.focused, MarkdownFence):
                self.update_fence_highlighting(
                    fence=self.screen.focused,
                    highlight=False,
                )

            self.screen.focus_next("MessageContent *")
            if isinstance(self.screen.focused, MarkdownFence):
                self.update_fence_highlighting(fence=self.screen.focused, highlight=True)
        else:
            self.screen.focus_next()

    def action_focus_previous(self) -> None:
        if self.can_focus_children:
            if isinstance(self.screen.focused, MarkdownFence):
                self.update_fence_highlighting(
                    fence=self.screen.focused,
                    highlight=False,
                )

            self.screen.focus_previous("MessageContent *")
            if isinstance(self.screen.focused, MarkdownFence):
                self.update_fence_highlighting(self.screen.focused, highlight=True)
        else:
            self.screen.focus_previous()

    def update_fence_highlighting(
        self,
        fence: MarkdownFence,
        *,
        highlight: bool,
    ) -> None:
        if highlight:
            accent_color = "#0178D4"
            block = Syntax(
                fence.code,
                lexer=fence.lexer,
                word_wrap=False,
                indent_guides=True,
                padding=(1, 2),
                theme=fence.theme,
                background_color=accent_color,
            )
        else:
            block = Syntax(
                fence.code,
                lexer=fence.lexer,
                word_wrap=False,
                indent_guides=True,
                padding=(1, 2),
                theme=fence.theme,
            )

        fence.get_child_by_type(Static).update(block)

    def action_copy(self) -> None:
        if self.has_focus:
            content = self.parse_from_children(self)
        else:
            for child in self.children:
                if child.has_focus:
                    content = self.parse_from_children(child)

        pyperclip.copy(content)

    def parse_from_children(self, block: MarkdownBlock, indent_depth: int = -2) -> str:
        children = block.children

        if isinstance(block, MarkdownFence):
            return block.code

        if len(children) > 0:
            text = ""
            for child in children:
                text += self.parse_from_children(child, indent_depth + 1)
            return text
        if isinstance(block, MarkdownBullet):
            return " " * indent_depth + "- "
        if isinstance(block, MarkdownFence):
            return block.code
        return str(block.renderable) + "\n"


class MessageBox(Horizontal, can_focus=False):
    CSS_PATH = PurePath(__file__).parent / "styles" / "message_box.tcss"

    def __init__(self, data: str, *, role: str) -> None:
        super().__init__(classes=f"message {role}")
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
        self._update_timer = self.set_interval(1 / 4, self._markdown_update, pause=True)

    def append(self, data: str):
        self.data += data
        self._update_timer.resume()

    def flush(self):
        if self._update_timer:
            self._update_timer.pause()
        self._markdown_update()

    def _markdown_update(self):
        if self._message_content:
            self._message_content.update(self.data)
        self.parent.scroll_end(animate=False)
