# Blackboard MCP — AI Install Prompts

Copy and paste the right prompt into your AI coding assistant.
The AI will install and configure everything for you automatically.

---

## Claude Desktop

Open Claude Desktop and paste this into the chat:

```
Install the Blackboard MCP server for me.

Run this in a terminal (you can open one via the terminal tool or tell me to do it):
  curl -fsSL https://raw.githubusercontent.com/sasindudilshanranwadana/blackboard-mcp/main/install.sh | bash

The script opens a browser — I will log in to my university Blackboard when it does.
After setup completes, tell me which clients were configured and how to test it.
```

---

## Claude Code (CLI)

Paste this into your Claude Code session:

```
Install the Blackboard MCP server for me from https://github.com/sasindudilshanranwadana/blackboard-mcp

Run this in the terminal:
  curl -fsSL https://raw.githubusercontent.com/sasindudilshanranwadana/blackboard-mcp/main/install.sh | bash

Wait for it to finish — it opens a browser for me to log in to my university Blackboard.
After setup completes, confirm which MCP clients were configured and tell me how to test it.

Do not ask me questions — just run the installer and report back.
```

---

## Cursor

Open Cursor and paste this into the AI chat (Cmd+L / Ctrl+L):

```
I want to install the Blackboard MCP server so I can talk to my university's Blackboard LMS through AI.

Repository: https://github.com/sasindudilshanranwadana/blackboard-mcp

Please do the following in the terminal:
1. Run: curl -fsSL https://raw.githubusercontent.com/sasindudilshanranwadana/blackboard-mcp/main/install.sh | bash
2. The script is interactive — it will open a browser window for me to log in. Let it run.
3. After it finishes, show me what was installed and configured.
4. If anything fails, diagnose and fix it.

Start now.
```

---

## Windsurf

Open Windsurf, open the AI panel, and paste:

```
Install the Blackboard MCP server for me.

Run in terminal:
  curl -fsSL https://raw.githubusercontent.com/sasindudilshanranwadana/blackboard-mcp/main/install.sh | bash

A browser will open during setup — I'll log in to my university Blackboard when it does.
Once done, verify the MCP server is configured in Windsurf and tell me how to test it.
```

---

## Codex CLI (OpenAI)

```
Install the Blackboard MCP server for me.

Run this shell command:
  curl -fsSL https://raw.githubusercontent.com/sasindudilshanranwadana/blackboard-mcp/main/install.sh | bash

A browser will open so I can log in to my university Blackboard — wait for that to complete.
After setup, confirm the server is registered in ~/.codex/config.json and how to invoke it.
```

---

## Cline (VS Code extension)

Open VS Code with Cline installed, open the Cline chat panel, and paste:

```
Install the Blackboard MCP server for me so I can query my university Blackboard from VS Code.

Run in terminal:
  curl -fsSL https://raw.githubusercontent.com/sasindudilshanranwadana/blackboard-mcp/main/install.sh | bash

The installer opens a browser — I will log in when prompted.
After setup, verify the server appears in Cline's MCP settings and tell me a test query to try.
```

---

## Zed

Open Zed, open the assistant panel (Cmd+?), and paste:

```
Install the Blackboard MCP server for me from https://github.com/sasindudilshanranwadana/blackboard-mcp

Run in the terminal:
  curl -fsSL https://raw.githubusercontent.com/sasindudilshanranwadana/blackboard-mcp/main/install.sh | bash

The setup wizard will open a browser for me to log in to my university Blackboard.
After setup completes, verify the context_servers entry is in my Zed settings.json and tell me how to use it.
```

---

## Continue (VS Code / JetBrains extension)

Open your editor with Continue installed and paste into the Continue chat:

```
Install the Blackboard MCP server so I can query my university Blackboard from Continue.

Run in terminal:
  curl -fsSL https://raw.githubusercontent.com/sasindudilshanranwadana/blackboard-mcp/main/install.sh | bash

A browser opens during setup — I'll log in to my university Blackboard when prompted.
After setup, confirm the MCP server is in ~/.continue/config.json and tell me a test query.
```

---

## Gemini CLI

```
Install the Blackboard MCP server for me from https://github.com/sasindudilshanranwadana/blackboard-mcp

Run:
  curl -fsSL https://raw.githubusercontent.com/sasindudilshanranwadana/blackboard-mcp/main/install.sh | bash

The script opens a browser for me to log in to my university Blackboard — let that complete.
After setup, confirm the server entry is in ~/.gemini/settings.json and how to test it.
```

---

## Manual install (any platform)

If your AI assistant can't run curl, give it these steps:

```
Help me install the Blackboard MCP server step by step.
Repo: https://github.com/sasindudilshanranwadana/blackboard-mcp

Run these commands one by one and show me the output of each:
1. git clone https://github.com/sasindudilshanranwadana/blackboard-mcp.git ~/blackboard-mcp
2. cd ~/blackboard-mcp
3. python3 -m venv .venv && source .venv/bin/activate
4. pip install -r requirements.txt
5. playwright install chromium
6. python3 setup.py
```

---

## After install — what to expect

1. **Restart your AI assistant** (quit fully and reopen)
2. **Connect your Blackboard** by saying:
   > *"Connect my Blackboard — my university URL is https://blackboard.myuniversity.edu"*
3. A browser opens → log in with your university credentials → done
4. Ask anything:

| Platform | Test query after connecting |
|----------|-----------------------------|
| Claude Desktop | *"What courses am I enrolled in?"* |
| Claude Code | *"List my Blackboard courses"* |
| Cursor | *"What assignments are due this week?"* |
| Windsurf | *"Catch me up on my Blackboard"* |
| Cline | *"Show my Blackboard grades"* |
| Zed | *"What announcements do I have?"* |
| Continue | *"What's due in Blackboard this week?"* |
| Codex CLI | *"Summarize my Blackboard activity"* |
| Gemini CLI | *"List my university courses"* |

---

## Troubleshooting

Paste this if something went wrong:

```
The Blackboard MCP server install at ~/blackboard-mcp failed or isn't working.
Repo: https://github.com/sasindudilshanranwadana/blackboard-mcp

Please:
1. Check if ~/blackboard-mcp exists and ~/blackboard-mcp/.venv exists
2. Run: ~/blackboard-mcp/.venv/bin/python3 ~/blackboard-mcp/server.py
   and show me any errors
3. Check my MCP config — try:
     cat ~/Library/Application\ Support/Claude/claude_desktop_config.json  # Claude Desktop (macOS)
     cat ~/.claude/claude_desktop_config.json                              # Claude Code
     cat ~/.cursor/mcp.json                                                # Cursor
     cat ~/.codeium/windsurf/mcp_config.json                              # Windsurf
4. Fix any issues you find and confirm it's working.
```
