from django.db import migrations

def update_categorias(apps, schema_editor):
    Categoria = apps.get_model('registros', 'Categoria_ecuacion_contable')
    
    # Mapeo de categorías antiguas a nuevas
    categoria_mapping = {
        'CAPITAL CONTABLE DEL PROPIETARIO': 'PATRIMONIO',
        'GASTOS': 'COSTOS_GASTOS'
    }
    
    for old_name, new_name in categoria_mapping.items():
        Categoria.objects.filter(nombre_categoria=old_name).update(nombre_categoria=new_name)

class Migration(migrations.Migration):
    dependencies = [
        ('registros', '0004_cuenta_activo'),  # Actualizada la dependencia a la última migración
    ]

    operations = [
        migrations.RunPython(update_categorias),
    ]
