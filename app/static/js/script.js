/**
 * =================================================================================
 * المكتبة الرقمية - script.js (النسخة المحسّنة والمنظمة)
 * =================================================================================
 * * هذا الملف يحتوي على كل منطق الواجهة الأمامية للمكتبة.
 * تم تنظيمه باستخدام كائن رئيسي (app) لتقسيم المسؤوليات:
 * - app.state: لتخزين كل البيانات المتغيرة.
 * - app.elements: لتخزين عناصر الصفحة (DOM).
 * - app.api: للتعامل مع كل طلبات الخادم (API).
 * - app.ui: لتحديث واجهة المستخدم فقط.
 * - app.handlers: لمعالجة أحداث المستخدم (clicks, submits).
 * - app.init: لتهيئة التطبيق.
 */
document.addEventListener('DOMContentLoaded', () => {

    const app = {
        // -----------------------------------------------------------------------------
        // 1. الحالة (State) وعناصر الصفحة (Elements)
        // -----------------------------------------------------------------------------
        state: {
            currentUser: null,
            currentToken: null,
            currentView: 'book',
            currentPage: 1,
            itemsPerPage: 12,
            isLastPage: false,
            translations: {},
            currentSearchQuery: '',
            currentFilters: {},
        },

        elements: {},

        // -----------------------------------------------------------------------------
        // 2. دالة التهيئة الرئيسية (Initialization)
        // -----------------------------------------------------------------------------
        init() {
            this.cacheElements();
            this.bindEvents();
            this.loadInitialState();
        },

        cacheElements() {
            // تخزين عناصر DOM الرئيسية لتجنب إعادة البحث عنها
            this.elements.libraryView = document.getElementById('library-view');
            this.elements.landingView = document.getElementById('landing-view');
            this.elements.exploreBtn = document.getElementById('explore-btn');
            this.elements.viewContainer = document.getElementById('view-container');
            this.elements.loaderContainer = document.getElementById('loader-container');
            this.elements.sidebarLinks = document.querySelectorAll('.sidebar-link');
            this.elements.mainTitle = document.getElementById('main-title');
            this.elements.languageSelect = document.getElementById('language-select');
            
            // التوثيق
            this.elements.loginDialog = document.getElementById('login-dialog');
            this.elements.registerDialog = document.getElementById('register-dialog');
            this.elements.loginForm = document.getElementById('login-form');
            this.elements.registerForm = document.getElementById('register-form');
            this.elements.authButtons = document.getElementById('auth-buttons');
            this.elements.userInfo = document.getElementById('user-info');
            this.elements.usernameDisplay = document.getElementById('username-display');
            this.elements.userAvatar = document.getElementById('user-avatar');
            this.elements.logoutBtn = document.getElementById('logout-btn');
            this.elements.adminLink = document.getElementById('admin-link');

            // نوافذ التفاصيل والتلخيص
            this.elements.detailsDialog = document.getElementById('details-dialog');
            this.elements.detailsPlaceholder = document.getElementById('item-details-placeholder');
            this.elements.commentsContainer = document.getElementById('comments-container');
            this.elements.submitFeedbackBtn = document.getElementById('submit-feedback-btn');
            this.elements.commentInput = document.getElementById('comment-input');
            this.elements.ratingStarsInput = document.getElementById('rating-stars-input');
            this.elements.summaryDialog = document.getElementById('summary-dialog');
            this.elements.summaryContent = document.getElementById('summary-content');
            
            // حاويات مساعدة
            this.elements.toastContainer = document.getElementById('toast-container');
            this.elements.paginationContainer = document.createElement('div');
            this.elements.paginationContainer.id = 'pagination-container';
            this.elements.paginationContainer.className = 'pagination-container';
            this.elements.viewContainer.insertAdjacentElement('afterend', this.elements.paginationContainer);
        },

        bindEvents() {
            // ربط جميع مستمعي الأحداث
            this.elements.sidebarLinks.forEach(link => link.addEventListener('click', this.handlers.onViewChange.bind(this)));
            this.elements.exploreBtn.addEventListener('click', this.handlers.onExplore.bind(this));
            this.elements.languageSelect.addEventListener('change', e => this.handlers.onLanguageChange(e.target.value));
            
            // أزرار فتح النوافذ
            document.getElementById('open-login-btn').addEventListener('click', () => this.elements.loginDialog.showModal());
            document.getElementById('open-register-btn').addEventListener('click', () => this.elements.registerDialog.showModal());
            
            // أزرار إغلاق النوافذ والتبديل بينها
            document.querySelectorAll('.close-dialog').forEach(btn => btn.addEventListener('click', () => btn.closest('dialog').close()));
            document.getElementById('switch-to-register').addEventListener('click', this.handlers.onSwitchToRegister.bind(this));
            document.getElementById('switch-to-login').addEventListener('click', this.handlers.onSwitchToLogin.bind(this));

            // نماذج التوثيق
            this.elements.loginForm.addEventListener('submit', this.handlers.onLogin.bind(this));
            this.elements.registerForm.addEventListener('submit', this.handlers.onRegister.bind(this));
            this.elements.logoutBtn.addEventListener('click', this.handlers.onLogout.bind(this));
            
            // الأحداث الديناميكية داخل حاوية المحتوى
            this.elements.viewContainer.addEventListener('click', this.handlers.onContentClick.bind(this));
            
            // إرسال التقييم
            this.elements.submitFeedbackBtn.addEventListener('click', this.handlers.onSubmitFeedback.bind(this));
        },

        async loadInitialState() {
            // تحميل الترجمات أولاً لأن كل شيء يعتمد عليها
            await this.handlers.onLanguageChange(localStorage.getItem('app_lang') || 'ar');
            
            // تحميل جلسة المستخدم
            const token = localStorage.getItem('token');
            const user = localStorage.getItem('user');
            if (token && user) {
                this.state.currentToken = token;
                this.state.currentUser = JSON.parse(user);
            }
            
            this.ui.updateAuthUI();
            this.ui.updateViewTemplate();
            this.loadContent();
        },

        // -----------------------------------------------------------------------------
        // 3. معالجات الأحداث (Handlers)
        // -----------------------------------------------------------------------------
        handlers: {
            onViewChange(e) {
                e.preventDefault();
                this.state.currentPage = 1;
                this.state.currentSearchQuery = '';
                this.state.currentView = e.currentTarget.dataset.view;
                
                this.ui.setActiveLink(e.currentTarget);
                this.ui.updateViewTemplate();
                this.loadContent();
            },
            onExplore() {
                this.elements.landingView.style.opacity = '0';
                setTimeout(() => {
                    this.elements.landingView.classList.add('hidden');
                    this.elements.libraryView.classList.remove('hidden');
                }, 500);
            },
            async onLanguageChange(lang) {
                await window.i18n.setLanguage(lang);
                this.state.translations = window.i18n.translations;
                this.loadContent(); // إعادة تحميل المحتوى لتحديث النصوص
            },
            onSwitchToRegister(e) {
                e.preventDefault();
                this.elements.loginDialog.close();
                this.elements.registerDialog.showModal();
            },
            onSwitchToLogin(e) {
                e.preventDefault();
                this.elements.registerDialog.close();
                this.elements.loginDialog.showModal();
            },
            async onLogin(e) {
                e.preventDefault();
                const formData = new URLSearchParams(new FormData(e.target));
                try {
                    const data = await this.api.login(formData);
                    this.state.currentToken = data.access_token;
                    this.state.currentUser = data.user;
                    localStorage.setItem('token', this.state.currentToken);
                    localStorage.setItem('user', JSON.stringify(this.state.currentUser));
                    
                    this.ui.updateAuthUI();
                    this.elements.loginDialog.close();
                    this.ui.showToast(this.state.translations.login_success, 'success');
                } catch (error) {
                    this.ui.handleApiError(error);
                }
            },
            async onRegister(e) {
                e.preventDefault();
                const userData = Object.fromEntries(new FormData(e.target));
                try {
                    await this.api.register(userData);
                    this.ui.showToast(this.state.translations.registration_success, 'success');
                    this.elements.registerDialog.close();
                    this.elements.loginDialog.showModal();
                } catch (error) {
                    this.ui.handleApiError(error);
                }
            },
            onLogout() {
                this.state.currentUser = null;
                this.state.currentToken = null;
                localStorage.clear();
                this.ui.updateAuthUI();
                this.ui.showToast(this.state.translations.logout_success, 'success');
            },
            onContentClick(e) {
                const detailsBtn = e.target.closest('.view-details-btn');
                const summarizeBtn = e.target.closest('.summarize-btn');
                if (detailsBtn) this.loadDetails(detailsBtn.dataset.id);
                if (summarizeBtn) this.loadSummary(summarizeBtn.dataset.id);
            },
            async onSubmitFeedback() {
                 if (!this.state.currentUser) {
                    this.ui.showToast(this.state.translations.login_to_comment, 'error');
                    return;
                }
                const contentId = this.elements.detailsDialog.dataset.currentItemId;
                const rating = this.elements.ratingStarsInput.querySelector('.fas.fa-star.active')?.dataset.rating;
                const comment = this.elements.commentInput.value;

                if (!rating) {
                    this.ui.showToast(this.state.translations.select_rating, 'error');
                    return;
                }
                if (comment.length < 10) {
                    this.ui.showToast(this.state.translations.comment_min_length, 'error');
                    return;
                }
                
                try {
                    await this.api.postFeedback({ content_id: contentId, rating: parseInt(rating), comment });
                    this.ui.showToast(this.state.translations.comment_success, 'success');
                    // تحديث التعليقات مباشرة
                    const comments = await this.api.getFeedback(contentId);
                    this.ui.renderComments(comments);
                    this.elements.commentInput.value = '';
                } catch (error) {
                    this.ui.handleApiError(error);
                }
            }
        },

        // -----------------------------------------------------------------------------
        // 4. منطق العمل الرئيسي (Business Logic)
        // -----------------------------------------------------------------------------
        async loadContent() {
            this.ui.toggleLoader(true);
            this.elements.viewContainer.querySelector('.content-grid')?.remove();
            
            try {
                const content = await this.api.getContent(this.state.currentView, this.state.currentPage, this.state.currentSearchQuery);
                this.state.isLastPage = content.length < this.state.itemsPerPage;
                this.ui.renderItems(content);
                this.ui.renderPagination();
            } catch (error) {
                this.ui.handleApiError(error);
            } finally {
                this.ui.toggleLoader(false);
            }
        },

        async loadDetails(itemId) {
            this.elements.detailsDialog.showModal();
            this.ui.renderItemDetails(null); // عرض هيكل التحميل
            try {
                const item = await this.api.getItemDetails(itemId);
                const comments = await this.api.getFeedback(itemId);
                this.ui.renderItemDetails(item);
                this.ui.renderComments(comments);
                this.elements.detailsDialog.dataset.currentItemId = itemId;
            } catch (error) {
                this.ui.handleApiError(error);
                this.elements.detailsDialog.close();
            }
        },
        
        async loadSummary(itemId) {
            if (!this.state.currentUser) {
                this.ui.showToast(this.state.translations.login_to_summarize, 'error');
                return;
            }
            this.elements.summaryContent.innerHTML = `<div class="loader"></div><p>${this.state.translations.summarizing}</p>`;
            this.elements.summaryDialog.showModal();
            try {
                const result = await this.api.getSummary(itemId);
                this.elements.summaryContent.innerHTML = `<p>${result.summary}</p>`;
            } catch(error) {
                this.ui.handleApiError(error);
                this.elements.summaryDialog.close();
            }
        },

        // -----------------------------------------------------------------------------
        // 5. طبقة الاتصال بالخادم (API Layer)
        // -----------------------------------------------------------------------------
        api: {
            async _request(endpoint, method = 'GET', body = null, headers = {}) {
                const url = `/api${endpoint}`;
                const defaultHeaders = { 'Content-Type': 'application/json' };
                if (app.state.currentToken) {
                    defaultHeaders['Authorization'] = `Bearer ${app.state.currentToken}`;
                }

                const options = { method, headers: { ...defaultHeaders, ...headers } };
                if (body) {
                    options.body = (body instanceof URLSearchParams) ? body : JSON.stringify(body);
                }
                
                const response = await fetch(url, options);
                const responseData = await response.json().catch(() => ({})); // تجنب الخطأ لو كان الرد فارغاً

                if (!response.ok) {
                    throw { status: response.status, data: responseData };
                }
                return responseData;
            },
            
            login(formData) {
                return this._request('/token', 'POST', formData, { 'Content-Type': 'application/x-www-form-urlencoded' });
            },
            register(userData) {
                return this._request('/register', 'POST', userData);
            },
            getContent(type, page, query) {
                const params = new URLSearchParams({ content_type: type, page, page_size: app.state.itemsPerPage });
                if (query) params.append('q', query);
                return this._request(`/content?${params.toString()}`);
            },
            getItemDetails(id) {
                return this._request(`/content/${id}`);
            },
            getFeedback(contentId) {
                return this._request(`/feedback/${contentId}`);
            },
            postFeedback(data) {
                return this._request('/feedback', 'POST', data);
            },
            getSummary(id) {
                return this._request(`/summarize/${id}`, 'POST');
            }
        },

        // -----------------------------------------------------------------------------
        // 6. طبقة واجهة المستخدم (UI Layer)
        // -----------------------------------------------------------------------------
        ui: {
            toggleLoader(show) {
                app.elements.loaderContainer.classList.toggle('hidden', !show);
            },
            
            updateAuthUI() {
                const isLoggedIn = !!app.state.currentUser;
                app.elements.authButtons.classList.toggle('hidden', isLoggedIn);
                app.elements.userInfo.classList.toggle('hidden', !isLoggedIn);
                if (isLoggedIn) {
                    app.elements.usernameDisplay.textContent = app.state.currentUser.username;
                    app.elements.userAvatar.textContent = app.state.currentUser.username.charAt(0).toUpperCase();
                    app.elements.adminLink.classList.toggle('hidden', !app.state.currentUser.is_admin);
                }
            },

            setActiveLink(activeLink) {
                app.elements.sidebarLinks.forEach(l => l.classList.remove('active'));
                activeLink.classList.add('active');
                app.elements.mainTitle.textContent = activeLink.textContent;
            },

            updateViewTemplate() {
                 const templateId = `${app.state.currentView}-view-template`;
                 const template = document.getElementById(templateId);
                 if (template) {
                     app.elements.viewContainer.innerHTML = template.innerHTML;
                     const searchBar = app.elements.viewContainer.querySelector('.section-search-bar');
                     if(searchBar) {
                         searchBar.value = app.state.currentSearchQuery;
                         searchBar.addEventListener('keypress', e => {
                            if(e.key === 'Enter') {
                                app.state.currentSearchQuery = e.target.value;
                                app.state.currentPage = 1;
                                app.loadContent();
                            }
                         });
                     }
                 }
            },
            
            renderItems(items) {
                let grid = app.elements.viewContainer.querySelector('.content-grid');
                if(!grid) return;
                
                if (app.state.currentPage === 1) grid.innerHTML = '';

                if (items.length === 0 && app.state.currentPage === 1) {
                    grid.innerHTML = `<p class="w-full text-center text-gray-500">${app.state.translations.no_matching_results}</p>`;
                    return;
                }
                
                const fragment = document.createDocumentFragment();
                items.forEach(item => {
                    const card = document.createElement('div');
                    card.className = 'content-card';
                    card.innerHTML = `
                        <div class="card-image">
                            <img src="${item.thumbnail || ''}" alt="${item.title}" onerror="this.onerror=null; this.src='https://placehold.co/400x240/e2e8f0/64748b?text=${encodeURIComponent(app.state.translations.no_image)}';">
                        </div>
                        <div class="card-body">
                            <h3 class="card-title">${item.title}</h3>
                            <p class="card-description">${item.description || app.state.translations.no_description}</p>
                        </div>
                        <div class="card-footer">
                            <span class="card-category">${app.state.translations[item.content_type] || item.content_type}</span>
                            <div class="card-actions">
                                <button class="action-btn primary view-details-btn" data-id="${item._id}">${app.state.translations.details || 'Details'}</button>
                                ${item.content_type !== 'hadith' ? `<button class="action-btn success summarize-btn" data-id="${item._id}">${app.state.translations.summarize_with_ai || 'Summarize'}</button>` : ''}
                            </div>
                        </div>
                    `;
                    fragment.appendChild(card);
                });
                grid.appendChild(fragment);
            },
            
            renderPagination() {
                const container = app.elements.paginationContainer;
                container.innerHTML = '';
                
                if (app.state.currentPage === 1 && app.state.isLastPage) return;

                const prevBtn = this.createPaginationButton(app.state.translations.previous || 'Previous', () => { app.state.currentPage--; app.loadContent(); });
                prevBtn.disabled = app.state.currentPage === 1;
                
                const nextBtn = this.createPaginationButton(app.state.translations.next || 'Next', () => { app.state.currentPage++; app.loadContent(); });
                nextBtn.disabled = app.state.isLastPage;
                
                const pageIndicator = document.createElement('span');
                pageIndicator.className = 'pagination-indicator';
                pageIndicator.textContent = app.state.currentPage;

                container.append(prevBtn, pageIndicator, nextBtn);
            },
            
            createPaginationButton(text, onClick) {
                const btn = document.createElement('button');
                btn.textContent = text;
                btn.className = 'pagination-btn';
                btn.addEventListener('click', onClick);
                return btn;
            },

            renderItemDetails(item) {
                if (!item) {
                    app.elements.detailsPlaceholder.innerHTML = '<div class="loader"></div>';
                    return;
                }
                app.elements.detailsPlaceholder.innerHTML = `
                    <h3 class="text-2xl font-bold mb-2">${item.title}</h3>
                    <img src="${item.thumbnail || ''}" alt="${item.title}" class="w-full h-64 object-cover rounded-lg mb-4" onerror="this.style.display='none'">
                    <p>${item.description || app.state.translations.no_description}</p>
                    <div class="mt-4 text-sm text-gray-600">
                        <span><strong>${app.state.translations.type}:</strong> ${item.content_type}</span> | 
                        <span><strong>${app.state.translations.source}:</strong> ${item.source}</span>
                    </div>
                `;
            },
            renderComments(comments) {
                const container = app.elements.commentsContainer;
                if(comments.length === 0) {
                    container.innerHTML = `<p>${app.state.translations.no_comments_yet}</p>`;
                    return;
                }
                container.innerHTML = comments.map(c => `
                    <div class="comment-card">
                        <strong class="comment-author">${c.username}</strong>
                        <p class="comment-text">${c.comment}</p>
                        <div class="comment-rating">${'★'.repeat(c.rating)}${'☆'.repeat(5-c.rating)}</div>
                    </div>
                `).join('');
            },

            showToast(message, type = 'success') {
                const toast = document.createElement('div');
                toast.className = `toast toast-${type}`;
                toast.textContent = message;
                app.elements.toastContainer.appendChild(toast);
                setTimeout(() => toast.classList.add('show'), 100);
                setTimeout(() => {
                    toast.classList.remove('show');
                    toast.addEventListener('transitionend', () => toast.remove());
                }, 3500);
            },
            
            handleApiError(error) {
                console.error("API Error:", error);
                let message = app.state.translations.login_error; // رسالة افتراضية
                if (error && error.data) {
                    message = error.data.details?.[0]?.message || error.data.message || JSON.stringify(error.data);
                } else if (error && error.message) {
                    message = error.message;
                }
                this.showToast(message, 'error');
            }
        }
    };

    // بدء تشغيل التطبيق
    app.init();
});
