# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2014 Pexego (<http://www.pexego.es>).
#    $Omar Castiñeira Saavedra$
#    $Alejandro Núñez Liz$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from django.http import HttpResponse
from django.template import RequestContext, loader
from django.shortcuts import redirect
from models import Usuario
import datetime,time
from django.utils import timezone

def timestamp(date):
    return time.mktime(date.timetuple())/3600



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
                    user_access.end = timezone.now()
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
                    'inicio': True,
                })
                return HttpResponse(template.render(context))
        except Exception as e:
            return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
            context = RequestContext(request, {
                'nouser': False,
                'inicio': True,
            })
            return HttpResponse(template.render(context))
            pass
        finally:

            cursor.commit()
            cursor.close()
    else:

        context = RequestContext(request, {
                'nouser': True,
                'inicio': True,
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
    oerp_ctx = {'lang': 'es_ES'}
    from erp import POOL, DB, USER
    cursor = DB.cursor()
    product_obj = POOL.get('mrp.production')


    try:
        product_ids = product_obj.search(cursor, USER, [('state', 'not in', ['done','cancel'])], order="name ASC")
        products = product_obj.browse(cursor, USER, product_ids, context=oerp_ctx)

        users_list = Usuario.objects.filter(end__isnull = True)
        context = RequestContext(request, {
            'users_list': users_list,
            'products_list': products,
        })
    except Exception as e:
        return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
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
    oerp_ctx = {'lang': 'es_ES'}
    from erp import POOL, DB, USER
    cursor = DB.cursor()

    production_obj = POOL.get('mrp.production')
    try:
        production = production_obj.browse(cursor, USER, [int(id)], context=oerp_ctx)
        users_list = Usuario.objects.filter(end__isnull = True)
        user_access = Usuario.objects.get(code = request.session['codigo'], end__isnull = True)
        user_access.project = id
        user_access.save()
        context = RequestContext(request, {
            'users_list': users_list,
            'product': production[0],
        })
    except Exception as e:
        return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
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
    oerp_ctx = {'lang': 'es_ES'}
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
        mrp = 0
        try:
            user_ids = user_obj.search(cursor, USER, [('code', '=', codigo )], order="login ASC")
            users = user_obj.browse(cursor, USER, user_ids, context=oerp_ctx)
            product = prod_obj.browse(cursor, USER, pr_id)
            vals['date_planned'] = timezone.now()
            vals['product_id'] = pr_id
            vals['product_qty'] = qty
            vals['warehouse_id'] = w_id
            vals['product_uom'] = product.uom_id.id
            vals['user_id'] = users[0].id

            mrp = mrp_obj.create(cursor, USER, vals)
            wf_service.trg_validate(USER, 'mrp.production', mrp, 'button_confirm', cursor)
            user_access = Usuario.objects.get(code = codigo, end__isnull = True)
            user_access.project = mrp
            user_access.save()
        except Exception as e:
            return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
            context = RequestContext(request, {
                'users_list': False,
                'products': False,
            })
            pass
        finally:
            cursor.commit()
            cursor.close()

            return redirect('/producto/' + str(mrp))

    else:
        template = loader.get_template('conector/crear_producto.html')
        context={}
        from erp import POOL, DB, USER
        cursor = DB.cursor()
        product_obj = POOL.get('product.product')
        warehouse_obj = POOL.get('stock.warehouse')
        try:
            products_ids = product_obj.search(cursor, USER, [('analytic_acc_id', '!=', False),('bom_ids', '!=', False)], order="name ASC")
            products = product_obj.browse(cursor, USER, products_ids, context=oerp_ctx)
            warehouse_ids = warehouse_obj.search(cursor, USER, [], order="name ASC")
            warehouses = warehouse_obj.browse(cursor, USER, warehouse_ids, context=oerp_ctx)
            users_list = Usuario.objects.filter(end__isnull = True)

            context = RequestContext(request, {
                'users_list': users_list,
                'products': products,
                'warehouses':warehouses,
            })
        except Exception as e:
            return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
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
    oerp_ctx = {'lang': 'es_ES'}


    try:
        product = mrp_obj.browse(cursor, USER, [pr_id], context=oerp_ctx)
        mrp = mrp_obj.force_production(cursor, USER, [product[0].id])
        #mrp_obj.action_produce(cursor, USER, product[0].id, product[0].product_qty, "consume_produce")
    except Exception as e:
        return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
        pass
    finally:
        cursor.commit()
        cursor.close()

        return HttpResponse('<script type="text/javascript">window.location.replace("/producto/'+id+'/");</script>')
        #return home(request)

def abrir(request, id):

    context={}
    pr_id = int(id)

    from erp import POOL, DB, USER

    mrp_obj = POOL.get('mrp.production')
    cursor = DB.cursor()

    try:
        mrp_obj.action_ready(cursor, USER, [pr_id], *args)
    except Exception as e:
        return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
        pass
    finally:
        cursor.commit()
        cursor.close()
        return home(request)

def finalizar(request, id):

    context={}
    pr_id = int(id)
    codigo = int(request.session.get('codigo', False))
    oerp_ctx = {'lang': 'es_ES'}
    from erp import POOL, DB, USER
    user_obj = POOL.get('res.users')
    mrp_obj = POOL.get('mrp.production')
    time_obj = POOL.get('hr.analytic.timesheet')
    hr_obj = POOL.get('hr.employee')
    cursor = DB.cursor()

    try:
        mrp = mrp_obj.browse(cursor, USER, pr_id)
        mrp_obj.action_produce(cursor, USER, mrp.id, mrp.product_qty, "consume_produce")
        mrp_obj.action_production_end(cursor, USER, [mrp.id,])
        user_access = Usuario.objects.filter(project = id, end__isnull = True)

        for u in user_access:
            u.end=timezone.now()
            u.save()
        users_time = Usuario.objects.filter(project = id )
        for t in users_time:

            user_ids = user_obj.search(cursor, USER, [('code', '=', t.code )], order="login ASC")
            usere = user_obj.browse(cursor, USER, user_ids)

            hr_ids = hr_obj.search(cursor, USER, [('user_id', '=', usere[0].id )], order="login ASC")
            hr_usere = hr_obj.browse(cursor, USER, hr_ids, context=oerp_ctx)

            vals = {}
            vals['production_id'] = pr_id
            vals['journal_id'] =  hr_usere[0].journal_id.id
            vals['product_uom_id'] = mrp.product_id.uom_id.id
            vals['product_id'] = mrp.product_id.id
            vals['general_account_id'] = False
            vals['account_id'] = mrp.product_id.analytic_acc_id.id
            vals['date'] = t.end
            vals['unit_amount'] = timestamp(t.end) - timestamp(t.start)
            vals['name'] = mrp.name
            vals['user_id'] = usere[0].id
            vals['amount'] = hr_usere[0].product_id.standard_price * vals['unit_amount']
            time_obj.create(cursor, USER, vals, context=oerp_ctx)

    except Exception as e:
        print "-->", e
        return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
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
    oerp_ctx = {'lang': 'es_ES'}
    move = move_obj.browse(cursor, USER, move_id, context=oerp_ctx)
    lot_ids = lot_obj.search(cursor, USER, [('product_id', '=', move.product_id.id),('stock_available', '>', 0.0)])
    try:
        if request.method == 'POST':
            selected_lots = []
            for field in  request.POST:
                if 'foo' in field:
                    selected_lots.append(int(request.POST[field]))

            if selected_lots:
                move_obj.apply_lots_in_production(cursor, USER, [move.id], selected_lots)
            return HttpResponse('<script type="text/javascript">opener.location.reload();window.close()</script>')
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
        return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
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
    oerp_ctx = {'lang': 'es_ES'}
    if request.method == 'POST':
        cantidad = int(request.POST.get("unidades"))
        from erp import POOL, DB, USER
        cursor = DB.cursor()
        prod_obj = POOL.get('stock.move')

        try:
            product = prod_obj.browse(cursor, USER, [pr_id], context=oerp_ctx)
            prod_obj = prod_obj.action_scrap(cursor, USER, [product[0].id], cantidad, product[0].location_id.id, context=oerp_ctx)
        except Exception as e:
            return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
            context = RequestContext(request, {
                'users_list': False,
                'products': False,
            })
            pass
        finally:
            cursor.commit()
            cursor.close()

            return HttpResponse('<script type="text/javascript">opener.location.reload();window.close();</script>')
    else:

        template = loader.get_template('conector/desechar.html')
        context={}

        from erp import POOL, DB, USER
        product_obj = POOL.get('stock.move')
        cursor = DB.cursor()
        try:
            product = product_obj.browse(cursor, USER, [pr_id], context=oerp_ctx)
            context = RequestContext(request, {
                'product': product[0],
            })
            return HttpResponse(template.render(context))
        except Exception as e:
            return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
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
    oerp_ctx = {'lang': 'es_ES'}

    if request.method == 'POST':
        from erp import POOL, DB, USER
        cursor = DB.cursor()
        move_obj = POOL.get('stock.move')
        lot_obj = POOL.get('stock.production.lot')

        try:
            updated=False
            move = move_obj.browse(cursor, USER, pr_id)
            new_lots = {}
            for product, qty in zip(request.POST.getlist("product"), request.POST.getlist("unidades")):
                qty = float(qty)
                product = int(product)
                if product == move.product_id.id and not updated:
                    move.write({'product_qty': qty})
                    updated = True
                else:
                    copy_vals = {'product_id': product, 'product_qty': qty}
                    if move.prodlot_id:
                        if move.product_id.id == product:
                            copy_vals['prodlot_id'] = move.prodlot_id.id
                        else:
                            if new_lots.get(product, False):
                                new_lot = new_lots[product]
                            else:
                                new_lot = lot_obj.copy(cursor, USER, move.prodlot_id.id, {'product_id': product})
                                new_lots[product] = new_lot
                            copy_vals['prodlot_id'] = new_lot
                    new_move = move_obj.copy(cursor, USER, move.id, copy_vals)

            if not updated and request.POST.get("product", False):
                move_obj.unlink(cursor, USER, [move.id])

        except Exception as e:
            return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
            context = RequestContext(request, {
                'users_list': False,
                'products': False,
            })
            pass
        finally:
            cursor.commit()
            cursor.close()

            return HttpResponse('<script type="text/javascript">opener.location.reload();window.close()</script>')
    else:

        from erp import POOL, DB, USER
        product_obj = POOL.get('product.product')
        move_obj = POOL.get('stock.move')
        cursor = DB.cursor()
        try:
            move = move_obj.browse(cursor, USER, [pr_id])
            products_ids = product_obj.search(cursor, USER, [('analytic_acc_id', '!=', False),('type', '=', 'product')], order="name ASC", context=oerp_ctx)
            products = product_obj.browse(cursor, USER, products_ids, context=oerp_ctx)
            context = RequestContext(request, {
                'move': move[0],
                'products': products,
            })
            return HttpResponse(template.render(context))
        except Exception as e:
            return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
            context = RequestContext(request, {
                'move': False,
                'products': []
            })
            return HttpResponse(template.render(context))
            pass
        finally:
            cursor.commit()
            cursor.close()

def tareas(request):
    template = loader.get_template('conector/tareas.html')
    context={}
    oerp_ctx = {'lang': 'es_ES'}
    from erp import POOL, DB, USER
    cursor = DB.cursor()
    tarea_obj = POOL.get('hr.task')
    time_obj = POOL.get('hr.analytic.timesheet')

    try:
        tarea_ids = tarea_obj.search(cursor, USER, [('state', 'not in', ['close','cancel'])], order="name ASC")

        tareas = tarea_obj.browse(cursor, USER, tarea_ids, context=oerp_ctx)

        users_list = Usuario.objects.filter(end__isnull = True)
        context = RequestContext(request, {
            'users_list': users_list,
            'tareas_list': tareas,
        })
    except Exception as e:
        return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
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
    oerp_ctx = {'lang': 'es_ES'}
    from erp import POOL, DB, USER
    cursor = DB.cursor()
    tar = False
    if request.method == 'POST':

        pr_id = int(request.POST.get("pr"))
        description = request.POST.get("description")
        note = request.POST.get("note")
        estado = request.POST.get("state", False)
        task_id = request.POST.get("taskid", False)
        kg_mov = request.POST.get("kg_mov", False)
        vals = {}

        codigo = int(request.session.get('codigo', False))
        tarea_obj = POOL.get('hr.task')
        user_obj = POOL.get('res.users')
        time_obj = POOL.get('hr.analytic.timesheet')
        hr_obj = POOL.get('hr.employee')

        try:
            if request.POST.get('accion') == "Guardar":
                tarea_id = tarea_obj.browse(cursor, USER, int(task_id), context=oerp_ctx)
                vals['name'] = description
                vals['product_id'] = pr_id
                vals['note'] = note
                tarea_obj.write(cursor, USER, [tarea_id.id], vals, context=oerp_ctx)
            else:

                #Si no existe la tarea, se crea.
                if not estado:
                    vals['name'] = description
                    vals['product_id'] = pr_id
                    vals['note'] = note
                    tareas=tarea_obj.create(cursor,USER, vals)
                    task_id = int(tareas)
                    user_access = Usuario.objects.get(code = codigo, end__isnull = True)
                    user_access.task = tareas
                    user_access.save()


                else:
                #Si existe, se finaliza o se abre, dependiendo del estado.
                    tareas_ids = tarea_obj.browse(cursor, USER, int(task_id), context=oerp_ctx)

                    user_access = Usuario.objects.get(code = codigo, end__isnull = True)
                    if tareas_ids.state == "draft":
                        tarea_obj.set_open(cursor, USER, [tareas_ids.id])
                        user_access.task = task_id
                        user_access.save()

                    else:
                        tar = True

                        user_access.task = task_id
                        user_access.end = timezone.now()
                        user_access.save()

                        user_access = Usuario.objects.filter(task = id, end__isnull = True)
                        for u in user_access:
                            u.end=timezone.now()
                            u.save()

                        users_time = Usuario.objects.filter(task = id )

                        for t in users_time:

                            user_ids = user_obj.search(cursor, USER, [('code', '=', t.code )], order="login ASC")
                            usere = user_obj.browse(cursor, USER, user_ids)

                            hr_ids = hr_obj.search(cursor, USER, [('user_id', '=', usere[0].id )], order="login ASC")
                            hr_usere = hr_obj.browse(cursor, USER, hr_ids, context=oerp_ctx)

                            vals = {}
                            vals['hr_task_id'] = tareas_ids.id
                            vals['journal_id'] =  hr_usere[0].journal_id.id
                            vals['product_uom_id'] = tareas_ids.product_id.uom_id.id
                            vals['product_id'] = tareas_ids.product_id.id
                            vals['general_account_id'] = False
                            vals['account_id'] = tareas_ids.product_id.analytic_acc_id.id
                            vals['date'] = t.end
                            vals['unit_amount'] = timestamp(t.end) - timestamp(t.start)
                            vals['name'] = tareas_ids.name
                            vals['user_id'] = usere[0].id
                            vals['amount'] = hr_usere[0].product_id.standard_price * vals['unit_amount']
                            time_obj.create(cursor, USER, vals, context=oerp_ctx)
                        
                        vals['name'] = description
                        vals['product_id'] = pr_id
                        vals['note'] = note
                        vals['kg_moved'] = kg_mov
                        tarea_obj.write(cursor, USER, [tareas_ids.id], vals, context=oerp_ctx)
                        tarea_obj.set_close(cursor, USER, [tareas_ids.id])

        except Exception as e:
            return HttpResponse('<script type="text/javascript">alert(Error message: '+unicode(e).replace("\"","|")+'");</script>')
            pass
        finally:
            cursor.commit()
            cursor.close()

            #return home(request)
        if tar == False:
            return HttpResponse('<script type="text/javascript">window.location.replace("/tarea/'+str(task_id)+'/");</script>')
        else:
            return HttpResponse('<script type="text/javascript">window.location.replace("/");</script>')
    else:


        tarea_obj = POOL.get('hr.task')
        trabajo_obj = POOL.get('product.product')
        try:
            if id != None:
                tarea = tarea_obj.browse(cursor, USER, [int(id)])
            trabajos_ids = trabajo_obj.search(cursor, USER, [('type', '=', 'service'),('analytic_acc_id', '!=', False)], order="name ASC")
            trabajos = trabajo_obj.browse(cursor, USER, trabajos_ids, context=oerp_ctx)
            users_list = Usuario.objects.filter(end__isnull = True)
            user_access = Usuario.objects.get(code = request.session['codigo'], end__isnull = True)
            user_access.task = id
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
            return HttpResponse('<script type="text/javascript">alert("Error message: '+e+'");</script>')
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


def salir(request):
    # Busco usuario,si exite,para el tiempo y borro sesion

    template = loader.get_template('conector/index.html')
    context={}
    codigo = int(request.session.get('codigo', False))
    from erp import POOL, DB, USER
    user_obj = POOL.get('res.users')
    cursor = DB.cursor()
    try:
        user_ids = user_obj.search(cursor, USER, [('code', '=', codigo )], order="login ASC")
        users = user_obj.browse(cursor, USER, user_ids)
        if users:
            user_access= Usuario.objects.get(code = codigo, end__isnull = True)
            user_access.end = timezone.now()
            user_access.save()
            del request.session['codigo']
        else:
            context = RequestContext(request, {
                'nouser': False,
            })
            return HttpResponse(template.render(context))
    except Exception as e:
        return HttpResponse('<script type="text/javascript">alert("Error message: '+unicode(e)+'");</script>')
        context = RequestContext(request, {
            'nouser': False,
        })
        pass
    finally:
        cursor.commit()
        cursor.close()
    return HttpResponse('<script type="text/javascript">window.location.replace("/");</script>')
