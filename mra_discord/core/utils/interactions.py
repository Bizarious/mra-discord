from typing import Optional, Callable
from enum import Enum, auto

from nextcord import Interaction, Embed, SelectOption
from nextcord.ui import View, Select
from nextcord.ext.commands import Context


class InteractionRestriction(Enum):
    EVERYONE = auto()
    AUTHOR = auto()


class DropDown(Select):

    def __init__(self,
                 view: "InteractionView",
                 callback: Callable[[list[str]], None],
                 placeholder: str,
                 options: list[dict[str: str]],
                 min_values: Optional[int] = 1,
                 max_values: Optional[int] = 1,
                 finish_interaction: Optional[bool] = True
                 ):

        self._view = view
        self._callback = callback
        self._finish_interaction = finish_interaction

        options = [SelectOption(label=option.get("label", ""), description=option.get("description", None))
                   for option in options
                   ]

        super().__init__(placeholder=placeholder,
                         min_values=min_values,
                         max_values=max_values,
                         options=options)

    async def callback(self, interaction: Interaction):
        self._callback(self.values)
        await self._view.post_interaction(interaction, self._finish_interaction)


class InteractionView(View):

    def __init__(self, context: Context,
                 timeout: Optional[float] = 180.0,
                 restriction: Optional[InteractionRestriction] = InteractionRestriction.AUTHOR
                 ):

        super().__init__(timeout=timeout)

        self._restriction = restriction
        self._context = context
        self._embed_generator = lambda: None

    async def interaction_check(self, interaction: Interaction) -> bool:
        if self._restriction == InteractionRestriction.EVERYONE:
            return True
        elif self._restriction == InteractionRestriction.AUTHOR:
            return self._context.author == interaction.user

    async def post_interaction(self, interaction: Interaction, clear: bool) -> None:
        if clear:
            self.clear_items()
        await interaction.response.edit_message(embed=self._embed_generator(),
                                                view=self
                                                )

    def set_embed_generator(self, embed_generator: Callable[[], Embed]):
        self._embed_generator = embed_generator

    def add_dropdown(self,
                     callback: Callable[[list[str]], None],
                     placeholder: str,
                     options: list[dict[str: str]],
                     min_values: Optional[int] = 1,
                     max_values: Optional[int] = 1,
                     finish_interaction: Optional[bool] = True
                     ):

        self.add_item(
            DropDown(
                self,
                callback,
                placeholder,
                options,
                min_values,
                max_values,
                finish_interaction
            )
        )
