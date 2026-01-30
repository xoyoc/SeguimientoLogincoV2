from django.db import migrations, models
import django.db.models.deletion


def migrate_regimen_data(apps, schema_editor):
    """Migrar datos de regimen CharField a ForeignKey"""
    Shipment = apps.get_model('shipments', 'Shipment')
    Regimen = apps.get_model('regimens', 'Regimen')

    # Mapeo de valores antiguos a nuevos regímenes
    # Los valores están normalizados (mayúsculas, sin espacios)
    regimen_map = {
        'A1': 'A1 - Importación Definitiva',
        'A4': 'A4 - Importación Temporal',
        'IN': 'IN - Introducción a Depósito Fiscal',
        'R1': 'R1 - Retorno de Temporales',
        'M3': 'M3 - Tránsito Interno',
        'A3': 'A3 - Importación Temporal para Elaboración',
        '1N': 'IN - Introducción a Depósito Fiscal',  # Typo común
    }

    # Cache de regímenes creados
    regimen_cache = {}
    for regimen in Regimen.objects.all():
        regimen_cache[regimen.text] = regimen

    # Procesar cada shipment
    for shipment in Shipment.objects.all():
        old_value = shipment.regimen
        if old_value:
            # Normalizar el valor
            normalized = old_value.strip().upper()

            # Buscar en el mapeo
            if normalized in regimen_map:
                regimen_text = regimen_map[normalized]
                if regimen_text in regimen_cache:
                    shipment.regimen_fk = regimen_cache[regimen_text]
                    shipment.save(update_fields=['regimen_fk'])


def reverse_migrate(apps, schema_editor):
    """Revertir migración (no hace nada con los datos)"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0007_change_transport_to_choices'),
        ('regimens', '0001_initial'),
    ]

    operations = [
        # 1. Agregar nuevo campo FK (temporal)
        migrations.AddField(
            model_name='shipment',
            name='regimen_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='shipments_new',
                to='regimens.regimen',
                verbose_name='Régimen'
            ),
        ),
        # 2. Migrar datos
        migrations.RunPython(migrate_regimen_data, reverse_migrate),
        # 3. Eliminar campo antiguo
        migrations.RemoveField(
            model_name='shipment',
            name='regimen',
        ),
        # 4. Renombrar nuevo campo
        migrations.RenameField(
            model_name='shipment',
            old_name='regimen_fk',
            new_name='regimen',
        ),
        # 5. Actualizar related_name
        migrations.AlterField(
            model_name='shipment',
            name='regimen',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='shipments',
                to='regimens.regimen',
                verbose_name='Régimen'
            ),
        ),
    ]
