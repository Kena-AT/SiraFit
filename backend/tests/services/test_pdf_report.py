from app.services.pdf_report import generate_report_pdf


def test_generate_report_pdf():
    title = "Test Report"
    markdown = """
    # Heading 1
    This is a **test** report.
    
    * List item 1
    * List item 2
    
    | Col 1 | Col 2 |
    | ----- | ----- |
    | A     | B     |
    """

    pdf_bytes = generate_report_pdf(title, markdown)
    assert pdf_bytes is not None
    pdf_data = pdf_bytes.getvalue()

    # Check for PDF magic number
    assert pdf_data.startswith(b"%PDF-")
    assert len(pdf_data) > 100
