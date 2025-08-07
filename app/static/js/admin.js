/**
 * =================================================================================
 * لوحة تحكم المدير - admin.js (النسخة المحسّنة والمنظمة)
 * =================================================================================
 */
document.addEventListener('DOMContentLoaded', () => {

    const adminApp = {
        elements: {
            userCount: document.getElementById('user-count'),
            contentCount: document.getElementById('book-count'),
            // أضف أي عناصر أخرى في لوحة التحكم هنا
        },

        init() {
            this.loadStats();
        },

        async loadStats() {
            const token = localStorage.getItem('token');

            if (!token) {
                this.ui.showToast('يجب تسجيل الدخول أولاً للوصول.', 'error');
                setTimeout(() => window.location.href = '/', 2000);
                return;
            }

            try {
                const stats = await this.api.getStats(token);
                this.ui.updateStats(stats);
                this.ui.showToast('تم تحميل الإحصائيات بنجاح.', 'success');
            } catch (error) {
                this.ui.handleApiError(error);
                // إعادة التوجيه في حالة الخطأ في الصلاحيات
                if (error.status === 401 || error.status === 403) {
                    setTimeout(() => window.location.href = '/', 2000);
                }
            }
        },

        api: {
            async getStats(token) {
                const response = await fetch('/api/admin/stats', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                if (!response.ok) {
                    throw { status: response.status, data: data };
                }
                return data;
            }
        },

        ui: {
            updateStats(stats) {
                adminApp.elements.userCount.textContent = stats.total_users;
                adminApp.elements.contentCount.textContent = stats.total_content;
            },

            showToast(message, type = 'success') {
                const toastContainer = document.querySelector('.container') || document.body;
                const toast = document.createElement('div');
                const bgColor = type === 'error' ? '#d32f2f' : '#388e3c';
                
                // استخدام تنسيقات PicoCSS المدمجة إذا أمكن
                toast.setAttribute('style', `
                    position: fixed;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background-color: ${bgColor};
                    color: white;
                    padding: 1rem 1.5rem;
                    border-radius: 0.5rem;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    z-index: 1000;
                    opacity: 0;
                    transition: opacity 0.3s ease, transform 0.3s ease;
                    transform: translateX(-50%) translateY(-20px);
                `);
                toast.textContent = message;
                document.body.appendChild(toast);
                
                setTimeout(() => {
                    toast.style.opacity = '1';
                    toast.style.transform = 'translateX(-50%) translateY(0)';
                }, 100);
                
                setTimeout(() => {
                    toast.style.opacity = '0';
                    toast.addEventListener('transitionend', () => toast.remove());
                }, 3500);
            },

            handleApiError(error) {
                console.error("Admin API Error:", error);
                let message = 'حدث خطأ غير متوقع.';
                if (error.status === 401) {
                    message = 'جلسة الدخول غير صالحة أو منتهية.';
                } else if (error.status === 403) {
                    message = 'ليس لديك صلاحيات كافية للوصول لهذه الصفحة.';
                } else if (error.data && (error.data.message || error.data.detail)) {
                    message = error.data.message || error.data.detail;
                }
                this.showToast(message, 'error');
            }
        }
    };

    adminApp.init();
});
