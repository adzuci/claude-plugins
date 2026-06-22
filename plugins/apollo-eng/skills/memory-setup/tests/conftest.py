import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def load_script_module(script_name: str):
    """Load a memory-setup script without leaking generic module names."""
    module_name = f"memory_setup_{script_name}"
    if module_name in sys.modules:
        return sys.modules[module_name]

    saved_path = list(sys.path)
    saved_aliases = {
        "lib": sys.modules.get("lib"),
    }

    try:
        if script_name != "lib":
            sys.modules["lib"] = load_script_module("lib")

        sys.path.insert(0, str(SCRIPTS))
        script_path = SCRIPTS / f"{script_name}.py"
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load {script_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise
        return module
    finally:
        sys.path[:] = saved_path
        for alias, previous in saved_aliases.items():
            if previous is None:
                sys.modules.pop(alias, None)
            else:
                sys.modules[alias] = previous
