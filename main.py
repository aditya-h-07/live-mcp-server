
import contextvars
import hashlib

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

EMAIL = "23f2004697@ds.study.iitm.ac.in"
RENDER_HOST = "live-mcp-server-aftb.onrender.com"

_current_challenge = contextvars.ContextVar(
    "current_exam_challenge",
    default="",
)


class ChallengeHeaderMiddleware:
    """Capture the challenge header for the current HTTP request."""

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
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            RENDER_HOST,
            f"{RENDER_HOST}:*",
            "localhost:*",
            "127.0.0.1:*",
            "[::1]:*",
        ],
    ),
)


@mcp.tool()
def solve_challenge() -> str:
    """Return the required SHA-256 digest for this request's challenge."""
    challenge = _current_challenge.get()
    value = f"{challenge}:{EMAIL.strip().lower()}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


app = ChallengeHeaderMiddleware(mcp.streamable_http_app())
