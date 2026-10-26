"""
XBRL Parser and Accounting Identity Verification Engine.
Parses SEC Form 10-K/10-Q XBRL filings, checks formal double-entry conservation laws,
and extracts structured disclosure footnotes for causal knowledge graph construction.
"""

from typing import Dict, Any, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("XBRLParser")

class XBRLAccountingParser:
    """
    Parses GAAP XBRL filings and enforces double-entry conservation identities.
    """
    def __init__(self, filing_data: Dict[str, Any]):
        self.metadata = filing_data.get("filing_metadata", {})
        self.balance_sheet = filing_data.get("balance_sheet_xbrl", {})
        self.income_statement = filing_data.get("income_statement_xbrl", {})
        self.footnotes = filing_data.get("disclosure_footnotes", [])
        
    def verify_gaap_conservation_identities(self) -> Dict[str, Any]:
        """
        Formally verifies arithmetic conservation laws:
        1. Balance Sheet: Total Assets == Total Liabilities + Stockholders' Equity
        2. Gross Margin: Gross Profit == Revenues - Cost of Goods Sold
        3. Operating Profit: Operating Income == Gross Profit - Operating Expenses
        """
        results = {}
        
        # 1. Fundamental Accounting Identity
        assets = self.balance_sheet.get("TotalAssets", 0.0)
        liabilities = self.balance_sheet.get("TotalLiabilities", 0.0)
        equity = self.balance_sheet.get("TotalStockholdersEquity", 0.0)
        bs_discrepancy = abs(assets - (liabilities + equity))
        results["balance_sheet_balanced"] = bs_discrepancy < 1e-3
        results["balance_sheet_delta"] = bs_discrepancy

        # 2. Gross Margin Identity
        rev = self.income_statement.get("Revenues", 0.0)
        cogs = self.income_statement.get("CostOfGoodsSold", 0.0)
        gp = self.income_statement.get("GrossProfit", 0.0)
        gp_discrepancy = abs(gp - (rev - cogs))
        results["gross_profit_valid"] = gp_discrepancy < 1e-3
        results["gross_profit_delta"] = gp_discrepancy

        # 3. Operating Income Identity
        opex = self.income_statement.get("OperatingExpenses", 0.0)
        opinc = self.income_statement.get("OperatingIncome", 0.0)
        opinc_discrepancy = abs(opinc - (gp - opex))
        results["operating_income_valid"] = opinc_discrepancy < 1e-3
        results["operating_income_delta"] = opinc_discrepancy

        # Overall Status
        results["all_identities_valid"] = (
            results["balance_sheet_balanced"] and
            results["gross_profit_valid"] and
            results["operating_income_valid"]
        )
        return results

    def extract_xbrl_nodes(self) -> List[Dict[str, Any]]:
        """
        Converts balance sheet, income statement, and footnote disclosures into graph nodes.
        """
        nodes = []
        
        # Balance Sheet line items
        for concept, val in self.balance_sheet.items():
            nodes.append({
                "node_id": f"XBRL_{concept}",
                "node_type": "XBRL_BalanceSheet",
                "concept": concept,
                "value": float(val),
                "statement": "Consolidated Balance Sheet",
                "source": "Form 10-Q"
            })
            
        # Income Statement line items
        for concept, val in self.income_statement.items():
            nodes.append({
                "node_id": f"XBRL_{concept}",
                "node_type": "XBRL_IncomeStatement",
                "concept": concept,
                "value": float(val),
                "statement": "Consolidated Statement of Operations",
                "source": "Form 10-Q"
            })
            
        # Footnote schedules & quantitative commitments
        for fn in self.footnotes:
            note_id = fn.get("note_id", "Note")
            title = fn.get("title", "")
            paragraph = fn.get("paragraph", 1)
            raw_text = fn.get("text", "")
            
            # Master footnote node
            nodes.append({
                "node_id": f"FN_{note_id.replace(' ', '_')}",
                "node_type": "XBRL_DisclosureFootnote",
                "concept": note_id,
                "title": title,
                "paragraph": paragraph,
                "text": raw_text,
                "source": f"Form 10-Q, {note_id}"
            })
            
            # Specific extracted commitments
            for fact_k, fact_v in fn.get("extracted_facts", {}).items():
                nodes.append({
                    "node_id": f"FACT_{note_id.replace(' ', '_')}_{fact_k}",
                    "node_type": "XBRL_FootnoteFact",
                    "concept": fact_k,
                    "value": fact_v,
                    "parent_note": note_id,
                    "source": f"Form 10-Q, {note_id}, Paragraph {paragraph}"
                })
                
        return nodes

    def get_footnote_by_id(self, note_id: str) -> Dict[str, Any]:
        """Returns the specific footnote dict matching note_id."""
        for fn in self.footnotes:
            if fn.get("note_id") == note_id:
                return fn
        return {}
