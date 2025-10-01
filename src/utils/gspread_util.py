import itertools
# from openpyxl import load_workbook
import gspread






def get_all_sheets_data():

    gc = gspread.service_account(filename='utils/creds.json')
    spreadsheet = gc.open('вопросы')

    all_worksheets = spreadsheet.worksheets()
    ranges = [ws.title for ws in all_worksheets]
    result = spreadsheet.values_batch_get(ranges)
    all_sheets_data = {'all_worksheets':ranges}

    for i, sheet_data in enumerate(result['valueRanges']):
        # sheet_name = all_worksheets[i].title
        rows = sheet_data.get('values', [])
        columns = []
        if rows:
            columns = [
                list(column) 
                for column in itertools.zip_longest(*rows, fillvalue=None)
            ]
        all_sheets_data[i] = columns
    return all_sheets_data




