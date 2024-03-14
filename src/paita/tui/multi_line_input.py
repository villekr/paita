# from textual import events
from textual.widgets import TextArea


class MultiLineInput(TextArea):
    def __init__(self, text="", *, id: str, multiline: bool = False, **kwargs):
        super().__init__(text, id=id, **kwargs)
        self.multiline = multiline

    # def on_key(self, event: events.Key) -> None:
    #     if self.multiline and event.key == "enter":
    #         self.text += "\n"
    #     else:
    #         super()._on_key(event)
