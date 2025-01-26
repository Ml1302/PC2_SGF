from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Max, Q
from .models import Cuenta, Transaccion, Categoria_ecuacion_contable
from .forms import CuentaForm, TransaccionForm

# Vista para crear una cuenta
def crear_cuenta(request):
    if request.method == 'POST':
        form = CuentaForm(request.POST)
        if form.is_valid():
            form.save()  # Guarda la cuenta en la base de datos
            return redirect(reverse('registros:listar_cuentas'))  # Redirige a la lista de cuentas con namespace
    else:
        form = CuentaForm()  # Si no es un POST, muestra el formulario vacío

    return render(request, 'crear_cuenta.html', {'form': form})

def custom_sort_key(cuenta):
    """
    Función auxiliar para ordenar cuentas por dígitos
    Convierte el ID en una lista de dígitos para comparación
    """
    return [int(d) for d in str(cuenta.id_cuenta)]

# Vista para listar las cuentas
def listar_cuentas(request):
    try:
        # Obtener todas las cuentas activas
        cuentas = Cuenta.objects.filter(activo=True).select_related('id_categoria')
        
        # Convertir QuerySet a lista y ordenar usando sorted con key personalizada
        cuentas_ordenadas = sorted(cuentas, key=custom_sort_key)
        
        return render(request, 'listar_cuentas.html', {'cuentas': cuentas_ordenadas})
    except Exception as e:
        print(f"Error en listar_cuentas: {e}")  # Para debugging
        return render(request, 'listar_cuentas.html', {'error': str(e)})

# Vista para crear una transacción
from django.db import transaction
from .models import DetalleTransaccion
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
import json
from .models import Transaccion, DetalleTransaccion, Cuenta

def ingresar_transaccion(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear la transacción principal
                nueva_transaccion = Transaccion.objects.create(
                    fecha_transaccion=request.POST.get('fecha'),
                    glosa=request.POST.get('glosa')
                )

                # Procesar los detalles
                detalles = json.loads(request.POST.get('detalles', '[]'))
                for detalle in detalles:
                    DetalleTransaccion.objects.create(
                        transaccion=nueva_transaccion,
                        cuenta_id=detalle['cuenta'],
                        monto=detalle['monto'],
                        es_debe=detalle['es_debe']
                    )

                messages.success(request, 'Transacción registrada exitosamente')
                return redirect('registros:listar_transacciones')
        except Exception as e:
            messages.error(request, f'Error al registrar la transacción: {str(e)}')
    
    cuentas = Cuenta.objects.filter(activo=True)
    return render(request, 'ingresar_transaccion.html', {'cuentas': cuentas})

def listar_transacciones(request):
    transacciones = Transaccion.objects.prefetch_related('detalles', 'detalles__cuenta').all()
    if request.method == 'POST':
        mes = request.POST.get('mes')
        anio = request.POST.get('anio')
        if mes and anio:
            transacciones = transacciones.filter(
                fecha_transaccion__month=mes,
                fecha_transaccion__year=anio
            )
    return render(request, 'listar_transacciones.html', {'transacciones': transacciones})

def home(request):
    return render(request, 'home.html')

def configuracion(request):
    if request.method == 'POST':
        menu_orientation = request.POST.get('menu_orientation')
        theme_color = request.POST.get('theme_color')

        # Guardar configuración en sesión (puedes adaptarlo a la base de datos si es necesario)
        request.session['menu_orientation'] = menu_orientation
        request.session['theme_color'] = theme_color

        return redirect('home')
    return render(request, 'configuracion.html')

def ver_diario(request):
    transacciones = Transaccion.objects.all()
    return render(request, 'diario.html',{'transacciones': transacciones})  

def ver_mayor(request):
    cuentas = Cuenta.objects.all()
    transacciones = DetalleTransaccion.objects.all()
    
    # Define todos los meses
    nombres_meses = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]

    # Ya no necesitamos filtrar los meses, usamos la lista completa
    meses_unicos = nombres_meses
    
    años_set = set()

    # Agrupar meses y años
    for detalle in transacciones:
        años_set.add(detalle.transaccion.fecha_transaccion.year)

    años_unicos = [(año, año) for año in sorted(años_set)]

    transacciones_debe = []
    transacciones_haber = []
    saldo_deudor = 0
    saldo_acreedor = 0
    nombre_cuenta = ""

    if request.method == 'POST':
        tipo_cuenta = request.POST.get('tipo_cuenta')
        mes = request.POST.get('mes')
        año = request.POST.get('año')

        if tipo_cuenta and mes and año:
            # Filtrar las transacciones por cuenta, mes y año
            transacciones_debe = DetalleTransaccion.objects.filter(
                cuenta_id=tipo_cuenta,
                es_debe=True,
                transaccion__fecha_transaccion__month=mes,
                transaccion__fecha_transaccion__year=año
            ).select_related('transaccion')

            transacciones_haber = DetalleTransaccion.objects.filter(
                cuenta_id=tipo_cuenta,
                es_debe=False,
                transaccion__fecha_transaccion__month=mes,
                transaccion__fecha_transaccion__year=año
            ).select_related('transaccion')

            # Calcular totales
            total_debe = sum(t.monto for t in transacciones_debe)
            total_haber = sum(t.monto for t in transacciones_haber)

            # Calcular saldos
            if total_debe > total_haber:
                saldo_deudor = total_debe - total_haber
            else:
                saldo_acreedor = total_haber - total_debe

            # Obtener el nombre de la cuenta
            if tipo_cuenta:
                cuenta = Cuenta.objects.get(id_cuenta=tipo_cuenta)
                nombre_cuenta = cuenta.nombre_cuenta

    return render(request, 'mayor.html', {
        'cuentas': cuentas,
        'transacciones_debe': transacciones_debe,
        'transacciones_haber': transacciones_haber,
        'meses': meses_unicos,
        'años': años_unicos,
        'nombre_cuenta': nombre_cuenta,
        'saldo_deudor': saldo_deudor,
        'saldo_acreedor': saldo_acreedor,
        'total_debe': sum(t.monto for t in transacciones_debe),
        'total_haber': sum(t.monto for t in transacciones_haber),
    })

