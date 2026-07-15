"""Tests for resume export service (HTML, DOCX, PDF)."""

import json
import uuid
from io import BytesIO

from app.models.job import ResumeVersion


def make_version(
    content_dict: dict, template: str = "minimal", version_number: int = 1
) -> ResumeVersion:
    """Helper to create a ResumeVersion for testing."""
    v = ResumeVersion()
    v.id = uuid.uuid4()
    v.resume_id = uuid.uuid4()
    v.version_number = version_number
    v.content = json.dumps(content_dict)
    v.template = template
    v.status = "completed"
    v.score = 80
    return v


MINIMAL_DATA = {
    "name": "Kena Ararso",
    "email": "kenaararso4@gmail.com",
    "phone": "+251911620012",
    "location": "Addis Ababa, Ethiopia",
    "linkedin": "www.linkedin.com/in/kenaararso-094939258",
    "github": "https://github.com/Kena-AT",
    "website": None,
    "summary": "Software engineering student focused on backend systems and web application development.",
    "experience": [
        {
            "title": "Software Engineering Intern",
            "company": "Berenda Technologies",
            "location": "Addis Ababa, Ethiopia",
            "period": "Feb 2026 – Present",
            "bullets": [
                "Contributed to development of MesaelGC construction company website",
                "Built features for Shegiye, a print-on-demand platform",
                "Collaborated with team to build and maintain web application features",
            ],
        },
        {
            "title": "Software Engineering Intern",
            "company": "Adwa Dynamics",
            "location": "Addis Ababa, Ethiopia",
            "period": "Jun 2024 – Sep 2024",
            "bullets": [
                "Developed and maintained React web application features",
                "Built cross-platform Flutter mobile interfaces",
                "Implemented backend services with Node.js",
            ],
        },
    ],
    "projects": [
        {
            "name": "KiloEats",
            "description": "Campus food delivery platform connecting students, restaurants, and riders.",
            "url": None,
        },
        {
            "name": "Micron",
            "description": "Cross-platform CLI tool in Go for build artifact analysis and cleanup.",
            "url": None,
        },
    ],
    "skills": [
        "Python",
        "JavaScript",
        "TypeScript",
        "Go",
        "FastAPI",
        "React",
        "PostgreSQL",
        "Docker",
    ],
    "education": [
        {
            "institution": "Addis Ababa University",
            "degree": "Bachelor of Science",
            "field_of_study": "Software Engineering",
            "period": "2023 – Expected Jun 2027",
        }
    ],
}


class TestExportResumeHtml:
    """Tests for HTML export."""

    def test_html_export_minimal_template(self):
        from app.services.resume_export import export_resume_html

        version = make_version(MINIMAL_DATA, "minimal")
        html = export_resume_html(version)

        assert "<html>" in html
        assert "Kena Ararso" in html
        assert "kenaararso4@gmail.com" in html
        assert "Berenda Technologies" in html
        assert "KiloEats" in html
        assert "Python" in html

    def test_html_export_all_templates(self):
        from app.services.resume_export import export_resume_html

        for tmpl in ("minimal", "technical", "modern", "corporate", "compact"):
            version = make_version(MINIMAL_DATA, tmpl)
            html = export_resume_html(version)
            assert "<html>" in html, f"Template {tmpl} produced invalid HTML"
            assert "Kena Ararso" in html, f"Name missing in template {tmpl}"

    def test_html_export_empty_content(self):
        from app.services.resume_export import export_resume_html

        version = make_version({}, "minimal")
        html = export_resume_html(version)

        assert "<html>" in html

    def test_html_export_xss_escaping(self):
        from app.services.resume_export import export_resume_html

        data = {
            **MINIMAL_DATA,
            "name": "John <script>alert('xss')</script>",
            "summary": "<img src=x onerror=alert(1)>",
        }
        version = make_version(data, "minimal")
        html = export_resume_html(version)

        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html

    def test_html_export_is_string(self):
        from app.services.resume_export import export_resume_html

        version = make_version(MINIMAL_DATA)
        result = export_resume_html(version)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_html_export_unknown_template_fallback(self):
        from app.services.resume_export import export_resume_html

        version = make_version(MINIMAL_DATA, "nonexistent_template")
        html = export_resume_html(version)

        # Should fall back gracefully
        assert "<html>" in html

    def test_html_export_none_template_fallback(self):
        from app.services.resume_export import export_resume_html

        version = make_version(MINIMAL_DATA)
        version.template = None
        html = export_resume_html(version)

        assert "<html>" in html

    def test_html_export_invalid_json_content(self):
        from app.services.resume_export import export_resume_html

        version = make_version({})
        version.content = "not valid json {"

        # Should not raise, should handle gracefully
        html = export_resume_html(version)
        assert isinstance(html, str)


