#!/usr/bin/env python3
"""
Comprehensive deal data extraction from PDFs into structured JSON.
Captures all financial metrics, budgets, financing, returns, unit mix, operating metrics.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class ComprehensiveDealExtractor:
    """Extract comprehensive deal data from PDF text."""

    def __init__(self):
        self.deal = {}

    def extract(self, text: str, filename: str) -> Optional[Dict]:
        """Extract all deal data from PDF text."""
        self.text = text

        deal = {
            "source_file": filename,
            "metadata": {
                "extraction_date": self._get_current_date(),
                "pages": len(re.findall(r"\[Page \d+\]", text)) or "unknown",
            },
            "property_information": self._extract_property_info(),
            "financial_summary": self._extract_financial_summary(),
            "equity_breakdown": self._extract_equity_breakdown(),
            "construction_financing": self._extract_construction_financing(),
            "permanent_financing": self._extract_permanent_financing(),
            "operating_assumptions": self._extract_operating_assumptions(),
            "rent_growth_assumptions": self._extract_rent_growth(),
            "exit_assumptions": self._extract_exit_assumptions(),
            "unit_mix": self._extract_unit_mix(),
            "other_income": self._extract_other_income(),
            "operating_expenses": self._extract_operating_expenses(),
            "project_returns": self._extract_project_returns(),
            "investor_returns": self._extract_investor_returns(),
            "incentives": self._extract_incentives(),
            "financing_rates_summary": self._extract_financing_rates_summary(),
        }

        # Only return if we found significant deal data
        if deal["property_information"]["project_name"] and (
            deal["construction_financing"]["loan_amount_numeric"]
            or deal["unit_mix"]
        ):
            return deal
        return None

    # ========== PROPERTY INFORMATION ==========
    def _extract_property_info(self) -> Dict:
        """Extract basic property information."""
        # Extract project name carefully
        proj_name = self._find_pattern(
            self.text,
            [
                r"Property Name\s+([A-Za-z\s,\-\.0-9]+?)(?:\s+Uses|\s+Location|\n)",
                r"Property Name\s+([A-Za-z\s,\-\.0-9]+)$",
            ],
        )
        if proj_name:
            proj_name = proj_name.split(" Uses")[0].strip()

        return {
            "project_name": proj_name,
            "location": self._find_pattern(
                self.text, [r"Location\s*:\s*([^\n]+)", r"Location\s+([A-Za-z\s]+?)(?:\n|Uses)"]
            ),
            "street_address": self._find_pattern(self.text, [r"Street Address\s+([^\n]+)"]),
            "city": self._extract_city(),
            "state": self._extract_state(),
            "zip": self._find_pattern(self.text, [r"\b(\d{5})\b"]),
            "total_units": self._extract_number(self.text, r"Total Units.*?(\d+)"),
            "rentable_sf": self._extract_number(
                self.text, r"Total.*?Rentable.*?(\d+(?:,\d+)*)\s*sf"
            ),
            "gross_sf": self._extract_number(self.text, r"Total Gross SF\s+(\d+(?:,\d+)*)"),
            "lot_size_acres": self._extract_number(self.text, r"Lot Size.*?(\d+(?:\.\d+)?)\s*ac"),
            "lot_size_sf": self._extract_number(self.text, r"Lot Size.*?(\d+(?:,\d+)*)\s*sf"),
            "density_units_per_acre": self._extract_number(
                self.text, r"Density.*?(\d+(?:\.\d+)?)"
            ),
            "land_value_per_sf": self._extract_money(
                self.text, r"Land Value per SF\s+\$\s*([\d,\.]+)"
            ),
            "land_value_per_unit": self._extract_money(
                self.text, r"Land Value per Unit\s+\$\s*([\d,\.]+)"
            ),
        }

    # ========== FINANCIAL SUMMARY ==========
    def _extract_financial_summary(self) -> Dict:
        """Extract complete sources & uses breakdown."""
        summary = {
            "total_cost": self._extract_cost_line(self.text, "Total Uses"),
            "land_costs": self._extract_cost_line(self.text, "Total Land Costs"),
            "hard_costs": self._extract_cost_line(self.text, "Total Hard Costs"),
            "soft_costs": self._extract_cost_line(self.text, "Total Soft Costs"),
            "financing_costs": self._extract_cost_line(self.text, "Total Financing"),
            "sources_total": self._extract_cost_line(self.text, "Total Sources"),
            "equity_total": self._extract_cost_line(self.text, "Total Equity"),
        }
        return summary

    def _extract_cost_line(self, text: str, label: str) -> Dict:
        """Extract a complete cost line with $, %, $/RSF, $/GSF, $/unit."""
        pattern = label + r".*?(\d+\.\d+)%\s+\$\s*([\d,\.]+)\s+\$\s*([\d,\.]+)\s+\$\s*([\d,\.]+)\s+\$\s*([\d,]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "percent": f"{match.group(1)}%",
                "per_rsf": f"${match.group(2)}",
                "per_gsf": f"${match.group(3)}",
                "per_unit": f"${match.group(4)}",
                "total": self._format_money(float(match.group(5).replace(",", ""))),
                "total_numeric": float(match.group(5).replace(",", "")),
            }
        return {
            "percent": None,
            "per_rsf": None,
            "per_gsf": None,
            "per_unit": None,
            "total": None,
            "total_numeric": None,
        }

    # ========== EQUITY BREAKDOWN ==========
    def _extract_equity_breakdown(self) -> Dict:
        """Extract investor equity breakdown."""
        equity = {}

        # Look for sponsor, common equity, preferred equity patterns
        investors = [
            ("sponsor", r"Sponsor\s*\(common eq\)\s+([\d.]+)%.*?\$\s*([\d,\.]+)"),
            ("common_equity_lps", r"Common Equity LPs\s+([\d.]+)%.*?\$\s*([\d,\.]+)"),
            ("preferred_equity_lps", r"Preferred Equity LPs\s+([\d.]+)%.*?\$\s*([\d,\.]+)"),
        ]

        for investor_type, pattern in investors:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                equity[investor_type] = {
                    "percent": f"{match.group(1)}%",
                    "amount": self._format_money(float(match.group(2).replace(",", ""))),
                    "amount_numeric": float(match.group(2).replace(",", "")),
                }

        return equity

    # ========== CONSTRUCTION FINANCING ==========
    def _extract_construction_financing(self) -> Dict:
        """Extract construction loan terms and rates."""
        return {
            "loan_type": self._find_pattern(self.text, [r"Type of Loan\s+([A-Za-z]+)"]),
            "loan_amount": self._extract_money(
                self.text, r"Loan Proceeds\s+\$\s*([\d,\.]+)"
            ),
            "loan_amount_numeric": self._extract_money_numeric(
                self.text, r"Loan Proceeds\s+\$\s*([\d,\.]+)"
            ),
            "ltc_percent": self._extract_percent(
                self.text, r"Loan to Cost\s+([\d.]+)%?"
            ),
            "loan_term_months": self._extract_number(
                self.text, r"Term\s+(\d+)\s+Months?"
            ),
            "loan_term_years": self._extract_number(
                self.text, r"Term\s+\d+\s+Months?\s+([\d.]+)\s+Years?"
            ),
            "amortization_months": self._extract_number(
                self.text, r"Amortization Term\s+(\d+)\s+Months?"
            ),
            "amortization_years": self._extract_number(
                self.text, r"Amortization Term\s+\d+\s+Months?\s+(\d+)\s+Years?"
            ),
            "interest_only_months": self._extract_number(
                self.text, r"Interest Only Term\s+(\d+)\s+Months?"
            ),
            "interest_rate_percent": self._extract_percent(
                self.text, r"Interest Rate\s+([\d.]+)%?"
            ),
            "io_payment_monthly": self._extract_money(
                self.text, r"I/O Pmt\s+\$\s*([\d,\.]+)"
            ),
            "pi_payment_monthly": self._extract_money(
                self.text, r"P&I Pmt\s+\$\s*([\d,\.]+)"
            ),
            "io_dscr": self._extract_number(self.text, r"I/O DSCR.*?(\d+\.\d+)"),
            "pi_dscr": self._extract_number(self.text, r"P&I DSCR.*?(\d+\.\d+)"),
            "yield_on_debt": self._extract_percent(
                self.text, r"Yield on Debt.*?([\d.]+)%?"
            ),
        }

    # ========== PERMANENT FINANCING ==========
    def _extract_permanent_financing(self) -> Dict:
        """Extract permanent loan terms."""
        return {
            "refinance": self._find_pattern(
                self.text, [r"PIK Refinance \(Yes/No\)\s+([A-Za-z]+)"]
            ),
            "refinance_month": self._extract_number(
                self.text, r"Refinance Month\s+Month\s+(\d+)"
            ),
            "loan_type": self._find_pattern(
                self.text,
                [
                    r"Financing Assumptions: Permanent Loan.*?([A-Za-z\s]+?)(?:\n|$)",
                ],
            ),
            "loan_amount": self._extract_money(
                self.text, r"LTV Loan Amount\s+\$\s*([\d,\.]+)"
            ),
            "loan_amount_numeric": self._extract_money_numeric(
                self.text, r"LTV Loan Amount\s+\$\s*([\d,\.]+)"
            ),
            "ltv_percent": self._extract_percent(
                self.text, r"Loan-to-Value\s+([\d.]+)%?"
            ),
            "loan_term_months": self._extract_number(
                self.text, r"(?:Permanent|Refinance).*?Term\s+(\d+)\s+Months?"
            ),
            "loan_term_years": self._extract_number(
                self.text, r"(?:Permanent|Refinance).*?Term\s+\d+\s+Months?\s+([\d.]+)\s+Years?"
            ),
            "amortization_months": self._extract_number(
                self.text, r"(?:Permanent|Refinance).*?Amortization.*?(\d+)\s+Months?"
            ),
            "amortization_years": self._extract_number(
                self.text, r"(?:Permanent|Refinance).*?Amortization.*?\d+\s+Months?\s+(\d+)\s+Years?"
            ),
            "interest_rate_percent": self._extract_percent(
                self.text, r"(?:Permanent|Refinance).*?Interest Rate\s+([\d.]+)%?"
            ),
            "dscr_requirement": self._extract_number(
                self.text, r"DSCR Requirement\s+([\d.]+)"
            ),
            "dscr_loan_amount": self._extract_money(
                self.text, r"DSCR Loan Amount\s+\$\s*([\d,\.]+)"
            ),
            "refinance_cost_percent": self._extract_percent(
                self.text, r"Cost of Refinance\s+([\d.]+)%?"
            ),
            "yield_on_debt": self._extract_percent(
                self.text, r"(?:Permanent|Refinance).*?Yield on Debt.*?([\d.]+)%?"
            ),
        }

    # ========== OPERATING ASSUMPTIONS ==========
    def _extract_operating_assumptions(self) -> Dict:
        """Extract operating assumptions."""
        return {
            "analysis_start_date": self._find_pattern(
                self.text, [r"Analysis Start Date.*?(\d+/\d+/\d+)"]
            ),
            "construction_start_date": self._find_pattern(
                self.text, [r"Construction Start.*?(\d+/\d+/\d+)"]
            ),
            "construction_duration_months": self._extract_number(
                self.text, r"Construction Term.*?(\d+)\s+Months?"
            ),
            "stabilized_month": self._find_pattern(
                self.text, [r"Stabilized Month\s+([A-Za-z]+)"]
            ),
            "first_full_stabilized_year": self._extract_number(
                self.text, r"First Full Stabilized Year\s+Year\s+(\d+)"
            ),
            "first_units_month": self._extract_number(
                self.text, r"First Units\s+[A-Za-z]+\s+(\d+)"
            ),
            "hold_period_years": self._extract_number(
                self.text, r"Hold Period\s+(\d+)\s+Years?"
            ),
            "general_vacancy_percent": self._extract_percent(
                self.text, r"General Vacancy\s+([\d.]+)%?"
            ),
            "operating_expense_ratio_percent": self._extract_percent(
                self.text, r"Operating Expense Ratio.*?\(Includes.*?\)\s+([\d.]+)%?"
            ),
            "break_even_occupancy_percent": self._extract_percent(
                self.text, r"Break Even Occupancy.*?\(Excludes.*?\)\s+([\d.]+)%?"
            ),
        }

    # ========== RENT GROWTH ==========
    def _extract_rent_growth(self) -> Dict:
        """Extract annual rent growth assumptions."""
        growth = {}
        for year in range(1, 7):
            pattern = f"Year {year}\\s+([\\d.]+)%"
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                growth[f"year_{year}_percent"] = f"{match.group(1)}%"
        return growth

    # ========== EXIT ASSUMPTIONS ==========
    def _extract_exit_assumptions(self) -> Dict:
        """Extract exit/sale assumptions."""
        return {
            "exit_cap_rate": self._extract_percent(
                self.text, r"Exit Cap Rate\s+([\d.]+)%?"
            ),
            "gross_sale_price": self._extract_money(
                self.text, r"Gross Sale Price\s+\$\s*([\d,\.]+)"
            ),
            "gross_sale_price_numeric": self._extract_money_numeric(
                self.text, r"Gross Sale Price\s+\$\s*([\d,\.]+)"
            ),
            "transaction_costs_percent": self._extract_percent(
                self.text, r"Trans\. Costs.*?\s+([\d.]+)%?"
            ),
            "market_value": self._extract_money(
                self.text, r"Market Value\s+\$\s*([\d,\.]+)"
            ),
            "market_value_numeric": self._extract_money_numeric(
                self.text, r"Market Value\s+\$\s*([\d,\.]+)"
            ),
        }

    # ========== UNIT MIX ==========
    def _extract_unit_mix(self) -> List[Dict]:
        """Extract detailed unit type breakdown."""
        units = []

        # Look for unit breakdown table
        unit_pattern = r"([A-Za-z\s]+?)\s+(\d+)\s+([\d.]+)%\s+(\d+)\s+(\d+(?:,\d+)*)\s+([\d.]+)%\s+\$\s*([\d.]+)\s+\$\s*(\d+(?:,\d+)*)\s+\$\s*(\d+(?:,\d+)*)"

        for match in re.finditer(unit_pattern, self.text):
            unit = {
                "unit_type": match.group(1).strip(),
                "total_units": int(match.group(2)),
                "percent_of_total": f"{match.group(3)}%",
                "avg_unit_rsf": int(match.group(4)),
                "total_sf": int(match.group(5).replace(",", "")),
                "percent_of_sf": f"{match.group(6)}%",
                "rent_per_sf": f"${match.group(7)}",
                "avg_rent_monthly": f"${match.group(8).replace(',', '')}",
                "annual_rent": f"${match.group(9).replace(',', '')}",
            }
            if unit["total_units"] > 0:
                units.append(unit)

        return units if units else None

    # ========== OTHER INCOME ==========
    def _extract_other_income(self) -> Dict:
        """Extract other income sources."""
        return {
            "utility_reimbursements": self._extract_other_income_item(
                self.text, r"Utility Reimbursements\s+\$\s*(\d+)", r"(\d+)\s+\$\s*(\d+)"
            ),
            "parking_income": self._extract_other_income_item(
                self.text, r"Parking Income\s+#.*?:\s+(\d+)", r"(\d+)\s+\$\s*(\d+)"
            ),
            "pet_rent": self._extract_other_income_item(
                self.text, r"Pet Rent\s+%.*?:\s+([\d.]+)%", r"([\d.]+)%.*?\$\s*(\d+)"
            ),
        }

    def _extract_other_income_item(self, text: str, *patterns) -> Dict:
        """Extract other income detail."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {"value": match.group(1), "unit_rate": match.group(2) if len(match.groups()) > 1 else None}
        return None

    # ========== OPERATING EXPENSES ==========
    def _extract_operating_expenses(self) -> Dict:
        """Extract operating expense categories."""
        expenses = {}

        expense_types = [
            ("real_estate_taxes", r"Real Estate Tax"),
            ("insurance", r"Insurance"),
            ("utilities", r"Utilities"),
            ("repairs_maintenance", r"R&M"),
            ("general_admin", r"G&A"),
            ("management_fee", r"Management Fee"),
            ("marketing", r"Marketing"),
            ("salaries", r"Salaries"),
            ("licenses_permits", r"Licenses"),
            ("reserves_replacement", r"Reserves"),
        ]

        for exp_type, pattern in expense_types:
            match = re.search(pattern + r"\s+\$\s*([\d,\.]+)", self.text, re.IGNORECASE)
            if match:
                expenses[exp_type] = self._format_money(float(match.group(1).replace(",", "")))

        return expenses if expenses else None

    # ========== PROJECT RETURNS ==========
    def _extract_project_returns(self) -> Dict:
        """Extract project return metrics."""
        return {
            "unlevered_irr_percent": self._extract_percent(
                self.text, r"Unlevered IRR.*?([\d.]+)%?"
            ),
            "unlevered_equity_multiple": self._extract_number(
                self.text, r"Unlevered.*?Multiple\s+([\d.]+)x?"
            ),
            "levered_irr_percent": self._extract_percent(
                self.text, r"Levered IRR.*?([\d.]+)%?"
            ),
            "levered_equity_multiple": self._extract_number(
                self.text, r"Levered.*?Multiple\s+([\d.]+)x?"
            ),
            "yield_on_total_project_costs": self._extract_percent(
                self.text, r"Yield on Total Project Costs\s+([\d.]+)%?"
            ),
            "yield_on_total_project_costs_incentive_adjusted": self._extract_percent(
                self.text, r"Yield on Total Project Costs - Incentive.*?([\d.]+)%?"
            ),
            "cash_on_cash_return": self._extract_percent(
                self.text, r"Cash on Cash Return\s+([\d.]+)%?"
            ),
        }

    # ========== INVESTOR RETURNS ==========
    def _extract_investor_returns(self) -> Dict:
        """Extract LP and preferred equity returns."""
        return {
            "lp_irr_percent": self._extract_percent(
                self.text, r"LP IRR.*?([\d.]+)%?"
            ),
            "lp_equity_multiple": self._extract_number(
                self.text, r"LP.*?Multiple\s+([\d.]+)x?"
            ),
            "lp_cash_flow_profit": self._extract_money(
                self.text, r"LP Cash Flow \(Profit\)\s+\$\s*([\d,\.]+)"
            ),
            "preferred_equity_irr": self._extract_percent(
                self.text, r"Preferred.*?IRR.*?([\d.]+)%?"
            ),
            "preferred_equity_yield": self._extract_percent(
                self.text, r"Preferred.*?Yield.*?([\d.]+)%?"
            ),
        }

    # ========== INCENTIVES ==========
    def _extract_incentives(self) -> Dict:
        """Extract incentive fund information."""
        incentives = {}

        # Look for incentive fund line
        match = re.search(r"INCENTIVE FUNDS\s+-?\s*\$?\s*([\d,\.]+)", self.text)
        if match:
            incentives["total_incentive_amount"] = self._format_money(
                float(match.group(1).replace(",", ""))
            )

        # Look for reimbursement schedule
        for installment in ["First", "Second", "Third"]:
            pattern = f"{installment} Installment Reimbursement.*?\\$\\s*([\\d,\\.]+)"
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                incentives[f"{installment.lower()}_installment"] = {
                    "amount": self._format_money(float(match.group(1).replace(",", ""))),
                    "timing": self._find_pattern(self.text, [f"Month of {installment} Installment\\s+Month\\s+(\\d+)"]),
                }

        return incentives if incentives else None

    # ========== FINANCING RATES SUMMARY ==========
    def _extract_financing_rates_summary(self) -> Dict:
        """Extract and categorize all financing rates by type."""
        return {
            "construction_rates": {
                "interest_rate_percent": self._extract_percent(
                    self.text, r"(?:Construction).*?Interest Rate\s+([\d.]+)%?"
                ),
                "sofr_component": self._find_pattern(
                    self.text, [r"SOFR\s*\+\s*(\d+)(?:\s*bps)?"]
                ),
                "all_in_rate_percent": self._extract_percent(
                    self.text, r"(?:Construction).*?All.in.*?([\d.]+)%?"
                ),
            },
            "permanent_rates": {
                "interest_rate_percent": self._extract_percent(
                    self.text, r"(?:Permanent|Refinance).*?Interest Rate\s+([\d.]+)%?"
                ),
                "sofr_component": self._find_pattern(
                    self.text, [r"(?:Permanent|Refinance).*?SOFR\s*\+\s*(\d+)"]
                ),
                "all_in_rate_percent": self._extract_percent(
                    self.text, r"(?:Permanent|Refinance).*?All.in.*?([\d.]+)%?"
                ),
            },
        }

    # ========== HELPER METHODS ==========
    def _find_pattern(self, text: str, patterns: List[str]) -> Optional[str]:
        """Try multiple regex patterns."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(1) if match.groups() else match.group(0)
                return result.strip() if result else None
        return None

    def _extract_number(self, text: str, pattern: str) -> Optional[float]:
        """Extract numeric value."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except:
                return None
        return None

    def _extract_percent(self, text: str, pattern: str) -> Optional[str]:
        """Extract percentage."""
        num = self._extract_number(text, pattern)
        return f"{num}%" if num else None

    def _extract_money(self, text: str, pattern: str) -> Optional[str]:
        """Extract money value formatted."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1).replace(",", "")
            try:
                val = float(amount)
                return self._format_money(val)
            except:
                return amount
        return None

    def _extract_money_numeric(self, text: str, pattern: str) -> Optional[float]:
        """Extract money as numeric value."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                val_str = match.group(1).replace(",", "").replace(" ", "")
                return float(val_str)
            except Exception as e:
                return None
        return None

    def _format_money(self, value: float) -> str:
        """Format numeric value as money."""
        if value >= 1000000:
            return f"${value / 1000000:,.1f}M"
        elif value >= 1000:
            return f"${value:,.0f}"
        else:
            return f"${value:,.2f}"

    def _extract_city(self) -> Optional[str]:
        """Extract city from City, State, Zip line."""
        match = re.search(
            r"City,\s*State,\s*Zip\s+([^,]+),\s*([A-Z]{2})\s+(\d{5})", self.text
        )
        return match.group(1).strip() if match else None

    def _extract_state(self) -> Optional[str]:
        """Extract state."""
        match = re.search(r"City,\s*State,\s*Zip\s+[^,]+,\s*([A-Z]{2})", self.text)
        return match.group(1) if match else None

    def _get_current_date(self) -> str:
        """Get current date."""
        from datetime import datetime

        return datetime.now().isoformat().split("T")[0]


