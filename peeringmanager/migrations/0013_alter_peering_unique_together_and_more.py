# Generated by Django 4.0.2 on 2022-02-04 02:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peeringmanager', '0012_auto_20171104_2327'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='peering',
            unique_together={('router', 'name'), ('router', 'asn'), ('router', 'wg_port')},
        ),
        migrations.AddField(
            model_name='peering',
            name='endpoint_internal_v4',
            field=models.GenericIPAddressField(default='127.0.0.1', help_text='Internal DN42 address of your router', protocol='IPv4', verbose_name='Internal IPv4 address'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='peering',
            name='endpoint_internal_v6',
            field=models.GenericIPAddressField(default='::1', help_text='Link-local IPv6 address of your router', protocol='IPv6', verbose_name='Link-local IPv6 address'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='peering',
            name='mbgp_enabled',
            field=models.BooleanField(default=True, help_text='If set, the router will establish a Multi-protocol session for both IPv4 and IPv6 over the IPv6 link-local address (RFC 4760)', verbose_name='Multi-protocol BGP over IPv6'),
        ),
        migrations.AlterField(
            model_name='peering',
            name='asn',
            field=models.BigIntegerField(help_text='Your maintainer object must be listed as mnt-by for the AS', verbose_name='AS Number'),
        ),
        migrations.AlterUniqueTogether(
            name='peering',
            unique_together={('router', 'name'), ('router', 'asn'), ('router', 'endpoint_internal_v4'), ('router', 'wg_port')},
        ),
        migrations.RemoveField(
            model_name='peering',
            name='endpoint_internal',
        ),
    ]
