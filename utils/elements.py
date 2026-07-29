from models.enums import Element


def parse_element(code: str, prefix: str) -> Element | None:
    if not code.startswith(prefix):
        return None
    try:
        return Element(code.removeprefix(prefix))
    except ValueError:
        return None
