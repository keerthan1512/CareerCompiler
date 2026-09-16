"""
LaTeX AST Parser
Converts raw LaTeX resume source into a structured raw AST with line references.

Strategy:
1. Try TexSoup for high-level structure parsing
2. Fall back to pylatexenc token walker for complex/malformed files
3. Regex patterns for contact info extraction (robust across all templates)

Supports: moderncv, awesome-cv, custom templates.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Data Classes ─────────────────────────────────────────────────────────────


@dataclass
class SourceRef:
    file: str
    line_start: int
    line_end: int

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }


@dataclass
class RawBullet:
    id: str
    text: str
    source_ref: SourceRef


@dataclass
class RawEntry:
    id: str
    raw_text: str
    source_ref: SourceRef
    title: str = ""
    organization: str = ""
    location: str = ""
    date_raw: str = ""
    bullets: list[RawBullet] = field(default_factory=list)


@dataclass
class RawSection:
    id: str
    name: str
    source_ref: SourceRef
    entries: list[RawEntry] = field(default_factory=list)
    raw_content: str = ""


@dataclass
class RawContact:
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""
    location: str = ""
    name_line: int = 0
    email_line: int = 0
    phone_line: int = 0
    linkedin_line: int = 0
    github_line: int = 0
    website_line: int = 0
    location_line: int = 0


@dataclass
class RawAST:
    filename: str
    total_lines: int
    contact: RawContact
    sections: list[RawSection]
    document_class: str = ""
    packages: list[str] = field(default_factory=list)
    detected_format: str = "unknown"
    parse_errors: list[str] = field(default_factory=list)


# ─── Parser ───────────────────────────────────────────────────────────────────


class LaTeXParser:
    """
    Main parser entry point.
    Orchestrates TexSoup parsing with regex fallback.
    """

    VERSION = "1.0.0"

    # Regex patterns for extracting content from LaTeX braces
    _BRACE_CONTENT = re.compile(r"\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")

    # Contact extraction patterns (work across most resume templates)
    _PATTERNS = {
        "name_moderncv": re.compile(r"\\name\{([^}]+)\}\{([^}]+)\}"),
        "name_generic": re.compile(r"\\(?:name|author|Name)\{([^}]+)\}"),
        "email": re.compile(
            r"\\(?:email|href\{mailto:)[^}]*\}?\{?([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})"
        ),
        "email_plain": re.compile(
            r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})"
        ),
        "phone": re.compile(
            r"\\(?:phone|mobile|tel)\{([^}]+)\}"
        ),
        "phone_plain": re.compile(
            r"(?:(?:\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4})"
        ),
        "linkedin": re.compile(
            r"linkedin\.com/in/([a-zA-Z0-9\-]+)"
        ),
        "github": re.compile(
            r"github\.com/([a-zA-Z0-9\-]+)"
        ),
        "website": re.compile(
            r"\\(?:homepage|website|personalsite)\{([^}]+)\}"
        ),
        "location": re.compile(
            r"\\(?:address|location|city)\{([^}]+)\}"
        ),
        "document_class": re.compile(
            r"\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}"
        ),
        "usepackage": re.compile(
            r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}"
        ),
        "section": re.compile(
            r"^\\(?:section|Section)\*?\{([^}]+)\}"
        ),
        "subsection": re.compile(
            r"^\\subsection\*?\{([^}]+)\}"
        ),
        # moderncv: \cventry{dates}{title}{company}{location}{grade/extra}{description}
        "cventry": re.compile(
            r"\\cventry\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}"
        ),
        # \cvitem{label}{text}
        "cvitem": re.compile(
            r"\\cvitem\{([^}]*)\}\{([^}]*)\}"
        ),
        # awesome-cv: \cventry{dates}{title}{company}{location}{description}
        "awesome_cventry": re.compile(
            r"\\cventry\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}"
        ),
        # \item bullet
        "item": re.compile(r"\\item\s+(.+?)(?=\\item|\\end\{|$)", re.DOTALL),
    }

    def parse(self, content: str, filename: str = "main.tex") -> RawAST:
        """
        Parse a LaTeX resume string into a RawAST.

        Args:
            content: Raw .tex file content
            filename: Source filename (for SourceRef tracking)

        Returns:
            RawAST with sections, bullets, contact info, and line references
        """
        lines = content.splitlines()
        total_lines = len(lines)

        ast = RawAST(
            filename=filename,
            total_lines=total_lines,
            contact=RawContact(),
            sections=[],
        )

        # Phase 1: Extract preamble info
        self._extract_preamble(lines, ast)

        # Phase 2: Extract contact info
        self._extract_contact(lines, ast.contact, filename)

        # Phase 3: Try TexSoup for structured parsing
        try:
            self._parse_with_texsoup(content, lines, ast, filename)
        except Exception as exc:
            logger.warning(
                "TexSoup parsing failed for %s: %s — falling back to regex",
                filename,
                exc,
            )
            ast.parse_errors.append(f"TexSoup failed: {exc}")
            self._parse_with_regex(content, lines, ast, filename)

        return ast

    # ─── Preamble ─────────────────────────────────────────────────────────────

    def _extract_preamble(self, lines: list[str], ast: RawAST) -> None:
        """Extract document class and packages from preamble."""
        for line in lines:
            stripped = line.strip()
            if not ast.document_class:
                m = self._PATTERNS["document_class"].search(stripped)
                if m:
                    ast.document_class = m.group(1).strip()
                    # Detect template format
                    dc = ast.document_class.lower()
                    if "moderncv" in dc:
                        ast.detected_format = "moderncv"
                    elif "awesome" in dc:
                        ast.detected_format = "awesome-cv"
                    else:
                        ast.detected_format = "custom"

            pkg = self._PATTERNS["usepackage"].search(stripped)
            if pkg:
                # packages can be comma-separated
                for p in pkg.group(1).split(","):
                    p = p.strip()
                    if p and p not in ast.packages:
                        ast.packages.append(p)

    # ─── Contact ──────────────────────────────────────────────────────────────

    def _extract_contact(
        self, lines: list[str], contact: RawContact, filename: str
    ) -> None:
        """Extract contact fields with line numbers (1-indexed)."""
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Name: moderncv style \name{First}{Last}
            if not contact.name:
                m = self._PATTERNS["name_moderncv"].search(stripped)
                if m:
                    contact.name = f"{m.group(1).strip()} {m.group(2).strip()}"
                    contact.name_line = i
                    continue
                m = self._PATTERNS["name_generic"].search(stripped)
                if m:
                    contact.name = self._clean_latex(m.group(1))
                    contact.name_line = i
                    continue

            # Email
            if not contact.email:
                m = self._PATTERNS["email"].search(stripped)
                if m:
                    contact.email = m.group(1).strip()
                    contact.email_line = i
                elif "@" in stripped:
                    m = self._PATTERNS["email_plain"].search(stripped)
                    if m:
                        contact.email = m.group(0)
                        contact.email_line = i

            # Phone
            if not contact.phone:
                m = self._PATTERNS["phone"].search(stripped)
                if m:
                    contact.phone = self._clean_latex(m.group(1))
                    contact.phone_line = i

            # LinkedIn
            if not contact.linkedin:
                m = self._PATTERNS["linkedin"].search(stripped)
                if m:
                    contact.linkedin = f"linkedin.com/in/{m.group(1)}"
                    contact.linkedin_line = i

            # GitHub
            if not contact.github:
                m = self._PATTERNS["github"].search(stripped)
                if m:
                    contact.github = f"github.com/{m.group(1)}"
                    contact.github_line = i

            # Website
            if not contact.website:
                m = self._PATTERNS["website"].search(stripped)
                if m:
                    contact.website = self._clean_latex(m.group(1))
                    contact.website_line = i

            # Location
            if not contact.location:
                m = self._PATTERNS["location"].search(stripped)
                if m:
                    contact.location = self._clean_latex(m.group(1))
                    contact.location_line = i

    # ─── TexSoup Parsing ──────────────────────────────────────────────────────

    def _parse_with_texsoup(
        self, content: str, lines: list[str], ast: RawAST, filename: str
    ) -> None:
        """Use TexSoup to extract sections and content."""
        try:
            import TexSoup
        except ImportError:
            raise ImportError("TexSoup is not installed")

        soup = TexSoup.TexSoup(content)
        current_section: Optional[RawSection] = None

        for node in soup.descendants:
            node_name = getattr(node, "name", None)

            # ── Section detection ──────────────────────────────────────────
            if node_name == "section":
                section_name = self._node_text(node)
                line_num = self._find_line(lines, f"\\section{{{section_name}}}")
                section = RawSection(
                    id=str(uuid.uuid4()),
                    name=section_name,
                    source_ref=SourceRef(filename, line_num, line_num),
                )
                ast.sections.append(section)
                current_section = section

            # ── moderncv \cventry ──────────────────────────────────────────
            elif node_name == "cventry" and current_section:
                args = list(node.args) if hasattr(node, "args") else []
                if len(args) >= 3:
                    entry = self._parse_cventry_node(args, lines, filename, current_section)
                    current_section.entries.append(entry)

            # ── moderncv \cvitem (skill row) ───────────────────────────────
            elif node_name == "cvitem" and current_section:
                args = list(node.args) if hasattr(node, "args") else []
                if len(args) >= 2:
                    label = self._clean_latex(str(args[0]))
                    text = self._clean_latex(str(args[1]))
                    line_num = self._find_line(lines, f"\\cvitem{{{label}}}")
                    entry = RawEntry(
                        id=str(uuid.uuid4()),
                        raw_text=f"{label}: {text}",
                        source_ref=SourceRef(filename, line_num, line_num),
                        title=label,
                        organization=text,
                    )
                    current_section.entries.append(entry)

        # If TexSoup found no sections, fall back to regex
        if not ast.sections:
            logger.debug("TexSoup found no sections, using regex parser")
            self._parse_with_regex(content, lines, ast, filename)

    def _parse_cventry_node(
        self,
        args: list,
        lines: list[str],
        filename: str,
        section: RawSection,
    ) -> RawEntry:
        """Convert a TexSoup cventry node into a RawEntry."""
        def arg_text(a) -> str:
            return self._clean_latex(str(a))

        dates = arg_text(args[0]) if len(args) > 0 else ""
        title = arg_text(args[1]) if len(args) > 1 else ""
        org = arg_text(args[2]) if len(args) > 2 else ""
        location = arg_text(args[3]) if len(args) > 3 else ""
        description = arg_text(args[5]) if len(args) > 5 else (arg_text(args[4]) if len(args) > 4 else "")

        line_num = self._find_line(lines, "\\cventry")
        entry = RawEntry(
            id=str(uuid.uuid4()),
            raw_text=description,
            source_ref=SourceRef(filename, line_num, line_num + 3),
            title=title,
            organization=org,
            location=location,
            date_raw=dates,
        )

        # Extract bullets from description
        if description:
            for bullet_text in self._extract_items(description):
                bullet_text = bullet_text.strip()
                if bullet_text:
                    entry.bullets.append(
                        RawBullet(
                            id=str(uuid.uuid4()),
                            text=bullet_text,
                            source_ref=SourceRef(filename, line_num + 1, line_num + 1),
                        )
                    )
        return entry

    # ─── Regex Fallback ───────────────────────────────────────────────────────

    def _parse_with_regex(
        self, content: str, lines: list[str], ast: RawAST, filename: str
    ) -> None:
        """
        Regex-based fallback parser.
        Works on any LaTeX resume that uses \\section{} headings.
        """
        # Split content at \section boundaries
        section_splits = re.split(
            r"(\\section\*?\{[^}]+\})", content
        )

        current_section: Optional[RawSection] = None

        for chunk in section_splits:
            chunk = chunk.strip()
            if not chunk:
                continue

            # Check if this chunk IS a section header
            m = re.match(r"\\section\*?\{([^}]+)\}", chunk)
            if m:
                section_name = self._clean_latex(m.group(1))
                line_num = self._find_line(lines, chunk)
                current_section = RawSection(
                    id=str(uuid.uuid4()),
                    name=section_name,
                    source_ref=SourceRef(filename, line_num, line_num),
                    raw_content="",
                )
                ast.sections.append(current_section)
                continue

            if current_section is None:
                continue

            current_section.raw_content += chunk

            # Try to parse entries from this chunk
            entries = self._parse_entries_from_chunk(chunk, lines, filename)
            current_section.entries.extend(entries)

    def _parse_entries_from_chunk(
        self, chunk: str, lines: list[str], filename: str
    ) -> list[RawEntry]:
        """Extract entries from a section body chunk."""
        entries = []

        # Try \cventry
        for m in self._PATTERNS["cventry"].finditer(chunk):
            dates = self._clean_latex(m.group(1))
            title = self._clean_latex(m.group(2))
            org = self._clean_latex(m.group(3))
            loc = self._clean_latex(m.group(4))
            description = self._clean_latex(m.group(6) or m.group(5))
            line_num = self._find_line(lines, "\\cventry")

            entry = RawEntry(
                id=str(uuid.uuid4()),
                raw_text=description,
                source_ref=SourceRef(filename, line_num, line_num + 3),
                title=title,
                organization=org,
                location=loc,
                date_raw=dates,
            )
            for bt in self._extract_items(description):
                bt = bt.strip()
                if bt:
                    entry.bullets.append(
                        RawBullet(str(uuid.uuid4()), bt, SourceRef(filename, line_num + 1, line_num + 1))
                    )
            entries.append(entry)

        # Try \cvitem (skill rows)
        for m in self._PATTERNS["cvitem"].finditer(chunk):
            label = self._clean_latex(m.group(1))
            text = self._clean_latex(m.group(2))
            line_num = self._find_line(lines, "\\cvitem")
            entries.append(
                RawEntry(
                    id=str(uuid.uuid4()),
                    raw_text=f"{label}: {text}",
                    source_ref=SourceRef(filename, line_num, line_num),
                    title=label,
                    organization=text,
                )
            )

        # If no cventry / cvitem found, try itemize blocks
        if not entries:
            itemize_blocks = re.findall(
                r"\\begin\{itemize\}(.*?)\\end\{itemize\}", chunk, re.DOTALL
            )
            for block in itemize_blocks:
                line_num = self._find_line(lines, "\\begin{itemize}")
                entry = RawEntry(
                    id=str(uuid.uuid4()),
                    raw_text=block,
                    source_ref=SourceRef(filename, line_num, line_num + 10),
                )
                for bt in self._extract_items(block):
                    bt = bt.strip()
                    if bt:
                        item_line = self._find_line(lines, bt[:30] if len(bt) > 30 else bt)
                        entry.bullets.append(
                            RawBullet(str(uuid.uuid4()), bt, SourceRef(filename, item_line, item_line))
                        )
                if entry.bullets:
                    entries.append(entry)

        return entries

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _extract_items(self, text: str) -> list[str]:
        """Extract \\item content from a LaTeX itemize/enumerate block."""
        # Split on \item and take everything after it until next \item or \end
        items = re.split(r"\\item\b", text)
        result = []
        for item in items[1:]:  # skip content before first \item
            # Trim at \end{ or next command block
            item = re.sub(r"\\(?:end|begin)\{[^}]*\}.*", "", item, flags=re.DOTALL)
            item = self._clean_latex(item).strip()
            if item:
                result.append(item)
        return result

    def _node_text(self, node) -> str:
        """Extract plain text from a TexSoup node."""
        try:
            text = str(node.string) if hasattr(node, "string") else str(node)
            return self._clean_latex(text)
        except Exception:
            return ""

    def _clean_latex(self, text: str) -> str:
        """
        Remove LaTeX commands and braces, returning readable plain text.
        Preserves meaningful content.
        """
        if not text:
            return ""
        # Remove \href{url}{text} → keep text
        text = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", text)
        # Remove \textbf{} → keep content
        text = re.sub(r"\\text(?:bf|it|rm|sc|tt|sf)\{([^}]*)\}", r"\1", text)
        # Remove \emph{} → keep content
        text = re.sub(r"\\emph\{([^}]*)\}", r"\1", text)
        # Remove \url{} → keep URL
        text = re.sub(r"\\url\{([^}]*)\}", r"\1", text)
        # Remove other known one-arg commands but keep arg
        text = re.sub(r"\\(?:color|colorbox|fbox|mbox)\{[^}]*\}\{([^}]*)\}", r"\1", text)
        # Remove LaTeX commands without args
        text = re.sub(r"\\[a-zA-Z]+\*?\s*", " ", text)
        # Remove curly braces
        text = re.sub(r"[{}]", "", text)
        # Remove tilde (non-breaking space) and other special chars
        text = text.replace("~", " ").replace("--", "–").replace("---", "—")
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _find_line(self, lines: list[str], search_text: str, start: int = 0) -> int:
        """
        Find the 1-indexed line number of the first occurrence of search_text.
        Returns 1 if not found (safe default).
        """
        search_text = search_text.strip()[:60]  # cap search text length
        for i, line in enumerate(lines[start:], start=start + 1):
            if search_text in line:
                return i
        return 1