def main():
    files_path = Path("/Users/bencolella/Desktop/SWG/SWAI Project/files")

    if not files_path.exists():
        print(f"Files path not found: {files_path}")
        return

    print(f"\n📋 Extracting comprehensive deal data from PDFs...\n")

    deals = {}
    extractor = ComprehensiveDealExtractor()

    for pdf_file in sorted(files_path.rglob("*.pdf")):
        # Skip market studies
        rel_path = str(pdf_file.relative_to(files_path)).lower()
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

            deal = extractor.extract(text, pdf_file.name)

            if deal:
                # Get deal name from extracted data or filename
                deal_name = deal["property_information"]["project_name"]
                if not deal_name:
                    name_from_file = re.search(
                        r"_([A-Za-z\s]+?)\s*-\s*vSW|_([A-Za-z\s]+?)\.xlsx",
                        pdf_file.name,
                    )
                    if name_from_file:
                        deal_name = (name_from_file.group(1) or name_from_file.group(2)).strip()
                        deal["property_information"]["project_name"] = deal_name

                if deal_name:
                    deals[deal_name] = deal
                    print(f"  ✓ Extracted: {deal_name}")
            else:
                print(f"  ⊘ No deal data found")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print(f"\n✓ Extracted {len(deals)} deals\n")

    # Save to JSON
    output_file = files_path.parent / "deals_database_comprehensive.json"
    with open(output_file, "w") as f:
        json.dump(deals, f, indent=2)

    print(f"✓ Saved to {output_file}")
    print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB\n")

    # Show sample
    if deals:
        first_deal = list(deals.values())[0]
        print("Sample categories extracted:")
        for key in first_deal.keys():
            print(f"  ✓ {key}")


if __name__ == "__main__":
    main()
