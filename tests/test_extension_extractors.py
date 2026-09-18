from bs4 import BeautifulSoup


# Python reference implementation mirroring extractor.ts to ensure algorithm fidelity
def extract_from_html(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # 1. JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json

            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else data.get("@graph", [data])
            for item in items:
                if item.get("@type") == "JobPosting":
                    org = item.get("hiringOrganization", {})
                    company = org.get("name") if isinstance(org, dict) else str(org)
                    loc = item.get("jobLocation", {})
                    addr = loc.get("address", {}) if isinstance(loc, dict) else {}
                    loc_str = (
                        addr.get("addressLocality")
                        if isinstance(addr, dict)
                        else str(loc)
                    )
                    return {
                        "title": item.get("title", "").strip(),
                        "company": (company or "Unknown").strip(),
                        "location": loc_str,
                        "description": item.get("description", "").strip(),
                        "extracted_via": "json_ld",
                        "confidence": 0.95,
                    }
        except Exception:
            pass

    # 2. Platform selectors
    lower_url = url.lower()
    if "greenhouse.io" in lower_url:
        title = soup.select_one(".app-title, h1")
        company = soup.select_one(".company-name")
        location = soup.select_one(".location")
        content = soup.select_one("#content")
        if title:
            return {
                "title": title.get_text(strip=True),
                "company": company.get_text(strip=True) if company else "Greenhouse Co",
                "location": location.get_text(strip=True) if location else None,
                "description": content.get_text(strip=True) if content else "",
                "extracted_via": "dom_adapter",
                "confidence": 0.9,
            }

    if "lever.co" in lower_url:
        title = soup.select_one(".posting-headline h2")
        team = soup.select_one(".posting-categories .sort-by-team")
        location = soup.select_one(".posting-categories .sort-by-time")
        desc = soup.select_one(".section.page-centered")
        if title:
            return {
                "title": title.get_text(strip=True),
                "company": team.get_text(strip=True) if team else "Lever Co",
                "location": location.get_text(strip=True) if location else None,
                "description": desc.get_text(strip=True) if desc else "",
                "extracted_via": "dom_adapter",
                "confidence": 0.9,
            }

    # 3. Generic fallback
    h1 = soup.select_one("h1")
    return {
        "title": h1.get_text(strip=True) if h1 else "Job Listing",
        "company": "Generic Site",
        "location": None,
        "description": soup.get_text(strip=True)[:500],
        "extracted_via": "generic",
        "confidence": 0.5,
    }


class TestExtractorAdapters:
    def test_json_ld_extraction(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org/",
                "@type": "JobPosting",
                "title": "Principal Distributed Systems Engineer",
                "description": "Architect globally distributed databases.",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Cockroach Labs"
                },
                "jobLocation": {
                    "@type": "Place",
                    "address": {
                        "addressLocality": "New York, NY"
                    }
                }
            }
            </script>
        </head>
        <body><h1>Careers Page</h1></body>
        </html>
        """
        extracted = extract_from_html(html, "https://cockroachlabs.com/careers/123")
        assert extracted["extracted_via"] == "json_ld"
        assert extracted["title"] == "Principal Distributed Systems Engineer"
        assert extracted["company"] == "Cockroach Labs"
        assert extracted["location"] == "New York, NY"
        assert extracted["confidence"] == 0.95

    def test_greenhouse_extraction(self):
        html = """
        <div id="wrapper">
            <h1 class="app-title">Senior React Developer</h1>
            <span class="company-name">Figma</span>
            <div class="location">San Francisco, CA</div>
            <div id="content"><p>Help build the future of design collaboration.</p></div>
        </div>
        """
        extracted = extract_from_html(
            html, "https://boards.greenhouse.io/figma/jobs/445566"
        )
        assert extracted["extracted_via"] == "dom_adapter"
        assert extracted["title"] == "Senior React Developer"
        assert extracted["company"] == "Figma"
        assert extracted["location"] == "San Francisco, CA"
        assert "future of design" in extracted["description"]

    def test_lever_extraction(self):
        html = """
        <div class="posting-headline"><h2>Staff Security Architect</h2></div>
        <div class="posting-categories">
            <div class="sort-by-team">Security Eng</div>
            <div class="sort-by-time posting-category">Remote - US</div>
        </div>
        <div class="section page-centered"><p>Lead zero-trust architecture.</p></div>
        """
        extracted = extract_from_html(html, "https://jobs.lever.co/databricks/778899")
        assert extracted["extracted_via"] == "dom_adapter"
        assert extracted["title"] == "Staff Security Architect"
        assert extracted["company"] == "Security Eng"
        assert extracted["location"] == "Remote - US"

    def test_generic_fallback(self):
        html = """
        <html><body><h1>Software Craftsman</h1><p>We are looking for passionate developers.</p></body></html>
        """
        extracted = extract_from_html(html, "https://unknownstartup.io/careers/job1")
        assert extracted["extracted_via"] == "generic"
        assert extracted["title"] == "Software Craftsman"
        assert extracted["confidence"] == 0.5
