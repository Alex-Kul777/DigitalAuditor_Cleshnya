from pathlib import Path

class ReportAssembler:
    def __init__(self, drafts_dir: Path):
        self.drafts_dir = drafts_dir
    
    def assemble(self, output_path: Path) -> Path:
        chapters = sorted(self.drafts_dir.glob("*.md"))
        content = []
        for chapter in chapters:
            content.append(chapter.read_text(encoding='utf-8'))
            content.append("\n\n---\n\n")
        output_path.write_text("".join(content), encoding='utf-8')
        return output_path
