from django.http import HttpResponse
from django.template import RequestContext, loader
from models import Usuario
import datetime

def home(request):
    # Busco usuario,si exite,para el tiempo y crea nuevo tiempo de trabajo
    # Si no exite,creo una nuevo tiempo de trabajo
    # guardo en una session, el id del usuario para futuras busquedas

    template = loader.get_template('conector/index.html')
    context={}

    if request.method == 'POST':

        from erp import POOL, DB, USER
        codigo = int(request.POST.get("code",False))
        user_obj = POOL.get('res.users')
        cursor = DB.cursor()
        try:
            user_ids = user_obj.search(cursor, USER, [('code', '=', codigo )], order="login ASC")
            users = user_obj.browse(cursor, USER, user_ids)
            if users:
                try:

                    user_access= Usuario.objects.get(code = codigo, end__isnull = True)
                    user_access.end = datetime.datetime.now()
                    user_access.save()
                    user_access = Usuario(code=codigo, name = users[0].name )
                    user_access.save()

                except:
                    user_access = Usuario(code=codigo, name = users[0].name )
                    user_access.save()
                request.session['codigo'] = user_access.code
                return selector(request)
            else:
                context = RequestContext(request, {
                    'nouser': False,
                })
                return HttpResponse(template.render(context))
        except Exception as e:

            context = RequestContext(request, {
                'nouser': False,
            })
            return HttpResponse(template.render(context))
            pass
        finally:

            cursor.commit()
            cursor.close()
    else:

        context = RequestContext(request, {
                'nouser': True,
            })
        return HttpResponse(template.render(context))

def selector(request):
    template = loader.get_template('conector/selector.html')

    users_list = Usuario.objects.filter(end__isnull = True)

    context = RequestContext(request, {
            'users_list': users_list,
    })
    return HttpResponse(template.render(context))


def productos(request):
    template = loader.get_template('conector/productos.html')
    context={}
    from erp import POOL, DB, USER
    cursor = DB.cursor()
    product_obj = POOL.get('mrp.production')


    try:
        product_ids = product_obj.search(cursor, USER, [('state', 'not in', ['done','cancel'])], order="name ASC")
        products = product_obj.browse(cursor, USER, product_ids, [])

        users_list = Usuario.objects.filter(end__isnull = True)
        context = RequestContext(request, {
            'users_list': users_list,
            'products_list': products,
        })
    except Exception as e:
        context = RequestContext(request, {
            'users_list': False,
            'products_list': False,
        })
        pass
    finally:
        return HttpResponse(template.render(context))
        cursor.commit()
        cursor.close()



def producto(request,id):
    template = loader.get_template('conector/producto.html')
    context={}
    from erp import POOL, DB, USER
    cursor = DB.cursor()

    production_obj = POOL.get('mrp.production')
    try:
        production = production_obj.browse(cursor, USER, [int(id)])
        users_list = Usuario.objects.filter(end__isnull = True)
        user_access = Usuario.objects.get(code = request.session['codigo'], end__isnull = True)
        user_access.project = id
        user_access.save()
        context = RequestContext(request, {
            'users_list': users_list,
            'product': production[0],
        })
    except Exception as e:
        context = RequestContext(request, {
            'users_list': False,
            'product': False,
        })
        pass
    finally:
        return HttpResponse(template.render(context))
        cursor.commit()
        cursor.close()


