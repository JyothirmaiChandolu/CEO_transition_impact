"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Loads and formats company data, KPIs, and sector information for injection into LLM prompts.
"""

import json
from pathlib import Path
from typing import Optional


class ContextBuilder:
    """Builds structured data context for LLM from companies and KPI data."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize context builder by loading companies data.

        Args:
            data_dir: Path to data directory (should contain companies.json)
        """
        self.data_dir = Path(data_dir)
        self.companies_data = self._load_companies()

        print(f"✓ ContextBuilder initialized with {len(self.companies_data)} companies")

    def _load_companies(self) -> list:
        """Load companies.json from data directory."""
        companies_path = self.data_dir / "companies.json"

        if not companies_path.exists():
            print(f"Warning: {companies_path} not found")
            return []

        with open(companies_path, 'r') as f:
            data = json.load(f)
            return data.get('companies', [])

    def _load_kpis(self, ticker: str) -> Optional[dict]:
        """Load KPI data for a specific ticker."""
        kpi_path = self.data_dir / "stocks" / "kpis" / f"{ticker}_kpis.json"

        if not kpi_path.exists():
            return None

        try:
            with open(kpi_path, 'r') as f:
                return json.load(f)
        except:
            return None

    def build_company_context(self, ticker: str, transition_date: Optional[str] = None) -> str:
        """
        Build context string for a specific company.

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            transition_date: Optional specific transition date to focus on

        Returns:
            Human-readable context string with company and KPI data
        """
        # Find company
        company = next((c for c in self.companies_data if c.get('ticker') == ticker), None)

        if not company:
            return f"Company {ticker} not found in database."

        # Load KPI data
        kpis = self._load_kpis(ticker)

        # Build context string
        context_parts = [
            f"Company: {company.get('name', ticker)} ({ticker})",
            f"Sector: {company.get('sector', 'Unknown')}",
        ]

        # Add CEO transitions
        transitions = company.get('transitions', [])
        if transitions:
            context_parts.append(f"\nCEO Transitions ({len(transitions)} total):")
            for transition in transitions[-3:]:  # Show last 3 transitions
                prev_ceo = transition.get('previousCEO', 'Unknown')
                new_ceo = transition.get('newCEO', 'Unknown')
                date = transition.get('transitionDate', 'Unknown')
                context_parts.append(f"  - {prev_ceo} → {new_ceo} ({date})")

        # Add KPI data if available
        if kpis:
            context_parts.append("\nKPI Metrics (Most Recent):")

            # Price metrics
            if 'price_metrics' in kpis:
                pm = kpis['price_metrics']
                context_parts.append(f"  Price:")
                context_parts.append(f"    - Total Return: {pm.get('total_return_pct', 'N/A')}%")
                context_parts.append(f"    - Current Price: ${pm.get('current_price', 'N/A')}")
                context_parts.append(f"    - Volatility: {pm.get('volatility_pct', 'N/A')}%")

            # Risk metrics
            if 'risk_metrics' in kpis:
                rm = kpis['risk_metrics']
                context_parts.append(f"  Risk:")
                context_parts.append(f"    - Sharpe Ratio: {rm.get('sharpe_ratio', 'N/A')}")
                context_parts.append(f"    - Max Drawdown: {rm.get('max_drawdown_pct', 'N/A')}%")

            # Transition impact
            if 'transition_impact' in kpis:
                ti = kpis['transition_impact']
                context_parts.append(f"  CEO Transition Impact:")
                context_parts.append(f"    - Transition Date: {ti.get('transition_date', 'N/A')}")
                context_parts.append(f"    - 90-Day Impact: {ti.get('impact_90days_pct', 'N/A')}%")
                context_parts.append(f"    - 1-Year Impact: {ti.get('impact_1year_pct', 'N/A')}%")
                context_parts.append(f"    - Macro Context: {ti.get('macro_economic_context', {}).get('context', 'Normal')}")

        return "\n".join(context_parts)

    def build_sector_context(self, sector: str) -> str:
        """
        Build context for all companies in a sector.

        Args:
            sector: Sector name (e.g., "Technology")

        Returns:
            Human-readable context with sector companies
        """
        sector_companies = [c for c in self.companies_data if c.get('sector') == sector]

        if not sector_companies:
            return f"Sector '{sector}' not found in database."

        context_parts = [
            f"Sector: {sector}",
            f"Companies: {len(sector_companies)}",
            f"Companies with transitions: {len([c for c in sector_companies if c.get('hasTransitions')])}"
        ]

        # List companies
        context_parts.append("\nCompanies:")
        for company in sector_companies[:10]:  # Show first 10
            ticker = company.get('ticker', 'Unknown')
            name = company.get('name', 'Unknown')
            transitions = len(company.get('transitions', []))
            context_parts.append(f"  - {ticker}: {name} ({transitions} transitions)")

        if len(sector_companies) > 10:
            context_parts.append(f"  ... and {len(sector_companies) - 10} more")

        return "\n".join(context_parts)

    def build_general_context(self) -> str:
        """
        Build general overview context.

        Returns:
            Human-readable overview of the dataset
        """
        total_transitions = sum(len(c.get('transitions', [])) for c in self.companies_data)
        companies_with_transitions = len([c for c in self.companies_data if c.get('hasTransitions')])

        context = f"""CEO Transition Impact Analysis Platform

Dataset Overview:
- Total Companies: {len(self.companies_data)}
- Companies with CEO transitions: {companies_with_transitions}
- Total CEO transitions: {total_transitions}
- Time Period: 1996-2025 (30 years)
- Data Quality: Verified via SEC 8-K filings and web research

Analysis Includes:
- Daily stock price data (OHLCV)
- CEO transition impact metrics (90-day and 1-year returns)
- Risk metrics (Sharpe ratio, volatility, max drawdown)
- Macro-economic context (recession periods)
- Sector-based outlier analysis (z-scores)

To get started, select a company to analyze CEO transition impact on stock performance."""

        return context


if __name__ == "__main__":
    # Test context builder
    builder = ContextBuilder()

    print("\n=== Testing Context Builder ===\n")

    # Test company context
    print("--- AAPL Context ---")
    print(builder.build_company_context("AAPL"))

    # Test sector context
    print("\n--- Technology Sector Context ---")
    print(builder.build_sector_context("Technology")[:500])

    # Test general context
    print("\n--- General Context ---")
    print(builder.build_general_context())
