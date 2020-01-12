import logging
import sys
import gspread
from enchant.checker import SpellChecker


def custom_logger(logger_name, level=logging.DEBUG):
    """
    Method to return a custom logger with the given name and level
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    format_string = "%(levelname)s %(asctime)s - %(message)s"

    log_format = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Creating and adding the console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # Creating and adding the file handler
    file_handler = logging.FileHandler(logger_name, mode='w')
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    return logger


def paste_csv_to_wks(csv_file, sheet, cell, logger):
    clean_wks = sheet.get_worksheet(0)
    total_rows = len(clean_wks.col_values(1))
    logger.info(f"Total number of rows on the worksheet: {total_rows}")

    clean_wks.resize(rows=3)

    if '!' in cell:
        (tabName, cell) = cell.split('!')
        wks = sheet.worksheet(tabName)
    else:
        wks = sheet.sheet1
    (firstRow, firstColumn) = gspread.utils.a1_to_rowcol(cell)

    with open(csv_file, 'r', encoding='utf-8') as f:
        csv_contents = f.read()
    body = {'requests': [{
        'pasteData': {"coordinate": {"sheetId": wks.id, "rowIndex": firstRow - 1, "columnIndex": firstColumn - 1, },
                      "data": csv_contents, "type": 'PASTE_NORMAL', "delimiter": ',', }}]}
    return sheet.batch_update(body)


def is_in_english(quote):
    d = SpellChecker("en_US")
    d.set_text(quote)
    errors = [err.word for err in d]
    return False if ((len(errors) > 5) or len(quote.split()) < 1) else True
