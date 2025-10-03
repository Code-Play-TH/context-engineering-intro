"""
Currency utilities for handling multi-currency operations.

This module provides utilities for currency conversion, formatting,
and normalization across different currencies.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Currency(str, Enum):
    """Common currency codes (ISO 4217)."""
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    THB = "THB"  # Thai Baht
    JPY = "JPY"  # Japanese Yen
    CNY = "CNY"  # Chinese Yuan
    KRW = "KRW"  # South Korean Won
    SGD = "SGD"  # Singapore Dollar
    AUD = "AUD"  # Australian Dollar
    CAD = "CAD"  # Canadian Dollar


# Currency symbols
CURRENCY_SYMBOLS = {
    Currency.USD: "$",
    Currency.EUR: "€",
    Currency.GBP: "£",
    Currency.THB: "฿",
    Currency.JPY: "¥",
    Currency.CNY: "¥",
    Currency.KRW: "₩",
    Currency.SGD: "S$",
    Currency.AUD: "A$",
    Currency.CAD: "C$",
}


# Currencies with no decimal places
ZERO_DECIMAL_CURRENCIES = {
    Currency.JPY,
    Currency.KRW,
}


# Static exchange rates (for demo/fallback - in production, use live rates)
# Base currency: USD
STATIC_EXCHANGE_RATES = {
    Currency.USD: Decimal("1.00"),
    Currency.EUR: Decimal("0.92"),
    Currency.GBP: Decimal("0.79"),
    Currency.THB: Decimal("35.50"),
    Currency.JPY: Decimal("149.00"),
    Currency.CNY: Decimal("7.24"),
    Currency.KRW: Decimal("1320.00"),
    Currency.SGD: Decimal("1.35"),
    Currency.AUD: Decimal("1.52"),
    Currency.CAD: Decimal("1.36"),
}


class CurrencyConverter:
    """
    Currency converter with exchange rate management.

    In production, this should fetch live exchange rates from an API
    (e.g., exchangerate-api.com, currencylayer.com, etc.)
    """

    def __init__(
        self,
        exchange_rates: Optional[Dict[Currency, Decimal]] = None,
        base_currency: Currency = Currency.USD
    ):
        """
        Initialize currency converter.

        Args:
            exchange_rates (Optional[Dict[Currency, Decimal]]): Exchange rates.
            base_currency (Currency): Base currency for rates (default: USD).
        """
        self.base_currency = base_currency
        self.exchange_rates = exchange_rates or STATIC_EXCHANGE_RATES

    def convert(
        self,
        amount: Decimal,
        from_currency: Currency,
        to_currency: Currency
    ) -> Decimal:
        """
        Convert amount from one currency to another.

        Args:
            amount (Decimal): Amount to convert.
            from_currency (Currency): Source currency.
            to_currency (Currency): Target currency.

        Returns:
            Decimal: Converted amount.

        Example:
            >>> converter = CurrencyConverter()
            >>> converter.convert(Decimal("100"), Currency.USD, Currency.THB)
            Decimal('3550.00')
        """
        if from_currency == to_currency:
            return amount

        # Get exchange rates
        from_rate = self.exchange_rates.get(from_currency)
        to_rate = self.exchange_rates.get(to_currency)

        if not from_rate or not to_rate:
            logger.error(f"Missing exchange rate for {from_currency} or {to_currency}")
            return amount

        # Convert to base currency first, then to target currency
        amount_in_base = amount / from_rate
        converted = amount_in_base * to_rate

        return converted

    def update_rates(self, rates: Dict[Currency, Decimal]) -> None:
        """
        Update exchange rates.

        Args:
            rates (Dict[Currency, Decimal]): New exchange rates.
        """
        self.exchange_rates.update(rates)

    def get_rate(self, from_currency: Currency, to_currency: Currency) -> Decimal:
        """
        Get exchange rate between two currencies.

        Args:
            from_currency (Currency): Source currency.
            to_currency (Currency): Target currency.

        Returns:
            Decimal: Exchange rate.
        """
        if from_currency == to_currency:
            return Decimal("1.00")

        from_rate = self.exchange_rates.get(from_currency, Decimal("1.00"))
        to_rate = self.exchange_rates.get(to_currency, Decimal("1.00"))

        return to_rate / from_rate


# Global converter instance
_default_converter = CurrencyConverter()


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    converter: Optional[CurrencyConverter] = None
) -> float:
    """
    Convert amount between currencies.

    Args:
        amount (float): Amount to convert.
        from_currency (str): Source currency code.
        to_currency (str): Target currency code.
        converter (Optional[CurrencyConverter]): Custom converter instance.

    Returns:
        float: Converted amount.
    """
    if converter is None:
        converter = _default_converter

    try:
        from_curr = Currency(from_currency.upper())
        to_curr = Currency(to_currency.upper())
        amount_decimal = Decimal(str(amount))

        result = converter.convert(amount_decimal, from_curr, to_curr)
        return float(result)

    except Exception as e:
        logger.error(f"Error converting currency: {e}")
        return amount


def format_currency(
    amount: float,
    currency: str,
    include_symbol: bool = True,
    locale: str = "en_US"
) -> str:
    """
    Format amount as currency string.

    Args:
        amount (float): Amount to format.
        currency (str): Currency code.
        include_symbol (bool): Include currency symbol.
        locale (str): Locale for formatting (currently not used).

    Returns:
        str: Formatted currency string.

    Example:
        >>> format_currency(1234.56, "USD")
        "$1,234.56"
        >>> format_currency(1234.56, "JPY")
        "¥1,235"
    """
    try:
        curr = Currency(currency.upper())

        # Determine decimal places
        if curr in ZERO_DECIMAL_CURRENCIES:
            formatted_amount = f"{int(amount):,}"
        else:
            formatted_amount = f"{amount:,.2f}"

        # Add symbol
        if include_symbol:
            symbol = CURRENCY_SYMBOLS.get(curr, curr.value)
            return f"{symbol}{formatted_amount}"

        return f"{formatted_amount} {curr.value}"

    except Exception as e:
        logger.error(f"Error formatting currency: {e}")
        return f"{amount:.2f} {currency}"


def normalize_amount(
    amount: float,
    currency: str,
    decimal_places: Optional[int] = None
) -> Decimal:
    """
    Normalize currency amount to Decimal with proper precision.

    Args:
        amount (float): Amount to normalize.
        currency (str): Currency code.
        decimal_places (Optional[int]): Override decimal places.

    Returns:
        Decimal: Normalized amount.
    """
    try:
        curr = Currency(currency.upper())

        # Determine decimal places
        if decimal_places is not None:
            places = decimal_places
        elif curr in ZERO_DECIMAL_CURRENCIES:
            places = 0
        else:
            places = 2

        # Convert to Decimal and round
        amount_decimal = Decimal(str(amount))
        quantize_value = Decimal(10) ** -places
        return amount_decimal.quantize(quantize_value, rounding=ROUND_HALF_UP)

    except Exception as e:
        logger.error(f"Error normalizing amount: {e}")
        return Decimal(str(amount))


def calculate_cost_metrics(
    total_cost: float,
    impressions: int = 0,
    engagements: int = 0,
    clicks: int = 0,
    views: int = 0,
    currency: str = "USD"
) -> Dict[str, Optional[float]]:
    """
    Calculate cost-based performance metrics.

    Args:
        total_cost (float): Total campaign cost.
        impressions (int): Number of impressions.
        engagements (int): Number of engagements.
        clicks (int): Number of clicks.
        views (int): Number of views.
        currency (str): Currency code.

    Returns:
        Dict[str, Optional[float]]: Cost metrics.

    Example:
        >>> calculate_cost_metrics(1000, impressions=50000, engagements=500)
        {
            "cpm": 20.0,
            "cpe": 2.0,
            "cpc": None,
            "cpv": None,
            "currency": "USD"
        }
    """
    metrics = {"currency": currency}

    # CPM - Cost per thousand impressions
    if impressions > 0:
        metrics["cpm"] = round((total_cost / impressions) * 1000, 2)
    else:
        metrics["cpm"] = None

    # CPE - Cost per engagement
    if engagements > 0:
        metrics["cpe"] = round(total_cost / engagements, 2)
    else:
        metrics["cpe"] = None

    # CPC - Cost per click
    if clicks > 0:
        metrics["cpc"] = round(total_cost / clicks, 2)
    else:
        metrics["cpc"] = None

    # CPV - Cost per view
    if views > 0:
        metrics["cpv"] = round(total_cost / views, 4)
    else:
        metrics["cpv"] = None

    return metrics


def allocate_budget(
    total_budget: float,
    allocations: Dict[str, float],
    currency: str = "USD"
) -> Dict[str, Dict[str, any]]:
    """
    Allocate budget across different categories/channels.

    Args:
        total_budget (float): Total budget to allocate.
        allocations (Dict[str, float]): Category: percentage (0-100).
        currency (str): Currency code.

    Returns:
        Dict[str, Dict[str, any]]: Budget allocation details.

    Example:
        >>> allocate_budget(10000, {"instagram": 40, "tiktok": 30, "youtube": 30})
        {
            "instagram": {"percentage": 40, "amount": 4000.0, "formatted": "$4,000.00"},
            "tiktok": {"percentage": 30, "amount": 3000.0, "formatted": "$3,000.00"},
            "youtube": {"percentage": 30, "amount": 3000.0, "formatted": "$3,000.00"},
            "total": {"amount": 10000.0, "formatted": "$10,000.00", "currency": "USD"}
        }
    """
    # Validate percentages
    total_percentage = sum(allocations.values())
    if abs(total_percentage - 100) > 0.01:
        logger.warning(f"Budget allocations don't sum to 100% (got {total_percentage}%)")

    result = {}

    for category, percentage in allocations.items():
        amount = total_budget * (percentage / 100)
        result[category] = {
            "percentage": percentage,
            "amount": round(amount, 2),
            "formatted": format_currency(amount, currency)
        }

    result["total"] = {
        "amount": total_budget,
        "formatted": format_currency(total_budget, currency),
        "currency": currency
    }

    return result


def get_currency_info(currency: str) -> Dict[str, any]:
    """
    Get information about a currency.

    Args:
        currency (str): Currency code.

    Returns:
        Dict[str, any]: Currency information.
    """
    try:
        curr = Currency(currency.upper())

        return {
            "code": curr.value,
            "symbol": CURRENCY_SYMBOLS.get(curr, curr.value),
            "decimal_places": 0 if curr in ZERO_DECIMAL_CURRENCIES else 2,
            "name": curr.name,
        }

    except ValueError:
        logger.error(f"Unknown currency: {currency}")
        return {
            "code": currency.upper(),
            "symbol": currency.upper(),
            "decimal_places": 2,
            "name": currency.upper(),
        }


def is_valid_currency(currency: str) -> bool:
    """
    Check if currency code is valid.

    Args:
        currency (str): Currency code to validate.

    Returns:
        bool: True if valid currency code.
    """
    try:
        Currency(currency.upper())
        return True
    except ValueError:
        return False
