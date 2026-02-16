import os
from .financials import FinancialDatasetsProvider
from .yahoo import YahooFinanceProvider

class DataProviderFactory:
    @staticmethod
    def get_provider(provider_name: str = "yahoo"):
        """
        Logic priority:
        1. Explicit provider_name (passed from CLI)
        2. Environment Variable (DATA_PROVIDER)
        3. Default (yahoo)
        """
        # 1. Check CLI/Function Argument, then Env Var, then Default
        choice = provider_name or os.getenv("DATA_PROVIDER", "yahoo").lower()

        if choice == "financial_datasets":
            api_key = os.getenv("FINANCIAL_DATASETS_API_KEY")
            if not api_key:
                raise ValueError("FINANCIAL_DATASETS_API_KEY not found in environment")
            return FinancialDatasetsProvider(api_key=api_key)
        
        elif choice == "yahoo":
            return YahooFinanceProvider()
        
        else:
            raise ValueError(f"Unknown data provider: {choice}")