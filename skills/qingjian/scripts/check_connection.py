"""Read-only QingJian MCP probe. Python 3.10+, standard library only."""
import argparse
import json
from pathlib import Path
import sys
import urllib.request


def probe(config, opener=None):
    if not config.get("enabled") or not isinstance(config.get("token"), str) or not config["token"]:
        raise ValueError("MCP is not enabled or credential is missing")
    url = config.get("publicUrl") if config.get("remote") else "http://127.0.0.1:%d/mcp" % int(config["port"])
    if config.get("remote") and not str(url).startswith("https://"):
        raise ValueError("Remote MCP requires HTTPS")
    # No environment HTTP proxy for a local credential-bearing request.
    # No redirect handler: never forward Authorization to another endpoint.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    headers = {"Authorization": "Bearer " + config["token"], "Content-Type": "application/json",
               "Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-11-25"}
    seq = 0

    def rpc(method, params=None, notification=False):
        nonlocal seq
        seq += 1
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notification:
            body["id"] = seq
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        with opener.open(req, timeout=10) as res:
            if res.headers.get("MCP-Session-Id"):
                headers["MCP-Session-Id"] = res.headers["MCP-Session-Id"]
            data = res.read(1048577)
        if len(data) > 1048576:
            raise ValueError("Response too large")
        if notification:
            return None
        value = json.loads(data)
        if value.get("error") or value.get("id") != seq:
            raise ValueError("RPC error or unexpected response")
        return value["result"]

    initialized = rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                    "clientInfo": {"name": "qingjian-readonly-check", "version": "1.0"}})
    version = initialized.get("protocolVersion")
    if version not in ("2025-11-25", "2025-06-18", "2025-03-26"):
        raise ValueError("Unsupported negotiated version")
    headers["MCP-Protocol-Version"] = version
    rpc("notifications/initialized", notification=True)
    manifest = rpc("tools/list", {})
    names = {tool["name"] for tool in manifest.get("tools", [])}
    if "qingjian_info" not in names:
        raise ValueError("QingJian info tool missing")
    result = rpc("tools/call", {"name": "qingjian_info", "arguments": {}})
    if result.get("isError"):
        raise ValueError("Info tool failed")
    info = result.get("structuredContent")
    if info is None:
        info = json.loads(next(c["text"] for c in result["content"] if c.get("type") == "text"))
    if not info.get("revision") or not info.get("localDate") or not info.get("timeZone"):
        raise ValueError("Invalid info response")
    return {"success": True, "toolCount": len(names), "localDate": info["localDate"],
            "timeZone": info["timeZone"], "scope": "host-to-app read-only; Agent registration not verified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        config = json.loads((args.app_dir / "data" / "mcp-config.json").read_text(encoding="utf-8-sig"))
        print(json.dumps(probe(config), ensure_ascii=False))
        return 0
    except Exception:
        # Never emit exception/request/config contents: credentials can be embedded.
        print(json.dumps({"success": False, "error": "Check app path, MCP enabled state, credentials, network and TLS. No task was changed."}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
