/**
 * WebDAV同步模块 - 与电脑端数据实时同步
 * 支持ZIP格式、双向同步和冲突处理
 * 性能优化版本：添加请求重试、请求队列和超时控制
 */

class WebDAVSync {
    // 同步文件名（与电脑端统一）
    static SYNC_FILENAME = 'timetracker_sync.zip';
    static SYNC_META_FILENAME = 'sync_meta.json';
    
    // 性能优化：请求配置
    static REQUEST_CONFIG = {
        maxRetries: 3,           // 最大重试次数
        retryDelay: 1000,        // 初始重试延迟（毫秒）
        timeout: 30000,          // 请求超时时间（毫秒）
        maxConcurrent: 2         // 最大并发请求数
    };

    constructor() {
        this.config = this.loadConfig();
        this._deviceId = this._getDeviceId();
        this._isSyncing = false;
        this._syncCallbacks = [];
        
        // 性能优化：请求队列
        this._requestQueue = [];
        this._activeRequests = 0;
        this._pendingRequests = new Map(); // 用于请求去重
    }

    // 获取设备唯一标识
    _getDeviceId() {
        let deviceId = localStorage.getItem('device_id');
        if (!deviceId) {
            deviceId = 'mobile_' + Math.random().toString(36).substring(2, 10);
            localStorage.setItem('device_id', deviceId);
        }
        return deviceId;
    }

    // 加载WebDAV配置
    loadConfig() {
        const defaultConfig = {
            enabled: false,
            serverUrl: '',
            username: '',
            password: '',
            remotePath: '/TimeTracker/',
            autoSync: true,
            syncInterval: 30,
            lastSync: null,
            lastSyncStatus: null,
            conflictStrategy: 'merge' // merge, local_first, remote_first
        };

        const saved = localStorage.getItem('webdav_config');
        if (saved) {
            try {
                const savedConfig = JSON.parse(saved);
                return { ...defaultConfig, ...savedConfig };
            } catch (e) {
                console.error('加载WebDAV配置失败:', e);
            }
        }
        return defaultConfig;
    }

    // 保存WebDAV配置
    saveConfig() {
        localStorage.setItem('webdav_config', JSON.stringify(this.config));
    }

