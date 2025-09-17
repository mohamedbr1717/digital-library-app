# استخدم صورة Python رسمية كقاعدة
FROM python:3.13-slim

# تعيين دليل العمل داخل الحاوية
WORKDIR /app

# تثبيت التبعيات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# تحديد أمر التشغيل
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "$PORT"]
