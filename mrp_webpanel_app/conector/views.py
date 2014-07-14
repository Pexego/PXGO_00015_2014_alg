from django.http import HttpResponse
from django.template import RequestContext, loader
from models import Usuario
from erp import POOL, DB, USER
#~

CURSOR = DB.cursor()

def home(request):
    template = loader.get_template('conector/index.html')
    context={}
    print "Entro"
    if request.method == 'POST':
        print "HOLA!"
        from erp import POOL, DB, USER
        codigo = int(request.POST.get("code"))
        user_obj = POOL.get('res.users')
        cursor = DB.cursor()

        try:
            user_ids = user_obj.search(cursor, USER, [('code', '=', codigo )], order="login ASC")
            users = user_obj.browse(cursor, USER, user_ids)
            if user_ids:
                userd= Usuario.objects.filter(code = request.POST.get("code"))
                if not userd:
                    user_acccess = Usuario(code=codigo, name = users[0].name )
                    user_acccess.save()
                return selector(request)
            else:
                context = RequestContext(request, {
                    'nouser': False,
                })
                return HttpResponse(template.render(context))
        except Exception as e:
            print "--->", e
            context = RequestContext(request, {
                'nouser': False,
            })
            return HttpResponse(template.render(context))
            pass
        finally:

            cursor.commit()
            cursor.close()
    else:
        print "SALGO"
        context = RequestContext(request, {
                'nouser': True,
            })
        return HttpResponse(template.render(context))

def selector(request):
    template = loader.get_template('conector/selector.html')

    users_list = Usuario.objects.all()
    print users_list
    context = RequestContext(request, {
            'users_list': users_list,
    })
    return HttpResponse(template.render(context))


def productos(request):
    template = loader.get_template('conector/productos.html')
    context={}

    product_obj = POOL.get('mrp.production')


    try:
        product_ids = product_obj.search(CURSOR, USER, [('state', 'not in', ['done','cancel'])], order="name ASC")
        products = product_obj.browse(CURSOR, USER, product_ids, [])
        print "products: ", products

        users_list = Usuario.objects.all()
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


def producto(request,id):
    template = loader.get_template('conector/producto.html')
    context={}

    production_obj = POOL.get('mrp.production')

    try:
        production = production_obj.browse(CURSOR, USER, [int(id)])
        users_list = Usuario.objects.all()
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


def crear_producto(request):
    print "HOLA"
    if request.method == 'POST':
        print "POST"
        pr_id = int(request.POST.get("pr"))
        vals = {}
        qty = int(request.POST.get("qty"))

        mrp_obj = POOL.get('mrp.production')
        prod_obj = POOL.get('product.product')

        product = prod_obj.browse(CURSOR, USER, pr_id)
        print "HOLA"
        vals['product_id'] = pr_id
        vals['product_qty'] = qty
        vals['product_uom'] = product.uom_id.id
        print "--->", vals
        mrp = mrp_obj.create(CURSOR, USER, vals)
        print "mrp -->", mrp
        mrp = mrp_obj.action_confirm(CURSOR, USER, [mrp])
        print "MRP.-->", mrp
        CURSOR.commit()
        return producto(request, mrp)

    else:
        print "NO POST"
        template = loader.get_template('conector/crear_producto.html')
        context={}

        product_obj = POOL.get('mrp.bom')

        try:
            products_ids = product_obj.search(CURSOR, USER, [('product_id.analytic_acc_id', '!=', False)], order="name ASC")
            products = product_obj.browse(CURSOR, USER, products_ids)
            users_list = Usuario.objects.all()

            context = RequestContext(request, {
                'users_list': users_list,
                'products': products,
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

def procesar(request, id):

    context={}
    pr_id = int(id)

    from erp import POOL, DB, USER

    mrp_obj = POOL.get('mrp.production')
    cursor = DB.cursor()

    try:

        products = mrp_obj.browse(cursor, USER, [pr_id, ])
        product = products[0]

        mrp_obj.action_produce(cursor, USER, product.id, product.product_qty, "consume_produce", context=None)

    except Exception as e:
        print "--->", e
        pass
    finally:
        cursor.commit()
        cursor.close()
        return productos(request)

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
        return productos(request)

def finalizar(request, id):

    context={}
    pr_id = int(id)

    from erp import POOL, DB, USER

    mrp_obj = POOL.get('mrp.production')
    cursor = DB.cursor()

    try:
        mrp_obj.action_production_end(cursor, USER, [pr_id,], *args)
    except Exception as e:
        print "--->", e
        pass
    finally:
        cursor.commit()
        cursor.close()
        return productos(request)