def crear_producto(request):
    if request.method == 'POST':
        pr_id = int(request.POST.get("pr"))
        w_id = int(request.POST.get("wr"))
        vals = {}
        from erp import POOL, DB, USER
        from openerp import netsvc
        wf_service = netsvc.LocalService("workflow")
        cursor = DB.cursor()
        qty = int(request.POST.get("qty"))

        codigo = int(request.session.get('codigo', False))
        mrp_obj = POOL.get('mrp.production')
        prod_obj = POOL.get('product.product')
        user_obj = POOL.get('res.users')

        try:
            user_ids = user_obj.search(cursor, USER, [('code', '=', codigo )], order="login ASC")
            users = user_obj.browse(cursor, USER, user_ids)
            product = prod_obj.browse(cursor, USER, pr_id)
            vals['date_planned'] = datetime.datetime.now()
            vals['product_id'] = pr_id
            vals['product_qty'] = qty
            vals['warehouse_id'] = w_id
            vals['product_uom'] = product.uom_id.id
            vals['user_id'] = users[0].id

            mrp = mrp_obj.create(cursor, USER, vals)
            print "creo el mrp", mrp
            wf_service.trg_validate(USER, 'mrp.production', mrp, 'button_confirm', cursor)
            user_access = Usuario.objects.get(code = codigo, end__isnull = True)
            user_access.project = mrp
            user_access.save()
        except Exception as e:
            context = RequestContext(request, {
                'users_list': False,
                'products': False,
            })
            pass
        finally:
            cursor.commit()
            cursor.close()

            return productos(request)

    else:
        print "NO POST"
        template = loader.get_template('conector/crear_producto.html')
        context={}
        from erp import POOL, DB, USER
        cursor = DB.cursor()
        product_obj = POOL.get('mrp.bom')
        warehouse_obj = POOL.get('stock.warehouse')
        try:
            products_ids = product_obj.search(cursor, USER, [('product_id.analytic_acc_id', '!=', False)], order="name ASC")
            products = product_obj.browse(cursor, USER, products_ids)
            warehouse_ids = warehouse_obj.search(cursor, USER, [], order="name ASC")
            warehouses = warehouse_obj.browse(cursor, USER, products_ids)
            users_list = Usuario.objects.filter(end__isnull = True)

            context = RequestContext(request, {
                'users_list': users_list,
                'products': products,
                'warehouses':warehouses,
            })
        except Exception as e:
            print "--->", e
            context = RequestContext(request, {
                'users_list': False,
                'products': False,
            })
            pass
        finally:
            return HttpResponse(template.render(context))
            cursor.commit()
            cursor.close()


def procesar(request, id):
    context={}
    pr_id = int(id)

    from erp import POOL, DB, USER
    mrp_obj = POOL.get('mrp.production')
    cursor = DB.cursor()


    try:
        product = mrp_obj.browse(cursor, USER, [pr_id, ])
        mrp = mrp_obj.force_production(cursor, USER, [product[0].id])
        mrp_obj.action_produce(cursor, USER, product[0].id, product[0].product_qty, "consume_produce")

    except Exception as e:
        print "--->", e
        pass
    finally:
        cursor.commit()
        cursor.close()
        return home(request)

def abrir(request, id):

    context={}
    pr_id = int(id)

    from erp import POOL, DB, USER

    mrp_obj = POOL.get('mrp.production')
    cursor = DB.cursor()

    try:
        mrp_obj.action_ready(cursor, USER, [pr_id,], *args)
    except Exception as e:
        print "--->", e
        pass
    finally:
        cursor.commit()
        cursor.close()
        return home(request)

def finalizar(request, id):

    context={}
    pr_id = int(id)
    codigo = int(request.session.get('codigo', False))
    from erp import POOL, DB, USER
    user_obj = POOL.get('res.users')
    mrp_obj = POOL.get('mrp.production')
    time_obj = POOL.get('hr.analytic.timesheet')
    hr_obj = POOL.get('hr,employee')
    cursor = DB.cursor()

    try:
        mrp = mrp_obj.browse(cursor, USER, pr_id)
        mrp_obj.action_production_end(cursor, USER, [pr_id,])
        user_access = Usuario.objects.filter(project = id, end__isnull = True)
        for u in user_access:
            u.end=datetime.datetime.now()
            u.save()
        users_time = Usuario.objects.filter(project = id )
        for t in users_time:
            user_ids = user_obj.search(cursor, USER, [('code', '=', codigo )], order="login ASC")
            usere = user_obj.browse(cursor, USER, user_ids)
            hr_ids = hr_obj.search(cursor, USER, [('user_id', '=', usere[0].id )], order="login ASC")
            hr_usere = hr_obj.browse(cursor, USER, hr_ids)
            vals = {}
            vals['production_id'] = pr_id
            vals['journal_id'] =  hr_usere[0].journal_id
            vals['product_uom_id'] = ""
            vals['product_id'] = mrp[0].product_id
            vals['general_account_id'] = ""
            vals['account_id'] = ""
            vals['date'] = t.end
            vals['unit_amount'] = ""
            vals['name'] = ""
            vals['user_id'] = usere[0].id
            vals['amount'] = ""
            print "--->", vals
            time_obj.create(cursor, USER, vals)

    except Exception as e:
        print "--->", e
        pass
    finally:
        cursor.commit()
        cursor.close()
        return home(request)


