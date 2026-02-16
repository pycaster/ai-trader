from typing import List
from .base import DataProvider
from src.data.models import Price, FinancialMetrics, LineItem, CompanyNews
from src.tools.api import (
    get_prices,
    get_financial_metrics,
    get_company_news,
    get_market_cap,
    search_line_items,
)


class FinancialDatasetsProvider(DataProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.provider_name = "Financial Datasets"

    def get_prices(self, ticker: str, start_date: str, end_date: str) -> List[Price]:
        return get_prices(ticker=ticker, start_date=start_date, end_date=end_date, api_key=self.api_key)

    def get_financial_metrics(self, ticker: str, end_date: str, period: str = "quarterly", limit: int = 10) -> List[FinancialMetrics]:
        return get_financial_metrics(ticker=ticker, end_date=end_date, period=period, limit=limit, api_key=self.api_key)

    def get_market_cap(self, ticker: str, end_date: str) -> float | None:
        return get_market_cap(ticker=ticker, end_date=end_date, api_key=self.api_key)

    def get_company_news(self, ticker: str, start_date: str, end_date: str, limit: int = 20) -> List[CompanyNews]:
        return get_company_news(ticker=ticker, start_date=start_date, end_date=end_date, limit=limit, api_key=self.api_key)

    def get_financial_line_items(self, ticker: str, line_items: List[str], end_date: str, period: str = "quarterly", limit: int = 10) -> List[LineItem]:
        return search_line_items(ticker=ticker, line_items=line_items, end_date=end_date, period=period, limit=limit, api_key=self.api_key)