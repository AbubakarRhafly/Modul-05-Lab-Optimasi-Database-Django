# Lab 05 - Optimasi Database Django

Project ini adalah pengerjaan **Modul Praktikum 5: Lab Optimasi Database (Django)** untuk membandingkan performa endpoint **baseline** dan **optimized** menggunakan **Django Silk**.

Fokus optimasi:

- Profiling query dengan Django Silk
- Identifikasi N+1 problem
- Optimasi relasi dengan `select_related()` dan `prefetch_related()`
- Optimasi statistik dengan `aggregate()` dan `annotate()`
- Operasi massal dengan `bulk_create()` dan `update()`
- Penambahan index database

---

## 1. Struktur Project

```text
Lab-05-Starter/
├── code/
│   ├── courses/
│   │   ├── migrations/
│   │   │   ├── 0001_initial.py
│   │   │   └── 0002_add_optimization_indexes.py
│   │   ├── management/commands/seed_data.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── lms/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── manage.py
│   └── requirements.txt
├── screenshots/
│   └── .gitkeep
├── docker-compose.yml
└── README.md
```

---

## 2. Cara Menjalankan Project

### 2.1 Jalankan Docker Compose

```bash
docker compose up -d
```

Cek container:

```bash
docker ps
```

Pastikan container `lms-app` dan `lms-db` berjalan.

### 2.2 Install dependency Django Silk

```bash
docker compose exec app pip install -r requirements.txt
```

### 2.3 Jalankan migrasi

```bash
docker compose exec app python manage.py migrate
```

### 2.4 Isi data dummy

```bash
docker compose exec app python manage.py seed_data
```

Data yang dibuat:

- 20 dosen
- 80 mahasiswa
- 100 course
- 500 anggota kelas
- 300 konten
- 1000 komentar

### 2.5 Akses Django Silk

```text
http://localhost:8000/silk/
```

---

## 3. Endpoint Praktikum

### 3.1 Course + Teacher

Baseline:

```text
http://localhost:8000/lab/course-list/baseline/
```

Optimized:

```text
http://localhost:8000/lab/course-list/optimized/
```

Teknik optimasi:

```python
Course.objects.select_related("teacher")
```

Penjelasan singkat:

Endpoint baseline menghasilkan N+1 query karena setiap akses `course.teacher.username` di dalam loop memanggil query tambahan ke tabel user. Endpoint optimized menggunakan `select_related()` sehingga data course dan teacher diambil sekaligus dengan JOIN.

---

### 3.2 Course + Members + Contents + Comment Count

Baseline:

```text
http://localhost:8000/lab/course-members/baseline/
```

Optimized:

```text
http://localhost:8000/lab/course-members/optimized/
```

Teknik optimasi:

```python
Course.objects.select_related("teacher").prefetch_related(...)
```

Penjelasan singkat:

Endpoint baseline mengambil member, content, dan jumlah komentar di dalam loop, sehingga muncul banyak query berulang. Endpoint optimized menggunakan kombinasi `select_related()`, `prefetch_related()`, `Prefetch()`, dan `annotate()` untuk menurunkan jumlah query secara signifikan.

---

### 3.3 Dashboard Statistik Course

Baseline:

```text
http://localhost:8000/lab/course-dashboard/baseline/
```

Optimized:

```text
http://localhost:8000/lab/course-dashboard/optimized/
```

Teknik optimasi:

```python
Course.objects.aggregate(...)
Course.objects.annotate(...)
```

Penjelasan singkat:

Endpoint baseline menghitung statistik dengan loop Python dan query terpisah untuk setiap course. Endpoint optimized memindahkan proses hitung ke database menggunakan `aggregate()` dan `annotate()`.

---

### 3.4 Bulk Operations

Bulk create contents:

```text
http://localhost:8000/lab/bulk/create-contents/?amount=1000
```

Bulk update harga course:

```text
http://localhost:8000/lab/bulk/update-prices/
```

Teknik optimasi:

```python
CourseContent.objects.bulk_create(contents, batch_size=500)
Course.objects.update(price=...)
```

---

## 4. Index Database yang Ditambahkan

Index ditambahkan pada `courses/models.py` dan migration `0002_add_optimization_indexes.py`.

