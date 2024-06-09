import contextlib
from pathlib import PurePath
from typing import List, Optional, Tuple

from cache3 import DiskCache
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.validation import Function, Number
from textual.widgets import Button, Checkbox, Header, Input, Select, TextArea

import paita.localization.labels as label
from paita.ai.enums import Tag
from paita.localization import labels
from paita.rag.rag_manager import RAGManager, RAGSourceType
from paita.tui.factory import create_rag_manager
from paita.tui.wait_screen import WaitScreen
from paita.utils.logger import log
from paita.utils.settings_manager import SettingsManager, SettingsModel
from paita.utils.string_utils import dict_to_str, str_to_dict, str_to_num, to_str, validate_and_fix_url

RAG_WIDGET_IDS = [
    # "ai_rag_enabled",
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

        rag_types = [item.value for item in RAGSourceType]
        if self.model.ai_rag_type is None:
            self.model.ai_rag_type = rag_types[0]

        self.ai_rag_source_loaded = self.model.ai_rag_source is not None  # TODO: simplified assumption about load state

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

                with Vertical(classes="settings_invisible_block"):
                    yield Checkbox(
                        label.AI_RAG_ENABLED,
                        value=self.model.ai_rag_enabled,
                        id="ai_rag_enabled",
                        classes="settings_checkbox",
                    )
                    with Horizontal(classes="settings_invisible_block", id="ai_rag_sources"):
                        yield Select(
                            [(item.value, item.value) for item in RAGSourceType],
                            value=self.model.ai_rag_type,
                            prompt="AI Rag Type",
                            id="ai_rag_type",
                            classes="settings_small_option",
                            allow_blank=False,
                        )
                        yield Input(
                            placeholder=label.AI_RAG_SOURCE_MAX_DEPTH,
                            value=str(self.model.ai_rag_source_max_depth),
                            id="ai_rag_source_max_depth",
                            classes="settings_small_input",
                            type="integer",
                            validators=[Number(minimum=1, maximum=5)],
                            max_length=1,
                        )

                        # TODO: Create a separate component to handle RAG source(s)
                        # ai_rag_source: not None
                        # - input = disable
                        # - button = "reset"
                        # ai_rag_source: None
                        # - input = enabled
                        # - button = "load"
                        value = self.model.ai_rag_source
                        ai_rag_source = Input(
                            placeholder=label.AI_RAG_SOURCE,
                            value=value if value else "",
                            id="ai_rag_source",
                            classes="settings_input",
                        )
                        ai_rag_source.disabled = bool(value)
                        yield ai_rag_source
                        if value:
                            yield Button(label="Reset", variant="warning", id="ai_rag_reset")
                        else:
                            yield Button(label="Load", variant="success", id="ai_rag_load", disabled=True)

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
        if self.model.ai_service is Select.BLANK or self.model.ai_model is Select.BLANK:
            self.query_one("#apply").disabled = True

            for rag_widget_id in RAG_WIDGET_IDS:
                with contextlib.suppress(NoMatches):
                    self.query_one(f"#{rag_widget_id}").disabled = True

            self.query_one("#ai_rag_enabled").disabled = True

        if self.model.ai_rag_enabled is False:
            for rag_widget_id in RAG_WIDGET_IDS:
                with contextlib.suppress(NoMatches):
                    self.query_one(f"#{rag_widget_id}").disabled = True

            # ai_rag_load = self.query_one(f"#ai_rag_load")
            # if self.query_one("#ai_rag_source").value != "":
            #     ai_rag_load.disabled = False
            # else:
            #     ai_rag_load.disabled = True

        self.query_one("#ai_persona").disabled = self.model.ai_rag_enabled

    @on(Input.Changed)
    async def input_changed(self, event: Input.Changed) -> None:
        log.debug(f"{event=}")
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
        log.debug(f"{event=}")
        if event.checkbox.id == "ai_rag_enabled":
            for rag_widget_id in RAG_WIDGET_IDS:
                with contextlib.suppress(NoMatches):
                    self.query_one(f"#{rag_widget_id}").disabled = not event.checkbox.value

            # Keep rag source input disabled if we think it's loaded
            # also if there's load button keep it disabled if there's content
            if event.checkbox.value:
                ai_rag_source = self.query_one("#ai_rag_source")
                if self.ai_rag_source_loaded:
                    ai_rag_source.disabled = True
                else:
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

            self.rag_manager = create_rag_manager(
                app_name=labels.APP_TITLE,
                app_author=labels.APP_AUTHOR,
                settings_model=self.settings_manager.model,
                cache=self.cache,
            )
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
        log.debug(f"{event=}")

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
        model.ai_rag_type = self.query_one("#ai_rag_type").value
        # TODO: PoC way to handle rag load state
        if self.ai_rag_source_loaded and (value := self.query_one("#ai_rag_source").value) != "":
            model.ai_rag_source = value
        model.ai_rag_source_max_depth = str_to_num(self.query_one("#ai_rag_source_max_depth").value)
        self.settings_manager.model = model

        if event.button.id == "apply":
            await self.settings_manager.save()
            self.dismiss(True)
        elif event.control.id == "ai_rag_load":
            ai_rag_source = self.query_one("#ai_rag_source")
            if (value := ai_rag_source.value) != "":
                try:
                    url = validate_and_fix_url(value)
                    ai_rag_source.remove_class("settings_textarea_error")
                    ai_rag_source.value = url

                    max_depth = str_to_num(self.query_one("#ai_rag_source_max_depth").value)
                    await self.parent.push_screen(WaitScreen(labels.APP_RAG_PROCESS_DOCUMENTS))
                    await self.rag_manager.load(url=url, max_depth=max_depth)
                    self.ai_rag_source_loaded = True
                    await event.control.remove()
                    await self.mount(Button(label="Reset", variant="warning", id="ai_rag_reset"), after=ai_rag_source)

                    await self.settings_manager.save()

                    self.parent.pop_screen()
                except ValueError:
                    log.exception(f"Invalid urls: {value}")
                    ai_rag_source.add_class("settings_textarea_error")
        elif event.control.id == "ai_rag_reset":
            self.ai_rag_source_loaded = False
            ai_rag_source = self.query_one("#ai_rag_source")
            await self.rag_manager.delete(url)
            ai_rag_source.value = ""
            ai_rag_source.disabled = False
            await event.control.remove()
            await self.mount(
                Button(label="Load", variant="success", id="ai_rag_load", disabled=True), after=ai_rag_source
            )
            await self.settings_manager.save()
        else:
            self.dismiss(False)
