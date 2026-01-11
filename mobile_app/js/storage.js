/**
 * 数据存储模块 - 与电脑端数据格式兼容
 */

class Storage {
    constructor() {
        this.DB_NAME = 'TimeTrackerDB';
        this.DB_VERSION = 1;
        this.db = null;
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

    // ==================== 通用CRUD操作 ====================
    
    async add(storeName, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.add(data);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async put(storeName, data) {
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

    async delete(storeName, key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(key);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async clear(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
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
    
    async exportAllData() {
        const memos = await this.getMemos();
        const diary = await this.getAllDiaryEntries();
        const timerRecords = await this.getTimerRecords();
        const usageRecords = await this.getUsageRecords();
        const config = await this.getConfig();

        return {
            version: '1.0',
            exportTime: new Date().toISOString(),
            data: {
                memos,
                diary,
                timer_records: timerRecords,
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

        // 导入日记
        if (data.diary && Array.isArray(data.diary)) {
            await this.clear('diary');
            for (const entry of data.diary) {
                await this.addDiaryEntry(entry);
            }
        }

        // 导入计时记录
        if (data.timer_records && Array.isArray(data.timer_records)) {
            await this.clear('timer_records');
            for (const record of data.timer_records) {
                await this.addTimerRecord(record);
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
