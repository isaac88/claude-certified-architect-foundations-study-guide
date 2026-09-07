# MCP on the wire — what the SDK hides

Captured 7 Sep 2026 by piping raw JSON-RPC frames into `mcp_server.py`'s
stdin — **no SDK, no client class** — and reading its stdout. This is the
whole protocol for one resource read. Study this if `read_resource` feels
abstract: every SDK call below maps to exactly one request/response pair.

The mental model: an MCP stdio server is a **child process**; requests are
JSON objects written to its stdin (one per line), responses come back on
stdout with a matching `id` (a correlation ID). `curl` semantics over a
pipe.

## 1. The handshake (`ClientSession.initialize()` — done once, in `connect()`)

```json
→ {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"raw-probe","version":"0"}}}
→ {"jsonrpc":"2.0","method":"notifications/initialized"}
← {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05",
     "capabilities":{"prompts":{},"resources":{},"tools":{}},
     "serverInfo":{"name":"DocumentMCP","version":"1.8.0"}}}
```

The server announces WHAT SPECIES of capability it has (tools, resources,
prompts) — not which ones. Listing those is a separate call per species.

## 2. `read_resource("docs://documents")` — the JSON resource

```json
→ {"jsonrpc":"2.0","id":2,"method":"resources/read","params":{"uri":"docs://documents"}}
← {"jsonrpc":"2.0","id":2,"result":{"contents":[
     {"uri":"docs://documents",
      "mimeType":"application/json",
      "text":"[\n  \"deposition.md\",\n  \"report.pdf\", ...]"}]}}
```

Note: `contents` is a LIST (protocol allows multipart); and the document
list is a STRING containing JSON — **everything crosses the pipe as
text**. `mimeType` is the server's label telling the client how to
rehydrate: `application/json` → `json.loads` → real Python list.

## 3. `read_resource("docs://documents/report.pdf")` — the templated, plain-text resource

```json
→ {"jsonrpc":"2.0","id":3,"method":"resources/read","params":{"uri":"docs://documents/report.pdf"}}
← {"jsonrpc":"2.0","id":3,"result":{"contents":[
     {"uri":"docs://documents/report.pdf",
      "mimeType":"text/plain",
      "text":"The report details the state of a 20m condenser tower."}]}}
```

`text/plain` → the client returns the string as-is.

## Mapping to the client code (mcp_client.py)

| Python | Wire reality |
|---|---|
| `async def` / `await` | a pipe round-trip happens here; the coroutine parks until the matching `id` returns |
| `AnyUrl(uri)` | client-side validation BEFORE anything is sent — fail fast on a malformed URI |
| `self.session()` | the already-open connection (handshake frame `id:1` happened once, in `connect()`) |
| `session.read_resource(...)` | write one `resources/read` frame to stdin, await the reply with the same `id` |
| `result.contents[0]` | first element of the (potentially multipart) `contents` list |
| `isinstance(resource, TextResourceContents)` | text-vs-blob variant check — Content-Type: text/* vs octet-stream |
| `json.loads(resource.text)` iff `application/json` | rehydrate the string the wire delivered |

Gap worth knowing: the course's `read_resource` has no blob branch — a
binary resource would silently return `None`.

Same protocol, other species: `tools/list`, `tools/call`, `prompts/list`,
`prompts/get`. A raised ValueError travels differently per species:
tool → `isError:true` RESULT; resource → JSON-RPC **error** frame, which
the SDK re-raises client-side as `McpError` (exercise 42's asymmetry).

Reproduce: pipe the `→` lines (one per line, in order) into
`.venv/bin/python mcp_server.py` from `mcp-project/`.
