from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    name = models.CharField("nama matkul", max_length=100)
    description = models.TextField("deskripsi", default='-')
    price = models.IntegerField("harga", default=10000)
    image = models.ImageField("gambar", null=True, blank=True)
    teacher = models.ForeignKey(
        User,
        verbose_name="pengajar",
        on_delete=models.RESTRICT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Mata Kuliah"
        verbose_name_plural = "Mata Kuliah"
        indexes = [
            # Dipakai untuk dashboard statistik dan order/filter berdasarkan harga.
            models.Index(fields=['price'], name='idx_course_price'),
            # Dipakai untuk pola query course berdasarkan dosen dan range/order harga.
            models.Index(fields=['teacher', 'price'], name='idx_course_teacher_price'),
        ]


ROLE_OPTIONS = [
    ('std', "Siswa"),
    ('ast', "Asisten"),
]


class CourseMember(models.Model):
    course_id = models.ForeignKey(
        Course,
        verbose_name="matkul",
        on_delete=models.RESTRICT
    )
    user_id = models.ForeignKey(
        User,
        verbose_name="siswa",
        on_delete=models.RESTRICT
    )
    roles = models.CharField(
        "peran",
        max_length=3,
        choices=ROLE_OPTIONS,
        default='std'
    )

    def __str__(self):
        return f"{self.user_id} - {self.course_id} ({self.roles})"

    class Meta:
        verbose_name = "Anggota Kelas"
        verbose_name_plural = "Anggota Kelas"
        indexes = [
            # Dipakai saat menghitung atau memfilter member per course dan role.
            models.Index(fields=['course_id', 'roles'], name='idx_cm_course_roles'),
            # Dipakai untuk lookup relasi user-course pada data enrollment.
            models.Index(fields=['user_id', 'course_id'], name='idx_cm_user_course'),
        ]


class CourseContent(models.Model):
    name = models.CharField("judul konten", max_length=200)
    description = models.TextField("deskripsi", default='-')
    video_url = models.CharField(
        'URL Video',
        max_length=200,
        null=True,
        blank=True
    )
    file_attachment = models.FileField("File", null=True, blank=True)
    course_id = models.ForeignKey(
        Course,
        verbose_name="matkul",
        on_delete=models.RESTRICT
    )
    parent_id = models.ForeignKey(
        "self",
        verbose_name="induk",
        on_delete=models.RESTRICT,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Konten Kelas"
        verbose_name_plural = "Konten Kelas"
        indexes = [
            # Dipakai saat mengambil daftar konten per course, termasuk konten parent/child.
            models.Index(fields=['course_id', 'parent_id'], name='idx_cc_course_parent'),
        ]


class Comment(models.Model):
    content_id = models.ForeignKey(
        CourseContent,
        verbose_name="konten",
        on_delete=models.CASCADE
    )
    member_id = models.ForeignKey(
        CourseMember,
        verbose_name="pengguna",
        on_delete=models.CASCADE
    )
    comment = models.TextField('komentar')

    def __str__(self):
        return f"Komentar oleh {self.member_id} pada {self.content_id}"

    class Meta:
        verbose_name = "Komentar"
        verbose_name_plural = "Komentar"
        indexes = [
            # Dipakai untuk menghitung komentar per content dan melacak komentar member.
            models.Index(fields=['content_id', 'member_id'], name='idx_comment_content_member'),
        ]
