/**
 * Internationalization (i18n) Support
 * Multi-language support for RAG Enterprise
 * Languages: Korean (ko), English (en), Japanese (ja), Chinese (zh)
 * Version: v8.3.0
 */

const SUPPORTED_LANGUAGES = ['ko', 'en', 'ja', 'zh'];
const DEFAULT_LANGUAGE = 'ko';
const STORAGE_KEY = 'app_language';

// Translation dictionaries
const translations = {
    ko: {
        // Common
        'app.title': 'RAG Enterprise',
        'app.welcome': '환영합니다!',
        'common.loading': '로딩 중...',
        'common.error': '오류',
        'common.success': '성공',
        'common.cancel': '취소',
        'common.confirm': '확인',
        'common.save': '저장',
        'common.delete': '삭제',
        'common.edit': '수정',
        'common.search': '검색',
        'common.logout': '로그아웃',

        // Auth
        'auth.login': '로그인',
        'auth.register': '회원가입',
        'auth.email': '이메일',
        'auth.password': '비밀번호',
        'auth.forgot_password': '비밀번호를 잊으셨나요?',
        'auth.login_success': '로그인 성공',
        'auth.logout_confirm': '로그아웃 하시겠습니까?',

        // Navigation
        'nav.home': '홈',
        'nav.search': '검색',
        'nav.profile': '프로필',
        'nav.dashboard': '대시보드',
        'nav.work_orders': '작업지시',

        // Search
        'search.placeholder': '제품을 검색하세요...',
        'search.results': '검색 결과',
        'search.no_results': '검색 결과가 없습니다',
        'search.recent': '최근 검색',

        // Product
        'product.name': '제품명',
        'product.code': '제품 코드',
        'product.category': '카테고리',
        'product.material': '재질',
        'product.capacity': '용량',
        'product.price': '가격',
        'product.stock': '재고',

        // Work Order
        'wo.status': '상태',
        'wo.priority': '우선순위',
        'wo.quantity': '수량',
        'wo.progress': '진행률',
        'wo.start_date': '시작일',
        'wo.due_date': '마감일',

        // Settings
        'settings.language': '언어',
        'settings.theme': '테마',
        'settings.dark_mode': '다크 모드',
        'settings.notifications': '알림 설정',
    },

    en: {
        // Common
        'app.title': 'RAG Enterprise',
        'app.welcome': 'Welcome!',
        'common.loading': 'Loading...',
        'common.error': 'Error',
        'common.success': 'Success',
        'common.cancel': 'Cancel',
        'common.confirm': 'Confirm',
        'common.save': 'Save',
        'common.delete': 'Delete',
        'common.edit': 'Edit',
        'common.search': 'Search',
        'common.logout': 'Logout',

        // Auth
        'auth.login': 'Login',
        'auth.register': 'Register',
        'auth.email': 'Email',
        'auth.password': 'Password',
        'auth.forgot_password': 'Forgot password?',
        'auth.login_success': 'Login successful',
        'auth.logout_confirm': 'Are you sure you want to logout?',

        // Navigation
        'nav.home': 'Home',
        'nav.search': 'Search',
        'nav.profile': 'Profile',
        'nav.dashboard': 'Dashboard',
        'nav.work_orders': 'Work Orders',

        // Search
        'search.placeholder': 'Search products...',
        'search.results': 'Search Results',
        'search.no_results': 'No results found',
        'search.recent': 'Recent Searches',

        // Product
        'product.name': 'Product Name',
        'product.code': 'Product Code',
        'product.category': 'Category',
        'product.material': 'Material',
        'product.capacity': 'Capacity',
        'product.price': 'Price',
        'product.stock': 'Stock',

        // Work Order
        'wo.status': 'Status',
        'wo.priority': 'Priority',
        'wo.quantity': 'Quantity',
        'wo.progress': 'Progress',
        'wo.start_date': 'Start Date',
        'wo.due_date': 'Due Date',

        // Settings
        'settings.language': 'Language',
        'settings.theme': 'Theme',
        'settings.dark_mode': 'Dark Mode',
        'settings.notifications': 'Notifications',
    },

    ja: {
        // Common
        'app.title': 'RAG Enterprise',
        'app.welcome': 'ようこそ！',
        'common.loading': '読み込み中...',
        'common.error': 'エラー',
        'common.success': '成功',
        'common.cancel': 'キャンセル',
        'common.confirm': '確認',
        'common.save': '保存',
        'common.delete': '削除',
        'common.edit': '編集',
        'common.search': '検索',
        'common.logout': 'ログアウト',

        // Auth
        'auth.login': 'ログイン',
        'auth.register': '新規登録',
        'auth.email': 'メール',
        'auth.password': 'パスワード',
        'auth.forgot_password': 'パスワードをお忘れですか？',
        'auth.login_success': 'ログイン成功',
        'auth.logout_confirm': 'ログアウトしますか？',

        // Navigation
        'nav.home': 'ホーム',
        'nav.search': '検索',
        'nav.profile': 'プロフィール',
        'nav.dashboard': 'ダッシュボード',
        'nav.work_orders': '作業指示',

        // Search
        'search.placeholder': '製品を検索...',
        'search.results': '検索結果',
        'search.no_results': '結果が見つかりません',
        'search.recent': '最近の検索',

        // Product
        'product.name': '製品名',
        'product.code': '製品コード',
        'product.category': 'カテゴリー',
        'product.material': '素材',
        'product.capacity': '容量',
        'product.price': '価格',
        'product.stock': '在庫',

        // Work Order
        'wo.status': 'ステータス',
        'wo.priority': '優先度',
        'wo.quantity': '数量',
        'wo.progress': '進捗',
        'wo.start_date': '開始日',
        'wo.due_date': '期限',

        // Settings
        'settings.language': '言語',
        'settings.theme': 'テーマ',
        'settings.dark_mode': 'ダークモード',
        'settings.notifications': '通知設定',
    },

    zh: {
        // Common
        'app.title': 'RAG Enterprise',
        'app.welcome': '欢迎！',
        'common.loading': '加载中...',
        'common.error': '错误',
        'common.success': '成功',
        'common.cancel': '取消',
        'common.confirm': '确认',
        'common.save': '保存',
        'common.delete': '删除',
        'common.edit': '编辑',
        'common.search': '搜索',
        'common.logout': '登出',

        // Auth
        'auth.login': '登录',
        'auth.register': '注册',
        'auth.email': '邮箱',
        'auth.password': '密码',
        'auth.forgot_password': '忘记密码？',
        'auth.login_success': '登录成功',
        'auth.logout_confirm': '确定要登出吗？',

        // Navigation
        'nav.home': '首页',
        'nav.search': '搜索',
        'nav.profile': '个人资料',
        'nav.dashboard': '仪表板',
        'nav.work_orders': '工作订单',

        // Search
        'search.placeholder': '搜索产品...',
        'search.results': '搜索结果',
        'search.no_results': '未找到结果',
        'search.recent': '最近搜索',

        // Product
        'product.name': '产品名称',
        'product.code': '产品代码',
        'product.category': '类别',
        'product.material': '材质',
        'product.capacity': '容量',
        'product.price': '价格',
        'product.stock': '库存',

        // Work Order
        'wo.status': '状态',
        'wo.priority': '优先级',
        'wo.quantity': '数量',
        'wo.progress': '进度',
        'wo.start_date': '开始日期',
        'wo.due_date': '截止日期',

        // Settings
        'settings.language': '语言',
        'settings.theme': '主题',
        'settings.dark_mode': '暗黑模式',
        'settings.notifications': '通知设置',
    }
};

