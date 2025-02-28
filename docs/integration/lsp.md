# MDP Language Server Protocol (LSP) Support

The MDP package includes a Language Server Protocol implementation that provides rich editing capabilities for MDP files in compatible editors and IDEs.

## Features

The MDP Language Server provides the following features:

- **Syntax Validation**: Real-time validation of MDP files, including both YAML frontmatter and Markdown content.
- **Diagnostics**: Error and warning messages for issues in your MDP files.
- **Autocompletion**: Intelligent suggestions for metadata fields, YAML values, and Markdown elements.
- **Hover Information**: Detailed information about metadata fields and their expected values when you hover over them.
- **Document Outline**: Provides a structured view of your document, including metadata fields and Markdown headings.
- **Formatting**: Automatic formatting of MDP files according to configurable style guidelines.

## Installation

The LSP server is included with the MDP package but requires additional dependencies:

```bash
pip install mdp[lsp]
```

## Usage with Editors

### Visual Studio Code

1. Install the [MDP Extension for VS Code](https://marketplace.visualstudio.com/items?itemName=mdp.mdp-vscode) (coming soon).
2. Open an MDP file (`.mdp` extension).
3. The language server will start automatically.

### Manually Configuring VS Code

If the extension is not available yet, you can manually configure VS Code to use the MDP Language Server:

1. Install the MDP package with LSP support: `pip install mdp[lsp]`.
2. Create a `.vscode/settings.json` file in your project with the following content:

```json
{
    "languageServerExample.trace.server": "verbose",
    "languageServer.command": "mdp-language-server",
    "files.associations": {
        "*.mdp": "markdown"
    },
    "languageServer.languages": [{
        "languageId": "markdown",
        "extensions": [".mdp"],
        "filenamePatterns": ["*.mdp"]
    }]
}
```

### Neovim

1. Install the MDP package with LSP support: `pip install mdp[lsp]`.
2. Configure Neovim's LSP client (using nvim-lspconfig or similar):

```lua
-- Using nvim-lspconfig
require('lspconfig').mdp.setup {
    cmd = { "mdp-language-server" },
    filetypes = { "mdp", "markdown" },
    root_dir = function(fname)
        return vim.fn.getcwd()
    end
}
```

### Emacs

1. Install the MDP package with LSP support: `pip install mdp[lsp]`.
2. Configure Emacs with lsp-mode:

```elisp
(use-package lsp-mode
  :ensure t
  :config
  (lsp-register-client
   (make-lsp-client :new-connection (lsp-stdio-connection '("mdp-language-server"))
                    :major-modes '(markdown-mode)
                    :server-id 'mdp)))
```

## Running the Server Manually

You can also run the language server manually for debugging or custom configurations:

```bash
mdp-language-server --debug
```

Command-line options:

- `--debug`: Enable debug logging
- `--log-file <path>`: Specify a log file (default: ~/.mdp/lsp.log)
- `--tcp`: Use TCP server instead of stdio (not fully implemented yet)
- `--host <host>`: TCP server host (default: 127.0.0.1)
- `--port <port>`: TCP server port (default: 2087)

## Development

If you're developing editor extensions or clients for the MDP Language Server, refer to these capabilities:

- Text document synchronization (open, close, change)
- Completion provider (with trigger characters: `:`, `-`, ` `, `[`, `.`)
- Hover provider
- Document symbol provider
- Document formatting provider

The server uses the standard Language Server Protocol, so any editor with LSP client support can integrate with it.

## Configuration

The MDP Language Server automatically uses the same configuration as the MDP command-line tools. You can create a `.mdp-config.yaml` file in your project root to customize behavior.

Example configuration:

```yaml
# Formatting options
metadata_order:
  - title
  - uuid
  - version
  - author
  - created_at
  - updated_at
  - tags
sort_tags: true
normalize_headings: true
wrap_content: 80
fix_links: true

# Linting options
required_fields:
  - title
  - uuid
```

## Troubleshooting

If you encounter issues with the language server:

1. Check the log file at `~/.mdp/lsp.log`
2. Run the server with debug logging: `mdp-language-server --debug`
3. Ensure your editor is properly configured to use the language server
4. Verify that the MDP package is installed with LSP support (`pip install mdp[lsp]`)

## Known Limitations

- Incremental text changes are not fully supported yet; the server processes the entire file on each change.
- TCP server mode is not fully implemented yet.
- The server may not work with all LSP clients; if you encounter issues, please report them. 