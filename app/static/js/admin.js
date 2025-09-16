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
                this.ui.showToast(window.i18n.translations.login_to_comment, 'error'); // ✅ استخدام رسالة مترجمة
                setTimeout(() => window.location.href = '/', 2000);
                return;
            }

            try {
                const stats = await this.api.getStats(token);
                this.ui.updateStats(stats);
                this.ui.showToast(window.i18n.translations.load_more, 'success'); // ✅ استخدام رسالة مترجمة
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

            // ✅ استخدام دالة التنبيهات من `script.js`
            showToast: window.app.ui.showToast,

            handleApiError(error) {
                console.error("Admin API Error:", error);
                let message = window.i18n.translations.login_error; // ✅ استخدام رسالة مترجمة
                if (error.status === 401) {
                    message = window.i18n.translations.login_fail; // ✅ رسالة فشل تسجيل الدخول
                } else if (error.status === 403) {
                    message = window.i18n.translations.view_not_available; // ✅ رسالة عدم توفر العرض
                } else if (error.data && (error.data.message || error.data.detail)) {
                    message = error.data.message || error.data.detail;
                }
                this.showToast(message, 'error');
            }
        }
    };

    adminApp.init();
});
