"""Abstract base class for L2dLLM tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel


class L2dTool(ABC):
    """Abstract base class for all L2dLLM tools.

    Subclasses must implement:
    - ``tool_name``: unique tool identifier
    - ``tool_description``: what the tool does
    - ``input_schema``: Pydantic model for tool arguments
    - ``_execute()``: the actual tool logic
    """

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the unique name of this tool."""

    @property
    @abstractmethod
    def tool_description(self) -> str:
        """Return a description of what this tool does."""

    @property
    @abstractmethod
    def input_schema(self) -> type[BaseModel]:
        """Return the Pydantic model class for tool input arguments."""

    @abstractmethod
    async def _execute(self, **kwargs: Any) -> str:
        """Execute the tool logic and return the result as a string."""

    def to_langchain_tool(self) -> BaseTool:
        """Convert this L2dTool to a LangChain BaseTool."""
        schema = self.input_schema
        tool_name = self.tool_name
        tool_description = self.tool_description

        async def _invoke(**kwargs: Any) -> str:
            validated = schema(**kwargs)
            return await self._execute(**validated.model_dump())

        return StructuredTool.from_function(
            coroutine=_invoke,
            name=tool_name,
            description=tool_description,
            args_schema=schema,
        )
