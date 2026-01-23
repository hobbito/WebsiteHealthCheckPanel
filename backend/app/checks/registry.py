from typing import Dict, Type, List
from app.checks.base import BaseCheck


class CheckRegistry:
    """
    Registry for all available check types.
    Provides dynamic check discovery and management.
    """

    _checks: Dict[str, Type[BaseCheck]] = {}

    @classmethod
    def register(cls, check_class: Type[BaseCheck]) -> Type[BaseCheck]:
        """
        Register a check class in the registry.

        Args:
            check_class: The check class to register

        Returns:
            The check class (allows use as decorator)
        """
        check_type = check_class.get_check_type()
        cls._checks[check_type] = check_class
        return check_class

    @classmethod
    def get_check(cls, check_type: str) -> Type[BaseCheck]:
        """
        Get a check class by its type identifier.

        Args:
            check_type: The check type identifier

        Returns:
            The check class

        Raises:
            KeyError: If check type is not registered
        """
        if check_type not in cls._checks:
            raise KeyError(f"Check type '{check_type}' not registered")
        return cls._checks[check_type]

    @classmethod
    def list_checks(cls) -> List[Dict[str, any]]:
        """
        List all registered checks with their metadata.

        Returns:
            List of dicts containing check type, name, and config schema
        """
        return [
            {
                "type": check_type,
                "display_name": check_class.get_display_name(),
                "config_schema": check_class.get_config_schema(),
            }
            for check_type, check_class in cls._checks.items()
        ]

    @classmethod
    def is_registered(cls, check_type: str) -> bool:
        """Check if a check type is registered"""
        return check_type in cls._checks

    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get list of all registered check type identifiers"""
        return list(cls._checks.keys())