def balanza_comprobacion(request):
    cuentas = Cuenta.objects.all()  # Obtener todas las cuentas
    transacciones = Transaccion.objects.all()  # Obtener todas las transacciones

    meses_set = set()
    años_set = set()

    # Agrupar meses y años manualmente
    for transaccion in transacciones:
        meses_set.add(transaccion.fecha_transaccion.month)
        años_set.add(transaccion.fecha_transaccion.year)

    nombres_meses = [
        '', 'enero', 'febrero', 'marzo', 'abril', 
        'mayo', 'junio', 'julio', 'agosto', 
        'septiembre', 'octubre', 'noviembre', 'diciembre'
    ]

    meses_unicos = [(mes, nombres_meses[mes]) for mes in sorted(meses_set)]
    años_unicos = [(año, año) for año in sorted(años_set)]

    # Inicializar el diccionario para los saldos de cada cuenta
    cuentas_saldos = {}

    # Inicializar los totales
    total_debe = 0
    total_haber = 0

    # Procesar la solicitud POST
    if request.method == 'POST':
        mes = request.POST.get('mes')
        año = request.POST.get('año')

        # Calcular saldos para todas las cuentas
        for cuenta in cuentas:
            # Filtrar transacciones para la cuenta actual
            transacciones_debe = transacciones.filter(id_cuenta_cargo_id=cuenta.id_cuenta)
            transacciones_haber = transacciones.filter(id_cuenta_abono_id=cuenta.id_cuenta)

            # Filtrar por mes y año, si se proporcionan
            if mes and año:
                transacciones_debe = transacciones_debe.filter(
                    fecha_transaccion__month=mes,
                    fecha_transaccion__year=año
                )
                transacciones_haber = transacciones_haber.filter(
                    fecha_transaccion__month=mes,
                    fecha_transaccion__year=año
                )

            # Calcular los montos totales
            total_debe_cuenta = sum(t.monto_transaccion for t in transacciones_debe)
            total_haber_cuenta = sum(t.monto_transaccion for t in transacciones_haber)

            # Calcular saldo_deudor y saldo_acreedor
            saldo_deudor = total_debe_cuenta - total_haber_cuenta if total_debe_cuenta > total_haber_cuenta else 0
            saldo_acreedor = total_haber_cuenta - total_debe_cuenta if total_haber_cuenta > total_debe_cuenta else 0

            # Almacenar en el diccionario
            cuentas_saldos[cuenta.nombre_cuenta] = {
                'saldo_deudor': saldo_deudor,
                'saldo_acreedor': saldo_acreedor
            }

            # Sumar al total
            total_debe += saldo_deudor
            total_haber += saldo_acreedor

    return render(request, 'balanza_comprobacion.html', {
        'cuentas': cuentas,
        'meses': meses_unicos,
        'años': años_unicos,
        'cuentas_saldos': cuentas_saldos,  # Pasar el diccionario de saldos a la plantilla
        'total_debe': total_debe,  # Pasar el total_debe a la plantilla
        'total_haber': total_haber,  # Pasar el total_haber a la plantilla
    })

