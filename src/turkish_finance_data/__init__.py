"""Source-aware Turkish financial research data clients."""

__all__ = ["EvdsClient", "EvdsError", "EvdsResponse", "parse_tefas_export"]


def __getattr__(name):
    # Lazy imports keep ``python -m turkish_finance_data.evds`` from importing
    # the CLI module twice while preserving the package-level convenience API.
    if name in {"EvdsClient", "EvdsError", "EvdsResponse"}:
        from .evds import EvdsClient, EvdsError, EvdsResponse

        return {"EvdsClient": EvdsClient, "EvdsError": EvdsError, "EvdsResponse": EvdsResponse}[name]
    if name == "parse_tefas_export":
        from .tefas_import import parse_tefas_export

        return parse_tefas_export
    raise AttributeError(name)
