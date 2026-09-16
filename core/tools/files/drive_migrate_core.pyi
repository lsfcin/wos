from _typeshed import Incomplete
from drive_core import SCOPES_READ as SCOPES_READ, SCOPES_WRITE as SCOPES_WRITE, copy_file as copy_file, find_or_create_folder as find_or_create_folder, list_folder as list_folder
from googleapiclient.errors import HttpError as HttpError

CIN_DISCIPLINAS_ID: str
SLIDE_MIMETYPES: Incomplete
FOLDER_MAP: Incomplete
STATE_FILE: Incomplete
MAP_FILE: Incomplete

def get_cin_service(): ...
def get_personal_service(): ...
