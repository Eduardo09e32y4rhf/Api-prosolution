import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class MaxBodySizeMiddleware:
    """Recusa requisições com corpo acima de `max_bytes` (413) antes de a aplicação processá-las.

    Confere o Content-Length e também conta os bytes recebidos, porque o cliente pode omitir o
    cabeçalho (chunked) ou mentir nele. É um middleware ASGI puro para agir antes do parser de
    formulários, que de outro modo gravaria em disco o upload inteiro.

    Estourado o limite no meio do envio, a resposta 413 sai na hora, a aplicação recebe um
    `http.disconnect` (para parar de ler) e o que ela tentar responder depois é descartado.
    Não usamos exceção porque o FastAPI a converteria em um 400 genérico.
    """

    def __init__(self, app: ASGIApp, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = dict(scope["headers"]).get(b"content-length", b"")
        if declared.isdigit() and int(declared) > self.max_bytes:
            await self._reject(send)
            return

        received = 0
        started = False
        rejected = False

        async def limited_receive() -> Message:
            nonlocal received, rejected
            if rejected:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    rejected = True
                    if not started:
                        await self._reject(send)
                    return {"type": "http.disconnect"}
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal started
            if rejected:
                return
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except Exception:
            # A aplicação pode falhar ao ler um corpo interrompido; a resposta (413) já foi enviada
            if not rejected:
                raise

    async def _reject(self, send: Send) -> None:
        body = json.dumps({"detail": "Arquivo grande demais."}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
            }
        )
        await send({"type": "http.response.body", "body": body})
