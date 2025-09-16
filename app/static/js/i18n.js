// i18n.js

// جعل الكائن متاحًا عالميًا
window.i18n = {
    translations: {}, // إضافة كائن لتخزين الترجمات

    // الدالة الآن ترجع Promise، مما يسمح لنا بانتظار اكتمالها
    setLanguage: async function(lang) {
        try {
            const response = await fetch(`/static/lang/${lang}.json`);
            if (!response.ok) {
                console.warn(`Language file for '${lang}' not found, defaulting to 'ar'.`);
                // في حال الفشل، نحاول تحميل اللغة العربية كخيار افتراضي
                if (lang !== 'ar') {
                    return this.setLanguage('ar'); 
                }
                throw new Error("Default language file 'ar.json' not found.");
            }
            
            // تخزين الترجمات في الكائن
            this.translations = await response.json();
            
            // تطبيق الترجمات على عناصر الصفحة
            document.querySelectorAll('[data-i18n]').forEach(element => {
                const key = element.getAttribute('data-i18n');
                if (this.translations[key]) {
                    element.textContent = this.translations[key];
                }
            });

            // ✅ تحديث العناوين والأوصاف بناءً على الترجمة
            const pageTitleElement = document.querySelector('title');
            if (pageTitleElement && this.translations.library_title) {
                pageTitleElement.textContent = this.translations.library_title;
            }
            
            document.documentElement.lang = lang;
            document.documentElement.dir = (lang === 'ar') ? 'rtl' : 'ltr';
            
            localStorage.setItem('app_lang', lang); // ✅ استخدام نفس مفتاح localStorage في script.js
            const switcher = document.getElementById('language-select'); // ✅ تم تصحيح الـ ID
            if(switcher) switcher.value = lang;
            
            // ✅ إطلاق حدث مخصص بعد تغيير اللغة
            document.dispatchEvent(new Event('language-changed'));

        } catch (error) {
            console.error('Error loading language file:', error);
            // في حال حدوث خطأ فادح، نضع قيم افتراضية بسيطة
            const pageTitleElement = document.querySelector('title');
            if (pageTitleElement) {
                pageTitleElement.textContent = "المكتبة";
            }
            document.documentElement.lang = 'ar';
            document.documentElement.dir = 'rtl';
        }
    }
};

// دالة تهيئة اللغة عند بدء التشغيل
async function initializeLanguage() {
    const languageSelect = document.getElementById('language-select');
    
    if (languageSelect) {
        languageSelect.addEventListener('change', (e) => {
            window.i18n.setLanguage(e.target.value);
        });
    }

    const savedLang = localStorage.getItem('app_lang');
    const userLang = navigator.language.split('-')[0];
    const supportedLangs = ['ar', 'en', 'fr', 'de', 'es'];
    
    let langToLoad = 'ar';
    if (savedLang && supportedLangs.includes(savedLang)) {
        langToLoad = savedLang;
    } else if (supportedLangs.includes(userLang)) {
        langToLoad = userLang;
    }
    
    await window.i18n.setLanguage(langToLoad);
}

// تشغيل تهيئة اللغة عند بدء التشغيل
document.addEventListener('DOMContentLoaded', () => {
    initializeLanguage();
});