def estado_resultados(request):
    cuentas = Cuenta.objects.all()  # Obtener todas las cuentas
    transacciones = Transaccion.objects.all()  # Obtener todas las transacciones

    meses_set = set()
    años_set = set()

    # Agrupar meses y años manualmente
    for transaccion in transacciones:
        meses_set.add(transaccion.fecha_transaccion.month)
        años_set.add(transaccion.fecha_transaccion.year)

    nombres_meses = [
        '', 'enero', 'febrero', 'marzo', 'abril', 
        'mayo', 'junio', 'julio', 'agosto', 
        'septiembre', 'octubre', 'noviembre', 'diciembre'
    ]

    meses_unicos = [(mes, nombres_meses[mes]) for mes in sorted(meses_set)]
    años_unicos = [(año, año) for año in sorted(años_set)]

    # Inicializar los diccionarios para los saldos de cada cuenta
    cuentas_ingresos = {}
    cuentas_gastos = {}

    # Inicializar los totales
    total_ingresos = 0
    total_gastos = 0

    # Procesar la solicitud POST
    if request.method == 'POST':
        mes = request.POST.get('mes')
        año = request.POST.get('año')

        # Calcular saldos para todas las cuentas
        for cuenta in cuentas:
            # Filtrar transacciones para la cuenta actual
            transacciones_debe = transacciones.filter(id_cuenta_cargo_id=cuenta.id_cuenta)
            transacciones_haber = transacciones.filter(id_cuenta_abono_id=cuenta.id_cuenta)

            # Filtrar por mes y año, si se proporcionan
            if mes and año:
                transacciones_debe = transacciones_debe.filter(
                    fecha_transaccion__month=mes,
                    fecha_transaccion__year=año
                )
                transacciones_haber = transacciones_haber.filter(
                    fecha_transaccion__month=mes,
                    fecha_transaccion__year=año
                )

            # Calcular los montos totales
            total_debe_cuenta = sum(t.monto_transaccion for t in transacciones_debe)
            total_haber_cuenta = sum(t.monto_transaccion for t in transacciones_haber)

            # Calcular saldo_deudor y saldo_acreedor
            saldo_deudor = total_debe_cuenta - total_haber_cuenta if total_debe_cuenta > total_haber_cuenta else 0
            saldo_acreedor = total_haber_cuenta - total_debe_cuenta if total_haber_cuenta > total_debe_cuenta else 0

            # Almacenar en los diccionarios según el tipo de cuenta
            if cuenta.id_categoria.nombre_categoria == 'Ingresos':  # Suponiendo que el tipo de cuenta es una cadena
                cuentas_ingresos[cuenta.nombre_cuenta] = {
                    'saldo_deudor': saldo_deudor,
                    'saldo_acreedor': saldo_acreedor
                }
                total_ingresos += saldo_acreedor  # Sumar al total de ingresos
            elif cuenta.id_categoria.nombre_categoria == 'Gastos':  # Suponiendo que el tipo de cuenta es una cadena
                cuentas_gastos[cuenta.nombre_cuenta] = {
                    'saldo_deudor': saldo_deudor,
                    'saldo_acreedor': saldo_acreedor
                }
                total_gastos += saldo_deudor  # Sumar al total de gastos

    utilidad_neta = total_ingresos - total_gastos

    return render(request, 'estado_resultados.html', {
        'cuentas': cuentas,
        'meses': meses_unicos,
        'años': años_unicos,
        'cuentas_ingresos': cuentas_ingresos,  # Pasar el diccionario de ingresos a la plantilla
        'cuentas_gastos': cuentas_gastos,  # Pasar el diccionario de gastos a la plantilla
        'total_ingresos': total_ingresos,  # Pasar el total_ingresos a la plantilla
        'total_gastos': total_gastos,  # Pasar el total_gastos a la plantilla
        'utilidad_neta': utilidad_neta
    })

from django.shortcuts import render

