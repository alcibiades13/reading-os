from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0007_bookdna_primary_genre_tag_and_more'),
    ]

    operations = [
        UnaccentExtension(),
    ]
