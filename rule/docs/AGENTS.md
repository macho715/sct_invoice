# AGENTS.md

## About Spec Kit and Specify

**GitHub Spec Kit** is a comprehensive toolkit for implementing Spec-Driven Development (SDD) - a methodology that emphasizes creating clear specifications before implementation. The toolkit includes templates, scripts, and workflows that guide development teams through a structured approach to building software.

**Specify CLI** is the command-line interface that bootstraps projects with the Spec Kit framework. It sets up the necessary directory structures, templates, and AI agent integrations to support the Spec-Driven Development workflow.

The toolkit supports multiple AI coding assistants, allowing teams to use their preferred tools while maintaining consistent project structure and development practices.

---

## General practices

- Any changes to `__init__.py` for the Specify CLI require a version rev in `pyproject.toml` and addition of entries to `CHANGELOG.md`.

## Adding New Agent Support

This section explains how to add support for new AI agents/assistants to the Specify CLI. Use this guide as a reference when integrating new AI tools into the Spec-Driven Development workflow.

### Overview

Specify supports multiple AI agents by generating agent-specific command files and directory structures when initializing projects. Each agent has its own conventions for:

- **Command file formats** (Markdown, TOML, etc.)
- **Directory structures** (`.claude/commands/`, `.windsurf/workflows/`, etc.)
- **Command invocation patterns** (slash commands, CLI tools, etc.)
- **Argument passing conventions** (`$ARGUMENTS`, `{{args}}`, etc.)

### Current Supported Agents

| Agent | Directory | Format | CLI Tool | Description |
|-------|-----------|---------|----------|-------------|
| **Claude Code** | `.claude/commands/` | Markdown | `claude` | Anthropic's Claude Code CLI |
| **Gemini CLI** | `.gemini/commands/` | TOML | `gemini` | Google's Gemini CLI |
| **GitHub Copilot** | `.github/prompts/` | Markdown | N/A (IDE-based) | GitHub Copilot in VS Code |
| **Cursor** | `.cursor/commands/` | Markdown | `cursor-agent` | Cursor CLI |
| **Qwen Code** | `.qwen/commands/` | TOML | `qwen` | Alibaba's Qwen Code CLI |
| **opencode** | `.opencode/command/` | Markdown | `opencode` | opencode CLI |
| **Windsurf** | `.windsurf/workflows/` | Markdown | N/A (IDE-based) | Windsurf IDE workflows |

### Step-by-Step Integration Guide

Follow these steps to add a new agent (using Windsurf as an example):

#### 1. Update AI_CHOICES Constant

Add the new agent to the `AI_CHOICES` dictionary in `src/specify_cli/__init__.py`:

```python
AI_CHOICES = {
    "copilot": "GitHub Copilot",
    "claude": "Claude Code",
    "gemini": "Gemini CLI",
    "cursor": "Cursor",
    "qwen": "Qwen Code",
    "opencode": "opencode",
    "windsurf": "Windsurf"  # Add new agent here
}
```

Also update the `agent_folder_map` in the same file to include the new agent's folder for the security notice:

```python
agent_folder_map = {
    "claude": ".claude/",
    "gemini": ".gemini/",
    "cursor": ".cursor/",
    "qwen": ".qwen/",
    "opencode": ".opencode/",
    "codex": ".codex/",
    "windsurf": ".windsurf/",  # Add new agent folder here
    "kilocode": ".kilocode/",
    "auggie": ".auggie/",
    "copilot": ".github/"
}
```

#### 2. Update CLI Help Text

Update all help text and examples to include the new agent:

- Command option help: `--ai` parameter description
- Function docstrings and examples
- Error messages with agent lists

#### 3. Update README Documentation

Update the **Supported AI Agents** section in `README.md` to include the new agent:

- Add the new agent to the table with appropriate support level (Full/Partial)
- Include the agent's official website link
- Add any relevant notes about the agent's implementation
- Ensure the table formatting remains aligned and consistent

#### 4. Update Release Package Script

Modify `.github/workflows/scripts/create-release-packages.sh`:

##### Add to ALL_AGENTS array:
```bash
ALL_AGENTS=(claude gemini copilot cursor qwen opencode windsurf)
```

