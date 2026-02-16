from abc import ABC, abstractmethod
from typing import List
from src.data.models import Price, FinancialMetrics, LineItem, CompanyNews


class DataProvider(ABC):
    @abstractmethod
    def get_prices(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
    ) -> List[Price]:
        """Returns a list of Price objects with fields: time, open, high, low, close, volume"""
        pass

    @abstractmethod
    def get_financial_metrics(
        self,
        ticker: str,
        end_date: str,
        period: str = "quarterly",
        limit: int = 10,
    ) -> List[FinancialMetrics]:
        """Returns fundamental ratios and metrics (P/E, ROE, etc.)"""
        pass

    @abstractmethod
    def get_financial_line_items(
        self,
        ticker: str,
        line_items: List[str],
        end_date: str,
        period: str = "quarterly",
        limit: int = 10,
    ) -> List[LineItem]:
        """Returns specific line items from financial statements"""
        pass

    @abstractmethod
    def get_company_news(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        limit: int = 20,
    ) -> List[CompanyNews]:
        """Returns news headlines and metadata"""
        pass

    @abstractmethod
    def get_market_cap(
        self,
        ticker: str,
        end_date: str,
    ) -> float | None:
        """Returns the market capitalization for the given ticker"""
        pass