def estado_capital_contable_propietario(request):
    cuentas = Cuenta.objects.all()  # Obtener todas las cuentas
    transacciones = Transaccion.objects.all()  # Obtener todas las transacciones

    meses_set = set()
    años_set = set()

    # Agrupar meses y años manualmente
    for transaccion in transacciones:
        meses_set.add(transaccion.fecha_transaccion.month)
        años_set.add(transaccion.fecha_transaccion.year)

    nombres_meses = [
        '', 'enero', 'febrero', 'marzo', 'abril',
        'mayo', 'junio', 'julio', 'agosto',
        'septiembre', 'octubre', 'noviembre', 'diciembre'
    ]

    meses_unicos = [(mes, nombres_meses[mes]) for mes in sorted(meses_set)]
    años_unicos = [(año, año) for año in sorted(años_set)]

    # Inicializar los diccionarios para los saldos de cada cuenta
    cuentas_ingresos = {}
    cuentas_gastos = {}

    # Inicializar los totales
    total_ingresos = 0
    total_gastos = 0

    # Inicializar variables para capital, retiros, inversiones, y el mes seleccionado
    capital_inicio_mes = 0
    retiros_propietario = 0
    inversiones = {'saldo_deudor': 0, 'saldo_acreedor': 0}
    mes_escogido = None
    año = None  # Inicializar la variable año aquí
    ultimo_dia_registrado_mes = None  # Inicializar la variable

    # Procesar la solicitud POST
    if request.method == 'POST':
        mes = int(request.POST.get('mes'))
        año = int(request.POST.get('año'))

        # Guardar el mes escogido
        mes_escogido = nombres_meses[mes]

        # Filtrar las transacciones hasta el mes y año anterior seleccionados
        transacciones_anteriores = transacciones.filter(
            fecha_transaccion__lt=f'{año}-{mes:02d}-01'  # Menor que el primer día del mes seleccionado
        )

        # Calcular saldo de la cuenta capital para meses anteriores
        cuenta_capital = Cuenta.objects.get(nombre_cuenta='Capital')
        transacciones_capital_debe = transacciones_anteriores.filter(id_cuenta_cargo_id=cuenta_capital.id_cuenta)
        transacciones_capital_haber = transacciones_anteriores.filter(id_cuenta_abono_id=cuenta_capital.id_cuenta)

        total_debe_capital = sum(t.monto_transaccion for t in transacciones_capital_debe)
        total_haber_capital = sum(t.monto_transaccion for t in transacciones_capital_haber)

        capital_inicio_mes = total_haber_capital - total_debe_capital  # Capital acumulado hasta el mes anterior

        # Calcular saldo de la cuenta retiros para el mes seleccionado
        cuenta_retiros = Cuenta.objects.get(nombre_cuenta='Retiros')
        transacciones_retiros_debe = transacciones.filter(
            id_cuenta_cargo_id=cuenta_retiros.id_cuenta,
            fecha_transaccion__year=año,
            fecha_transaccion__month=mes
        )
        transacciones_retiros_haber = transacciones.filter(
            id_cuenta_abono_id=cuenta_retiros.id_cuenta,
            fecha_transaccion__year=año,
            fecha_transaccion__month=mes
        )

        total_debe_retiros = sum(t.monto_transaccion for t in transacciones_retiros_debe)
        total_haber_retiros = sum(t.monto_transaccion for t in transacciones_retiros_haber)

        retiros_propietario = total_debe_retiros - total_haber_retiros  # Saldos de la cuenta retiros en el mes seleccionado

        # Calcular saldo de la cuenta capital (deudor y acreedor) para el mes seleccionado (inversiones)
        transacciones_capital_debe_mes = transacciones.filter(
            id_cuenta_cargo_id=cuenta_capital.id_cuenta,
            fecha_transaccion__year=año,
            fecha_transaccion__month=mes
        )
        transacciones_capital_haber_mes = transacciones.filter(
            id_cuenta_abono_id=cuenta_capital.id_cuenta,
            fecha_transaccion__year=año,
            fecha_transaccion__month=mes
        )

        inversiones['saldo_deudor'] = sum(t.monto_transaccion for t in transacciones_capital_debe_mes)
        inversiones['saldo_acreedor'] = sum(t.monto_transaccion for t in transacciones_capital_haber_mes)

        # Calcular saldos para todas las cuentas
        for cuenta in cuentas:
            # Filtrar transacciones para la cuenta actual
            transacciones_debe = transacciones.filter(id_cuenta_cargo_id=cuenta.id_cuenta)
            transacciones_haber = transacciones.filter(id_cuenta_abono_id=cuenta.id_cuenta)

            # Filtrar por mes y año, si se proporcionan
            if mes and año:
                transacciones_debe = transacciones_debe.filter(
                    fecha_transaccion__month=mes,
                    fecha_transaccion__year=año
                )
                transacciones_haber = transacciones_haber.filter(
                    fecha_transaccion__month=mes,
                    fecha_transaccion__year=año
                )

            # Calcular los montos totales
            total_debe_cuenta = sum(t.monto_transaccion for t in transacciones_debe)
            total_haber_cuenta = sum(t.monto_transaccion for t in transacciones_haber)

            # Calcular saldo_deudor y saldo_acreedor
            saldo_deudor = total_debe_cuenta - total_haber_cuenta if total_debe_cuenta > total_haber_cuenta else 0
            saldo_acreedor = total_haber_cuenta - total_debe_cuenta if total_haber_cuenta > total_debe_cuenta else 0

            # Almacenar en los diccionarios según el tipo de cuenta
            if cuenta.id_categoria.nombre_categoria == 'Ingresos':                
                cuentas_ingresos[cuenta.nombre_cuenta] = {
                    'saldo_deudor': saldo_deudor,
                    'saldo_acreedor': saldo_acreedor
                }
                total_ingresos += saldo_acreedor
            elif cuenta.id_categoria.nombre_categoria == 'Gastos':                
                cuentas_gastos[cuenta.nombre_cuenta] = {
                    'saldo_deudor': saldo_deudor,
                    'saldo_acreedor': saldo_acreedor
                }
                total_gastos += saldo_deudor

        # Filtrar las transacciones del mes y año seleccionados para obtener el último día registrado
        transacciones_mes = transacciones.filter(
            fecha_transaccion__year=año,
            fecha_transaccion__month=mes
        )

        # Obtener el último día registrado en ese mes
        ultimo_dia_registrado_mes = transacciones_mes.aggregate(Max('fecha_transaccion'))['fecha_transaccion__max']

    utilidad_neta = total_ingresos - total_gastos
    total_suma_utilidad_inversiones = utilidad_neta + inversiones['saldo_acreedor']
    capital_fin_mes = total_suma_utilidad_inversiones - retiros_propietario

    return render(request, 'estado_capital_contable_propietario.html', {
        'cuentas': cuentas,
        'meses': meses_unicos,
        'años': años_unicos,
        'cuentas_ingresos': cuentas_ingresos,
        'cuentas_gastos': cuentas_gastos,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'utilidad_neta': utilidad_neta,
        'capital_inicio_mes': capital_inicio_mes,
        'retiros_propietario': retiros_propietario,
        'inversiones': inversiones,
        'mes': mes_escogido,
        'año': año,  # Asegúrate de pasar la variable año, incluso si es None
        'total_suma_utilidad_inversiones': total_suma_utilidad_inversiones,
        'capital_fin_mes': capital_fin_mes,
        'ultimo_dia_registrado_mes': ultimo_dia_registrado_mes  # Pasar el último día registrado
    })

