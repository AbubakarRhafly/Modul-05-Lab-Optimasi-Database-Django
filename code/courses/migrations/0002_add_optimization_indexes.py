# Generated manually for Lab 05 Optimasi Database.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['price'], name='idx_course_price'),
        ),
        migrations.AddIndex(
            model_name='course',
            index=models.Index(fields=['teacher', 'price'], name='idx_course_teacher_price'),
        ),
        migrations.AddIndex(
            model_name='coursemember',
            index=models.Index(fields=['course_id', 'roles'], name='idx_cm_course_roles'),
        ),
        migrations.AddIndex(
            model_name='coursemember',
            index=models.Index(fields=['user_id', 'course_id'], name='idx_cm_user_course'),
        ),
        migrations.AddIndex(
            model_name='coursecontent',
            index=models.Index(fields=['course_id', 'parent_id'], name='idx_cc_course_parent'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['content_id', 'member_id'], name='idx_comment_content_member'),
        ),
    ]
