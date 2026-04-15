"""Engine adapters for IF Hub jukebox.

Each adapter module exposes a setup(game_dir, deploy_dir, conf) function that
takes built game output from an engine workspace and produces hub-ready files
in the deploy directory.
"""

ADAPTERS = {
    "inform7": "adapters.inform7",
    "zmachine": "adapters.zmachine",
    "ink": "adapters.ink",
    # sharpee: builds in its own workspace (npmsharpee/tools/ship.py).
    # IF Hub does not build Sharpee games; sharpee workspaces call
    # register_game.py / publish.py / push_hub.py directly.
    "rez": "adapters.rez",
    "wwwbasic": "adapters.basic",
    "applesoft": "adapters.basic",
    "qbjc": "adapters.basic",
    "bwbasic": "adapters.basic",
}


def get_adapter(engine):
    """Return the adapter module for the given engine name."""
    import importlib
    module_name = ADAPTERS.get(engine)
    if not module_name:
        raise ValueError(f"No adapter for engine '{engine}'. Available: {', '.join(sorted(ADAPTERS))}")
    return importlib.import_module(module_name)