##### Add case statement for directory structure:
```bash
case $agent in
  # ... existing cases ...
  windsurf)
    mkdir -p "$base_dir/.windsurf/workflows"
    generate_commands windsurf md "\$ARGUMENTS" "$base_dir/.windsurf/workflows" "$script" ;;
esac
```

#### 4. Update GitHub Release Script

Modify `.github/workflows/scripts/create-github-release.sh` to include the new agent's packages:

```bash
gh release create "$VERSION" \
  # ... existing packages ...
  .genreleases/spec-kit-template-windsurf-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-windsurf-ps-"$VERSION".zip \
  # Add new agent packages here
```

#### 5. Update Agent Context Scripts

##### Bash script (`scripts/bash/update-agent-context.sh`):

Add file variable:
```bash
WINDSURF_FILE="$REPO_ROOT/.windsurf/rules/specify-rules.md"
```

Add to case statement:
```bash
case "$AGENT_TYPE" in
  # ... existing cases ...
  windsurf) update_agent_file "$WINDSURF_FILE" "Windsurf" ;;
  "")
    # ... existing checks ...
    [ -f "$WINDSURF_FILE" ] && update_agent_file "$WINDSURF_FILE" "Windsurf";
    # Update default creation condition
    ;;
esac
```

##### PowerShell script (`scripts/powershell/update-agent-context.ps1`):

Add file variable:
```powershell
$windsurfFile = Join-Path $repoRoot '.windsurf/rules/specify-rules.md'
```

Add to switch statement:
```powershell
switch ($AgentType) {
    # ... existing cases ...
    'windsurf' { Update-AgentFile $windsurfFile 'Windsurf' }
    '' {
        foreach ($pair in @(
            # ... existing pairs ...
            @{file=$windsurfFile; name='Windsurf'}
        )) {
            if (Test-Path $pair.file) { Update-AgentFile $pair.file $pair.name }
        }
        # Update default creation condition
    }
}
```

#### 6. Update CLI Tool Checks (Optional)

For agents that require CLI tools, add checks in the `check()` command and agent validation:

```python
# In check() command
tracker.add("windsurf", "Windsurf IDE (optional)")
windsurf_ok = check_tool_for_tracker("windsurf", "https://windsurf.com/", tracker)

# In init validation (only if CLI tool required)
elif selected_ai == "windsurf":
    if not check_tool("windsurf", "Install from: https://windsurf.com/"):
        console.print("[red]Error:[/red] Windsurf CLI is required for Windsurf projects")
        agent_tool_missing = True
```

**Note**: Skip CLI checks for IDE-based agents (Copilot, Windsurf).

## Agent Categories

### CLI-Based Agents
Require a command-line tool to be installed:
- **Claude Code**: `claude` CLI
- **Gemini CLI**: `gemini` CLI
- **Cursor**: `cursor-agent` CLI
- **Qwen Code**: `qwen` CLI
- **opencode**: `opencode` CLI

### IDE-Based Agents
Work within integrated development environments:
- **GitHub Copilot**: Built into VS Code/compatible editors
- **Windsurf**: Built into Windsurf IDE

## Command File Formats

### Markdown Format
Used by: Claude, Cursor, opencode, Windsurf

```markdown
---
description: "Command description"
---

Command content with {SCRIPT} and $ARGUMENTS placeholders.
```

### TOML Format
Used by: Gemini, Qwen

```toml
description = "Command description"

prompt = """
Command content with {SCRIPT} and {{args}} placeholders.
"""
```

## Directory Conventions

- **CLI agents**: Usually `.<agent-name>/commands/`
- **IDE agents**: Follow IDE-specific patterns:
  - Copilot: `.github/prompts/`
  - Cursor: `.cursor/commands/`
  - Windsurf: `.windsurf/workflows/`

## Argument Patterns

Different agents use different argument placeholders:
- **Markdown/prompt-based**: `$ARGUMENTS`
- **TOML-based**: `{{args}}`
- **Script placeholders**: `{SCRIPT}` (replaced with actual script path)
- **Agent placeholders**: `__AGENT__` (replaced with agent name)

## Testing New Agent Integration

