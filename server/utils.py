from datetime import datetime, date

def parse_date(value):
    if not value:
        return date.today()

    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except:
            pass

    return date.today()