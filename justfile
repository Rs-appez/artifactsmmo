default: run

@run *ARGS:
    uv run main.py {{ ARGS }}

@sandbox *ARGS:
    SANDBOX=True just run {{ ARGS }}

@fetch:
    uv run python -m standalone_scripts.fetch_game_data

