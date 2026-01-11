/**
 * Time Tracker Mobile App - 主应用程序
 * 整合待办事项、日记、计时器功能
 * 支持 WebDAV 实时同步，与桌面端数据兼容
 */

// 全局应用实例
let app = null;

// 应用主类
class App {
    constructor() {
        this.currentTab = 'timerPage';
        this.storage = null;
        this.webdav = null;
        this.timer = null;
        this.memo = null;
        this.diary = null;
        this.isInitialized = false;
        this.syncInterval = null;
        this.syncPending = false;
    }

    // 初始化应用
    async init() {
        try {
            // 显示加载状态
            this.showLoading('正在初始化应用...');

            // 初始化存储
            this.storage = new Storage();
            await this.storage.init();

            // 初始化 WebDAV
            this.webdav = new WebDAVSync();

            // 初始化各模块
            this.timer = new TimerModule();
            this.memo = new MemoManager(this.storage);
            this.diary = new DiaryModule(this.storage);

            // 初始化导航
            this.initNavigation();

            // 初始化设置页面
            this.initSettings();

            // 初始化同步按钮
            this.initSyncButton();

            // 初始化各模块
            await this.timer.init();
            await this.memo.init();
            await this.diary.init();

            // 隐藏加载状态
            this.hideLoading();

            // 显示默认标签页
            this.showTab('timerPage');

            // 启动实时同步
            this.startRealtimeSync();

            this.isInitialized = true;
            console.log('应用初始化完成');

        } catch (error) {
            console.error('应用初始化失败:', error);
            this.hideLoading();
            this.showToast('应用初始化失败: ' + error.message, 'error');
        }
    }