def estado_balance_general(request):
    cuentas = Cuenta.objects.all()  # Obtener todas las cuentas
    transacciones = Transaccion.objects.all()  # Obtener todas las transacciones

    meses_set = set()
    años_set = set()

    # Obtener la última transacción
    fecha_ultima_transaccion = None  # Inicializar la variable
    if transacciones.exists():
        fecha_ultima_transaccion = transacciones.latest('fecha_transaccion').fecha_transaccion

    # Agrupar meses y años manualmente
    for transaccion in transacciones:
        meses_set.add(transaccion.fecha_transaccion.month)
        años_set.add(transaccion.fecha_transaccion.year)

    nombres_meses = [
        '', 'enero', 'febrero', 'marzo', 'abril', 
        'mayo', 'junio', 'julio', 'agosto', 
        'septiembre', 'octubre', 'noviembre', 'diciembre'
    ]

    meses_unicos = [(mes, nombres_meses[mes]) for mes in sorted(meses_set)]
    años_unicos = [(año, año) for año in sorted(años_set)]

    # Inicializar los diccionarios para los saldos de cada cuenta
    cuentas_ingresos = {}
    cuentas_gastos = {}
    cuentas_activos = {}  # Para cuentas de la categoría Activos
    cuentas_pasivos = {}  # Para cuentas de la categoría Pasivos
    cuentas_capital = {}  # Para cuentas de la categoría Capital Contable

    # Inicializar los totales
    total_ingresos = 0
    total_gastos = 0
    total_activos = 0
    total_pasivos = 0
    total_capital = 0

    # Inicializar las variables para las sumas de saldos
    suma_saldo_activos = 0  # Para saldos deudores de activos
    suma_saldos_pasivos = 0  # Para saldos acreedores de pasivos
    suma_saldo_capital_contable_propietario = 0  # Para saldos acreedores de capital contable

    # Inicializar las variables para los saldos totales de ingresos y gastos
    saldo_total_ingresos = 0
    saldo_total_gastos = 0

    # Procesar la solicitud POST
    if request.method == 'POST':
        mes = request.POST.get('mes')
        año = request.POST.get('año')

        # Calcular saldos para todas las cuentas
        for cuenta in cuentas:
            # Filtrar transacciones para la cuenta actual
            transacciones_debe = transacciones.filter(id_cuenta_cargo_id=cuenta.id_cuenta)
            transacciones_haber = transacciones.filter(id_cuenta_abono_id=cuenta.id_cuenta)

            # Filtrar por mes y año, si se proporcionan
            if mes and año:
                transacciones_debe = transacciones_debe.filter(
                    fecha_transaccion__month=mes,
                    fecha_transaccion__year=año
                )
                transacciones_haber = transacciones_haber.filter(
                    fecha_transaccion__month=mes,
                    fecha_transaccion__year=año
                )

            # Calcular los montos totales
            total_debe_cuenta = sum(t.monto_transaccion for t in transacciones_debe)
            total_haber_cuenta = sum(t.monto_transaccion for t in transacciones_haber)

            # Calcular saldo_deudor y saldo_acreedor
            saldo_deudor = total_debe_cuenta - total_haber_cuenta if total_debe_cuenta > total_haber_cuenta else 0
            saldo_acreedor = total_haber_cuenta - total_debe_cuenta if total_haber_cuenta > total_debe_cuenta else 0

            # Almacenar en los diccionarios según el tipo de cuenta
            if cuenta.id_categoria.nombre_categoria == 'Ingresos':
                cuentas_ingresos[cuenta.nombre_cuenta] = {
                    'saldo_deudor': saldo_deudor,
                    'saldo_acreedor': saldo_acreedor
                }
                saldo_total_ingresos += saldo_acreedor
            elif cuenta.id_categoria.nombre_categoria == 'Gastos':
                cuentas_gastos[cuenta.nombre_cuenta] = {
                    'saldo_deudor': saldo_deudor,
                    'saldo_acreedor': saldo_acreedor
                }
                saldo_total_gastos += saldo_deudor
            elif cuenta.id_categoria.nombre_categoria == 'Activos':
                cuentas_activos[cuenta.nombre_cuenta] = {
                    'saldo_deudor': saldo_deudor,
                    'saldo_acreedor': saldo_acreedor
                }
                suma_saldo_activos += saldo_deudor
            elif cuenta.id_categoria.nombre_categoria == 'Pasivos':
                cuentas_pasivos[cuenta.nombre_cuenta] = {
                    'saldo_deudor': saldo_deudor,
                    'saldo_acreedor': saldo_acreedor
                }
                suma_saldos_pasivos += saldo_acreedor
            elif cuenta.id_categoria.nombre_categoria == 'Capital contable del propietario':
                cuentas_capital[cuenta.nombre_cuenta] = {
                    'saldo_deudor': saldo_deudor,
                    'saldo_acreedor': saldo_acreedor
                }
                suma_saldo_capital_contable_propietario += saldo_acreedor

    suma_saldo_capital_contable_propietario = suma_saldo_capital_contable_propietario + saldo_total_ingresos - saldo_total_gastos
    utilidad_neta = saldo_total_ingresos - saldo_total_gastos
    suma_pasivos_totales_capital_propietario = suma_saldo_capital_contable_propietario + suma_saldos_pasivos

    return render(request, 'estado_balance_general.html', {
        'cuentas': cuentas,
        'meses': meses_unicos,
        'años': años_unicos,
        'cuentas_ingresos': cuentas_ingresos,
        'cuentas_gastos': cuentas_gastos,
        'cuentas_activos': cuentas_activos,
        'cuentas_pasivos': cuentas_pasivos,
        'cuentas_capital': cuentas_capital,
        'total_ingresos': saldo_total_ingresos,
        'total_gastos': saldo_total_gastos,
        'saldo_total_ingresos': saldo_total_ingresos,  # Pasar el saldo total de ingresos a la plantilla
        'saldo_total_gastos': saldo_total_gastos,      # Pasar el saldo total de gastos a la plantilla
        'utilidad_neta': utilidad_neta,
        'total_activos': suma_saldo_activos,
        'total_pasivos': suma_saldos_pasivos,
        'total_capital': suma_saldo_capital_contable_propietario,
        'suma_saldo_activos': suma_saldo_activos,
        'suma_saldos_pasivos': suma_saldos_pasivos,
        'suma_saldo_capital_contable_propietario': suma_saldo_capital_contable_propietario,
        'suma_pasivos_totales_capital_propietario': suma_pasivos_totales_capital_propietario,
        'fecha_ultima_transaccion': fecha_ultima_transaccion
    })

