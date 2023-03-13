from fastapi import FastAPI, Request, Form, UploadFile
from fastapi.params import Path, File
from starlette.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from starlette.templating import Jinja2Templates
from db import *
from random import *

app = FastAPI()
app_api = FastAPI()

templates = Jinja2Templates(directory="pet_choc_files")


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    """Return root page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get('/basket', response_class=HTMLResponse)
def basket(request: Request):
    """Return client basket. Works on cookies. If there are cookies, which are individual for each user, then we get a
    list of products from the database that the user has chosen. If there is no cookie, then we show that the client
    has not added anything yet. The cookie is set in the add_basket function."""

    if not request.cookies.get('client', None):  # if dont have cookie
        return templates.TemplateResponse("basket.html", {"request": request, 'empty': True})
    else:
        basket_list = get_basket_list(request.cookies.get('client', None))
        empty = is_empty_basket(request.cookies.get('client', None))
        total = total_price(request.cookies.get('client', None))
        return templates.TemplateResponse("basket.html",
                                          {"request": request, 'empty': empty, 'basket_list': basket_list,
                                           'total': total})


@app.post('/basket', response_class=HTMLResponse)
def basket(request: Request, name=Form(), email=Form(), phone=Form(), comment=Form()):
    """Here you can set a post request to create an order."""
    cookie = request.cookies.get('client', None)
    create_order(cookie, name, email, phone, comment)
    resp = RedirectResponse('/finish')
    resp.status_code = 302
    return resp


@app.get('/finish', response_class=HTMLResponse)
def finish(request: Request):
    return templates.TemplateResponse("finishorder.html", {"request": request})


@app.get('/error', response_class=HTMLResponse)
def error(request: Request):
    return templates.TemplateResponse("errorpass.html", {"request": request})


@app.get('/contact', response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.get('/about', response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.post('/reviews', response_class=HTMLResponse)
def reviews(name=Form(), email=Form(), comm=Form()):
    """Creating a new review, which is immediately added to the database and displayed on the site."""
    resp = RedirectResponse('/reviews')
    resp.status_code = 302
    create_review(name, email, comm)
    return resp


@app.get('/reviews', response_class=HTMLResponse)
def reviews(request: Request):
    revs = get_reviews()
    return templates.TemplateResponse("reviews.html", {"request": request, 'revs': revs})


@app.get('/sweets', response_class=HTMLResponse)
def sweets(request: Request):
    sweet_list = get_sweets() # get list of sweets from bd
    return templates.TemplateResponse("sweets.html", {"request": request, 'sweets': sweet_list})


@app.post('/admin', response_class=HTMLResponse)
def admin(login=Form(), password=Form()):
    """Login to the admin panel using a pre-specified one login and password, without querying the database."""
    if login == 'admin' and str(password) == '12345':
        resp = RedirectResponse("/panel")
        resp.set_cookie('admin', max_age=86400, value='True')
        resp.status_code = 302
        return resp

    return RedirectResponse("/error")


@app.get('/admin', response_class=HTMLResponse)
def admin(request: Request):
    """If we have recently logged into the panel, then there is no need to additionally enter a login."""
    if request.cookies.get('admin', None) != None:
        return RedirectResponse('/panel')

    return templates.TemplateResponse("adminin.html", {"request": request})


@app.get('/panel', response_class=HTMLResponse)
def panel(request: Request):
    revs = get_reviews()
    sweets = get_sweets_panel()
    list_order = get_orders()
    return templates.TemplateResponse("panel.html",
                                      {"request": request, 'revs': revs, 'sweets': sweets, 'ord': list_order})


@app.get('/add', response_class=HTMLResponse)
def add(request: Request):
    """Page of creation new product"""
    return templates.TemplateResponse("newprod.html", {"request": request})


@app.post('/add', response_class=HTMLResponse)
def add(pic: UploadFile, name=Form(), price=Form(), desc=Form(), pack=Form()):
    """Adding a new product to the database."""
    create_sweet(name, price, desc, pic, pack)
    resp = RedirectResponse("/panel")
    resp.status_code = 302
    return resp


@app.get('/delete_rev_{pk}')
def delete_review(pk: int = Path(...)):
    r = delete_rev(pk)
    return RedirectResponse('/panel')


@app.get('/delete_sweet_{pk}')
def delete_sweet(pk: int = Path(...)):
    r = delete_sw(pk)
    return RedirectResponse('/panel', status_code=302)


@app.get('/update_sweet_{pk}')
def update_sweet(pk: int = Path(...)):
    """We turn on, turn off the display of the product on the site, does not delete the product."""
    switch_sweet(pk)
    return RedirectResponse('/panel', status_code=302)


@app.get('/update_bas_{pk}')
def add_basket(request: Request, pk: int = Path(...)):
    """If there is no cookie, then we create, we make a new copy of the BASKET and the USER.
    If there are cookies, then either we add a new record about the choice of the product, or we update the number of
    goods already in the existing record.
    """
    if not request.cookies.get('client', None):  # if dont have cookie
        host = str(request.client.host)
        resp = RedirectResponse("/sweets")
        cook = ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(7))
        resp.set_cookie('client', max_age=259200, value=cook)
        resp.status_code = 302
        create_user(host, cook)
        add_sw_basket(pk, cook)
        return resp

    else:
        c = request.cookies.get('client', None)
        if is_have_sw(c, pk):
            update_basket_count(c, pk)
            return RedirectResponse("/basket")
        else:
            add_sw_basket(pk, c)
            return RedirectResponse("/basket")


@app.get('/delete_from_bas_{pk}')
def minus_basket(request: Request, pk: int = Path(...)):
    """Reduce or remove the number of products in a user's cart entry"""
    c = request.cookies.get('client', None)
    minus_basket_count(c, pk)
    return RedirectResponse("/basket")


@app.get('/order_{pk}')
def order_info(request: Request, pk: int = Path(...)):
    """Get one order's record """
    order, list_prod = get_one_order(pk)
    return templates.TemplateResponse("order_page.html", {"request": request, 'order': order, 'prods': list_prod})


@app.get('/change_{pk}')
def change_stage(pk: int = Path(...)):
    """Change status of order, it can be:
    new, paid, cooking, awaiting delivery, delivery, finished;
    If status 'finished', then delete the order.
    """
    change_st(pk)
    return RedirectResponse('/panel')


@app.get('/delete_ord_{pk}')
def delete_order(pk: int = Path(...)):
    delete_order_db(pk)
    return RedirectResponse('/panel')
