from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='User',
            name='qualifications',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='User',
            name='hospital_affiliations',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='User',
            name='languages',
            field=models.CharField(blank=True, max_length=200, default=''),
        ),
        migrations.AddField(
            model_name='User',
            name='working_hours',
            field=models.CharField(blank=True, max_length=100, default=''),
        ),
        migrations.AddField(
            model_name='User',
            name='emergency_contact',
            field=models.CharField(blank=True, max_length=200, default=''),
        ),
        migrations.AddField(
            model_name='User',
            name='office_address',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='User',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pics/'),
        ),
        migrations.AddField(
            model_name='User',
            name='assigned_doctor',
            field=models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='assigned_patients', limit_choices_to={'user_type': 'doctor'}),
        ),
    ] 