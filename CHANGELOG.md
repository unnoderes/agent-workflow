# Changelog

## [2025-01-XX] - Notion-Based Two-Phase Workflow

### Added

#### New Skills
- **`collect-video-materials`** (`.agents/skills/collect-video-materials/SKILL.md`)
  - Phase 1: Materials collection with Notion workspace creation
  - Web search 3+ times for hooks, data, cases, comparisons
  - Structured materials written to Notion library
  - Returns Notion workspace URL for next phase

- **`generate-video-script`** (`.agents/skills/generate-video-script/SKILL.md`)
  - Phase 2: Script generation from Notion materials
  - Automatic coverage analysis and optional supplementary search (0-3 times)
  - Structure design and segmented script generation
  - Production parameter recommendations (ratio, style, TTS)
  - Full script written back to Notion

#### Documentation
- **`NOTION_WORKFLOW.md`**: Complete guide for the two-phase workflow
  - Usage examples
  - Best practices for materials library
  - Team collaboration scenarios
  - Troubleshooting guide

### Changed
- **Pipeline architecture**: Split materials collection and script generation into two independent phases
- **`agents.md`**: Updated skill index and pipeline diagram to reflect new workflow
- **`README.md`**: Updated quick start guide, skills table, and pipeline diagram

### Deprecated
- **`video-script-planning`**: Marked as deprecated in favor of the new two-phase approach
  - Original functionality split into `collect-video-materials` + `generate-video-script`
  - Legacy skill file preserved for reference with deprecation notice

### Benefits
- **Separation of concerns**: Materials collection and script generation are independent
- **Reviewable**: Human review/editing of materials in Notion between phases
- **Reusable**: One materials library can generate multiple script versions
- **Collaborative**: Multiple team members can edit materials in Notion simultaneously
- **Traceable**: All intermediate artifacts permanently stored in Notion

### Migration Guide

**Old workflow**:
```bash
"Create a 60-second video script about [topic]"
```

**New workflow**:
```bash
# Phase 1: Collect materials
"Collect materials for video: [topic]"
# → Returns Notion workspace URL

# Phase 2: Generate script
"Generate script from workspace: [Notion URL]"
# → Returns Notion script page URL
```

### Technical Details
- Notion MCP Server integration for page creation and content updates
- Smart search strategy: 0-3 supplementary searches based on materials coverage
- Structured Notion workspace: Main page + Materials library + Script placeholder
- Materials taxonomy: Hooks, Data, Cases, Comparisons, References

---

For detailed usage instructions, see [NOTION_WORKFLOW.md](NOTION_WORKFLOW.md).
