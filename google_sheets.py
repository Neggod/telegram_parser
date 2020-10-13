import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = "yor-auth-file-from-google-api.json"  # Имя файла с закрытым ключом, вы должны подставить свое

# Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                               ['https://www.googleapis.com/auth/spreadsheets',
                                                                'https://www.googleapis.com/auth/drive'])

http_auth = credentials.authorize(httplib2.Http())  # Авторизуемся в системе
service = apiclient.discovery.build('sheets', 'v4', http=http_auth)  # Выбираем работу с таблицами и 4 версию API
# https://docs.google.com/spreadsheets/d/1KQS3adR3ZS5SwgrRHCZ3PfHCvxxlMyhQY28coWgP1cs
spreadsheet_id = "YOUR_SHEETSPREAD_ID"


# service.spreadsheets().create(body={
#     'properties': {'title': 'Первый тестовый документ', 'locale': 'ru_RU'},
#     'sheets': [{'properties': {'sheetType': 'GRID',
#                                'sheetId': 0,
#                                'title': 'Лист номер один',
#                                'gridProperties': {'rowCount': 100, 'columnCount': 15}}}]
# }).execute()
# spreadsheetId = spreadsheet['spreadsheetId']  # сохраняем идентификатор файла
# print('https://docs.google.com/spreadsheets/d/' + spreadsheetId)
def change_email(email: str):
    drive_service = apiclient.discovery.build('drive', 'v3', http=http_auth)
    access = drive_service.permissions().create(
        fileId=spreadsheet_id,
        body={'type': 'user', 'role': 'writer', 'emailAddress': email},
        # Открываем доступ на редактирование
        fields='id'
    ).execute()


# Добавление листа


def create_worksheet(sheet_name: str, row_count=100, column_count=20):
    results = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=
        {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "gridProperties": {
                                "rowCount": row_count,
                                "columnCount": column_count,
                            }
                        }
                    }
                }
            ]
        }).execute()
    return results


def get_sheets_data(list_name) -> list:
    ranges = [f"{list_name}!A1:F100"]  #

    results = service.spreadsheets().values().batchGet(spreadsheetId=spreadsheet_id,
                                                       ranges=ranges,
                                                       valueRenderOption='FORMATTED_VALUE',
                                                       dateTimeRenderOption='FORMATTED_STRING').execute()

    sheet_values = results['valueRanges'][0]['values']

    return sheet_values


def write_data(list_name: str, row_number: int, values: list):
    results = service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body={
        "valueInputOption": "USER_ENTERED",
        # Данные воспринимаются, как вводимые пользователем (считается значение формул)
        "data": [
            {"range": f"{list_name}!A{row_number}:O{row_number}",
             "majorDimension": "ROWS",  # Сначала заполнять строки, затем столбцы
             "values": values}
        ]
    }).execute()
    results = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {'updateBorders': {'range': {'sheetId': 123123123123,
                                             'startRowIndex': 1,
                                             'endRowIndex': row_number,
                                             'startColumnIndex': 1,
                                             'endColumnIndex': len(values)},
                                   'bottom': {
                                       # Задаем стиль для верхней границы
                                       'style': 'SOLID',  # Сплошная линия
                                       'width': 1,  # Шириной 1 пиксель
                                       'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},  # Черный цвет
                                   'top': {
                                       # Задаем стиль для нижней границы
                                       'style': 'SOLID',
                                       'width': 1,
                                       'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                                   'left': {  # Задаем стиль для левой границы
                                       'style': 'SOLID',
                                       'width': 1,
                                       'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                                   'right': {
                                       # Задаем стиль для правой границы
                                       'style': 'SOLID',
                                       'width': 1,
                                       'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                                   'innerHorizontal': {
                                       # Задаем стиль для внутренних горизонтальных линий
                                       'style': 'SOLID',
                                       'width': 1,
                                       'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                                   'innerVertical': {
                                       # Задаем стиль для внутренних вертикальных линий
                                       'style': 'SOLID',
                                       'width': 1,
                                       'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}}

                                   }}
            ]
        }).execute()
    return results


def to_googlesheet(values_dict: dict):
    """

    :param values_dict: like {
        "date": "01-01-0001",
        "group_name_1: 13,
        "group_name_2: 94,
        ...
        "group_name_N: M.
    }
    :return:
    """
    try:
        sheet_values = get_sheets_data("Statistics")
        for i in range(len(sheet_values)):
            if sheet_values[i]:
                continue
            sheet_values.pop(i)
        head = sheet_values[0]
        string_number = len(sheet_values)
    except KeyError:
        head = ["Дата", ]
        for key in values_dict.keys():
            if key == 'date':
                continue
            head.append(key)
        write_data('Statistics', 1, [head,])
        string_number = 2

    row = [values_dict.get("date")]
    for val in head:
        if val == 'Дата':
            continue
        row.append(values_dict.get(val, 0))
    write_data('Statistics', string_number, [row,])


if __name__ == '__main__':
    import sys

    _, *args = sys.argv
    if args and args[0].startswith("--email"):
        change_email(args[0].split('=')[-1])
    input("Press any key to continue: ")
