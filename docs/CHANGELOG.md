# Changelog

All notable changes to the RAG Enterprise project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **SESSION PROTOCOL** in CLAUDE.md for operational enforcement
  - Mandatory session start/end checklists
  - Change management workflow (classify → verify → complete → document)
  - Immediate CHANGELOG.md update requirement after any code change
  - No "check later" promises - monitor NOW or don't mention
  - References `docs/CHANGE_MANAGEMENT_GOVERNANCE.md` for full framework
- **Pre-migration checklist** (`PRE_MIGRATION_CHECKLIST.md`)
  - Comprehensive system integrity verification
  - Security audit results
  - Step-by-step publishing workflow
  - Release notes template

### Changed
- **Documentation Optimization**: Split PROGRESS.md into token-efficient structure
  - Created `PROGRESS_CURRENT.md` (~100 lines) - Active status and blockers only
  - Created `PROGRESS_ARCHIVE.md` (~380 lines) - Historical milestones v1.0.0-v3.0.0
  - **Token savings**: ~1,200 tokens per session (25% reduction from documentation)
  - Future sessions load current status only, archive available for reference

## [3.1.0] - 2025-11-03

### Added
- **Materials Coverage**: Expanded packaging materials from 5 to 7 plastics
  - Added PETG (Glycol-modified PET) for enhanced clarity/toughness containers
  - Added LLDPE (Linear Low-Density PE) for flexible films and wraps
  - Added LDPE (Low-Density PE) for squeeze bottles and flexible packaging
  - Complete list: PET, PETG, PP, HDPE, LLDPE, LDPE, PS

- **Regulatory Framework Specification**: Region-specific compliance standards
  - **United States**: FDA 21 CFR 177 (Food Contact Substances)
  - **Europe**: EU 10/2011 (Plastic Materials & Articles), REACH (Chemical Safety)
  - **Korea**: 식품위생법 (Food Sanitation Act), 식품용기규격 (Food Container Standards)

- **Test Coverage**: Comprehensive material validation
  - JSONL parser tests: 7 products covering all materials (3 → 7)
  - CSV parser tests: 7 products with complete material coverage
  - All assertions updated for new materials (PETG, LLDPE, LDPE, PS)
  - Test results: ✅ 10/10 tests passing

### Changed
- **Documentation Updates**:
  - `.claude/skills/rag-pipeline/SKILL.md`: 5 sections updated with new materials and regulatory standards
  - `CLAUDE.md`: Packaging Expert section updated with detailed regional regulations
  - `PROGRESS.md`: Added 2025-11-03 entry documenting all changes
  - Version bumped to 3.1.0 to reflect materials/regulatory enhancement

- **Model Configuration**: Unified all references to local open-source stack
  - Consolidated model selection documentation (lines 880-919 in SKILL.md)
  - Emphasized zero-cost architecture ($0/month vs $300-660/year API-based)
  - Updated resource usage breakdown: 14-15GB used (58%), 9-10GB free (42%)

### Removed
- **PVC Material**: Removed from materials list in favor of safer alternatives

### Fixed
- **Model Configuration Consistency**: Resolved conflicting documentation between local and API-based models

## [3.0.0] - 2025-01-25

### Added
- SKILL-centric architecture with 75% token reduction (2100 → 500 tokens)
- Unified RAG pipeline SKILL for orchestration
- Manufacturing expert and packaging expert domain SKILLs
- Bottle expert SKILL for cosmetic packaging recommendations

### Changed
- Migrated from 7 MCP servers to 3 essential servers
- Consolidated rag-master, rag-document-processor, rag-vector-search into single pipeline

### Removed
- claude_api, ollama, rag_orchestrator, note_keeper MCP servers (functionality moved to SKILLs)

## [2.0.0] - 2025-10-24

### Added
- Plugin integration with RAG orchestrator
- Complete testing coverage (39 tests: E2E, RAG pipeline, MCP protocol)
- Manufacturing Expert Plugin (330 lines, 150+ terms, 8 doc types)
- Packaging Expert Plugin (300 lines, 40+ materials, 30+ standards)

### Changed
- Overall completion: 85% → 100%
- Status: Production-ready with comprehensive testing

### Fixed
- get_plugin_info() to use plugin.get_domain_name() method
- process_document() to correctly access ProcessingResult structure
- Enhanced concurrent test with substantial manufacturing content

---

## Version History

- **3.1.0 (2025-11-03)**: Materials & regulatory standards enhancement
- **3.0.0 (2025-01-25)**: SKILL-centric architecture migration
- **2.0.0 (2025-10-24)**: Plugin integration & testing complete
- **1.0.0**: Initial production release

---

## Categories

### Added
For new features.

### Changed
For changes in existing functionality.

### Deprecated
For soon-to-be removed features.

### Removed
For now removed features.

### Fixed
For any bug fixes.

### Security
In case of vulnerabilities.

---

**Maintained By**: RAG Enterprise Team
**License**: MIT
