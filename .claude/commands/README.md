# Claude Code Slash Commands - Complete List

## 📄 Document Processing Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/xlsx` | Excel spreadsheet processing | `/xlsx read sales_data.xlsx` |
| `/excel` | Excel with database comparison (alias) | `/excel report.xlsx --compare` |
| `/pdf` | PDF processing and manipulation | `/pdf extract document.pdf` |
| `/docx` | Word document processing | `/docx read report.docx` |
| `/pptx` | PowerPoint presentation handling | `/pptx extract slides.pptx` |

## 🎨 Design Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/canvas` | Create visual designs and posters | `/canvas create poster --style modern` |
| `/art` | Generate algorithmic art | `/art generate fractal --type mandelbrot` |
| `/theme` | Create application themes | `/theme create dark-mode --primary #007AFF` |
| `/brand` | Manage brand guidelines | `/brand create guidelines --company "StartupX"` |

## 🛠️ Development Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/artifact` | Build interactive web artifacts | `/artifact create dashboard --components charts` |
| `/webapp` | Test web applications | `/webapp test https://myapp.com --flow login` |

## 🚀 Productivity Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/gif` | Create animated GIFs for Slack | `/gif create "Ship It!" --effect bounce` |
| `/comms` | Generate internal communications | `/comms newsletter --type weekly` |

## Quick Start Examples

### Process a PDF
```bash
/pdf extract invoice.pdf
```

### Analyze Excel Data
```bash
/excel products.xlsx --all --compare
```

### Create a Presentation
```bash
/pptx create sales_deck.pptx --from notes.md
```

### Generate Art
```bash
/art generate fractal --colors vibrant
```

### Create a GIF
```bash
/gif create "Success!" --effect celebration
```

## How to Use

1. **Direct Command**: Type the slash command directly
   ```
   /pdf document.pdf
   ```

2. **With Options**: Add flags and parameters
   ```
   /excel data.xlsx --extract-images --report json
   ```

3. **Natural Language**: Some commands work with descriptions
   ```
   /canvas design a modern poster for our product launch
   ```

## Command Structure

```
/[command] [target] [--option value] [--flag]
```

- **command**: The skill name (pdf, excel, canvas, etc.)
- **target**: File or description
- **options**: Parameters with values
- **flags**: Boolean switches

## File Locations

- **Input Files**: Can be anywhere in the project
- **Output**: Same directory as input (unless specified)
- **Temp Files**: Auto-cleaned after processing

## Getting Help

For any command, you can ask:
- "How do I use /pdf?"
- "What options does /excel have?"
- "Show me examples of /canvas"

## Troubleshooting

### Command Not Found
- Check spelling: `/excel` not `/excell`
- Some commands have aliases: `/sc:excel` also works

### File Not Found
- Use full path if file is in different directory
- Check file extension (.xlsx not .xls)

### Missing Features
- Some commands require dependencies
- Run `pip install -r requirements.txt` if needed

## Advanced Usage

### Chaining Commands
Process multiple operations:
```bash
# Extract from PDF, then create Excel
/pdf extract data.pdf | /excel create from-pdf.xlsx
```

### Batch Processing
Handle multiple files:
```bash
/excel *.xlsx --all --merge output.xlsx
```

### Custom Options
Many commands support advanced options:
```bash
/canvas create poster \
  --size 1920x1080 \
  --font "Work Sans" \
  --theme dark \
  --export png,svg
```

---

*Last Updated: 2025-01-22*
*Total Commands: 14*
*Categories: Documents, Design, Development, Productivity*