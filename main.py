from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    # Servidor de desenvolvimento; em produção use startup.sh / docker-compose
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)  # noqa: S104