def estado_flujo_efectivo(request):
    cuentas = Cuenta.objects.all()  # Obtener todas las cuentas
    transacciones = Transaccion.objects.all()  # Obtener todas las transacciones

    meses_set = set()
    años_set = set()

    # Agrupar meses y años manualmente
    for transaccion in transacciones:
        meses_set.add(transaccion.fecha_transaccion.month)
        años_set.add(transaccion.fecha_transaccion.year)

    nombres_meses = [
        '', 'enero', 'febrero', 'marzo', 'abril', 
        'mayo', 'junio', 'julio', 'agosto', 
        'septiembre', 'octubre', 'noviembre', 'diciembre'
    ]

    meses_unicos = [(mes, nombres_meses[mes]) for mes in sorted(meses_set)]
    años_unicos = [(año, año) for año in sorted(años_set)]

    # Inicializar el diccionario para los cargos y abonos de cada cuenta
    cuentas_cargo_abono = {}

    # Inicializar los totales
    total_ingresos = 0
    total_gastos = 0
    
    # Inicializar las variables para evitar errores de referencia
    utilidad_neta = 0
    cobro_clientes = 0
    pago_proveedores = 0
    pago_empleados = 0
    pago_total = 0
    efectivo_neto_actividades_operacion = 0
    adquisicion_terreno = 0
    venta_terreno = 0
    efectivo_neto_inversion = 0
    capital = 0
    retiros = 0
    efectivo_neto_actividades_financiamiento = 0
    incremento_neto_efectivo = 0

    mes_seleccionado = 1
    año_seleccionado = 2025

    fecha_ultima_transaccion = datetime.now()
    saldo_efectivo_ultimo_dia_mes = 0
    efectivo_saldo_meses_anteriores = 0

    # Procesar la solicitud POST
    if request.method == 'POST':
        mes_seleccionado = request.POST.get('mes')
        año_seleccionado = request.POST.get('año')


        # Convertir a enteros para cálculos
        mes_seleccionado = int(mes_seleccionado) if mes_seleccionado else None
        año_seleccionado = int(año_seleccionado) if año_seleccionado else None

        # Obtener la última transacción
        if transacciones.exists():
            fecha_ultima_transaccion = transacciones.latest('fecha_transaccion').fecha_transaccion

        # Calcular saldos para todas las cuentas
        for cuenta in cuentas:
            # Inicializar los montos para cada cuenta
            total_cargo_cuenta = 0
            total_abono_cuenta = 0

            # Filtrar transacciones para la cuenta actual
            transacciones_debe = transacciones.filter(id_cuenta_cargo_id=cuenta.id_cuenta)
            transacciones_haber = transacciones.filter(id_cuenta_abono_id=cuenta.id_cuenta)

            # Filtrar por mes y año, si se proporcionan
            if mes_seleccionado and año_seleccionado:
                transacciones_debe = transacciones_debe.filter(
                    fecha_transaccion__month=mes_seleccionado,
                    fecha_transaccion__year=año_seleccionado
                )
                transacciones_haber = transacciones_haber.filter(
                    fecha_transaccion__month=mes_seleccionado,
                    fecha_transaccion__year=año_seleccionado
                )

            # Calcular los montos totales de cargo y abono
            total_cargo_cuenta = sum(t.monto_transaccion for t in transacciones_debe)
            total_abono_cuenta = sum(t.monto_transaccion for t in transacciones_haber)

            # Almacenar en el diccionario de cargos y abonos
            cuentas_cargo_abono[cuenta.nombre_cuenta] = {
                'cargo': total_cargo_cuenta,
                'abono': total_abono_cuenta
            }

            # Sumar al total de ingresos o gastos
            if cuenta.id_categoria.nombre_categoria == 'Ingresos':                
                total_ingresos += total_abono_cuenta
            elif cuenta.id_categoria.nombre_categoria == 'Gastos':                
                total_gastos += total_cargo_cuenta

        utilidad_neta = total_ingresos - total_gastos

        # Entradas
        cobro_clientes = cuentas_cargo_abono.get('Ingresos por servicios', {}).get('abono', 0) + cuentas_cargo_abono.get('Cuentas por cobrar', {}).get('cargo', 0)
        
        # Pagos
        pago_proveedores = (
            cuentas_cargo_abono.get('Gasto por renta, Computadora', {}).get('cargo', 0) +
            cuentas_cargo_abono.get('Gasto por renta, Oficina', {}).get('cargo', 0) +
            cuentas_cargo_abono.get('Cuentas por pagar', {}).get('cargo', 0) +
            cuentas_cargo_abono.get('Gastos por servicios generales', {}).get('cargo', 0)
        )
        pago_empleados = cuentas_cargo_abono.get('Gastos por salarios', {}).get('cargo', 0)
        pago_total = pago_proveedores + pago_empleados
        efectivo_neto_actividades_operacion = cobro_clientes - pago_total

        # Flujos de efectivo de las actividades de inversión
        adquisicion_terreno = cuentas_cargo_abono.get('Terreno', {}).get('cargo', 0)
        venta_terreno = cuentas_cargo_abono.get('Terreno', {}).get('abono', 0)
        efectivo_neto_inversion = adquisicion_terreno - venta_terreno

        # Flujos de efectivo provenientes de actividades de financiamiento
        capital = cuentas_cargo_abono.get('Capital', {}).get('abono', 0)
        retiros = cuentas_cargo_abono.get('Retiros', {}).get('cargo', 0)
        efectivo_neto_actividades_financiamiento = capital - retiros
        incremento_neto_efectivo = efectivo_neto_actividades_operacion + efectivo_neto_actividades_financiamiento - efectivo_neto_inversion

        # Calcular saldos de meses anteriores para la cuenta de efectivo
        efectivo_saldo_meses_anteriores = {'saldo_deudor': 0, 'saldo_acreedor': 0}

        # Filtrar transacciones de la cuenta de efectivo
        cuenta_efectivo = cuentas.filter(nombre_cuenta='Efectivo').first()
        if cuenta_efectivo:
            transacciones_anteriores = transacciones.filter(
                id_cuenta_cargo_id=cuenta_efectivo.id_cuenta,
                fecha_transaccion__lt=f"{año_seleccionado}-{mes_seleccionado:02d}-01"
            ).union(
                transacciones.filter(
                    id_cuenta_abono_id=cuenta_efectivo.id_cuenta,
                    fecha_transaccion__lt=f"{año_seleccionado}-{mes_seleccionado:02d}-01"
                )
            )

            # Calcular saldos deudores y acreedores
            efectivo_saldo_meses_anteriores['saldo_deudor'] = sum(
                t.monto_transaccion for t in transacciones_anteriores if t.id_cuenta_cargo_id == cuenta_efectivo.id_cuenta
            )
            efectivo_saldo_meses_anteriores['saldo_acreedor'] = sum(
                t.monto_transaccion for t in transacciones_anteriores if t.id_cuenta_abono_id == cuenta_efectivo.id_cuenta
            )

        saldo_efectivo_ultimo_dia_mes = efectivo_saldo_meses_anteriores['saldo_deudor'] + incremento_neto_efectivo

    return render(request, 'estado_flujo_efectivo.html', {
        'cuentas_cargo_abono': cuentas_cargo_abono,  # Pasar el diccionario de cargos y abonos a la plantilla
        'total_ingresos': total_ingresos,  # Pasar el total_ingresos a la plantilla
        'total_gastos': total_gastos,  # Pasar el total_gastos a la plantilla
        'utilidad_neta': utilidad_neta,
        'cobro_clientes': cobro_clientes,
        'pago_proveedores': pago_proveedores,
        'pago_empleados': pago_empleados,
        'pago_total': pago_total,
        'efectivo_neto_actividades_operacion': efectivo_neto_actividades_operacion,
        'adquisicion_terreno': adquisicion_terreno,
        'venta_terreno': venta_terreno,
        'efectivo_neto_inversion': efectivo_neto_inversion,
        'capital': capital,
        'retiros': retiros,
        'efectivo_neto_actividades_financiamiento': efectivo_neto_actividades_financiamiento,
        'incremento_neto_efectivo': incremento_neto_efectivo,
        'meses': meses_unicos,
        'años': años_unicos,
        'mes_seleccionado': nombres_meses[mes_seleccionado] if mes_seleccionado else '',
        'año_seleccionado': año_seleccionado,
        'fecha_ultima_transaccion': fecha_ultima_transaccion,
        'efectivo_saldo_meses_anteriores': efectivo_saldo_meses_anteriores,  # Pasar saldos de meses 
        'saldo_efectivo_ultimo_dia_mes': saldo_efectivo_ultimo_dia_mes
    })

def editar_cuenta(request, id_cuenta):
    cuenta = get_object_or_404(Cuenta, id_cuenta=id_cuenta)
    if request.method == 'POST':
        form = CuentaForm(request.POST, instance=cuenta)
        if form.is_valid():
            form.save()
            return redirect(reverse('registros:listar_cuentas'))  # Redirige con namespace
    else:
        form = CuentaForm(instance=cuenta)
    return render(request, 'editar_cuenta.html', {'form': form, 'cuenta': cuenta})

def eliminar_cuenta(request, id_cuenta):
    cuenta = get_object_or_404(Cuenta, id_cuenta=id_cuenta)
    if request.method == 'POST':
        cuenta.delete()
        return redirect(reverse('registros:listar_cuentas'))  # Redirige con namespace
    return render(request, 'eliminar_cuenta.html', {'cuenta': cuenta})