    // 更新配置
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.saveConfig();
    }

    // 更新最后同步时间
    updateLastSync() {
        this.config.lastSync = new Date().toISOString();
        this.config.lastSyncStatus = 'success';
        this.saveConfig();
    }

    // 检查是否已配置
    isConfigured() {
        return this.config.enabled && this.config.serverUrl;
    }

    // 添加同步回调
    addSyncCallback(callback) {
        this._syncCallbacks.push(callback);
    }

    // 移除同步回调
    removeSyncCallback(callback) {
        const index = this._syncCallbacks.indexOf(callback);
        if (index > -1) {
            this._syncCallbacks.splice(index, 1);
        }
    }

    // 通知同步完成
    _notifySyncComplete(success, message) {
        this._syncCallbacks.forEach(callback => {
            try {
                callback(success, message);
            } catch (e) {
                console.error('同步回调执行失败:', e);
            }
        });
    }

    // 获取完整的远程URL
    getRemoteUrl(filename = '') {
        let url = this.config.serverUrl;
        if (!url.endsWith('/')) url += '/';

        let path = this.config.remotePath || '/TimeTracker/';
        if (!path.startsWith('/')) path = '/' + path;
        if (!path.endsWith('/')) path += '/';

        // 移除开头的斜杠以避免双斜杠
        path = path.substring(1);

        return url + path + filename;
    }

    // 获取认证头
    getAuthHeaders(contentType = 'application/json') {
        const headers = {};
        if (contentType) {
            headers['Content-Type'] = contentType;
        }

        if (this.config.username && this.config.password) {
            const auth = btoa(`${this.config.username}:${this.config.password}`);
            headers['Authorization'] = `Basic ${auth}`;
        }

        return headers;
    }

    // 测试连接
    async testConnection(tempConfig = null) {
        const config = tempConfig || this.config;

        if (!config.serverUrl) {
            return { success: false, message: '未配置服务器地址' };
        }

        try {
            let url = config.serverUrl;
            if (!url.endsWith('/')) url += '/';

            const headers = {};
            if (config.username && config.password) {
                const auth = btoa(`${config.username}:${config.password}`);
                headers['Authorization'] = `Basic ${auth}`;
            }

            const response = await fetch(url, {
                method: 'PROPFIND',
                headers: {
                    ...headers,
                    'Depth': '0'
                }
            });

            if (response.ok || response.status === 207) {
                return { success: true, message: '连接成功' };
            } else if (response.status === 401) {
                return { success: false, message: '认证失败，请检查用户名和密码' };
            } else {
                return { success: false, message: `服务器返回错误: ${response.status}` };
            }
        } catch (error) {
            return { success: false, message: `连接失败: ${error.message}` };
        }
    }

    // 确保远程目录存在
    async ensureRemoteDir() {
        if (!this.isConfigured()) return false;

        try {
            const url = this.getRemoteUrl();
            const headers = this.getAuthHeaders(null);

            await fetch(url, {
                method: 'MKCOL',
                headers
            });

            return true;
        } catch (error) {
            console.error('创建远程目录失败:', error);
            return false;
        }
    }

    // ==================== 性能优化：请求重试和队列 ====================
    
    /**
     * 带超时的 fetch 请求
     * @param {string} url - 请求URL
     * @param {object} options - fetch 选项
     * @param {number} timeout - 超时时间（毫秒）
     * @returns {Promise<Response>}
     */
    async _fetchWithTimeout(url, options, timeout = WebDAVSync.REQUEST_CONFIG.timeout) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            return response;
        } finally {
            clearTimeout(timeoutId);
        }
    }
    
    /**
     * 带重试机制的 fetch 请求
     * @param {string} url - 请求URL
     * @param {object} options - fetch 选项
     * @param {number} maxRetries - 最大重试次数
     * @returns {Promise<Response>}
     */
    async _fetchWithRetry(url, options, maxRetries = WebDAVSync.REQUEST_CONFIG.maxRetries) {
        let lastError;
        
        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                const response = await this._fetchWithTimeout(url, options);
                
                // 成功或客户端错误（4xx）不重试
                if (response.ok || (response.status >= 400 && response.status < 500)) {
                    return response;
                }
                
                // 服务器错误（5xx）需要重试
                if (response.status >= 500) {
                    lastError = new Error(`服务器错误: ${response.status}`);
                    console.warn(`[WebDAV] 请求失败 (${response.status})，尝试 ${attempt + 1}/${maxRetries + 1}`);
                } else {
                    return response;
                }
            } catch (error) {
                lastError = error;
                
                // 超时或网络错误
                if (error.name === 'AbortError') {
                    console.warn(`[WebDAV] 请求超时，尝试 ${attempt + 1}/${maxRetries + 1}`);
                } else {
                    console.warn(`[WebDAV] 网络错误: ${error.message}，尝试 ${attempt + 1}/${maxRetries + 1}`);
                }
            }
            
            // 如果不是最后一次尝试，等待后重试（指数退避）
            if (attempt < maxRetries) {
                const delay = WebDAVSync.REQUEST_CONFIG.retryDelay * Math.pow(2, attempt);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
        
        throw lastError || new Error('请求失败');
    }
    
    /**
     * 请求队列：防止重复请求
     * @param {string} key - 请求唯一标识
     * @param {Function} requestFn - 请求函数
     * @returns {Promise<any>}
     */
    async _queueRequest(key, requestFn) {
        // 检查是否有相同的请求正在进行
        if (this._pendingRequests.has(key)) {
            console.log(`[WebDAV] 复用已有请求: ${key}`);
            return this._pendingRequests.get(key);
        }
        
        // 等待并发数降低
        while (this._activeRequests >= WebDAVSync.REQUEST_CONFIG.maxConcurrent) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        // 创建新请求
        this._activeRequests++;
        const promise = requestFn()
            .finally(() => {
                this._activeRequests--;
                this._pendingRequests.delete(key);
            });
        
        this._pendingRequests.set(key, promise);
        return promise;
    }
    
    /**
     * 优化的网络请求方法
     * @param {string} url - 请求URL
     * @param {object} options - fetch 选项
     * @param {string} requestKey - 请求唯一标识（用于去重）
     * @returns {Promise<Response>}
     */
    async _optimizedFetch(url, options, requestKey = null) {
        const key = requestKey || `${options.method || 'GET'}:${url}`;
        
        return this._queueRequest(key, () => this._fetchWithRetry(url, options));
    }

    // 计算数据哈希
    _calculateDataHash(data) {
        const str = JSON.stringify(data);
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return hash.toString(16);
    }

    // 创建同步ZIP文件（使用JSZip库）
    async _createSyncZip(data) {
        // 检查JSZip是否可用
        if (typeof JSZip === 'undefined') {
            throw new Error('JSZip库未加载');
        }

        const zip = new JSZip();
        const rawData = data.data || data;

        // 添加数据文件（格式与电脑端兼容）
        // timer_records.json: 直接数组
        zip.file('timer_records.json', JSON.stringify(rawData.timer_records || [], null, 2));

        // memos.json: { items: [...], categories: [...] }
        zip.file('memos.json', JSON.stringify({
            items: rawData.memos || [],
            categories: rawData.categories || ['默认', '工作', '学习', '生活'],
            saved_at: new Date().toISOString()
        }, null, 2));

        // diary_entries.json: { entries: [...], tags: [...] }
        zip.file('diary_entries.json', JSON.stringify({
            entries: rawData.diary || [],
            tags: rawData.tags || ['日常', '工作', '学习', '生活', '旅行', '读书', '电影', '美食'],
            saved_at: new Date().toISOString()
        }, null, 2));

        // config.json
        zip.file('config.json', JSON.stringify(rawData.config || {}, null, 2));

        // 添加同步元数据
        const syncMeta = {
            sync_time: new Date().toISOString(),
            device_id: this._deviceId,
            device_type: 'mobile',
            data_hash: this._calculateDataHash(rawData),
            version: '2.0'
        };
        zip.file(WebDAVSync.SYNC_META_FILENAME, JSON.stringify(syncMeta, null, 2));

        // 生成ZIP文件
        return await zip.generateAsync({ type: 'blob' });
    }

    // 解压同步ZIP文件
    async _extractSyncZip(zipBlob) {
        if (typeof JSZip === 'undefined') {
            throw new Error('JSZip库未加载');
        }

        const zip = await JSZip.loadAsync(zipBlob);
        const result = {
            data: {
                memos: [],
                diary: [],
                timer_records: [],
                config: {}
            },
            meta: {}
        };

        // 读取元数据
        const metaFile = zip.file(WebDAVSync.SYNC_META_FILENAME);
        if (metaFile) {
            try {
                result.meta = JSON.parse(await metaFile.async('string'));
            } catch (e) {
                console.warn('读取同步元数据失败:', e);
            }
        }

        // 读取各数据文件
        const files = [
            { name: 'timer_records.json', key: 'timer_records', extract: d => Array.isArray(d) ? d : (d.records || []) },
            { name: 'memos.json', key: 'memos', extract: d => Array.isArray(d) ? d : (d.items || []) },
            { name: 'diary_entries.json', key: 'diary', extract: d => Array.isArray(d) ? d : (d.entries || []) },
            { name: 'config.json', key: 'config', extract: d => d || {} }
        ];

        for (const file of files) {
            const zipFile = zip.file(file.name);
            if (zipFile) {
                try {
                    const content = JSON.parse(await zipFile.async('string'));
                    result.data[file.key] = file.extract(content);
                } catch (e) {
                    console.warn(`读取 ${file.name} 失败:`, e);
                }
            }
        }

        return result;
    }

    // 按ID合并数据（保留最新的记录）
    _mergeById(localItems, remoteItems) {
        const merged = {};

        // 先添加本地数据
        for (const item of localItems) {
            if (item && typeof item === 'object') {
                const itemId = item.id || item.date || JSON.stringify(item);
                merged[itemId] = item;
            }
        }

        // 合并远程数据（如果更新时间更新则覆盖）
        for (const item of remoteItems) {
            if (item && typeof item === 'object') {
                const itemId = item.id || item.date || JSON.stringify(item);

                if (merged[itemId]) {
                    const localTime = merged[itemId].updated_at || merged[itemId].created_at || '';
                    const remoteTime = item.updated_at || item.created_at || '';

                    if (remoteTime > localTime) {
                        merged[itemId] = item;
                    }
                } else {
                    merged[itemId] = item;
                }
            }
        }

        return Object.values(merged);
    }

    // 合并数据
    _mergeData(localData, remoteData, strategy = 'merge') {
        if (strategy === 'local_first') {
            return localData;
        }

        if (strategy === 'remote_first') {
            return remoteData;
        }

        // 合并策略
        return {
            memos: this._mergeById(localData.memos || [], remoteData.memos || []),
            diary: this._mergeById(localData.diary || [], remoteData.diary || []),
            timer_records: this._mergeById(localData.timer_records || [], remoteData.timer_records || []),
            config: { ...(localData.config || {}), ...(remoteData.config || {}) }
        };
    }

    // 上传备份（ZIP格式）- 使用优化的请求方法
    async uploadBackup(data) {
        if (!this.isConfigured()) {
            throw new Error('WebDAV未配置');
        }

        await this.ensureRemoteDir();

        // 创建ZIP文件
        const zipBlob = await this._createSyncZip(data);

        // 上传ZIP文件 - 使用优化的请求方法（带重试和超时）
        const url = this.getRemoteUrl(WebDAVSync.SYNC_FILENAME);
        const headers = this.getAuthHeaders('application/zip');

        const response = await this._optimizedFetch(url, {
            method: 'PUT',
            headers,
            body: zipBlob
        }, 'upload:sync');

        if (!response.ok && response.status !== 201 && response.status !== 204) {
            throw new Error(`上传失败: ${response.status}`);
        }

        return true;
    }

    // 下载备份（ZIP格式）- 使用优化的请求方法
    async downloadBackup() {
        if (!this.isConfigured()) {
            throw new Error('WebDAV未配置');
        }

        const url = this.getRemoteUrl(WebDAVSync.SYNC_FILENAME);
        const headers = this.getAuthHeaders(null);

        // 使用优化的请求方法（带重试、超时和去重）
        const response = await this._optimizedFetch(url, {
            method: 'GET',
            headers
        }, 'download:sync');

        if (!response.ok) {
            if (response.status === 404) {
                // 远程文件不存在，返回空数据
                return {
                    data: { memos: [], diary: [], timer_records: [], config: {} },
                    meta: {}
                };
            }
            throw new Error(`下载失败: ${response.status}`);
        }

        const zipBlob = await response.blob();
        return await this._extractSyncZip(zipBlob);
    }

    // 双向同步
    async bidirectionalSync(localData) {
        if (!this.isConfigured()) {
            throw new Error('WebDAV未配置');
        }

        if (this._isSyncing) {
            throw new Error('同步正在进行中');
        }

        this._isSyncing = true;

        try {
            // 1. 下载远程数据
            let remoteResult;
            try {
                remoteResult = await this.downloadBackup();
            } catch (e) {
                console.warn('下载远程数据失败，将只上传本地数据:', e);
                remoteResult = {
                    data: { memos: [], diary: [], timer_records: [], config: {} },
                    meta: {}
                };
            }

            const remoteData = remoteResult.data;
            const remoteMeta = remoteResult.meta;

            // 2. 检查是否需要合并
            const localHash = this._calculateDataHash(localData);
            const remoteHash = remoteMeta.data_hash || '';

            let mergedData = localData;
            if (localHash !== remoteHash && remoteHash) {
                // 3. 合并数据
                const strategy = this.config.conflictStrategy || 'merge';
                mergedData = this._mergeData(localData, remoteData, strategy);
            }

            // 4. 上传合并后的数据
            await this.uploadBackup(mergedData);

            // 5. 更新同步状态
            this.updateLastSync();
            this._notifySyncComplete(true, '双向同步完成');

            return mergedData;

        } catch (error) {
            this._notifySyncComplete(false, error.message);
            throw error;
        } finally {
            this._isSyncing = false;
        }
    }

    // 标记数据已修改（触发同步）
    markDirty() {
        if (window.app) {
            window.app.markDataDirty();
        }
    }
}

// 导出模块
window.WebDAVSync = WebDAVSync;
