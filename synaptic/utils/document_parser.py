"""
Document Parser — extracts structured content from PDF, DOC/DOCX, and TXT files.
Single Responsibility: owns all document ingestion and text extraction.
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from synaptic.utils.logger import synaptic_log


@dataclass
class DocumentSection:
    """Represents a section within a document with hierarchical structure."""
    title: str
    level: int  # Heading level (1=H1, 2=H2, etc.)
    content: str
    subsections: List['DocumentSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Result of parsing a document."""
    filename: str
    title: str
    sections: List[DocumentSection]
    raw_text: str
    tables: List[List[List[str]]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentParser:
    """
    Parses PDF, DOC/DOCX, and TXT files into structured representations.
    Extracts headings, content, tables, and metadata for estimation analysis.
    """

    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}

    def __init__(self):
        self._parsers = {
            '.pdf': self._parse_pdf,
            '.docx': self._parse_docx,
            '.doc': self._parse_docx,
            '.txt': self._parse_txt,
        }

    def parse(self, file_path: str) -> ParsedDocument:
        """Parse a document file and return structured content."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}. Supported: {self.SUPPORTED_EXTENSIONS}")

        synaptic_log.info(f"Parsing document: {file_path}")
        return self._parsers[ext](file_path)

    def _parse_txt(self, file_path: str) -> ParsedDocument:
        """Parse plain text file with heading detection."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        sections = []
        current_section = None
        current_content = []

        lines = raw_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if self._is_heading(line):
                if current_section:
                    current_section.content = '\n'.join(current_content)
                    sections.append(current_section)
                current_section = DocumentSection(
                    title=line,
                    level=self._heading_level(line),
                    content=""
                )
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            current_section.content = '\n'.join(current_content)
            sections.append(current_section)

        root_sections = self._build_hierarchy(sections)

        title = root_sections[0].title if root_sections else os.path.basename(file_path)

        return ParsedDocument(
            filename=os.path.basename(file_path),
            title=title,
            sections=root_sections,
            raw_text=raw_text.strip(),
            tables=[],
            metadata={"lines": len(lines)}
        )

    def _parse_pdf(self, file_path: str) -> ParsedDocument:
        """Parse PDF using pdfplumber."""
        try:
            import pdfplumber
        except ImportError:
            synaptic_log.error("pdfplumber not installed. Run: pip install pdfplumber")
            raise ImportError("pdfplumber required for PDF parsing")

        raw_text = ""
        tables = []
        sections = []
        current_section = None
        current_content = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                raw_text += text + "\n"

                page_tables = page.extract_tables()
                for table in page_tables:
                    if table:
                        tables.append(table)

                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if self._is_heading(line):
                        if current_section:
                            current_section.content = '\n'.join(current_content)
                            sections.append(current_section)
                        current_section = DocumentSection(
                            title=line,
                            level=self._heading_level(line),
                            content=""
                        )
                        current_content = []
                    else:
                        current_content.append(line)

            if current_section:
                current_section.content = '\n'.join(current_content)
                sections.append(current_section)

            root_sections = self._build_hierarchy(sections)

            return ParsedDocument(
                filename=os.path.basename(file_path),
                title=root_sections[0].title if root_sections else "Untitled",
                sections=root_sections,
                raw_text=raw_text.strip(),
                tables=tables,
                metadata={"pages": len(pdf.pages)}
            )

    def _parse_docx(self, file_path: str) -> ParsedDocument:
        """Parse DOCX using python-docx."""
        try:
            from docx import Document
        except ImportError:
            synaptic_log.error("python-docx not installed. Run: pip install python-docx")
            raise ImportError("python-docx required for DOCX parsing")

        doc = Document(file_path)
        raw_text = ""
        sections = []
        tables = []
        current_section = None
        current_content = []

        for table in doc.tables:
            table_data = []
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                table_data.append(row_data)
            tables.append(table_data)

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            raw_text += text + "\n"

            if para.style.name.startswith('Heading'):
                if current_section:
                    current_section.content = '\n'.join(current_content)
                    sections.append(current_section)
                level = self._extract_heading_level(para.style.name)
                current_section = DocumentSection(
                    title=text,
                    level=level,
                    content=""
                )
                current_content = []
            else:
                current_content.append(text)

        if current_section:
            current_section.content = '\n'.join(current_content)
            sections.append(current_section)

        root_sections = self._build_hierarchy(sections)

        return ParsedDocument(
            filename=os.path.basename(file_path),
            title=doc.core_properties.title or (root_sections[0].title if root_sections else "Untitled"),
            sections=root_sections,
            raw_text=raw_text.strip(),
            tables=tables,
            metadata={
                "author": doc.core_properties.author,
                "created": str(doc.core_properties.created) if doc.core_properties.created else None
            }
        )

    def _is_heading(self, line: str) -> bool:
        """Heuristic to detect if a line is a heading."""
        if line.isupper() and 10 < len(line) < 100:
            return True
        if line.endswith(':') and len(line) < 80:
            return True
        if re.match(r'^\d+(\.\d+)*\s+\w+', line):
            return True
        return False

    def _heading_level(self, line: str) -> int:
        """Estimate heading level from text."""
        if re.match(r'^\d+\.\d+\.\d+', line):
            return 3
        if re.match(r'^\d+\.\d+', line):
            return 2
        if re.match(r'^\d+\s+', line):
            return 1
        if line.isupper():
            return 1
        return 2

    def _extract_heading_level(self, style_name: str) -> int:
        """Extract level from Word heading style name."""
        match = re.search(r'Heading\s*(\d+)', style_name)
        return int(match.group(1)) if match else 2

    def _build_hierarchy(self, flat_sections: List[DocumentSection]) -> List[DocumentSection]:
        """Build a hierarchical tree from flat sections."""
        if not flat_sections:
            return []

        root = []
        stack = []

        for section in flat_sections:
            while stack and stack[-1].level >= section.level:
                stack.pop()

            if stack:
                stack[-1].subsections.append(section)
            else:
                root.append(section)

            stack.append(section)

        return root

    def extract_requirements(self, doc: ParsedDocument) -> List[Dict[str, Any]]:
        """Extract requirement-like statements from parsed document."""
        requirements = []
        requirement_patterns = [
            r'(?:must|shall|should|will|need to|required to)\s+(.+?)(?:\.|\n)',
            r'(?:requirement|spec|specification):?\s*(.+?)(?:\.|\n)',
            r'(?:functional|non-functional)\s+requirement:?\s*(.+?)(?:\.|\n)',
        ]

        text = doc.raw_text
        for pattern in requirement_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                req_text = match.group(1).strip()
                if len(req_text) > 10:
                    requirements.append({
                        "text": req_text,
                        "type": self._classify_requirement(req_text),
                        "priority": self._estimate_priority(req_text)
                    })

        return requirements

    def _classify_requirement(self, text: str) -> str:
        """Classify requirement as functional or non-functional."""
        non_func_keywords = ['performance', 'security', 'scalability', 'reliability',
                            'availability', 'latency', 'throughput', 'capacity',
                            'maintainability', 'usability', 'compatibility']
        text_lower = text.lower()
        if any(kw in text_lower for kw in non_func_keywords):
            return "non-functional"
        return "functional"

    def _estimate_priority(self, text: str) -> str:
        """Estimate priority from language."""
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['critical', 'must', 'shall', 'mandatory']):
            return "high"
        if any(kw in text_lower for kw in ['should', 'important', 'recommended']):
            return "medium"
        return "low"
