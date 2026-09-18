def select(records, start, end):
    return [record for record in records if start.replace(tzinfo=None) <= record["at"].replace(tzinfo=None) <= end.replace(tzinfo=None)]
