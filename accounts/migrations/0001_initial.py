# Generated by Django 5.1.1 on 2024-12-01 18:13

from django.db import migrations, models
import django.contrib.auth.models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(max_length=150, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('user_type', models.CharField(choices=[('patient', 'Patient'), ('doctor', 'Doctor')], max_length=10, default='patient')),
                ('phone_number', models.CharField(blank=True, max_length=15, default='')),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('address', models.TextField(blank=True, default='')),
                ('specialization', models.CharField(blank=True, max_length=100, default='')),
                ('license_number', models.CharField(blank=True, max_length=50, default='')),
                ('years_of_experience', models.IntegerField(blank=True, null=True)),
                ('qualifications', models.TextField(blank=True, default='')),
                ('hospital_affiliations', models.TextField(blank=True, default='')),
                ('languages', models.CharField(blank=True, max_length=200, default='')),
                ('working_hours', models.CharField(blank=True, max_length=100, default='')),
                ('emergency_contact', models.CharField(blank=True, max_length=200, default='')),
                ('office_address', models.TextField(blank=True, default='')),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pics/')),
                ('assigned_doctor', models.ForeignKey('self', blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_patients', limit_choices_to={'user_type': 'doctor'})),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'auth_user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
