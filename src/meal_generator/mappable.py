from abc import ABC, abstractmethod
from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar("T", bound="_PydanticMappable")


class _PydanticMappable(ABC):
    """
    An abstract base class that enforces the implementation of a `from_pydantic`
    factory method.
    """

    @classmethod
    @abstractmethod
    def from_pydantic(cls: Type[T], pydantic_model: BaseModel) -> T:
        """
        A factory method to create an instance of the class from a
        corresponding Pydantic model.

        Args:
            pydantic_model: The Pydantic model instance to map from.

        Returns:
            A new instance of the class implementing this method.
        """
        raise NotImplementedError
