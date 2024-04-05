from pathlib import PurePath
from typing import List, Tuple

from cache3 import DiskCache
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.validation import Function, Number
from textual.widgets import Button, Checkbox, Header, Input, Select, TextArea

import paita.localization.labels as label
from paita.ai.enums import Tag
from paita.utils.logger import log
from paita.utils.settings_manager import SettingsManager, SettingsModel
from paita.utils.string_utils import dict_to_str, str_to_dict, str_to_num, to_str


class SettingsScreen(ModalScreen[bool]):
    CSS_PATH = PurePath(__file__).parent / "styles" / "settings_screen.tcss"

    def __init__(
        self,
        *,
        settings: SettingsManager,
        cache: DiskCache,
        allow_cancel: bool = False,
    ):
        super().__init__()
        self._settings: SettingsManager = settings
        self._model: SettingsModel = settings.model.model_copy()
        self._cache: DiskCache = cache
        self._allow_cancel: bool = allow_cancel

        # Prefill select options based on stored settings values
        self._ai_services: List[Tuple[str, str]] = list(self._cache.keys(tag=Tag.AI_MODELS.value))
        if self._model.ai_service not in self._ai_services:
            self._model.ai_service = self._ai_services[0]

        self._ai_models: List[Tuple[str, str]] = self._cache.get(self._model.ai_service, [], tag=Tag.AI_MODELS.value)
        if self._model.ai_model not in self._ai_models:
            self._model.ai_model = self._ai_models[0]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="settings"):
            with VerticalScroll(id="settings"):
                yield Select(
                    [(item, item) for item in self._ai_services],
                    value=self._model.ai_service,
                    prompt="AI Service",
                    id="ai_service",
                    classes="settings_option",
                    allow_blank=False,
                )
                yield Select(
                    [(item, item) for item in self._ai_models],
                    value=self._model.ai_model,
                    prompt="AI Model",
                    id="ai_model",
                    classes="settings_option",
                    allow_blank=False,
                )
                yield TextArea(
                    text=self._model.ai_persona,
                    id="ai_persona",
                    classes="settings_textarea",
                )
                yield Input(
                    placeholder=label.AI_MODEL_KWARGS,
                    value=dict_to_str(self._model.ai_model_kwargs),
                    id="ai_model_kwargs",
                    classes="settings_input",
                    validators=[Function(self.validate_ai_model_kwargs, "Invalid dictionary")],
                )
                yield Input(
                    placeholder=label.AI_MAX_TOKENS,
                    value=to_str(self._model.ai_max_tokens),
                    id="ai_max_tokens",
                    classes="settings_input",
                    type="integer",
                    validators=[Number(minimum=1, maximum=100000)],
                    # max_length=4,
                )
                yield Input(
                    placeholder=label.AI_HISTORY_DEPTH,
                    value=to_str(self._model.ai_history_depth),
                    id="ai_history_depth",
                    classes="settings_input",
                    type="integer",
                    validators=[Number(minimum=0, maximum=100)],
                    # max_length=2,
                )
                yield Input(
                    placeholder=label.AI_N,
                    value=to_str(self._model.ai_n),
                    id="ai_n",
                    classes="settings_input",
                    type="integer",
                    validators=[Number(minimum=1, maximum=10)],
                    # max_length=2,
                )
                yield Checkbox(
                    label.AI_STREAMING,
                    value=self._model.ai_streaming,
                    id="ai_streaming",
                    classes="settings_checkbox",
                )
                with Horizontal(classes="settings_block"):
                    yield Button(label="Apply", variant="success", id="apply")
                    if self._allow_cancel:
                        yield Button(label="Cancel", variant="warning", id="cancel")

    @staticmethod
    def validate_ai_model_kwargs(value: str):
        try:
            str_to_dict(value)
        except ValueError:
            return False
        else:
            return True

    async def on_mount(self) -> None:
        if self._model.ai_service is Select.BLANK or self._model.ai_model is Select.BLANK:
            self.query_one("#apply").disabled = True

    @on(Select.Changed)
    async def select_changed(self, event: Select.Changed) -> None:
        if event.control.id == "ai_service":
            value = event.value
            if value == self._model.ai_service:
                return
            models = self._cache.get(event.value, Select.BLANK, tag=Tag.AI_MODELS.value)
            widget: Select = self.query_one("#ai_model")
            widget.set_options((item, item) for item in models)
        elif event.control.id == "ai_model":
            value = event.value
            if value == self._model.ai_model:
                return
            self.query_one("#apply").disabled = False
        else:
            log.error(f"Undefined {event.id=}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            model: SettingsModel = SettingsModel(
                ai_service=self.query_one("#ai_service").value,
                ai_model=self.query_one("#ai_model").value,
            )
            if (value := self.query_one("#ai_persona").text) != "":
                model.ai_persona = value
            if (value := self.query_one("#ai_model_kwargs").value) != "":
                model.ai_model_kwargs = str_to_dict(value)
            if (value := self.query_one("#ai_n").value) != "":
                model.ai_n = str_to_num(value)
            if (value := self.query_one("#ai_max_tokens").value) != "":
                model.ai_max_tokens = str_to_num(value)
            if (value := self.query_one("#ai_history_depth").value) != "":
                model.ai_history_depth = str_to_num(value)
            model.ai_streaming = self.query_one("#ai_streaming").value

            self._settings.model = model
            await self._settings.save()
            self.dismiss(True)
        else:
            self.dismiss(False)
