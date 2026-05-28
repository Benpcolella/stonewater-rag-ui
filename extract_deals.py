#!/usr/bin/env python3
"""
Extract structured deal data from PDFs into a comprehensive JSON database.
Handles: deal name, location, units, costs, financing, returns, timelines.
Leaves market studies in RAG (less standardizable).
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class DealExtractor:
    """Extract deal data from text into structured format."""

    def __init__(self):
        self.deals = {}

    def extract_from_text(self, text: str, filename: str) -> Optional[Dict]:
        """Extract deal data from PDF text."""

        deal = {
            "source_file": filename,
            "project_info": self._extract_project_info(text),
            "location": self._extract_location(text),
            "units": self._extract_units(text),
            "costs": self._extract_costs(text),
            "financing": self._extract_financing(text),
            "returns": self._extract_returns(text),
            "timeline": self._extract_timeline(text),
            "occupancy_market": self._extract_occupancy_market(text),
        }

        # Only return if we found meaningful deal data
        if deal["project_info"]["name"] or deal["financing"]["loan_amount"]:
            return deal
        return None

    def _extract_project_info(self, text: str) -> Dict:
        """Extract project name, type, phases."""
        name = self._find_pattern(
            text,
            [
                r"Property Name\s+([A-Za-z\s,\-\.]+?)\s+Uses",
                r"Property Name\s+([A-Za-z\s,\-\.]+?)(?:\n|$)",
                r"^([A-Z][^,\n]*(?:Phase|Project)[^,\n]*?)(?:\n|Uses)",
            ],
        )
        return {
            "name": name.strip() if name else None,
            "type": self._find_pattern(
                text, [
                    r"Type of\s+Loan\s+([A-Za-z\s]+?)(?:\n|$)",
                    r"(?:Development|Residential|Mixed-Use)"
                ]
            ),
            "phase": self._find_pattern(text, [r"Phase\s+(\d+|[IVX]+|[A-Z])"]),
        }

    def _extract_location(self, text: str) -> Dict:
        """Extract city, state, zip, market."""
        # Try to extract City, State, Zip line
        city_match = re.search(r"City,\s*State,\s*Zip\s+([^,]+),\s*([A-Z]{2})\s+(\d{5})", text, re.IGNORECASE)
        city = state = zip_code = None
        if city_match:
            city, state, zip_code = city_match.groups()

        return {
            "city": city or self._find_pattern(
                text,
                [
                    r"(?:City|Location):\s*([^,\n]+)",
                    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2})",
                ],
            ),
            "state": state or self._find_pattern(text, [r"\b([A-Z]{2})\s+\d{5}\b"]),
            "zip": zip_code or self._find_pattern(text, [r"\b(\d{5})\b"]),
            "market": self._find_pattern(
                text,
                [r"(?:Location|Market|Area):\s*([A-Za-z\s]+?)(?:\n|Street)", r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:County|Area|Market)"],
            ),
        }

    def _extract_units(self, text: str) -> Dict:
        """Extract unit count, unit mix, rentable SF."""
        # Look for "Total Units | Rentable SF" pattern
        units_match = re.search(r"Total Units.*?(\d+)\s+Units?\s+(\d+(?:,\d+)*)\s*sf", text, re.IGNORECASE)
        unit_count = None
        rentable_sf = None
        if units_match:
            unit_count = int(units_match.group(1))
            rentable_sf = int(units_match.group(2).replace(",", ""))

        gross_sf_match = re.search(r"Total Gross SF\s+(\d+(?:,\d+)*)\s*sf", text, re.IGNORECASE)
        gross_sf = int(gross_sf_match.group(1).replace(",", "")) if gross_sf_match else None

        # Density pattern
        density_match = re.search(r"Density.*?(\d+(?:\.\d+)?)\s*(?:units?/acre|u/ac)", text, re.IGNORECASE)
        density = float(density_match.group(1)) if density_match else None

        return {
            "total_units": unit_count,
            "unit_types": self._extract_unit_mix(text),
            "rentable_sf": rentable_sf,
            "gross_sf": gross_sf,
            "density_units_per_acre": density,
        }

    def _extract_costs(self, text: str) -> Dict:
        """Extract total cost, hard/soft costs, cost per unit."""
        # Look for "Total Uses" line which contains total cost
        total_match = re.search(r"Total Uses.*?100\.0%\s+\$\s*(\d+(?:\.\d+)?)\s+\$\s*(\d+(?:\.\d+)?)\s+\$\s*([\d,]+(?:\.\d+)?)", text)
        total_cost = None
        total_numeric = None
        if total_match:
            try:
                total_numeric = float(total_match.group(3).replace(",", ""))
                total_cost = self._format_money(total_numeric)
            except:
                pass

        # Hard costs: "Total Hard Costs 74.2% $ 238.22..."
        hard_match = re.search(r"Total Hard Costs\s+\d+\.\d+%\s+\$\s*(\d+(?:\.\d+)?)", text)
        hard_numeric = float(hard_match.group(1)) if hard_match else None
        hard_cost = self._format_money(hard_numeric) if hard_numeric else None

        # Soft costs
        soft_match = re.search(r"Total Soft Costs\s+\d+\.\d+%\s+\$\s*(\d+(?:\.\d+)?)", text)
        soft_numeric = float(soft_match.group(1)) if soft_match else None
        soft_cost = self._format_money(soft_numeric) if soft_numeric else None

        # Extract unit count for cost per unit
        units_match = re.search(r"Total Units.*?(\d+)\s+Units?", text)
        unit_count = int(units_match.group(1)) if units_match else None

        cost_per_unit = None
        if total_numeric and unit_count:
            cost_per_unit = f"${total_numeric * 1000000 / unit_count:,.0f}"

        return {
            "total_cost": total_cost,
            "total_cost_numeric": total_numeric,
            "hard_costs": hard_cost,
            "hard_costs_percent": self._extract_percent(text, r"Total Hard Costs\s+(\d+(?:\.\d+)?)%"),
            "soft_costs": soft_cost,
            "soft_costs_percent": self._extract_percent(text, r"Total Soft Costs\s+(\d+(?:\.\d+)?)%"),
            "land_cost": self._extract_money(text, r"Total Land Costs\s+\d+\.\d+%\s+\$?\s*([\d,]+(?:\.\d+)?)"),
            "cost_per_unit": cost_per_unit,
            "cost_per_sf": self._extract_money(
                text, r"(?:\$\s*/\s*)?(?:Unit|RSF).*?(\d+(?:\.\d+)?)",
            ),
        }

    def _extract_financing(self, text: str) -> Dict:
        """Extract loan amount, LTC, LTV, rates, terms."""
        # Loan amount pattern: look for "Loan Proceeds" or "Loan Amount"
        loan_match = re.search(r"Loan\s+(?:Proceeds|Amount)\s+\$?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        loan_amount = None
        loan_numeric = None
        if loan_match:
            amount_str = loan_match.group(1).replace(",", "")
            try:
                loan_numeric = float(amount_str)
                loan_amount = self._format_money(loan_numeric)
            except:
                pass

        # LTC pattern
        ltc_match = re.search(r"Loan to Cost\s+(\d+(?:\.\d+)?)\%?", text, re.IGNORECASE)
        ltc_percent = f"{ltc_match.group(1)}%" if ltc_match else None

        # Term patterns
        term_match = re.search(r"Term\s+(\d+)\s+Months?\s+(\d+(?:\.\d+)?)\s+Years?", text, re.IGNORECASE)
        term_months = int(term_match.group(1)) if term_match else None
        term_years = float(term_match.group(2)) if term_match else None

        # Amortization pattern
        amort_match = re.search(r"Amortization Term\s+(\d+)\s+Months?\s+(\d+)\s+Years?", text, re.IGNORECASE)
        amort_months = int(amort_match.group(1)) if amort_match else None
        amort_years = int(amort_match.group(2)) if amort_match else None

        return {
            "loan_amount": loan_amount,
            "loan_amount_numeric": loan_numeric,
            "ltc_percent": ltc_percent,
            "ltv_percent": self._extract_percent(text, r"LTV:\s*(\d+(?:\.\d+)?)%?"),
            "interest_rate": self._find_pattern(
                text,
                [
                    r"Interest\s+Rate:\s*(\d+\.\d+%)",
                    r"(SOFR\s*\+\s*\d+)",
                ],
            ),
            "sofr_spread": self._find_pattern(text, [r"SOFR\s*\+\s*(\d+)\s*(?:bps|basis)"]),
            "all_in_rate": self._find_pattern(
                text, [r"All[- ]?in\s+(?:rate|Rate):\s*(\d+\.\d+%)"]
            ),
            "loan_term_months": term_months,
            "loan_term_years": term_years,
            "amortization_months": amort_months,
            "amortization_years": amort_years,
            "io_period_months": self._extract_number(text, r"Interest Only Term\s+(\d+)\s+Months?"),
            "facility_type": self._find_pattern(
                text,
                [
                    r"Type of Loan\s+([A-Za-z\s]+?)(?:\n|$)",
                ],
            ),
        }

    def _extract_returns(self, text: str) -> Dict:
        """Extract IRR, CoC, equity, yield."""
        # Equity contribution pattern: "TOTAL Equity Contribution $ 29,608,800"
        equity_match = re.search(r"TOTAL\s+Equity\s+Contribution\s+\$\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        equity_numeric = None
        equity_str = None
        if equity_match:
            equity_numeric = float(equity_match.group(1).replace(",", ""))
            equity_str = self._format_money(equity_numeric)

        return {
            "equity_contribution": equity_str or self._extract_money(
                text, r"(?:Equity|Sponsor)\s+(?:Contribution|Investment):\s*\$?([0-9,.]+M?)"
            ),
            "equity_contribution_numeric": equity_numeric or self._extract_money_numeric(
                text, r"(?:Equity|Sponsor)\s+(?:Contribution|Investment):\s*\$?([0-9,.]+M?)"
            ),
            "irr_percent": self._extract_percent(text, r"IRR:\s*(\d+(?:\.\d+)?)%?"),
            "coc_percent": self._extract_percent(
                text, r"(?:CoC|Cash[- ]on[- ]Cash):\s*(\d+(?:\.\d+)?)%?"
            ),
            "cap_rate": self._extract_percent(text, r"Cap\s+Rate:\s*(\d+(?:\.\d+)?)%?"),
            "yield_percent": self._extract_percent(text, r"Yield:\s*(\d+(?:\.\d+)?)%?"),
        }

    def _extract_timeline(self, text: str) -> Dict:
        """Extract construction timeline, opening date."""
        return {
            "construction_duration_months": self._extract_number(
                text, r"(?:Construction|Build)\s+(?:Duration|Period):\s*(\d+)\s*month"
            ),
            "start_date": self._find_pattern(text, [r"(?:Start|Break[- ]?ground):\s*(\d{1,2}/\d{1,2}/\d{2,4})"]),
            "completion_date": self._find_pattern(
                text, [r"(?:Completion|Opening):\s*(\d{1,2}/\d{1,2}/\d{2,4})"]
            ),
        }

    def _extract_occupancy_market(self, text: str) -> Dict:
        """Extract occupancy, rents, market metrics."""
        return {
            "initial_occupancy_percent": self._extract_percent(
                text, r"(?:Initial|Opening)\s+(?:Occupancy|Occupied):\s*(\d+(?:\.\d+)?)%?"
            ),
            "stabilized_occupancy_percent": self._extract_percent(
                text, r"(?:Stabilized|Target)\s+(?:Occupancy|Occupied):\s*(\d+(?:\.\d+)?)%?"
            ),
            "rent_per_sf": self._extract_money(
                text, r"(?:Rent|Rate|Market\s+Rate):\s*\$?(\d+(?:\.\d+)?)/SF"
            ),
            "market_absorption_rate": self._find_pattern(
                text, [r"(?:Absorption|Absorption\s+Rate):\s*([^\n]+)"]
            ),
        }

    # Helper methods
    def _find_pattern(self, text: str, patterns: List[str]) -> Optional[str]:
        """Try multiple regex patterns, return first match."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(1) if match.groups() else match.group(0)
                return result.strip() if result else None
        return None

    def _extract_number(self, text: str, pattern: str) -> Optional[float]:
        """Extract first number from text."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                num_str = match.group(1).replace(",", "")
                return float(num_str)
            except:
                return None
        return None

    def _extract_percent(self, text: str, pattern: str) -> Optional[str]:
        """Extract percentage value."""
        num = self._extract_number(text, pattern)
        if num:
            return f"{num}%"
        return None

    def _extract_money(self, text: str, pattern: str) -> Optional[str]:
        """Extract money value formatted with $ and M."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1).replace(",", "")
            if "M" in amount.upper():
                return amount
            else:
                try:
                    val = float(amount)
                    if val >= 1000000:
                        return f"${val / 1000000:.1f}M"
                    else:
                        return f"${val:,.0f}"
                except:
                    return amount
        return None

    def _extract_money_numeric(self, text: str, pattern: str) -> Optional[float]:
        """Extract money value as numeric (in millions)."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1).replace(",", "").upper()
            try:
                val = float(amount.replace("M", ""))
                if "M" not in amount and val < 1000:
                    val = val / 1000000  # Convert to millions
                return val
            except:
                return None
        return None

    def _format_money(self, value: float) -> str:
        """Format numeric value as money string."""
        if value >= 1000000:
            return f"${value / 1000000:,.1f}M"
        elif value >= 1000:
            return f"${value:,.0f}"
        else:
            return f"${value:,.2f}"

    def _extract_unit_mix(self, text: str) -> Optional[Dict]:
        """Extract unit type breakdown (if available)."""
        mix = {}
        patterns = {
            "studio": r"(\d+)\s+studio",
            "1br": r"(\d+)\s+(?:one[- ]bed|1\s*br)",
            "2br": r"(\d+)\s+(?:two[- ]bed|2\s*br)",
            "3br": r"(\d+)\s+(?:three[- ]bed|3\s*br)",
        }
        for unit_type, pattern in patterns.items():
            count = self._extract_number(text, pattern)
            if count:
                mix[unit_type] = int(count)
        return mix if mix else None


def extract_deals_from_pdfs(base_path: Path) -> Dict:
    """Scan PDFs and extract deal data."""
    extractor = DealExtractor()
    deals_db = {}

    for pdf_file in sorted(base_path.rglob("*.pdf")):
        # Skip market studies - they go in RAG
        rel_path = str(pdf_file.relative_to(base_path)).lower()
        if "market" in rel_path or "study" in rel_path:
            print(f"⊘ Skipping market study: {pdf_file.name}")
            continue

        print(f"Processing: {pdf_file.name}")

        try:
            import pdfplumber

            text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""

            deal = extractor.extract_from_text(text, pdf_file.name)

            # If we didn't find a name but found financing data, try extracting from filename
            if deal and not deal["project_info"]["name"] and deal["financing"]["loan_amount"]:
                # Try to extract name from filename patterns
                name_from_file = re.search(r"_([A-Za-z\s]+?)\s*-\s*vSW|_([A-Za-z\s]+?)\.xlsx", pdf_file.name)
                if name_from_file:
                    deal["project_info"]["name"] = (name_from_file.group(1) or name_from_file.group(2)).strip()

            if deal and deal["project_info"]["name"]:
                deal_name = deal["project_info"]["name"]
                deals_db[deal_name] = deal
                print(f"  ✓ Extracted: {deal_name}")
            else:
                print(f"  ⊘ No deal data found")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    return deals_db


def main():
    files_path = Path("/Users/bencolella/Desktop/SWG/SWAI Project/files")

    if not files_path.exists():
        print(f"Files path not found: {files_path}")
        return

    print(f"\n📋 Extracting deal data from PDFs...\n")
    deals = extract_deals_from_pdfs(files_path)

    print(f"\n✓ Extracted {len(deals)} deals\n")

    # Save to JSON database
    output_file = files_path.parent / "deals_database.json"
    with open(output_file, "w") as f:
        json.dump(deals, f, indent=2)

    print(f"✓ Saved to {output_file}")
    print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB\n")

    # Show sample
    if deals:
        first_deal = list(deals.values())[0]
        print("Sample extracted deal:")
        print(json.dumps(first_deal, indent=2)[:500] + "...\n")


if __name__ == "__main__":
    main()