class TestExportResumePdf:
    """Tests for PDF export."""

    def test_pdf_export_returns_bytesio(self):
        from app.services.resume_export import export_resume_pdf

        version = make_version(MINIMAL_DATA)
        result = export_resume_pdf(version)

        assert isinstance(result, BytesIO)
        content = result.read()
        assert content.startswith(b"%PDF")
        assert len(content) > 500

    def test_pdf_export_positioned_at_start(self):
        from app.services.resume_export import export_resume_pdf

        version = make_version(MINIMAL_DATA)
        result = export_resume_pdf(version)

        assert result.tell() == 0

    def test_pdf_export_all_templates(self):
        from app.services.resume_export import export_resume_pdf

        for tmpl in ("minimal", "technical", "modern", "corporate", "compact"):
            version = make_version(MINIMAL_DATA, tmpl)
            result = export_resume_pdf(version)
            content = result.read()
            assert content.startswith(b"%PDF"), f"Template {tmpl} failed to produce PDF"

    def test_pdf_export_empty_content(self):
        from app.services.resume_export import export_resume_pdf

        version = make_version({})
        result = export_resume_pdf(version)
        content = result.read()

        # Should still produce a valid PDF even with empty data
        assert content.startswith(b"%PDF")


class TestExportResumeDocx:
    """Tests for DOCX export."""

    def test_docx_export_returns_bytesio(self):
        from app.services.resume_export import export_resume_docx

        version = make_version(MINIMAL_DATA)
        result = export_resume_docx(version)

        assert isinstance(result, BytesIO)
        content = result.read()
        assert len(content) > 0

    def test_docx_export_positioned_at_start(self):
        from app.services.resume_export import export_resume_docx

        version = make_version(MINIMAL_DATA)
        result = export_resume_docx(version)

        assert result.tell() == 0

    def test_docx_export_valid_zipfile(self):
        """DOCX files are ZIP archives — verify structure."""
        import zipfile
        from app.services.resume_export import export_resume_docx

        version = make_version(MINIMAL_DATA)
        result = export_resume_docx(version)

        with zipfile.ZipFile(result) as z:
            names = z.namelist()
            assert "word/document.xml" in names

    def test_docx_export_contains_name(self):
        """Check that name appears somewhere in the docx XML."""
        import zipfile
        from app.services.resume_export import export_resume_docx

        version = make_version(MINIMAL_DATA)
        result = export_resume_docx(version)

        with zipfile.ZipFile(result) as z:
            doc_xml = z.read("word/document.xml").decode("utf-8")
            assert "Kena Ararso" in doc_xml

    def test_docx_export_contains_experience(self):
        """Check that experience data is present in docx."""
        import zipfile
        from app.services.resume_export import export_resume_docx

        version = make_version(MINIMAL_DATA)
        result = export_resume_docx(version)

        with zipfile.ZipFile(result) as z:
            doc_xml = z.read("word/document.xml").decode("utf-8")
            assert "Berenda Technologies" in doc_xml

    def test_docx_export_empty_content(self):
        """Empty content should produce a valid DOCX."""
        import zipfile
        from app.services.resume_export import export_resume_docx

        version = make_version({})
        result = export_resume_docx(version)

        with zipfile.ZipFile(result) as z:
            assert "word/document.xml" in z.namelist()
