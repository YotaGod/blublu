def parse_input(data: str) -> dict:
    tokens = data.strip().split()
    return {"raw": data, "tokens": tokens, "count": len(tokens)}
