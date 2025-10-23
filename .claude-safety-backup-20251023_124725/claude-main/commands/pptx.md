# /pptx - PowerPoint Presentation Processing

Process PowerPoint presentations with slide manipulation, content extraction, and creation capabilities.

## Core Capabilities
- **Extract**: Text, images, charts from slides
- **Create**: Generate presentations from content
- **Modify**: Update slides, layouts, themes
- **Convert**: HTML to PPTX, PPTX to images
- **Analyze**: Slide structure, speaker notes
- **Rearrange**: Reorder, duplicate, delete slides

## Usage Examples

### Extract Content
```
/pptx extract presentation.pptx
# Extracts all text and images from slides
```

### Create Presentation
```
/pptx create sales_deck.pptx --from markdown.md
# Creates presentation from markdown content
```

### Convert HTML to Slides
```
/pptx html2pptx webpage.html --output slides.pptx
# Converts HTML content to presentation
```

### Generate Thumbnails
```
/pptx thumbnails deck.pptx --size 1920x1080
# Creates thumbnail images of all slides
```

## Available Scripts
- `html2pptx.js` - Convert HTML to PowerPoint
- `inventory.py` - List all slide contents
- `rearrange.py` - Reorder slides
- `replace.py` - Replace content
- `thumbnail.py` - Generate slide thumbnails

## Implementation
When invoked, I will:
1. Parse presentation structure
2. Process slides, layouts, and masters
3. Handle multimedia content
4. Maintain animations and transitions
5. Generate output as specified