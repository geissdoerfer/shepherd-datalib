import platform
from contextlib import suppress
from importlib import import_module
from typing import Optional

from ..data_models import ShpModel


class PythonInventory(ShpModel):
    # versions
    python: Optional[str] = None
    numpy: Optional[str] = None
    h5py: Optional[str] = None
    pydantic: Optional[str] = None
    yaml: Optional[str] = None
    shepherd_core: Optional[str] = None
    shepherd_sheep: Optional[str] = None

    class Config:
        min_anystr_length = 0

    @classmethod
    def collect(cls):
        model_dict = {"python": platform.python_version()}
        module_names = [
            "numpy",
            "h5py",
            "pydantic",
            "yaml",
            "shepherd_core",
            "shepherd_sheep",
        ]

        for module_name in module_names:
            with suppress(ImportError):
                module = import_module(module_name)
                model_dict[module_name] = module.__version__
                globals()

        return cls(**model_dict)