| Model | Index | Alasan |
|---|---|---|
| Course | `idx_course_price` | Membantu filter/order/statistik berdasarkan harga |
| Course | `idx_course_teacher_price` | Membantu query course berdasarkan teacher dan price |
| CourseMember | `idx_cm_course_roles` | Membantu hitung/filter member per course dan role |
| CourseMember | `idx_cm_user_course` | Membantu lookup enrollment user-course |
| CourseContent | `idx_cc_course_parent` | Membantu pengambilan konten per course dan parent |
| Comment | `idx_comment_content_member` | Membantu hitung komentar per content/member |

---

## 5. Tabel Perbandingan Silk

Isi angka query dan total time berdasarkan hasil screenshot Django Silk di laptop masing-masing.

| Kasus | Endpoint Baseline | Endpoint Optimized | Perbandingan Silk | Teknik |
|---|---|---|---|---|
| Course + teacher | `/lab/course-list/baseline/` | `/lab/course-list/optimized/` | contoh: 101 query -> 1 query, 250ms -> 15ms | `select_related()` |
| Course + members + content + comments | `/lab/course-members/baseline/` | `/lab/course-members/optimized/` | contoh: banyak query -> sedikit query | `select_related()`, `prefetch_related()`, `annotate()` |
| Statistik dashboard | `/lab/course-dashboard/baseline/` | `/lab/course-dashboard/optimized/` | contoh: ratusan query -> beberapa query | `aggregate()`, `annotate()` |

> Catatan: Angka pasti bisa berbeda tergantung laptop, container, dan kondisi database. Yang penting endpoint optimized menunjukkan penurunan query/time minimal 50% dibanding baseline.

---

## 6. Screenshot yang Perlu Dimasukkan

Simpan screenshot ke folder `screenshots/` sebelum upload ke GitHub.

Minimal screenshot:

1. `/silk/` bisa diakses
2. Request Silk untuk `/lab/course-list/baseline/`
3. Request Silk untuk `/lab/course-list/optimized/`
4. Request Silk untuk `/lab/course-members/baseline/`
5. Request Silk untuk `/lab/course-members/optimized/`
6. Request Silk untuk `/lab/course-dashboard/baseline/`
7. Request Silk untuk `/lab/course-dashboard/optimized/`
8. SQL tab dari Django Silk untuk menunjukkan duplicate query baseline

---

## 7. Jawaban Analisis Singkat

### 7.1 Kenapa `course_list_baseline` termasuk N+1 problem?

Karena query pertama mengambil seluruh data course. Setelah itu, setiap course memanggil `course.teacher.username`, sehingga Django mengambil data teacher satu per satu. Jika ada 100 course, query bisa menjadi sekitar 1 query utama + 100 query teacher.

### 7.2 Query mana yang berulang?

Query yang berulang adalah query ke tabel user/auth user untuk mengambil data teacher berdasarkan `teacher_id`.

### 7.3 Apa dampaknya jika data menjadi 1000 course?

Jumlah query akan ikut naik menjadi sekitar 1001 query. Dampaknya response menjadi lambat, database lebih berat, dan endpoint tidak scalable.

### 7.4 Kenapa `select_related()` cocok untuk teacher?

Karena `teacher` adalah relasi ForeignKey dari Course ke User. `select_related()` cocok untuk relasi single object seperti ForeignKey dan OneToOne.

### 7.5 Kenapa `prefetch_related()` cocok untuk members dan contents?

Karena members dan contents adalah reverse ForeignKey dari Course. Relasi seperti ini bisa memiliki banyak data, sehingga lebih tepat menggunakan `prefetch_related()`.

### 7.6 Kenapa `aggregate()` dan `annotate()` lebih optimal?

Karena perhitungan statistik dilakukan langsung oleh database, bukan dihitung manual dengan banyak query di dalam loop Python.

---

## 8. Cara Upload ke GitHub

Jika repository belum dibuat:

```bash
git init
git add .
git commit -m "Implement Lab 05 database optimization"
git branch -M main
git remote add origin https://github.com/USERNAME/NAMA-REPO.git
git push -u origin main
```

Jika repository sudah ada:

```bash
git add .
git commit -m "Implement Lab 05 database optimization"
git push
```

---

## 9. Kesimpulan

Optimasi database berhasil dilakukan dengan membandingkan endpoint baseline dan optimized. Teknik `select_related()`, `prefetch_related()`, `aggregate()`, `annotate()`, bulk operation, dan database indexing digunakan untuk mengurangi jumlah query dan mempercepat response API.
