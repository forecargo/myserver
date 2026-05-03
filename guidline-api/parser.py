import re
from dataclasses import dataclass, field


@dataclass
class GuidelineChunk:
    section_id: str
    title: str
    text: str
    requirement_type: str  # "basic" | "desirable" | "general"
    breadcrumb: str
    footnotes: list[dict] = field(default_factory=list)

    @property
    def embed_text(self) -> str:
        parts = [self.breadcrumb, ""]
        if self.requirement_type == "basic":
            parts.append("【基本的な対応事項】")
        elif self.requirement_type == "desirable":
            parts.append("【対応が望ましい事項】")
        parts.append(self.text)
        return "\n".join(parts)

    @property
    def snippet(self) -> str:
        clean = self.text.strip()
        return clean[:200] + "…" if len(clean) > 200 else clean


_SECTION_NUM_RE = re.compile(r"^(\d+(?:\.\d+)*)")
_FOOTNOTE_DEF_RE = re.compile(r"^\[\^([^\]]+)\]:\s*(.+)")
_FOOTNOTE_REF_RE = re.compile(r"\[\^([^\]]+)\]")
_BASIC_MARKER = "【基本的な対応事項】"
_DESIRABLE_MARKER = "【対応が望ましい事項】"


def _heading_depth(line: str) -> int:
    m = re.match(r"^(#{1,6})\s", line)
    return len(m.group(1)) if m else 0


def _heading_text(line: str) -> str:
    return re.sub(r"^#{1,6}\s+", "", line).strip()


def _extract_section_id(title: str) -> str:
    m = _SECTION_NUM_RE.match(title)
    return m.group(1) if m else ""


def _build_breadcrumb(stack: list[str]) -> str:
    return " > ".join(stack)


def _resolve_footnotes(text: str, footnote_table: dict[str, str]) -> list[dict]:
    refs = _FOOTNOTE_REF_RE.findall(text)
    result = []
    seen: set[str] = set()
    for ref in refs:
        if ref in footnote_table and ref not in seen:
            result.append({"ref": f"^{ref}", "text": footnote_table[ref]})
            seen.add(ref)
    return result


def parse_guideline(filepath: str) -> list[GuidelineChunk]:
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    # Pass 1: collect all footnote definitions
    footnote_table: dict[str, str] = {}
    for line in lines:
        m = _FOOTNOTE_DEF_RE.match(line.strip())
        if m:
            footnote_table[m.group(1)] = m.group(2).strip()

    # Pass 2: parse structure
    chunks: list[GuidelineChunk] = []
    heading_stack: list[str] = []  # titles at each depth
    current_lines: list[str] = []
    current_type: str = "general"
    current_section_id: str = ""
    current_title: str = ""
    in_toc: bool = False
    in_frontmatter: bool = False
    frontmatter_count: int = 0

    def flush_chunk():
        text = "".join(current_lines).strip()
        if not text or not current_title:
            return
        breadcrumb = _build_breadcrumb(heading_stack)
        title = current_title
        section_id = current_section_id
        footnotes = _resolve_footnotes(text, footnote_table)
        chunks.append(GuidelineChunk(
            section_id=section_id,
            title=title,
            text=text,
            requirement_type=current_type,
            breadcrumb=breadcrumb,
            footnotes=footnotes,
        ))

    for i, raw_line in enumerate(lines):
        line = raw_line.rstrip("\n")

        # Handle YAML frontmatter
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            frontmatter_count = 1
            continue
        if in_frontmatter:
            if line.strip() == "---":
                frontmatter_count += 1
                if frontmatter_count == 2:
                    in_frontmatter = False
            continue

        # Skip footnote definition lines (already collected)
        if _FOOTNOTE_DEF_RE.match(line.strip()):
            continue

        depth = _heading_depth(line)

        # Detect and skip TOC (## 目次 block)
        if depth == 2 and "目次" in _heading_text(line):
            in_toc = True
            continue
        if in_toc:
            if depth == 2:
                in_toc = False
                # fall through to process this heading
            else:
                continue

        # Requirement type markers (appear as ##### headings)
        if depth >= 4:
            heading = _heading_text(line)
            if _BASIC_MARKER in heading or _DESIRABLE_MARKER in heading:
                flush_chunk()
                current_lines = []
                if _BASIC_MARKER in heading:
                    current_type = "basic"
                else:
                    current_type = "desirable"
                continue

        # Regular section heading
        if depth > 0:
            flush_chunk()
            current_lines = []
            current_type = "general"

            title = _heading_text(line)
            section_id = _extract_section_id(title)

            # Update heading stack: pop all items at this depth or deeper
            while len(heading_stack) >= depth - 1:
                heading_stack.pop()
            heading_stack.append(title)

            current_title = title
            current_section_id = section_id
            continue

        current_lines.append(raw_line)

    flush_chunk()
    return chunks
