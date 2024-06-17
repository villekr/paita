import contextlib
from pathlib import PurePath
from typing import List, Optional, Tuple

from cache3 import DiskCache
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll, Widget
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.validation import Function, Number
from textual.widgets import Button, Checkbox, Header, Input, Select, TextArea

import paita.localization.labels as label
from paita.llm.enums import Tag
from paita.localization import labels
from paita.rag.models import RAGSource, RAGSources
from paita.rag.rag_manager import RAGManager, RAGSourceType
from paita.tui.wait_screen import WaitScreen
from paita.utils.logger import log
from paita.utils.settings_manager import SettingsManager, SettingsModel
from paita.utils.string_utils import dict_to_str, str_to_dict, str_to_num, to_str, validate_and_fix_url

RAG_WIDGET_IDS = [
    "ai_rag_type",
    "ai_rag_source",
    "ai_rag_source_max_depth",
    "ai_rag_load",
    "ai_rag_reset",
    "ai_rag_contextualize_prompt",
    "ai_rag_system_prompt",
]


class SettingsScreen(ModalScreen[bool]):
    CSS_PATH = PurePath(__file__).parent / "styles" / "settings_screen.tcss"

    def __init__(
        self,
        *,
        settings_manager: SettingsManager,
        rag_manager: Optional[RAGManager],
        cache: DiskCache,
        allow_cancel: bool = False,
    ):
        super().__init__()
        self.settings_manager: SettingsManager = settings_manager
        self.rag_manager: RAGManager = rag_manager
        self.model: SettingsModel = settings_manager.model.model_copy()
        self.cache: DiskCache = cache
        self.allow_cancel: bool = allow_cancel

        # Prefill select options based on stored settings values
        self._ai_services: List[Tuple[str, str]] = list(self.cache.keys(tag=Tag.AI_MODELS.value))
        if self.model.ai_service not in self._ai_services:
            self.model.ai_service = self._ai_services[0]

        self._ai_models: List[Tuple[str, str]] = self.cache.get(self.model.ai_service, [], tag=Tag.AI_MODELS.value)
        if self.model.ai_model not in self._ai_models:
            self.model.ai_model = self._ai_models[0]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="settings"):
            with VerticalScroll(id="settings"):
                with Horizontal(classes="settings_invisible_block"):
                    yield Select(
                        [(item, item) for item in self._ai_services],
                        value=self.model.ai_service,
                        prompt="AI Service",
                        id="ai_service",
                        classes="settings_small_option",
                        allow_blank=False,
                    )
                    yield Select(
                        [(item, item) for item in self._ai_models],
                        value=self.model.ai_model,
                        prompt="AI Model",
                        id="ai_model",
                        classes="settings_option",
                        allow_blank=False,
                    )
                    yield Checkbox(
                        label.AI_STREAMING,
                        value=self.model.ai_streaming,
                        id="ai_streaming",
                        classes="settings_checkbox",
                    )

                yield TextArea(
                    text=self.model.ai_persona,
                    id="ai_persona",
                    classes="settings_textarea",
                )

                with Horizontal(classes="settings_invisible_block"):
                    yield Input(
                        placeholder=label.AI_MODEL_KWARGS,
                        value=dict_to_str(self.model.ai_model_kwargs),
                        id="ai_model_kwargs",
                        classes="settings_input",
                        validators=[Function(self.validate_ai_model_kwargs, "Invalid dictionary")],
                    )
                    yield Input(
                        placeholder=label.AI_MAX_TOKENS,
                        value=to_str(self.model.ai_max_tokens),
                        id="ai_max_tokens",
                        classes="settings_small_input",
                        type="integer",
                        validators=[Number(minimum=1, maximum=99999)],
                        max_length=5,
                    )
                    yield Input(
                        placeholder=label.AI_HISTORY_DEPTH,
                        value=to_str(self.model.ai_history_depth),
                        id="ai_history_depth",
                        classes="settings_small_input",
                        type="integer",
                        validators=[Number(minimum=0, maximum=100)],
                        max_length=3,
                    )
                    # yield Input(
                    #     placeholder=label.AI_N,
                    #     value=to_str(self.model.ai_n),
                    #     id="ai_n",
                    #     classes="settings_input",
                    #     type="integer",
                    #     validators=[Number(minimum=1, maximum=10)],
                    #     max_length=4,
                    # )

                with Vertical(classes="settings_invisible_block", id="ai_rag_container"):
                    yield Checkbox(
                        label.AI_RAG_ENABLED,
                        value=self.model.ai_rag_enabled,
                        id="ai_rag_enabled",
                        classes="settings_checkbox",
                    )
                    yield TextArea(
                        text=self.model.ai_rag_contextualize_prompt,
                        id="ai_rag_contextualize_prompt",
                        classes="settings_textarea",
                    )
                    yield TextArea(
                        text=self.model.ai_rag_system_prompt,
                        id="ai_rag_system_prompt",
                        classes="settings_textarea",
                    )

                with Horizontal(classes="settings_block"):
                    yield Button(label="Apply", variant="success", id="apply")
                    if self.allow_cancel:
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
        ai_rag_disabled = not self.model.ai_rag_enabled
        if self.model.ai_service is Select.BLANK or self.model.ai_model is Select.BLANK:
            self.query_one("#apply").disabled = True

            for rag_widget_id in RAG_WIDGET_IDS:
                with contextlib.suppress(NoMatches):
                    self.query_one(f"#{rag_widget_id}").disabled = True

            ai_rag_disabled = True
            self.query_one("#ai_rag_enabled").disabled = True

        # TODO: Create a separate component to handle RAG source(s)
        self.query_one("#ai_rag_contextualize_prompt").disabled = ai_rag_disabled
        self.query_one("#ai_rag_system_prompt").disabled = ai_rag_disabled

        rag_sources: RAGSources = await self.rag_manager.read()
        rag_source: RAGSource = rag_sources.rag_sources[-1] if rag_sources.rag_sources else RAGSource()

        widgets: [Widget] = [
            Select(
                [(item.value, item.value) for item in RAGSourceType],
                value=rag_source.rag_source_type.value,
                prompt="AI Rag Type",
                id="ai_rag_type",
                classes="settings_small_option",
                allow_blank=False,
                disabled=ai_rag_disabled,
            ),
            Input(
                placeholder=label.AI_RAG_SOURCE_MAX_DEPTH,
                value=str(rag_source.rag_source_max_depth),
                id="ai_rag_source_max_depth",
                classes="settings_small_input",
                type="integer",
                validators=[Number(minimum=1, maximum=5)],
                max_length=1,
                disabled=ai_rag_disabled,
            ),
        ]

        # ai_rag_source: not None
        # - input = disable
        # - button = "reset"
        # ai_rag_source: None
        # - input = enabled
        # - button = "load"
        input_disabled = ai_rag_disabled or bool(rag_source.rag_source)
        ai_rag_source = Input(
            placeholder=label.AI_RAG_SOURCE,
            value=rag_source.rag_source if rag_source.rag_source else "",
            id="ai_rag_source",
            classes="settings_input",
            disabled=input_disabled,
        )
        widgets.append(ai_rag_source)

        button_disabled = ai_rag_disabled
        if not ai_rag_disabled and ai_rag_source.value == "":
            button_disabled = True
        if bool(rag_source.rag_source):
            widgets.append(Button(label="Reset", variant="warning", id="ai_rag_reset", disabled=button_disabled))
        else:
            widgets.append(Button(label="Load", variant="success", id="ai_rag_load", disabled=button_disabled))

        horizontal = Horizontal(classes="settings_invisible_block", id="ai_rag_sources")
        rag_container = self.query_one("#ai_rag_container")
        await rag_container.mount(horizontal)
        await horizontal.mount(*widgets)
        self.query_one("#ai_persona").disabled = self.model.ai_rag_enabled

    @on(Input.Changed)
    async def input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "ai_rag_source":
            try:
                ai_rag_load = self.query_one("#ai_rag_load")
                if event.input.value != "":
                    ai_rag_load.disabled = False
                else:
                    ai_rag_load.disabled = True
            except NoMatches:
                pass

    @on(Checkbox.Changed)
    async def checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "ai_rag_enabled":
            for rag_widget_id in RAG_WIDGET_IDS:
                with contextlib.suppress(NoMatches):
                    self.query_one(f"#{rag_widget_id}").disabled = not event.checkbox.value

            # Keep 'rag source'-input field disabled when we think source is loaded
            # If there's 'load'-button keep it disabled if 'rag source' field has content
            if event.checkbox.value:
                ai_rag_source = self.query_one("#ai_rag_source")
                try:
                    ai_rag_load = self.query_one("#ai_rag_load")
                    if ai_rag_source.value != "":
                        ai_rag_load.disabled = False
                    else:
                        ai_rag_load.disabled = True
                except NoMatches:
                    pass

            self.query_one("#ai_persona").disabled = event.checkbox.value

    @on(Select.Changed)
    async def select_changed(self, event: Select.Changed) -> None:
        if event.control.id == "ai_service":
            value = event.value
            if value == self.model.ai_service:
                return
            self.settings_manager.ai_service = value

            models = self.cache.get(event.value, Select.BLANK, tag=Tag.AI_MODELS.value)
            widget: Select = self.query_one("#ai_model")
            widget.set_options((item, item) for item in models)
        elif event.control.id == "ai_model":
            value = event.value
            if value == self.model.ai_model:
                return
            self.query_one("#apply").disabled = False
        elif event.control.id == "ai_rag_type":
            pass  # TODO: Handle different RAG types
        else:
            log.error(f"Undefined {event.control.id=}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        # PoC RAG approach, we always update model and save
        model: SettingsModel = SettingsModel(
            ai_service=self.query_one("#ai_service").value,
            ai_model=self.query_one("#ai_model").value,
        )
        if (value := self.query_one("#ai_persona").text) != "":
            model.ai_persona = value
        if (value := self.query_one("#ai_model_kwargs").value) != "":
            model.ai_model_kwargs = str_to_dict(value)
        model.ai_streaming = self.query_one("#ai_streaming").value
        # if (value := self.query_one("#ai_n").value) != "":
        #     model.ai_n = str_to_num(value)
        if (value := self.query_one("#ai_max_tokens").value) != "":
            model.ai_max_tokens = str_to_num(value)
        if (value := self.query_one("#ai_history_depth").value) != "":
            model.ai_history_depth = str_to_num(value)

        # RAG
        model.ai_rag_enabled = self.query_one("#ai_rag_enabled").value
        if (value := self.query_one("#ai_rag_contextualize_prompt").text) != "":
            model.ai_rag_contextualize_prompt = value
        if (value := self.query_one("#ai_rag_system_prompt").text) != "":
            model.ai_rag_system_prompt = value

        self.settings_manager.model = model

        if event.button.id == "apply":
            await self.settings_manager.save()
            self.dismiss(True)
        elif event.control.id == "ai_rag_load":
            ai_rag_source = self.query_one("#ai_rag_source")
            if (value := ai_rag_source.value) != "":
                try:
                    url = validate_and_fix_url(value)
                    ai_rag_source.remove_class("settings_input_error", update=True)
                    ai_rag_source.value = url

                    max_depth = str_to_num(self.query_one("#ai_rag_source_max_depth").value)
                    await self.parent.push_screen(WaitScreen(labels.APP_RAG_PROCESS_DOCUMENTS))
                    await self.rag_manager.create(url=url, max_depth=max_depth)
                    await event.control.remove()
                    await self.mount(Button(label="Reset", variant="warning", id="ai_rag_reset"), after=ai_rag_source)

                    await self.settings_manager.save()

                    self.parent.pop_screen()
                except ValueError:
                    ai_rag_source.add_class("settings_input_error", update=True)
        elif event.control.id == "ai_rag_reset":
            ai_rag_source = self.query_one("#ai_rag_source")
            await self.rag_manager.delete(ai_rag_source.value)
            ai_rag_source.value = ""
            ai_rag_source.disabled = False
            await event.control.remove()
            await self.mount(
                Button(label="Load", variant="success", id="ai_rag_load", disabled=True), after=ai_rag_source
            )
            await self.settings_manager.save()
        else:
            self.dismiss(False)
