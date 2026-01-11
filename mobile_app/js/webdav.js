/**
 * WebDAV同步模块 - 与电脑端数据实时同步
 */

class WebDAVSync {
    constructor() {
        this.config = this.loadConfig();
    }

    // 加载WebDAV配置
    loadConfig() {
        const defaultConfig = {
            enabled: false,
            serverUrl: '',
            username: '',
            password: '',
            remotePath: '/TimeTracker/',
            lastSync: null,
            lastSyncStatus: null
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
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

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
            const headers = this.getAuthHeaders();

            // 尝试创建目录
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

    // 上传备份数据
    async uploadBackup(data) {
        if (!this.isConfigured()) {
            throw new Error('WebDAV未配置');
        }

        await this.ensureRemoteDir();

        const headers = this.getAuthHeaders();

        // 上传各类数据文件
        const files = {
            'memos.json': { memos: data.memos || [] },
            'diary.json': { entries: data.diary || [] },
            'timer_records.json': { records: data.timer_records || [] },
            'config.json': { config: data.config || {} }
        };

        for (const [filename, content] of Object.entries(files)) {
            const url = this.getRemoteUrl(filename);

            const response = await fetch(url, {
                method: 'PUT',
                headers,
                body: JSON.stringify(content, null, 2)
            });

            if (!response.ok && response.status !== 201 && response.status !== 204) {
                throw new Error(`上传 ${filename} 失败: ${response.status}`);
            }
        }

        return true;
    }

    // 下载备份数据
    async downloadBackup() {
        if (!this.isConfigured()) {
            throw new Error('WebDAV未配置');
        }

        const headers = this.getAuthHeaders();
        const data = {
            memos: [],
            diary: [],
            timer_records: [],
            config: {}
        };

        const files = [
            { name: 'memos.json', key: 'memos', extract: d => d.memos || [] },
            { name: 'diary.json', key: 'diary', extract: d => d.entries || [] },
            { name: 'timer_records.json', key: 'timer_records', extract: d => d.records || [] },
            { name: 'config.json', key: 'config', extract: d => d.config || {} }
        ];

        for (const file of files) {
            try {
                const url = this.getRemoteUrl(file.name);
                const response = await fetch(url, {
                    method: 'GET',
                    headers
                });

                if (response.ok) {
                    const content = await response.json();
                    data[file.key] = file.extract(content);
                }
            } catch (error) {
                console.warn(`下载 ${file.name} 失败:`, error);
            }
        }

        return data;
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
