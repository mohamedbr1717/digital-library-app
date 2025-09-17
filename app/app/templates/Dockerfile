# استخدم صورة Python التي تحتوي على أدوات البناء
FROM python:3.13

# قم بتثبيت تبعيات النظام التي قد تحتاجها بعض مكتبات Python
# يمكنك إضافة أي حزم أخرى هنا إذا تطلبت مكتباتك ذلك
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt1-dev

# تعيين دليل العمل
WORKDIR /app

# نسخ وتثبيت تبعيات Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# تحديد أمر التشغيل
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "$PORT"]
