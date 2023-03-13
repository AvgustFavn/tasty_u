from starlette.requests import Request
from starlette.responses import RedirectResponse


def admin_already(request: Request):
    if request.cookies.get('admin', None) != None:
        return RedirectResponse('/admin/panel')
