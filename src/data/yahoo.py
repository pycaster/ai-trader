import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
from .base import DataProvider
from src.data.models import Price, FinancialMetrics, LineItem, CompanyNews

class YahooFinanceProvider(DataProvider):
    def __init__(self, api_key: str = None):
        self.api_key  = api_key
        self.provider_name = "Yahoo Finance"

    def get_prices(self, ticker: str, start_date: str, end_date: str) -> list[Price]:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if df.empty:
                return []

            # Flatten MultiIndex if necessary
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [col.lower() for col in df.columns]

            # Drop rows with NaN values in critical columns
            df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])

            prices = []
            for timestamp, row in df.iterrows():
                price_obj = Price(
                    time=timestamp.strftime('%Y-%m-%d'),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume'])
                )
                prices.append(price_obj)

            return prices
        except Exception:
            return []

    def get_financial_metrics(self, ticker: str, end_date: str, period: str = "quarterly", limit: int = 10) -> List[FinancialMetrics]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info:
                return []

            # yfinance only provides current metrics, not historical
            # Filter out if the current date is after end_date
            current_date = pd.Timestamp.now().strftime('%Y-%m-%d')
            if end_date and current_date > end_date:
                # For backtesting, we can't get historical metrics from yfinance
                # Return the metrics but with the end_date as report_period
                report_period = end_date
            else:
                report_period = current_date

            # Safely compute free_cash_flow_per_share
            fcf = info.get("freeCashflow")
            shares = info.get("sharesOutstanding")
            fcf_per_share = (fcf / shares) if (fcf and shares) else None

            metrics = FinancialMetrics(
                ticker=ticker,
                report_period=report_period,
                period=period,
                currency="USD",
                market_cap=info.get("marketCap"),
                enterprise_value=info.get("enterpriseValue"),
                price_to_earnings_ratio=info.get("trailingPE"),
                price_to_book_ratio=info.get("priceToBook"),
                price_to_sales_ratio=info.get("priceToSalesTrailing12Months"),
                enterprise_value_to_ebitda_ratio=info.get("enterpriseToEbitda"),
                enterprise_value_to_revenue_ratio=info.get("enterpriseToRevenue"),
                free_cash_flow_yield=None,
                peg_ratio=info.get("pegRatio"),
                gross_margin=info.get("grossMargins"),
                operating_margin=info.get("operatingMargins"),
                net_margin=info.get("profitMargins"),
                return_on_equity=info.get("returnOnEquity"),
                return_on_assets=info.get("returnOnAssets"),
                return_on_invested_capital=None,
                asset_turnover=None,
                inventory_turnover=None,
                receivables_turnover=None,
                days_sales_outstanding=None,
                operating_cycle=None,
                working_capital_turnover=None,
                current_ratio=info.get("currentRatio"),
                quick_ratio=info.get("quickRatio"),
                cash_ratio=None,
                operating_cash_flow_ratio=None,
                debt_to_equity=info.get("debtToEquity"),
                debt_to_assets=None,
                interest_coverage=None,
                revenue_growth=info.get("revenueGrowth"),
                earnings_growth=info.get("earningsGrowth"),
                book_value_growth=None,
                earnings_per_share_growth=None,
                free_cash_flow_growth=None,
                operating_income_growth=None,
                ebitda_growth=None,
                payout_ratio=info.get("payoutRatio"),
                earnings_per_share=info.get("trailingEps"),
                book_value_per_share=info.get("bookValue"),
                free_cash_flow_per_share=fcf_per_share,
            )
            return [metrics][:limit]
        except Exception:
            return []

    def get_financial_line_items(self, ticker: str, line_items: List[str], end_date: str, period: str = "quarterly", limit: int = 10) -> List[LineItem]:
        try:
            stock = yf.Ticker(ticker)

            # Get financials (Income, Balance, Cash Flow)
            if period == "quarterly":
                inc = stock.quarterly_income_stmt
                bal = stock.quarterly_balance_sheet
                cf = stock.quarterly_cashflow
            else:
                inc = stock.financials
                bal = stock.balance_sheet
                cf = stock.cashflow

            # Handle empty DataFrames
            dfs = [df for df in [inc, bal, cf] if df is not None and not df.empty]
            if not dfs:
                return []

            combined = pd.concat(dfs).T

            # Filter by end_date - only include periods on or before end_date
            if end_date:
                end_dt = pd.to_datetime(end_date)
                combined = combined[combined.index <= end_dt]

            if combined.empty:
                return []

            # Sort by date descending (most recent first)
            combined = combined.sort_index(ascending=False)

            # Mapping yfinance column names to requested line_items
            # yfinance column names can vary, so we try multiple variants
            mapping = {
                "revenue": ["Total Revenue", "Revenue"],
                "earnings_per_share": ["Basic EPS", "Diluted EPS"],
                "net_income": ["Net Income", "Net Income Common Stockholders"],
                "operating_income": ["Operating Income", "Operating Revenue"],
                "gross_profit": ["Gross Profit"],
                "gross_margin": ["Gross Profit"],  # Will need to compute ratio
                "operating_margin": ["Operating Income"],  # Will need to compute ratio
                "free_cash_flow": ["Free Cash Flow"],
                "capital_expenditure": ["Capital Expenditure", "Capital Expenditures"],
                "cash_and_equivalents": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
                "total_debt": ["Total Debt", "Long Term Debt"],
                "total_assets": ["Total Assets"],
                "total_liabilities": ["Total Liabilities Net Minority Interest", "Total Liabilities"],
                "current_assets": ["Current Assets"],
                "current_liabilities": ["Current Liabilities"],
                "shareholders_equity": ["Stockholders Equity", "Total Equity Gross Minority Interest", "Common Stock Equity"],
                "outstanding_shares": ["Ordinary Shares Number", "Share Issued"],
                "book_value_per_share": ["Book Value Per Share"],  # Usually needs computation
                "ebit": ["EBIT", "Operating Income"],
                "ebitda": ["EBITDA", "Normalized EBITDA"],
                "interest_expense": ["Interest Expense", "Interest Expense Non Operating"],
                "depreciation_and_amortization": ["Depreciation And Amortization", "Depreciation"],
                "dividends_and_other_cash_distributions": ["Cash Dividends Paid", "Common Stock Dividend Paid"],
                "issuance_or_purchase_of_equity_shares": ["Repurchase Of Capital Stock", "Common Stock Issuance"],
                "research_and_development": ["Research And Development", "Research And Development Expense"],
                "operating_expense": ["Operating Expense", "Total Operating Expenses"],
                "working_capital": ["Working Capital"],
                "return_on_invested_capital": [],  # Computed metric, not in statements
            }

            def get_value(row, keys):
                """Try multiple column names and return the first match."""
                for key in keys:
                    if key in row.index and pd.notna(row.get(key)):
                        return float(row[key])
                return None

            results = []
            for date, row in combined.head(limit).iterrows():
                report_period = date.strftime('%Y-%m-%d')
                revenue = get_value(row, mapping.get("revenue", []))

                # Build dynamic fields for LineItem
                dynamic_fields = {}
                for requested_item in line_items:
                    keys = mapping.get(requested_item, [requested_item.replace('_', ' ').title()])
                    value = get_value(row, keys)

                    # Compute margin ratios if needed
                    if requested_item == "gross_margin" and revenue and value:
                        value = value / revenue
                    elif requested_item == "operating_margin" and revenue and value:
                        value = value / revenue

                    dynamic_fields[requested_item] = value

                # Create LineItem with required fields + dynamic fields
                line_item = LineItem(
                    ticker=ticker,
                    report_period=report_period,
                    period=period,
                    currency="USD",
                    **dynamic_fields
                )
                results.append(line_item)

            return results
        except Exception:
            return []

    def get_company_news(self, ticker: str, start_date: str, end_date: str, limit: int = 20) -> List[CompanyNews]:
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if news is None:
                return []
        except Exception:
            return []

        formatted_news = []
        start_timestamp = pd.to_datetime(start_date).timestamp() if start_date else None
        end_timestamp = pd.to_datetime(end_date).timestamp() if end_date else None

        for n in news:
            # Handle both old and new yfinance API structures
            publish_time = n.get("providerPublishTime")
            if publish_time is None:
                # Try newer yfinance structure
                publish_time = n.get("publish_time") or n.get("publishedAt")
            if publish_time is None:
                continue

            # Convert to timestamp if it's a string (newer API format)
            if isinstance(publish_time, str):
                publish_time = pd.to_datetime(publish_time).timestamp()

            # Skip if publish time is outside the date range
            if start_timestamp and publish_time < start_timestamp:
                continue
            if end_timestamp and publish_time > end_timestamp:
                continue

            date_str = pd.to_datetime(publish_time, unit='s').strftime('%Y-%m-%d')

            news_item = CompanyNews(
                ticker=ticker,
                title=n.get("title") or "",
                author="",
                source=n.get("publisher") or n.get("source") or "",
                date=date_str,
                url=n.get("link") or n.get("url") or "",
                sentiment=None,
            )
            formatted_news.append(news_item)

            # Apply limit after filtering
            if len(formatted_news) >= limit:
                break

        return formatted_news
    
    def get_market_cap(self, ticker: str, end_date: str) -> float | None:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info:
                return None
            # Note: yfinance only provides current market cap, not historical
            # For backtesting accuracy, historical market cap would require price * shares outstanding
            return info.get("marketCap")
        except Exception:
            return None