class I18n {
    constructor() {
        this.currentLanguage = this.loadLanguage();
    }

    /**
     * Load saved language or detect browser language
     */
    loadLanguage() {
        // Check localStorage
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved && SUPPORTED_LANGUAGES.includes(saved)) {
            return saved;
        }

        // Detect browser language
        const browserLang = navigator.language.split('-')[0];
        if (SUPPORTED_LANGUAGES.includes(browserLang)) {
            return browserLang;
        }

        return DEFAULT_LANGUAGE;
    }

    /**
     * Set language
     */
    setLanguage(lang) {
        if (!SUPPORTED_LANGUAGES.includes(lang)) {
            console.warn(`Unsupported language: ${lang}`);
            return;
        }

        this.currentLanguage = lang;
        localStorage.setItem(STORAGE_KEY, lang);

        // Update page
        this.updatePage();

        // Dispatch event
        window.dispatchEvent(new CustomEvent('languageChanged', {detail: {language: lang}}));
    }

    /**
     * Get translation
     */
    t(key, params = {}) {
        const dict = translations[this.currentLanguage] || translations[DEFAULT_LANGUAGE];
        let text = dict[key] || key;

        // Replace parameters
        Object.keys(params).forEach(param => {
            text = text.replace(`{${param}}`, params[param]);
        });

        return text;
    }

    /**
     * Get current language
     */
    getLanguage() {
        return this.currentLanguage;
    }

    /**
     * Get supported languages
     */
    getSupportedLanguages() {
        return SUPPORTED_LANGUAGES;
    }

    /**
     * Update all elements with data-i18n attribute
     */
    updatePage() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const text = this.t(key);

            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = text;
            } else {
                element.textContent = text;
            }
        });

        // Update title
        const titleElements = document.querySelectorAll('[data-i18n-title]');
        titleElements.forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });

        // Update document title
        document.title = this.t('app.title');
    }
}

// Global instance
const i18n = new I18n();

// Auto-update page on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        i18n.updatePage();
    });
} else {
    i18n.updatePage();
}

// Export
window.i18n = i18n;
window.t = (key, params) => i18n.t(key, params);