def verstock(request, id):
    # Busco usuario,si exite,para el tiempo y crea nuevo tiempo de trabajo
    # Si no exite,creo una nuevo tiempo de trabajo
    # guardo en una session, el id del usuario para futuras busquedas

    template = loader.get_template('conector/verstock.html')
    context={}
    move_id = int(id)
    from erp import POOL, DB, USER
    lot_obj = POOL.get('stock.production.lot')
    prod_obj = POOL.get('product.product')
    move_obj = POOL.get('stock.move')
    cursor = DB.cursor()
    move = move_obj.browse(cursor, USER, move_id)
    lot_ids = lot_obj.search(cursor, USER, [('product_id', '=', move.product_id.id),('stock_available', '>', 0.0)])
    try:
        if request.method == 'POST':
            selected_lots = []
            for field in  request.POST:
                if 'foo' in field:
                    selected_lots.append(int(request.POST[field]))

            if selected_lots:
                print "SELECT_LOTS: ", selected_lots
                move_obj.apply_lots_in_production(cursor, USER, [move.id], selected_lots)

        else:
            lots = lot_obj.browse(cursor, USER, lot_ids)
            lots_qty = sum([x.stock_available for x in lots])
            product = move.product_id
            qty_without_lot = product.qty_available - lots_qty
            if qty_without_lot > 0:
                lots.append({'name': 'Sin lote',
                             'product_id': product,
                             'stock_available': qty_without_lot,
                             'expiry_date': '',
                             'id': 0})

            context = RequestContext(request, {
                'lots': lots,
            })
            return HttpResponse(template.render(context))
    except Exception as e:
        context = RequestContext(request, {
            'lots': [],
        })
        return HttpResponse(template.render(context))
        pass
    finally:
        cursor.commit()
        cursor.close()

def desechar(request, id):
    # Busco usuario,si exite,para el tiempo y crea nuevo tiempo de trabajo
    # Si no exite,creo una nuevo tiempo de trabajo
    # guardo en una session, el id del usuario para futuras busquedas
    pr_id = int(id)
    if request.method == 'POST':
        cantidad = int(request.POST.get("unidades"))
        from erp import POOL, DB, USER
        cursor = DB.cursor()
        prod_obj = POOL.get('stock.move')

        try:
            product = prod_obj.browse(cursor, USER, [pr_id])
            prod_obj = prod_obj.action_scrap(cursor, USER, [product[0].id], cantidad, product[0].location_id.id, context=None)
        except Exception as e:
            context = RequestContext(request, {
                'users_list': False,
                'products': False,
            })
            pass
        finally:
            cursor.commit()
            cursor.close()

            return HttpResponse('<script type="text/javascript">window.close()</script>')
    else:

        template = loader.get_template('conector/desechar.html')
        context={}

        from erp import POOL, DB, USER
        product_obj = POOL.get('stock.move')
        cursor = DB.cursor()
        try:
            product = product_obj.browse(cursor, USER, [pr_id])
            context = RequestContext(request, {
                'product': product[0],
            })
            return HttpResponse(template.render(context))
        except Exception as e:

            context = RequestContext(request, {
                'product': False,
            })
            return HttpResponse(template.render(context))
            pass
        finally:
            cursor.commit()
            cursor.close()

def dividir(request, id):
    # Una vez recibido el post, tengo que llamar a alguna funcion que me pase omar.
    pr_id = int(id)
    template = loader.get_template('conector/dividir.html')
    context={}
    if request.method == 'POST':
        cantidad = int(request.POST.get("unidades"))
        from erp import POOL, DB, USER
        cursor = DB.cursor()
        prod_obj = POOL.get('stock.move')

        try:
            product = prod_obj.browse(cursor, USER, [pr_id])
            # Aqui deberia ir la funcion de Omar
            # split_in_lots(cursor, USER, ids (movimientos), lots=[], context={})

        except Exception as e:
            context = RequestContext(request, {
                'users_list': False,
                'products': False,
            })
            pass
        finally:
            cursor.commit()
            cursor.close()

            return HttpResponse('<script type="text/javascript">window.close()</script>')
    else:

        from erp import POOL, DB, USER
        product_obj = POOL.get('stock.move')
        cursor = DB.cursor()
        try:
            product = product_obj.browse(cursor, USER, [pr_id])
            context = RequestContext(request, {
                'product': product[0],
            })
            return HttpResponse(template.render(context))
        except Exception as e:

            context = RequestContext(request, {
                'product': False,
            })
            return HttpResponse(template.render(context))
            pass
        finally:
            cursor.commit()
            cursor.close()

