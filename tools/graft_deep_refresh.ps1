$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$node = 'C:\nvm4w\nodejs\node.exe'
$graft = 'C:\nvm4w\nodejs\node_modules\@nanonets\graft\dist\cli.js'
$proxyPort = Get-Random -Minimum 18000 -Maximum 24000
$proxyScript = Join-Path ([IO.Path]::GetTempPath()) "graft-deepseek-proxy-$PID.mjs"
$proxyOut = Join-Path ([IO.Path]::GetTempPath()) "graft-deepseek-proxy-$PID.stdout.log"
$proxyErr = Join-Path ([IO.Path]::GetTempPath()) "graft-deepseek-proxy-$PID.stderr.log"

$env:GRAFT_API_KEY = [Environment]::GetEnvironmentVariable('GRAFT_API_KEY', 'User')
$env:GRAFT_PROVIDER = [Environment]::GetEnvironmentVariable('GRAFT_PROVIDER', 'User')
$env:GRAFT_UPSTREAM = [Environment]::GetEnvironmentVariable('GRAFT_BASE_URL', 'User')
$env:GRAFT_MODEL = [Environment]::GetEnvironmentVariable('GRAFT_MODEL', 'User')
$env:GRAFT_PROXY_PORT = [string]$proxyPort

if (-not $env:GRAFT_API_KEY -or -not $env:GRAFT_UPSTREAM -or -not $env:GRAFT_MODEL) {
    throw 'GRAFT_API_KEY, GRAFT_BASE_URL and GRAFT_MODEL must exist in the Windows user environment.'
}

$proxySource = @'
import http from "node:http";

const upstream = process.env.GRAFT_UPSTREAM?.replace(/\/$/, "");
const port = Number(process.env.GRAFT_PROXY_PORT);

function targetIds(body) {
  const ids = [];
  for (const message of body.messages || []) {
    const text = typeof message.content === "string" ? message.content : "";
    for (const match of text.matchAll(/^- id=(.*?) \|/gm)) ids.push(match[1]);
  }
  return ids;
}

function normaliseToolArguments(response, ids) {
  if (!ids.length) return response;
  const exact = new Set(ids);
  for (const choice of response.choices || []) {
    for (const call of choice.message?.tool_calls || []) {
      let args;
      try { args = JSON.parse(call.function?.arguments || "{}"); } catch { continue; }
      if (!Array.isArray(args.symbols)) continue;
      const used = new Set();
      args.symbols.forEach((symbol, index) => {
        if (exact.has(symbol.id) && !used.has(symbol.id)) {
          used.add(symbol.id);
          return;
        }
        const name = String(symbol.id || "").split("#").at(-1).split("(")[0];
        const byName = ids.find((id) =>
          !used.has(id) && id.split("#").at(-1).split("(")[0] === name,
        );
        const replacement = byName || (args.symbols.length === ids.length ? ids[index] : undefined);
        if (replacement) {
          symbol.id = replacement;
          used.add(replacement);
        }
      });
      call.function.arguments = JSON.stringify(args);
    }
  }
  return response;
}

http.createServer(async (request, reply) => {
  try {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    const raw = Buffer.concat(chunks);
    let body;
    try { body = JSON.parse(raw.toString("utf8")); } catch { body = null; }
    if (body?.tool_choice && Array.isArray(body.tools)) body.reasoning_effort = "none";
    const headers = { ...request.headers };
    delete headers.host;
    delete headers["content-length"];
    const upstreamResponse = await fetch(`${upstream}${request.url}`, {
      method: request.method,
      headers,
      body: body ? JSON.stringify(body) : raw,
    });
    const responseText = await upstreamResponse.text();
    let output = responseText;
    try {
      output = JSON.stringify(normaliseToolArguments(JSON.parse(responseText), body ? targetIds(body) : []));
    } catch {}
    reply.writeHead(upstreamResponse.status, {
      "content-type": upstreamResponse.headers.get("content-type") || "application/json",
    });
    reply.end(output);
  } catch {
    reply.writeHead(502, { "content-type": "application/json" });
    reply.end(JSON.stringify({ error: { message: "local Graft compatibility proxy failure" } }));
  }
}).listen(port, "127.0.0.1", () => process.stdout.write("READY\n"));
'@

[IO.File]::WriteAllText($proxyScript, $proxySource, [Text.UTF8Encoding]::new($false))
$proxyProcess = Start-Process -FilePath $node -ArgumentList @($proxyScript) -PassThru `
    -WindowStyle Hidden -RedirectStandardOutput $proxyOut -RedirectStandardError $proxyErr

try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 50; $attempt++) {
        if ($proxyProcess.HasExited) { throw 'The Graft compatibility proxy exited during startup.' }
        try {
            $client = [Net.Sockets.TcpClient]::new('127.0.0.1', $proxyPort)
            $client.Dispose()
            $ready = $true
            break
        } catch {
            Start-Sleep -Milliseconds 100
        }
    }
    if (-not $ready) { throw 'The Graft compatibility proxy did not become ready.' }

    $env:GRAFT_BASE_URL = "http://127.0.0.1:$proxyPort"
    Push-Location $repoRoot
    try {
        & $node $graft build --deep .
        if ($LASTEXITCODE -ne 0) { throw "Graft deep refresh failed with exit code $LASTEXITCODE." }
    } finally {
        Pop-Location
    }
} finally {
    if ($proxyProcess -and -not $proxyProcess.HasExited) {
        Stop-Process -Id $proxyProcess.Id -Force
        $proxyProcess.WaitForExit(5000) | Out-Null
    }
    foreach ($path in ($proxyScript, $proxyOut, $proxyErr)) {
        for ($attempt = 0; $attempt -lt 20 -and [IO.File]::Exists($path); $attempt++) {
            try {
                [IO.File]::Delete($path)
            } catch [IO.IOException] {
                Start-Sleep -Milliseconds 100
            }
        }
        if ([IO.File]::Exists($path)) {
            Write-Warning "Could not remove temporary Graft proxy file: $path"
        }
    }
}
