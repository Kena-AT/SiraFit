"""Tests for PDF rendering service."""

from io import BytesIO

from app.services.pdf_rendering import render_html_to_pdf_bytes, render_html_to_pdf


class TestPdfRendering:
    """Tests for HTML-to-PDF conversion."""

    def test_simple_html_to_pdf(self):
        """Test converting basic HTML to PDF."""
        html = "<html><body><p>Hello World</p></body></html>"
        result = render_html_to_pdf_bytes(html)

        assert isinstance(result, BytesIO)
        assert result.tell() == 0  # Stream positioned at start
        content = result.read()
        assert len(content) > 0
        assert content.startswith(b"%PDF")  # PDF magic bytes

    def test_styled_html_to_pdf(self):
        """Test converting styled HTML to PDF."""
        html = """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; font-size: 24px; }
        p { line-height: 1.6; }
    </style>
</head>
<body>
    <h1>Test Document</h1>
    <p>This is a test paragraph with some <strong>bold text</strong> and <em>italic text</em>.</p>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)

        assert isinstance(result, BytesIO)
        content = result.read()
        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_empty_html(self):
        """Test that empty HTML still produces a valid PDF."""
        html = "<html><body></body></html>"
        result = render_html_to_pdf_bytes(html)

        content = result.read()
        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_html_with_special_characters(self):
        """Test HTML with special characters renders correctly."""
        html = """<html>
<body>
    <p>Special characters: &lt; &gt; &amp; &quot;</p>
    <p>Unicode: ñ é ü © ™</p>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)

        content = result.read()
        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_multi_page_html(self):
        """Test HTML that should span multiple pages."""
        paragraphs = "\n".join([f"<p>Paragraph {i} with some content to fill space.</p>" for i in range(100)])
        html = f"<html><body>{paragraphs}</body></html>"

        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")
        # Multi-page PDFs are significantly larger
        assert len(content) > 1000

    def test_render_html_to_pdf_bytes_returns_bytes(self):
        """Test that the bytes variant returns raw bytes."""
        html = "<html><body><h1>Test</h1></body></html>"
        result = render_html_to_pdf(html)

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result.startswith(b"%PDF")

    def test_html_with_lists(self):
        """Test HTML with ordered and unordered lists."""
        html = """<html>
<body>
    <h2>Unordered List</h2>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>
    <h2>Ordered List</h2>
    <ol>
        <li>First</li>
        <li>Second</li>
        <li>Third</li>
    </ol>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_html_with_table(self):
        """Test HTML with a simple table."""
        html = """<html>
<body>
    <table border="1">
        <tr>
            <th>Name</th>
            <th>Role</th>
        </tr>
        <tr>
            <td>John Doe</td>
            <td>Engineer</td>
        </tr>
        <tr>
            <td>Jane Smith</td>
            <td>Designer</td>
        </tr>
    </table>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_html_with_inline_styles(self):
        """Test HTML with inline styles."""
        html = """<html>
<body>
    <p style="color: red; font-size: 16px;">Red paragraph</p>
    <div style="background-color: #f0f0f0; padding: 10px;">
        <span style="font-weight: bold;">Bold in div</span>
    </div>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_malformed_html(self):
        """Test that malformed HTML doesn't crash the renderer."""
        html = "<html><body><p>Unclosed paragraph<div>Overlapping tags</p></div>"
        result = render_html_to_pdf_bytes(html)

        content = result.read()
        # xhtml2pdf is lenient and will still produce a PDF
        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_html_with_utf8_encoding(self):
        """Test HTML with UTF-8 encoding declaration."""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body>
    <p>UTF-8 content: 你好世界 مرحبا العالم</p>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_long_unbroken_line(self):
        """Test HTML with very long unbroken text."""
        long_word = "A" * 1000
        html = f"<html><body><p>{long_word}</p></body></html>"

        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_nested_elements(self):
        """Test deeply nested HTML elements."""
        html = """<html>
<body>
    <div>
        <div>
            <div>
                <div>
                    <p>Deeply nested content</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        result = render_html_to_pdf_bytes(html)
        content = result.read()

        assert len(content) > 0
        assert content.startswith(b"%PDF")
