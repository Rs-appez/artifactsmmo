default: run

@run *ARGS:
    uv run main.py {{ ARGS }}

@sandbox *ARGS:
    SANDBOX=True just run {{ ARGS }}

