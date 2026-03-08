def format_number(value):
    try:
        return f"{int(value):,}"
    except:
        return "N/A"


def format_float(value, decimals=2):
    try:
        return f"{float(value):,.{decimals}f}"
    except:
        return "N/A"


def format_currency(value, symbol="$", decimals=2):
    try:
        return f"{symbol}{float(value):,.{decimals}f}"
    except:
        return "N/A"


def format_percentage(value, decimals=1):
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except:
        return "N/A"
