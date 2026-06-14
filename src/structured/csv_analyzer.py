import re

import pandas as pd

from src.config import CSV_PATH


class CSVAnalyzer:
    """Template-based analytical queries over inventory_aging.csv."""

    def __init__(self, csv_path=None):
        self.csv_path = csv_path or CSV_PATH
        self.df = pd.read_csv(self.csv_path)

    def can_answer(self, question: str) -> bool:
        return self._detect_intent(question) is not None

    def answer(self, question: str) -> dict | None:
        intent = self._detect_intent(question)
        if not intent:
            return None

        n = self._extract_top_n(question)

        if intent == "highest_sales_branch":
            branch_sales = self.df.groupby("branch")["sales"].sum()
            top_branch = branch_sales.idxmax()
            top_sales = int(branch_sales.max())
            answer = (
                f"The branch with the highest total sales is **{top_branch}** "
                f"with ${top_sales:,} in sales."
            )
            snippet = branch_sales.sort_values(ascending=False).to_string()

        elif intent == "average_aging":
            avg = self.df["aging_days"].mean()
            answer = (
                f"The average inventory aging across all SKUs is **{avg:.1f} days**."
            )
            snippet = f"mean(aging_days) = {avg:.2f}"

        elif intent == "top_skus_by_aging":
            top = self.df.nlargest(n, "aging_days")[["sku", "branch", "aging_days"]]
            lines = [
                f"{row.sku} ({row.branch}): {int(row.aging_days)} days"
                for row in top.itertuples()
            ]
            answer = f"Top {n} SKUs by aging days:\n" + "\n".join(
                f"{i+1}. {line}" for i, line in enumerate(lines)
            )
            snippet = top.to_string(index=False)

        elif intent == "lowest_sales_branch":
            branch_sales = self.df.groupby("branch")["sales"].sum()
            low_branch = branch_sales.idxmin()
            low_sales = int(branch_sales.min())
            answer = (
                f"The branch with the lowest total sales is **{low_branch}** "
                f"with ${low_sales:,} in sales."
            )
            snippet = branch_sales.sort_values().to_string()

        else:
            return None

        return {
            "answer": answer,
            "sources": [
                {
                    "file": self.csv_path.name,
                    "snippet": snippet,
                    "score": 1.0,
                }
            ],
            "confidence": "high",
            "query_type": "structured",
        }

    def _detect_intent(self, question: str) -> str | None:
        q = question.lower()

        if re.search(r"highest|most|top\b.*\bsales|best.*sales", q) and "branch" in q:
            return "highest_sales_branch"
        if re.search(r"lowest|least|worst.*sales", q) and "branch" in q:
            return "lowest_sales_branch"
        if re.search(r"average|mean", q) and "aging" in q:
            return "average_aging"
        if re.search(r"top\s*\d*|top\b", q) and re.search(r"sku|aging", q):
            return "top_skus_by_aging"
        if "which branch" in q and "sales" in q:
            return "highest_sales_branch"

        return None

    def _extract_top_n(self, question: str) -> int:
        match = re.search(r"top\s*(\d+)", question.lower())
        return int(match.group(1)) if match else 5

    def summary_text(self) -> str:
        """Text summary for RAG fallback over CSV stats."""
        branch_sales = self.df.groupby("branch")["sales"].sum()
        avg_aging = self.df["aging_days"].mean()
        top_aging = self.df.nlargest(5, "aging_days")[["sku", "branch", "aging_days"]]
        return (
            f"Inventory Aging CSV Summary ({self.csv_path.name}):\n"
            f"- Branches: {', '.join(sorted(self.df['branch'].unique()))}\n"
            f"- Average aging days: {avg_aging:.1f}\n"
            f"- Highest sales branch: {branch_sales.idxmax()} (${int(branch_sales.max()):,})\n"
            f"- Top 5 SKUs by aging:\n{top_aging.to_string(index=False)}"
        )