def tareas(request):
    template = loader.get_template('conector/tareas.html')
    context={}
    from erp import POOL, DB, USER
    cursor = DB.cursor()
    tarea_obj = POOL.get('hr.task')


    try:
        tarea_ids = tarea_obj.search(cursor, USER, [('state', 'not in', ['close','cancel'])], order="name ASC")

        tareas = tarea_obj.browse(cursor, USER, tarea_ids, [])

        users_list = Usuario.objects.filter(end__isnull = True)
        context = RequestContext(request, {
            'users_list': users_list,
            'tareas_list': tareas,
        })
    except Exception as e:
        context = RequestContext(request, {
            'users_list': False,
            'tareas_list': False,
        })
        pass
    finally:
        return HttpResponse(template.render(context))
        cursor.commit()
        cursor.close()

def tarea(request,id=None):
    template = loader.get_template('conector/tarea.html')
    context={}
    from erp import POOL, DB, USER
    cursor = DB.cursor()
    if request.method == 'POST':
        pr_id = int(request.POST.get("pr"))
        description = request.POST.get("description")
        note = request.POST.get("note")
        estado = request.POST.get("state", False)
        vals = {}

        codigo = int(request.session.get('codigo', False))
        tarea_obj = POOL.get('hr.task')
        user_obj = POOL.get('res.users')

        try:
            user_ids = user_obj.search(cursor, USER, [('code', '=', codigo )], order="login ASC")
            users = user_obj.browse(cursor, USER, user_ids)
            #Si no existe la tarea, se crea.
            if not estado:
                vals['name'] = description
                vals['product_id'] = pr_id
                vals['note'] = note
                tareas=tarea_obj.create(cursor,USER, vals)
                #~ set_open(cursor, USER, [tareas[0].id])
                user_access = Usuario.objects.get(code = codigo, end__isnull = True)
                user_access.project = tareas[0].id
                user_access.end = datetime.datetime.now()
                user_access.save()

            else:
            #Si existe, se finaliza.
                tareas_ids = tarea_obj.browse(cursor, USER, pr_id)
                tarea_obj.set_close(cursor, USER, tareas_ids)
                user_access = Usuario.objects.get(code = codigo, end__isnull = True)
                user_access.project = pr_id
                user_access.save()

        except Exception as e:
            print "--->", e
            context = RequestContext(request, {
                'users_list': False,
                'products': False,
            })
            pass
        finally:
            cursor.commit()
            cursor.close()
            return home(request)

    else:


        tarea_obj = POOL.get('hr.task')
        trabajo_obj = POOL.get('product.product')
        try:
            if id != None:
                tarea = tarea_obj.browse(cursor, USER, [int(id)])
            trabajos_ids = trabajo_obj.search(cursor, USER, [('type', '=', 'service'),('analytic_acc_id', '!=', False)], order="name ASC")
            trabajos = trabajo_obj.browse(cursor, USER, trabajos_ids)
            users_list = Usuario.objects.filter(end__isnull = True)
            user_access = Usuario.objects.get(code = request.session['codigo'], end__isnull = True)
            user_access.project = id
            user_access.save()
            if id != None:
                context = RequestContext(request, {
                    'users_list': users_list,
                    'tarea': tarea[0],
                    'trabajos':trabajos,
                })
            else:
                context = RequestContext(request, {
                    'users_list': users_list,
                    'tarea': False,
                    'trabajos':trabajos,
                })
        except Exception as e:
            print "-->", e
            context = RequestContext(request, {
                'users_list': False,
                'tarea': False,
                'trabajos':False,
            })
            pass
        finally:
            return HttpResponse(template.render(context))
            cursor.commit()
            cursor.close()
