from django import template
register = template.Library()

@register.filter
def traduccion(arg):
    estados = {'draft': 'Borrador', 'open': 'Abierto', 'confirmed': 'Confirmada', 'assigned': 'Lista para producir', 'ready': 'Listo para fabricar', 'in_production': 'Produccion iniciada',}
    return estados.get(arg)
