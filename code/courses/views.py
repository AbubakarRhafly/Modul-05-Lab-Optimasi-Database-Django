"""
Views untuk Simple LMS - Lab 05: Optimasi Database.

Endpoint dibuat berpasangan agar hasil baseline dan optimized bisa dibandingkan
langsung melalui Django Silk.
"""

from django.db.models import Avg, Count, F, Max, Min, Prefetch
from django.db.models.functions import Cast
from django.db.models import IntegerField
from django.http import JsonResponse

from .models import Comment, Course, CourseContent, CourseMember


def _safe_avg(value):
    """Ubah nilai AVG dari database agar aman ditampilkan sebagai JSON."""
    if value is None:
        return 0
    return round(float(value), 2)


# =============================================================================
# 1) Daftar course + teacher
# =============================================================================

def course_list_baseline(request):
    """
    Baseline: sengaja belum optimal.

    Masalah:
    - Course.objects.all() mengambil data course saja.
    - Saat c.teacher.username dipanggil dalam loop, Django melakukan query
      tambahan untuk setiap course.
    - Dengan 100 course, pola ini menjadi N+1 query.
    """
    courses = Course.objects.all().order_by("id")
    data = []

    for course in courses:
        data.append({
            "id": course.id,
            "course": course.name,
            "teacher": course.teacher.username,
            "price": course.price,
        })

    return JsonResponse({"mode": "baseline", "data": data})


def course_list_optimized(request):
    """
    Optimized: select_related() untuk relasi ForeignKey Course.teacher.

    Hasilnya data Course dan User teacher diambil dengan satu query JOIN,
    sehingga tidak ada query berulang saat loop.
    """
    courses = Course.objects.select_related("teacher").all().order_by("id")
    data = []

    for course in courses:
        data.append({
            "id": course.id,
            "course": course.name,
            "teacher": course.teacher.username,
            "price": course.price,
        })

    return JsonResponse({"mode": "optimized", "data": data})


# =============================================================================
# 2) Daftar course + members + konten + jumlah komentar
# =============================================================================

def course_members_baseline(request):
    """
    Baseline: sengaja banyak query di dalam loop.

    Masalah utama:
    - Mengakses teacher dalam loop.
    - Mengambil member per course.
    - Mengambil content per course.
    - Menghitung comment per content.
    Pola ini akan menghasilkan banyak duplicate query di Silk.
    """
    courses = Course.objects.all().order_by("id")
    payload = []

    for course in courses:
        members = []
        for member in course.coursemember_set.all().order_by("id"):
            members.append({
                "username": member.user_id.username,
                "role": member.roles,
            })

        contents = []
        for content in course.coursecontent_set.all().order_by("id"):
            contents.append({
                "title": content.name,
                "comment_count": content.comment_set.count(),
            })

        payload.append({
            "id": course.id,
            "course": course.name,
            "teacher": course.teacher.username,
            "member_count": len(members),
            "members": members,
            "content_count": len(contents),
            "contents": contents,
        })

    return JsonResponse({"mode": "baseline", "data": payload})


def course_members_optimized(request):
    """
    Optimized:
    - select_related('teacher') untuk ForeignKey.
    - prefetch_related() untuk reverse ForeignKey CourseMember dan CourseContent.
    - select_related('user_id') di dalam Prefetch agar username member tidak N+1.
    - annotate(comment_count=Count('comment')) agar jumlah komentar dihitung oleh DB.
    """
    member_qs = CourseMember.objects.select_related("user_id").order_by("id")
    content_qs = (
        CourseContent.objects
        .annotate(comment_count=Count("comment"))
        .order_by("id")
    )

    courses = (
        Course.objects
        .select_related("teacher")
        .prefetch_related(
            Prefetch("coursemember_set", queryset=member_qs, to_attr="prefetched_members"),
            Prefetch("coursecontent_set", queryset=content_qs, to_attr="prefetched_contents"),
        )
        .order_by("id")
    )

    payload = []
    for course in courses:
        members = [
            {"username": member.user_id.username, "role": member.roles}
            for member in course.prefetched_members
        ]
        contents = [
            {"title": content.name, "comment_count": content.comment_count}
            for content in course.prefetched_contents
        ]

        payload.append({
            "id": course.id,
            "course": course.name,
            "teacher": course.teacher.username,
            "member_count": len(members),
            "members": members,
            "content_count": len(contents),
            "contents": contents,
        })

    return JsonResponse({"mode": "optimized", "data": payload})


