# /docx - Word Document Processing

Process Microsoft Word documents (.docx) with full OOXML support for reading, creation, and modification.

## Core Capabilities
- **Read**: Extract text, tables, images, and formatting
- **Create**: Generate Word documents from scratch
- **Modify**: Edit existing documents preserving formatting
- **Convert**: Transform to/from other formats
- **Analyze**: Document structure, styles, comments
- **Templates**: Work with Word templates and mail merge

## Usage Examples

### Extract Content
```
/docx read report.docx
# Extracts all content from Word document
```

### Create Document
```
/docx create meeting_notes.docx --template formal
# Creates new Word document with template
```

### Modify Document
```
/docx update contract.docx --replace "old_term" "new_term"
# Updates specific content in document
```

### Extract Tables
```
/docx extract-tables data.docx --format csv
# Extracts all tables to CSV format
```

## Implementation
When invoked, I will:
1. Parse DOCX structure using OOXML schemas
2. Process document elements (paragraphs, tables, images)
3. Maintain formatting and styles
4. Handle comments and track changes
5. Generate or modify documents as needed

## File Locations
- Input: Any .docx file path
- Output: Same directory or specified location
- Templates: .claude-plugin/plugins/anthropic-agent-skills/document-skills/docx/templates/