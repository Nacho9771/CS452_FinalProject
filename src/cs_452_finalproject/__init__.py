def main() -> None:
    """Start the local backend; the terminal logs explain each HTTP request."""
    import uvicorn

    from .configuration import load_environment

    load_environment()
    uvicorn.run("cs_452_finalproject.api:app", host="127.0.0.1", port=8000)