# =============================================================================
# 3) Statistik course untuk dashboard dosen
# =============================================================================

def course_dashboard_baseline(request):
    """
    Baseline: statistik dihitung tidak efisien menggunakan loop Python.

    Contoh bottleneck:
    - Count member per course dilakukan dengan query terpisah.
    - Count content per course dilakukan dengan query terpisah.
    - Count comment per course dilakukan dengan query terpisah.
    """
    courses = Course.objects.all().order_by("id")
    course_stats = []
    prices = []

    for course in courses:
        prices.append(course.price)
        member_count = CourseMember.objects.filter(course_id=course).count()
        content_count = CourseContent.objects.filter(course_id=course).count()
        comment_count = Comment.objects.filter(content_id__course_id=course).count()

        course_stats.append({
            "id": course.id,
            "course": course.name,
            "teacher": course.teacher.username,
            "member_count": member_count,
            "content_count": content_count,
            "comment_count": comment_count,
            "price": course.price,
        })

    total = len(course_stats)
    global_stats = {
        "total_courses": total,
        "max_price": max(prices) if prices else 0,
        "min_price": min(prices) if prices else 0,
        "avg_price": round(sum(prices) / total, 2) if total else 0,
    }

    return JsonResponse({
        "mode": "baseline",
        "global_stats": global_stats,
        "courses": course_stats,
    })


def course_dashboard_optimized(request):
    """
    Optimized:
    - aggregate() untuk statistik global dalam 1 query.
    - annotate() untuk member_count, content_count, dan comment_count.
    - select_related('teacher') agar teacher tidak memicu N+1.
    """
    global_stats = Course.objects.aggregate(
        total_courses=Count("id"),
        max_price=Max("price"),
        min_price=Min("price"),
        avg_price=Avg("price"),
    )

    courses = (
        Course.objects
        .select_related("teacher")
        .annotate(
            member_count=Count("coursemember", distinct=True),
            content_count=Count("coursecontent", distinct=True),
            comment_count=Count("coursecontent__comment", distinct=True),
        )
        .order_by("-member_count", "name")
    )

    course_stats = []
    for course in courses:
        course_stats.append({
            "id": course.id,
            "course": course.name,
            "teacher": course.teacher.username,
            "member_count": course.member_count,
            "content_count": course.content_count,
            "comment_count": course.comment_count,
            "price": course.price,
        })

    return JsonResponse({
        "mode": "optimized",
        "global_stats": {
            "total_courses": global_stats["total_courses"],
            "max_price": global_stats["max_price"] or 0,
            "min_price": global_stats["min_price"] or 0,
            "avg_price": _safe_avg(global_stats["avg_price"]),
        },
        "courses": course_stats,
    })


# =============================================================================
# 4) Bulk operations - demo tambahan untuk bukti praktikum
# =============================================================================

def bulk_create_contents(request):
    """
    Demo bulk_create untuk membuat banyak CourseContent sekaligus.

    Contoh akses:
    /lab/bulk/create-contents/?amount=1000
    """
    amount = int(request.GET.get("amount", 1000))
    amount = max(1, min(amount, 5000))

    course = Course.objects.first()
    if course is None:
        return JsonResponse({"error": "Belum ada course. Jalankan python manage.py seed_data dulu."}, status=400)

    contents = [
        CourseContent(
            name=f"Bulk Content {i + 1}",
            description="Konten dibuat menggunakan bulk_create untuk Lab 05.",
            course_id=course,
        )
        for i in range(amount)
    ]
    CourseContent.objects.bulk_create(contents, batch_size=500)

    return JsonResponse({
        "operation": "bulk_create",
        "created": amount,
        "batch_size": 500,
    })


def bulk_update_course_prices(request):
    """
    Demo update massal menggunakan QuerySet.update().

    Contoh akses:
    /lab/bulk/update-prices/
    """
    updated = Course.objects.update(
        price=Cast(F("price") * 1.1, output_field=IntegerField())
    )

    return JsonResponse({
        "operation": "bulk_update_price",
        "updated_courses": updated,
        "formula": "price = price * 1.1",
    })
