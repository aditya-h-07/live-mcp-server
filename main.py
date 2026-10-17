import contextvars
import hashlib

from mcp.server.fastmcp import FastMCP

EMAIL = "23f2004697@ds.study.iitm.ac.in"

# Store the challenge for the current HTTP request.
_current_challenge = contextvars.ContextVar(
    "current_exam_challenge", default=""
)


class ChallengeHeaderMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }

        challenge = headers.get("x-exam-challenge", "")
        token = _current_challenge.set(challenge)

        try:
            await self.app(scope, receive, send)
        finally:
            _current_challenge.reset(token)


mcp = FastMCP(
    "Live MCP Server",
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def solve_challenge() -> str:
    """Calculate the answer using the challenge in the current HTTP request."""
    challenge = _current_challenge.get()
    value = f"{challenge}:{EMAIL.strip().lower()}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


app = ChallengeHeaderMiddleware(mcp.streamable_http_app())