1. **Build test**: Run package creation script locally
2. **CLI test**: Test `specify init --ai <agent>` command
3. **File generation**: Verify correct directory structure and files
4. **Command validation**: Ensure generated commands work with the agent
5. **Context update**: Test agent context update scripts

## Common Pitfalls

1. **Forgetting update scripts**: Both bash and PowerShell scripts must be updated
2. **Missing CLI checks**: Only add for agents that actually have CLI tools
3. **Wrong argument format**: Use correct placeholder format for each agent type
4. **Directory naming**: Follow agent-specific conventions exactly
5. **Help text inconsistency**: Update all user-facing text consistently

## Future Considerations

When adding new agents:
- Consider the agent's native command/workflow patterns
- Ensure compatibility with the Spec-Driven Development process
- Document any special requirements or limitations
- Update this guide with lessons learned

---

## HVDC Project Visualization Guide

### Enhanced System Visualization (v3.6-VISUALIZATION)

AI Agents working on the HVDC project should be aware of the following visualization capabilities and standards:

#### 1. Mermaid Architecture Diagrams

**Location**: `diagrams/hvdc-system-architecture.mmd`

**Usage**:
```mermaid
%%{init: { "theme":"neutral", "layout":"elk", "securityLevel":"strict" }}%%
architecture-beta
group public(cloud)[Public Interface] {
  service ui(users)[Web UI]
  service api(gateway)[API Gateway]
}
group core(server)[Core Systems] {
  service invoice(database)[HVDC Invoice Audit]
  service hitachi(database)[Hitachi Sync]
  service ml(cloud)[ML Optimization]
}
```

**Key Features**:
- ELK layout for professional appearance
- Group-based organization (Public/Core/Storage/Support)
- Service relationships with directional arrows
- GitHub-compatible rendering

#### 2. Enhanced NetworkX Graphs

**Location**: `scripts/visualize_systems_enhanced.py`

**Generated Files**:
- `docs/visualizations/SYSTEM_RELATIONSHIPS_V2.png`
- `docs/visualizations/FILES_PER_SUBSYSTEM_V2.png`

**Features**:
- Hierarchical layout with shell positioning
- Group-based coloring (Core/Storage/Support/Documentation)
- Directed graphs with curved edges
- File count proportional node sizing

#### 3. Professional Visualization Standards

**Reference**: `SYSTEM GRAPH.MD`

**Supported Tools**:
- Mermaid v11 (architecture-beta + ELK)
- Structurizr DSL + CLI (C4 model export)
- D2 CLI (concise DSL)
- Graphviz 13.x (precise routing)
- Cytoscape.js 3.33.x (interactive dashboards)

#### 4. System Analysis Documentation

**Location**: `hitachi/docs/`

**Files**:
- `HVDC_SYSTEM_DETAILED_ANALYSIS.md` (Part 1)
- `HVDC_SYSTEM_DETAILED_ANALYSIS_PART2.md` (Part 2)
- `HVDC_SYSTEM_DETAILED_ANALYSIS_PART3.md` (Part 3)

**Content**:
- 2,792 lines of Python code analysis
- 70+ KB comprehensive documentation
- 28 unit tests + 7 KPI validations
- Flow code analysis and warehouse logic

### AI Agent Commands for Visualization

#### Generate System Graphs
```bash
# Enhanced system relationship graphs
python scripts/visualize_systems_enhanced.py

# Mermaid diagram rendering
npx mmdc -i diagrams/hvdc-system-architecture.mmd -o build/arch.svg
```

#### Update Documentation
```bash
# Update all documentation
/update-docs

# Generate system analysis
/analyze-code

# Create visualizations
/visualize-system
```

### Integration Guidelines

1. **Always use absolute paths** for output files
2. **Group systems by function** (Core/Storage/Support/Documentation)
3. **Apply consistent coloring** across all visualizations
4. **Include file counts** in node labels
5. **Use directed edges** to show data flow
6. **Generate both static and interactive** versions when possible

### Quality Standards

- **Resolution**: 300 DPI for PNG outputs
- **Layout**: Hierarchical with clear groupings
- **Colors**: Consistent palette across all diagrams
- **Labels**: Descriptive and informative
- **File Organization**: All outputs in `docs/visualizations/`

---

*This documentation should be updated whenever new agents are added to maintain accuracy and completeness.*