    // 初始化导航
    initNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const pageId = item.dataset.page;
                if (pageId) {
                    this.showTab(pageId);
                }
            });
        });
    }

    // 显示标签页
    showTab(pageId) {
        this.currentTab = pageId;

        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === pageId);
        });

        // 更新内容区域
        document.querySelectorAll('.page').forEach(content => {
            content.classList.toggle('active', content.id === pageId);
        });

        // 触发标签页切换事件
        this.onTabChange(pageId);
    }

    // 标签页切换回调
    onTabChange(pageId) {
        switch (pageId) {
            case 'timerPage':
                this.timer?.render?.();
                break;
            case 'memoPage':
                this.memo?.render?.();
                break;
            case 'diaryPage':
                this.diary?.renderEntryList?.();
                break;
            case 'settingsPage':
                this.refreshSettings();
                break;
        }
    }

    // 初始化同步按钮
    initSyncButton() {
        const syncBtn = document.getElementById('syncBtn');
        if (syncBtn) {
            syncBtn.addEventListener('click', () => this.manualSync());
        }
    }

    // 初始化设置页面
    initSettings() {
        // WebDAV 设置保存按钮
        const saveWebdavBtn = document.getElementById('saveWebdavBtn');
        if (saveWebdavBtn) {
            saveWebdavBtn.addEventListener('click', () => this.saveWebDAVSettings());
        }

        // 测试连接按钮
        const testWebdavBtn = document.getElementById('testConnectionBtn');
        if (testWebdavBtn) {
            testWebdavBtn.addEventListener('click', () => this.testWebDAVConnection());
        }

        // 数据同步按钮
        const uploadBackupBtn = document.getElementById('uploadBackupBtn');
        if (uploadBackupBtn) {
            uploadBackupBtn.addEventListener('click', () => this.uploadToWebDAV());
        }

        const downloadBackupBtn = document.getElementById('downloadBackupBtn');
        if (downloadBackupBtn) {
            downloadBackupBtn.addEventListener('click', () => this.downloadFromWebDAV());
        }

        const clearDataBtn = document.getElementById('clearDataBtn');
        if (clearDataBtn) {
            clearDataBtn.addEventListener('click', () => this.clearAllData());
        }

        // 加载当前设置
        this.refreshSettings();
    }

    // 刷新设置页面
    refreshSettings() {
        const config = this.webdav?.config || {};

        const webdavServer = document.getElementById('webdavServer');
        const webdavUsername = document.getElementById('webdavUsername');
        const webdavPassword = document.getElementById('webdavPassword');
        const webdavPath = document.getElementById('webdavPath');
        const webdavEnabled = document.getElementById('webdavEnabled');

        if (webdavServer) webdavServer.value = config.serverUrl || '';
        if (webdavUsername) webdavUsername.value = config.username || '';
        if (webdavPassword) webdavPassword.value = config.password || '';
        if (webdavPath) webdavPath.value = config.remotePath || '/TimeTracker/';
        if (webdavEnabled) webdavEnabled.checked = config.enabled || false;

        // 更新同步状态
        this.updateSyncStatus();
    }

    // 保存 WebDAV 设置
    saveWebDAVSettings() {
        const serverUrl = document.getElementById('webdavServer')?.value?.trim();
        const username = document.getElementById('webdavUsername')?.value?.trim();
        const password = document.getElementById('webdavPassword')?.value;
        const remotePath = document.getElementById('webdavPath')?.value?.trim() || '/TimeTracker/';
        const enabled = document.getElementById('webdavEnabled')?.checked || false;

        if (enabled && !serverUrl) {
            this.showToast('请输入 WebDAV 服务器地址', 'warning');
            return;
        }

        this.webdav.updateConfig({
            enabled,
            serverUrl,
            username,
            password,
            remotePath
        });

        // 重启实时同步
        this.startRealtimeSync();

        this.showToast('WebDAV 设置已保存', 'success');
        this.updateSyncStatus();
    }

    // 测试 WebDAV 连接
    async testWebDAVConnection() {
        const serverUrl = document.getElementById('webdavServer')?.value?.trim();
        const username = document.getElementById('webdavUsername')?.value?.trim();
        const password = document.getElementById('webdavPassword')?.value;

        if (!serverUrl) {
            this.showToast('请输入服务器地址', 'warning');
            return;
        }

        this.showLoading('正在测试连接...');

        try {
            // 临时更新配置进行测试
            const tempConfig = {
                serverUrl,
                username,
                password,
                remotePath: document.getElementById('webdavPath')?.value?.trim() || '/TimeTracker/'
            };

            const result = await this.webdav.testConnection(tempConfig);
            this.hideLoading();

            if (result.success) {
                this.showToast('连接成功！', 'success');
            } else {
                this.showToast('连接失败: ' + result.message, 'error');
            }
        } catch (error) {
            this.hideLoading();
            this.showToast('连接失败: ' + error.message, 'error');
        }
    }

    // 启动实时同步
    startRealtimeSync() {
        // 清除现有的同步定时器
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }

        // 检查是否启用同步
        if (!this.webdav?.isConfigured()) {
            this.updateSyncIndicator('disabled');
            return;
        }

        // 立即执行一次同步
        this.performSync();

        // 设置定时同步（每30秒）
        this.syncInterval = setInterval(() => {
            this.performSync();
        }, 30000);

        console.log('实时同步已启动');
    }

    // 执行同步
    async performSync() {
        if (this.syncPending || !this.webdav?.isConfigured()) {
            return;
        }

        this.syncPending = true;
        this.updateSyncIndicator('syncing');

        try {
            // 获取本地数据
            const localData = await this.storage.exportAllData();

            // 上传到 WebDAV
            await this.webdav.uploadBackup(localData);

            // 更新同步状态
            this.webdav.updateLastSync();
            this.updateSyncIndicator('synced');
            this.updateSyncStatus();

        } catch (error) {
            console.error('同步失败:', error);
            this.updateSyncIndicator('error');
        } finally {
            this.syncPending = false;
        }
    }

    // 手动同步
    async manualSync() {
        if (!this.webdav?.isConfigured()) {
            this.showToast('请先配置 WebDAV 设置', 'warning');
            return;
        }

        this.showLoading('正在同步...');

        try {
            await this.performSync();
            this.hideLoading();
            this.showToast('同步完成', 'success');
        } catch (error) {
            this.hideLoading();
            this.showToast('同步失败: ' + error.message, 'error');
        }
    }

    // 更新同步指示器
    updateSyncIndicator(status) {
        const indicator = document.getElementById('syncIndicator');
        if (!indicator) return;

        indicator.className = 'sync-indicator';
        
        // 获取或创建图标和文字元素
        let icon = indicator.querySelector('i');
        let textSpan = indicator.querySelector('.sync-text');
        
        if (!icon) {
            icon = document.createElement('i');
            icon.className = 'fas fa-circle';
            indicator.insertBefore(icon, indicator.firstChild);
        }
        
        if (!textSpan) {
            textSpan = document.createElement('span');
            textSpan.className = 'sync-text';
            indicator.appendChild(textSpan);
        }

        switch (status) {
            case 'syncing':
                indicator.classList.add('syncing');
                indicator.title = '正在同步...';
                icon.className = 'fas fa-sync-alt fa-spin';
                textSpan.textContent = '同步中';
                break;
            case 'synced':
                indicator.classList.add('synced');
                indicator.title = '已同步';
                icon.className = 'fas fa-check-circle';
                textSpan.textContent = '已同步';
                break;
            case 'error':
                indicator.classList.add('error');
                indicator.title = '同步失败';
                icon.className = 'fas fa-exclamation-circle';
                textSpan.textContent = '同步失败';
                break;
            case 'disabled':
                indicator.classList.add('disabled');
                indicator.title = '同步未启用';
                icon.className = 'fas fa-circle';
                textSpan.textContent = '未启用';
                break;
            default:
                indicator.title = '未知状态';
                icon.className = 'fas fa-question-circle';
                textSpan.textContent = '未知';
        }
    }

    // 更新同步状态显示
    updateSyncStatus() {
        const lastSyncEl = document.getElementById('lastSyncTime');
        const statusEl = document.getElementById('syncStatusText');

        if (lastSyncEl) {
            const lastSync = this.webdav?.config?.lastSync;
            if (lastSync) {
                const date = new Date(lastSync);
                lastSyncEl.textContent = date.toLocaleString('zh-CN');
            } else {
                lastSyncEl.textContent = '从未';
            }
        }

        if (statusEl) {
            if (this.webdav?.isConfigured()) {
                statusEl.textContent = '已配置';
                statusEl.style.color = '#16a34a';
            } else {
                statusEl.textContent = '未配置';
                statusEl.style.color = '#6b7280';
            }
        }
    }

    // 上传到 WebDAV
    async uploadToWebDAV() {
        if (!this.webdav?.isConfigured()) {
            this.showToast('请先配置并启用 WebDAV 设置', 'warning');
            return;
        }

        this.showLoading('正在上传数据...');

        try {
            const data = await this.storage.exportAllData();
            await this.webdav.uploadBackup(data);
            this.webdav.updateLastSync();

            this.hideLoading();
            this.showToast('数据上传成功！', 'success');
            this.updateSyncStatus();
        } catch (error) {
            this.hideLoading();
            this.showToast('上传失败: ' + error.message, 'error');
        }
    }

    // 从 WebDAV 下载
    async downloadFromWebDAV() {
        if (!this.webdav?.isConfigured()) {
            this.showToast('请先配置并启用 WebDAV 设置', 'warning');
            return;
        }

        if (!confirm('下载将覆盖本地数据，确定继续吗？')) {
            return;
        }

        this.showLoading('正在下载数据...');

        try {
            const data = await this.webdav.downloadBackup();

            if (data) {
                await this.storage.importAllData(data);
                await this.refreshAllModules();
            }

            this.hideLoading();
            this.showToast('数据下载成功！', 'success');
            this.updateSyncStatus();
        } catch (error) {
            this.hideLoading();
            this.showToast('下载失败: ' + error.message, 'error');
        }
    }

    // 刷新所有模块
    async refreshAllModules() {
        // 重新加载数据
        await this.memo?.loadMemos?.();
        await this.diary?.loadEntries?.();

        // 重新渲染
        this.memo?.render?.();
        this.diary?.renderEntryList?.();
        this.timer?.renderHistory?.();
    }

    // 清除所有数据
    async clearAllData() {
        if (!confirm('确定要清除所有本地数据吗？此操作不可恢复！')) {
            return;
        }

        if (!confirm('再次确认：所有待办、日记、计时记录都将被删除！')) {
            return;
        }

        try {
            await this.storage.clearAllData();
            await this.refreshAllModules();
            this.showToast('所有数据已清除', 'success');
        } catch (error) {
            this.showToast('清除失败: ' + error.message, 'error');
        }
    }

    // 标记数据已修改（触发同步）
    markDataDirty() {
        // 如果启用了实时同步，立即执行同步
        if (this.webdav?.isConfigured()) {
            // 延迟1秒执行，避免频繁同步
            setTimeout(() => this.performSync(), 1000);
        }
    }

    // 显示加载状态
    showLoading(message = '加载中...') {
        let loading = document.getElementById('loadingOverlay');
        if (!loading) {
            loading = document.createElement('div');
            loading.id = 'loadingOverlay';
            loading.className = 'loading-overlay';
            loading.innerHTML = `
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span class="loading-text">${message}</span>
                </div>
            `;
            document.body.appendChild(loading);
        } else {
            loading.querySelector('.loading-text').textContent = message;
            loading.style.display = 'flex';
        }
    }

    // 隐藏加载状态
    hideLoading() {
        const loading = document.getElementById('loadingOverlay');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    // 显示提示消息
    showToast(message, type = 'info') {
        // 移除现有的 toast
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // 动画显示
        setTimeout(() => toast.classList.add('show'), 10);

        // 自动隐藏
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// DOM 加载完成后初始化应用
document.addEventListener('DOMContentLoaded', async () => {
    app = new App();
    window.app = app; // 暴露到全局，供其他模块使用
    await app.init();
});

// 全局辅助函数
function showTab(tabName) {
    app?.showTab(tabName);
}

function showToast(message, type) {
    app?.showToast(message, type);
}

// 处理页面可见性变化（用于暂停/恢复计时器等）
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // 页面隐藏时
        app?.timer?.onPageHidden?.();
    } else {
        // 页面显示时
        app?.timer?.onPageVisible?.();
        // 恢复时执行一次同步
        app?.performSync?.();
    }
});

// 处理在线/离线状态
window.addEventListener('online', () => {
    app?.showToast('网络已连接', 'success');
    app?.performSync?.();
});

window.addEventListener('offline', () => {
    app?.showToast('网络已断开，数据将在本地保存', 'warning');
});
