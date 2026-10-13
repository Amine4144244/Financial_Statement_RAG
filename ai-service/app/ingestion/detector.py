import os
import re
from typing import Dict, Any, List, Optional
import pymupdf


class DocumentMetadataDetector:
    """Inspects the cover and introductory pages of financial PDFs to automatically

    detect the company, reporting fiscal year, and period type.
    """

    def detect_metadata(
        self,
        file_path: str,
        original_filename: Optional[str] = None,
        known_companies: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {
                "detected_company_id": None,
                "detected_company_name": None,
                "detected_fiscal_year": None,
                "detected_period_type": "FY",
                "confidence": "low",
                "evidence": f"File not found: {file_path}",
                "preview_snippet": "",
            }

        extracted_text = ""
        preview_snippet = ""
        try:
            doc = pymupdf.open(file_path)
            # Scan up to the first 3 pages
            num_pages = min(len(doc), 3)
            pages_text = []
            for i in range(num_pages):
                page_text = doc[i].get_text("text") or ""
                pages_text.append(page_text)
            doc.close()
            extracted_text = "\n".join(pages_text)
            if pages_text:
                preview_snippet = pages_text[0].strip()[:200]
        except Exception as e:
            # Fallback or error reading
            extracted_text = ""
            preview_snippet = f"Could not read PDF text: {str(e)}"

        filename = original_filename or os.path.basename(file_path)
        combined_text = f"{filename}\n{extracted_text}"

        # 1. Detect Company
        detected_company_id = None
        detected_company_name = None
        company_evidence = []
        company_score = 0

        companies = known_companies or []

        # Try matching known companies first
        best_match = None
        best_match_score = 0

        for comp in companies:
            c_id = comp.get("id", "")
            c_name = comp.get("name", "")
            c_ticker = comp.get("ticker", "")

            score = 0
            ev = []

            # Check exact or partial name in first page
            if c_name and len(c_name) > 3:
                name_pattern = re.escape(c_name)
                # Word boundary match
                matches = len(re.findall(rf"\b{name_pattern}\b", extracted_text, re.IGNORECASE))
                if matches > 0:
                    score += 50 + (matches * 5)
                    ev.append(f"Found company name '{c_name}' ({matches}x)")

            # Check ticker with word boundary
            if c_ticker and len(c_ticker) >= 2:
                ticker_pattern = rf"\b{re.escape(c_ticker)}\b"
                ticker_matches = len(re.findall(ticker_pattern, extracted_text))
                if ticker_matches > 0:
                    score += 30 + (ticker_matches * 5)
                    ev.append(f"Found ticker '{c_ticker}'")

            # Check in filename
            if (c_ticker and re.search(rf"\b{re.escape(c_ticker)}\b", filename, re.IGNORECASE)) or \
               (c_id and re.search(rf"\b{re.escape(c_id)}\b", filename, re.IGNORECASE)) or \
               (c_name and re.search(re.escape(c_name), filename, re.IGNORECASE)):
                score += 25
                ev.append("Matched company identifier in filename")

            if score > best_match_score:
                best_match_score = score
                best_match = comp
                company_evidence = ev

        if best_match and best_match_score >= 30:
            detected_company_id = best_match.get("id")
            detected_company_name = best_match.get("name")
            company_score = best_match_score
        else:
            # Attempt generic extraction from title / cover
            title_match = re.search(
                r"^([A-Z0-9][A-Za-z0-9\s,\.\-&]{2,50}?)\s*(?:[-–—]\s*Annual Report|[-–—]\s*Form 10-K|Annual Report|Form 10-K)",
                extracted_text,
                re.MULTILINE | re.IGNORECASE,
            )
            if title_match:
                candidate = title_match.group(1).strip()
                if len(candidate) > 2 and candidate.lower() not in ["united states", "form", "item", "part"]:
                    detected_company_name = candidate
                    company_evidence.append(f"Extracted header title '{candidate}'")
                    company_score = 25

        # 2. Detect Fiscal Year
        detected_fiscal_year = None
        year_evidence = []
        year_score = 0

        # Pattern 1: Explicit "Fiscal Year Ended ... 202X" or "For the Year Ended ... 202X"
        fy_match = re.search(
            r"(?:Fiscal\s+Year\s+Ended|Year\s+Ended|Period\s+Ended|Form\s+10-K|Annual\s+Report)[^\n\r\d]{1,60}\b(20[12]\d)\b",
            combined_text,
            re.IGNORECASE,
        )
        if fy_match:
            detected_fiscal_year = int(fy_match.group(1))
            year_evidence.append(f"Found explicit fiscal period match: {detected_fiscal_year}")
            year_score += 40

        # Pattern 2: "December 31, 202X" or "Sept 30, 202X" on cover
        if not detected_fiscal_year:
            date_match = re.search(
                r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*(20[12]\d)",
                extracted_text[:1500],
                re.IGNORECASE,
            )
            if date_match:
                detected_fiscal_year = int(date_match.group(1))
                year_evidence.append(f"Found statement ending date year: {detected_fiscal_year}")
                year_score += 30

        # Pattern 3: Filename year e.g. 2025
        if not detected_fiscal_year:
            fn_year_match = re.search(r"\b(20[12]\d)\b", filename)
            if fn_year_match:
                detected_fiscal_year = int(fn_year_match.group(1))
                year_evidence.append(f"Extracted year {detected_fiscal_year} from filename")
                year_score += 20

        # 3. Detect Period Type
        detected_period_type = "FY"
        period_evidence = []
        if re.search(r"\b(?:10-Q|quarterly\s+report|first\s+quarter|three\s+months\s+ended)\b", combined_text, re.IGNORECASE):
            if re.search(r"\b(?:first\s+quarter|Q1)\b", combined_text, re.IGNORECASE):
                detected_period_type = "Q1"
            elif re.search(r"\b(?:second\s+quarter|Q2)\b", combined_text, re.IGNORECASE):
                detected_period_type = "Q2"
            elif re.search(r"\b(?:third\s+quarter|Q3)\b", combined_text, re.IGNORECASE):
                detected_period_type = "Q3"
            elif re.search(r"\b(?:fourth\s+quarter|Q4)\b", combined_text, re.IGNORECASE):
                detected_period_type = "Q4"
            else:
                detected_period_type = "Q1"
            period_evidence.append(f"Identified quarterly filing ({detected_period_type})")
        else:
            detected_period_type = "FY"
            period_evidence.append("Identified annual filing (FY / Form 10-K)")

        # Determine confidence
        total_score = company_score + year_score
        if company_score >= 30 and year_score >= 30:
            confidence = "high"
        elif company_score >= 20 or year_score >= 20:
            confidence = "medium"
        else:
            confidence = "low"

        evidence_items = company_evidence + year_evidence + period_evidence
        evidence_summary = " | ".join(evidence_items) if evidence_items else "No strong metadata detected"

        return {
            "detected_company_id": detected_company_id,
            "detected_company_name": detected_company_name,
            "detected_fiscal_year": detected_fiscal_year,
            "detected_period_type": detected_period_type,
            "confidence": confidence,
            "evidence": evidence_summary,
            "preview_snippet": preview_snippet,
        }
