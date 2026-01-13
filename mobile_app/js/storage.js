/**
 * 数据存储模块 - 与电脑端数据格式兼容
 * 性能优化版本：添加内存缓存、批量操作支持
 */

class Storage {
    constructor() {
        this.DB_NAME = 'TimeTrackerDB';
        this.DB_VERSION = 1;
        this.db = null;
        
        // 性能优化：内存缓存
        this._cache = window.Performance?.MemoryCache
            ? new window.Performance.MemoryCache(300000) // 5分钟 TTL
            : null;
        
        // 缓存键前缀
        this._cacheKeys = {
            memos: 'store:memos',
            diary: 'store:diary',
            timer_records: 'store:timer_records',
            usage_records: 'store:usage_records',
            config: 'store:config'
        };
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // 待办事项存储
                if (!db.objectStoreNames.contains('memos')) {
                    const memoStore = db.createObjectStore('memos', { keyPath: 'id' });
                    memoStore.createIndex('completed', 'completed', { unique: false });
                    memoStore.createIndex('category', 'category', { unique: false });
                }
                
                // 日记存储
                if (!db.objectStoreNames.contains('diary')) {
                    const diaryStore = db.createObjectStore('diary', { keyPath: 'id' });
                    diaryStore.createIndex('date', 'date', { unique: false });
                    diaryStore.createIndex('created_at', 'created_at', { unique: false });
                }
                
                // 计时记录存储
                if (!db.objectStoreNames.contains('timer_records')) {
                    const timerStore = db.createObjectStore('timer_records', { keyPath: 'id', autoIncrement: true });
                    timerStore.createIndex('timestamp', 'timestamp', { unique: false });
                    timerStore.createIndex('start_time', 'start_time', { unique: false });
                }
                
                // 应用使用记录存储
                if (!db.objectStoreNames.contains('usage_records')) {
                    db.createObjectStore('usage_records', { keyPath: 'date' });
                }
                
                // 配置存储
                if (!db.objectStoreNames.contains('config')) {
                    db.createObjectStore('config', { keyPath: 'key' });
                }
            };
        });
    }

    // ==================== 缓存辅助方法 ====================
    
    /**
     * 使指定存储的缓存失效
     */
    _invalidateCache(storeName) {
        if (this._cache) {
            this._cache.delete(this._cacheKeys[storeName]);
        }
    }
    
    /**
     * 使所有缓存失效
     */
    _invalidateAllCache() {
        if (this._cache) {
            this._cache.clear();
        }
    }

    // ==================== 通用CRUD操作 ====================
    
    async add(storeName, data) {
        // 写操作后使缓存失效
        this._invalidateCache(storeName);
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.add(data);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async put(storeName, data) {
        // 写操作后使缓存失效
        this._invalidateCache(storeName);
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.put(data);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async get(storeName, key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getAll(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }
    
    /**
     * 带缓存的 getAll - 优先从缓存读取
     */
    async getAllCached(storeName) {
        const cacheKey = this._cacheKeys[storeName];
        
        // 尝试从缓存获取
        if (this._cache) {
            const cached = this._cache.get(cacheKey);
            if (cached !== undefined) {
                return cached;
            }
        }
        
        // 从 IndexedDB 获取
        const result = await this.getAll(storeName);
        
        // 存入缓存
        if (this._cache) {
            this._cache.set(cacheKey, result);
        }
        
        return result;
    }

    async delete(storeName, key) {
        // 写操作后使缓存失效
        this._invalidateCache(storeName);
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(key);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async clear(storeName) {
        // 写操作后使缓存失效
        this._invalidateCache(storeName);
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }
    
    // ==================== 批量操作（性能优化）====================
    
    /**
     * 批量添加数据 - 使用单个事务提高性能
     */
    async batchAdd(storeName, items) {
        if (!items || items.length === 0) return [];
        
        // 写操作后使缓存失效
        this._invalidateCache(storeName);
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const results = [];
            let completed = 0;
            
            transaction.oncomplete = () => resolve(results);
            transaction.onerror = () => reject(transaction.error);
            
            for (const item of items) {
                const request = store.add(item);
                request.onsuccess = () => {
                    results.push(request.result);
                    completed++;
                };
            }
        });
    }
    
    /**
     * 批量更新数据 - 使用单个事务提高性能
     */
    async batchPut(storeName, items) {
        if (!items || items.length === 0) return [];
        
        // 写操作后使缓存失效
        this._invalidateCache(storeName);
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const results = [];
            
            transaction.oncomplete = () => resolve(results);
            transaction.onerror = () => reject(transaction.error);
            
            for (const item of items) {
                const request = store.put(item);
                request.onsuccess = () => {
                    results.push(request.result);
                };
            }
        });
    }
    
    /**
     * 批量删除数据 - 使用单个事务提高性能
     */
    async batchDelete(storeName, keys) {
        if (!keys || keys.length === 0) return;
        
        // 写操作后使缓存失效
        this._invalidateCache(storeName);
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            
            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
            
            for (const key of keys) {
                store.delete(key);
            }
        });
    }

    // ==================== 待办事项操作 ====================
    
    async getMemos() {
        return this.getAll('memos');
    }

    async getMemo(id) {
        return this.get('memos', id);
    }

    async saveMemo(memo) {
        return this.put('memos', memo);
    }

    async addMemo(memo) {
        return this.add('memos', memo);
    }

    async deleteMemo(id) {
        return this.delete('memos', id);
    }

    // ==================== 日记操作 ====================
    
    async getAllDiaryEntries() {
        return this.getAll('diary');
    }

    async getDiaryEntry(id) {
        return this.get('diary', id);
    }

    async addDiaryEntry(entry) {
        return this.put('diary', entry);
    }

    async updateDiaryEntry(entry) {
        return this.put('diary', entry);
    }

    async deleteDiaryEntry(id) {
        return this.delete('diary', id);
    }

    // ==================== 计时记录操作 ====================
    
    async getTimerRecords() {
        return this.getAll('timer_records');
    }

    async addTimerRecord(record) {
        return this.put('timer_records', record);
    }

    async deleteTimerRecord(id) {
        return this.delete('timer_records', id);
    }

    // ==================== 使用记录操作 ====================
    
    async getUsageRecords() {
        return this.getAll('usage_records');
    }

    async saveUsageRecord(record) {
        return this.put('usage_records', record);
    }

    // ==================== 配置操作 ====================
    
    async getConfig(key = 'app_config') {
        const result = await this.get('config', key);
        return result?.value;
    }

    async setConfig(key, value) {
        return this.put('config', { key, value });
    }

    // ==================== 数据导入导出 ====================
    
    /**
     * 导出所有数据（用于WebDAV同步）
     * 计时器记录会转换为桌面端兼容格式（移除id字段）
     */
    async exportAllData() {
        const memos = await this.getMemos();
        const diary = await this.getAllDiaryEntries();
        const timerRecords = await this.getTimerRecords();
        const usageRecords = await this.getUsageRecords();
        const config = await this.getConfig();

        // 转换计时器记录为桌面端兼容格式（移除id字段）
        const desktopCompatibleTimerRecords = timerRecords.map(record => ({
            mode: record.mode,
            duration: record.duration,
            note: record.note || '',
            timestamp: record.timestamp,
            completed: record.completed !== undefined ? record.completed : true
        }));

        return {
            version: '1.0',
            exportTime: new Date().toISOString(),
            data: {
                memos,
                diary,
                timer_records: desktopCompatibleTimerRecords,
                usage_records: usageRecords,
                config
            }
        };
    }

    async importAllData(backup) {
        const data = backup.data || backup;

        // 导入待办事项
        if (data.memos && Array.isArray(data.memos)) {
            await this.clear('memos');
            for (const memo of data.memos) {
                await this.saveMemo(memo);
            }
        }

        // 导入日记（为桌面端记录生成date字段）
        if (data.diary && Array.isArray(data.diary)) {
            await this.clear('diary');
            for (const entry of data.diary) {
                // 桌面端记录没有date字段，需要从created_at提取
                const normalizedEntry = {
                    id: entry.id,
                    // 如果没有date字段，从created_at提取日期部分
                    date: entry.date || (entry.created_at ? entry.created_at.split('T')[0] : new Date().toISOString().split('T')[0]),
                    title: entry.title || '',
                    content: entry.content || '',
                    mood: entry.mood || '',
                    weather: entry.weather || '',
                    tags: entry.tags || [],
                    images: entry.images || [],
                    created_at: entry.created_at || new Date().toISOString(),
                    updated_at: entry.updated_at || new Date().toISOString()
                };
                await this.addDiaryEntry(normalizedEntry);
            }
        }

        // 导入计时记录（为桌面端记录生成id）
        if (data.timer_records && Array.isArray(data.timer_records)) {
            await this.clear('timer_records');
            for (const record of data.timer_records) {
                // 桌面端记录没有id字段，需要生成
                const normalizedRecord = {
                    id: record.id || new Date(record.timestamp).getTime().toString(),
                    mode: record.mode || 'countdown',
                    duration: record.duration || 0,
                    note: record.note || '',
                    timestamp: record.timestamp || new Date().toISOString(),
                    completed: record.completed !== undefined ? record.completed : true
                };
                await this.addTimerRecord(normalizedRecord);
            }
        }

        // 导入使用记录
        if (data.usage_records && Array.isArray(data.usage_records)) {
            await this.clear('usage_records');
            for (const record of data.usage_records) {
                await this.saveUsageRecord(record);
            }
        }

        // 导入配置
        if (data.config) {
            await this.setConfig('app_config', data.config);
        }
    }

    async clearAllData() {
        await this.clear('memos');
        await this.clear('diary');
        await this.clear('timer_records');
        await this.clear('usage_records');
        await this.clear('config');
    }
}

// 导出类
window.Storage = Storage;
