from typing import Dict, Type, List
from .base import BaseCheck


class CheckRegistry:
    _checks: Dict[str, Type[BaseCheck]] = {}

    @classmethod
    def register(cls, check_class: Type[BaseCheck]) -> None:
        instance = check_class()
        check_type = instance.check_type

        if check_type in cls._checks:
            raise ValueError(f"Check type '{check_type}' is already registered")

        cls._checks[check_type] = check_class
        print(f"✓ Registered check type: {check_type}")

    @classmethod
    def is_registered(cls, check_type: str) -> bool:
        return check_type in cls._checks

    @classmethod
    def get_check(cls, check_type: str) -> Type[BaseCheck]:
        if check_type not in cls._checks:
            available = ", ".join(cls._checks.keys())
            raise KeyError(f"Check type '{check_type}' not found. Available: {available}")
        return cls._checks[check_type]

    @classmethod
    def list_checks(cls) -> List[Dict[str, any]]:
        result = []
        for check_type, check_class in cls._checks.items():
            instance = check_class()
            result.append({
                "type": check_type,
                "display_name": instance.display_name,
                "description": instance.description,
                "config_schema": instance.get_config_schema()
            })
        return result


def register_check(check_class: Type[BaseCheck]) -> Type[BaseCheck]:
    CheckRegistry.register(check_class)
    return check_class
