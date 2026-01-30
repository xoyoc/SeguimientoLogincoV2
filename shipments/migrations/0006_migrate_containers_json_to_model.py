from django.db import migrations


def migrate_containers_to_model(apps, schema_editor):
    """
    Migra los datos de contenedores del JSONField al nuevo modelo Container.
    El JSONField tiene formato: [{"name": "XXX", "size": "YYY"}, ...]
    """
    Shipment = apps.get_model('shipments', 'Shipment')
    Container = apps.get_model('shipments', 'Container')

    for shipment in Shipment.objects.all():
        if shipment.containers and isinstance(shipment.containers, list):
            for container_data in shipment.containers:
                # Skip if container_data is None or not a dict
                if not container_data or not isinstance(container_data, dict):
                    continue

                # El JSONField usa 'name' para el número de contenedor
                number = container_data.get('name', '') or container_data.get('number', '')
                size = container_data.get('size', '')

                if number:  # Solo crear si hay número
                    Container.objects.create(
                        shipment=shipment,
                        number=number,
                        size=size
                    )


def reverse_migration(apps, schema_editor):
    """
    Revierte la migración: elimina todos los Container creados.
    Los datos originales permanecen en el JSONField.
    """
    Container = apps.get_model('shipments', 'Container')
    Container.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0005_container'),
    ]

    operations = [
        migrations.RunPython(migrate_containers_to_model, reverse_migration),
    ]
