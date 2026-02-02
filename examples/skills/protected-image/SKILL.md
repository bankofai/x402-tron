---
name: protected-image
description: Fetch an x402-protected image from the local demo server (/protected). Pays via x402 on TRON Nile and returns the image as a saved file plus base64.
metadata: {"clawdbot":{"requires":{"anyBins":["node"]},"env":["TRON_PRIVATE_KEY"],"optionalEnv":["TRON_NETWORK","IMAGE_FINDER_URL","IMAGE_FINDER_OUTPUT_DIR"]}}
---

# Image Finder

Fetches a protected image from the demo resource server:

- `GET http://localhost:8000/protected`

The endpoint is protected by x402 and returns `image/png` on success.

## Configuration

The TRON private key must be available via one of these methods:

**Option 1: Environment variable**
```bash
export TRON_PRIVATE_KEY="..."
```

**Option 2: Config file (Recommended)**

The script checks for `x402-config.json` in these locations (in order):
1. Current directory: `./x402-config.json`
2. Home directory: `~/.x402-config.json` ← **Recommended**
3. Working directory: `$PWD/x402-config.json`

Create the config file:
```json
{
  "tron_private_key": "..."
}
```

**Example (home directory - works for any user):**
```bash
echo '{"private_key": "0x..."}' > ~/.x402-config.json
```

## Environment Variables

```bash
export TRON_NETWORK="tron:nile"
export IMAGE_FINDER_URL="http://localhost:8000/protected"
export IMAGE_FINDER_OUTPUT_DIR="$PWD"
```

## Usage

```bash
scripts/analyze.sh
```

Optionally pass a URL:

```bash
scripts/analyze.sh "http://localhost:8000/protected"
```

The script:
- Automatically handles 402 Payment Required via x402
- Saves the returned image to `IMAGE_FINDER_OUTPUT_DIR` (defaults to current directory)
- Prints a single-line JSON payload containing:
  - `file_path`
  - `content_type`
  - `bytes`
  - `base64`

## Examples
```bash
scripts/analyze.sh
```

## Capabilities
- Fetch x402-protected resources (402 → pay → retry)
- Persist binary image payloads to disk
- Return image bytes as base64 for downstream tools

## Error Handling
- **Missing TRON_PRIVATE_KEY** → Configure `TRON_PRIVATE_KEY` (see Configuration above)
- **HTTP 402 loop** → Ensure facilitator and server are running and funded
- **Non-image response** → Ensure you're hitting `/protected` and the server has `protected.png`
