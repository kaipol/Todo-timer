/**
 * 计时器模块 - 番茄钟和正计时功能
 * 性能优化版本：使用 requestAnimationFrame、DOM 缓存、防抖
 */

class TimerModule {
    constructor() {
        this.mode = 'countdown'; // countdown | stopwatch
        this.running = false;
        this.paused = false;
        this.seconds = 25 * 60;
        this.initialSeconds = 25 * 60;
        this.stopwatchSeconds = 0;
        this.currentNote = '';
        this.storage = null;
        
        // 性能优化：使用 requestAnimationFrame 替代 setInterval
        this._rafId = null;
        this._lastTickTime = 0;
        
        // 性能优化：缓存 DOM 元素
        this._displayEl = null;
        this._statusEl = null;
        this._progressCircle = null;
        this._startBtn = null;
        this._historyEl = null;
        
        // 性能优化：防抖的显示更新
        this._throttledUpdateDisplay = null;
    }

    async init() {
        // 从全局 app 获取 storage
        this.storage = window.app?.storage;
        
        // 缓存 DOM 元素引用
        this._cacheElements();
        
        // 初始化节流的显示更新
        if (window.Performance?.rafThrottle) {
            this._throttledUpdateDisplay = window.Performance.rafThrottle(() => this._doUpdateDisplay());
        }
        
        this.bindEvents();
        await this.loadHistory();
        this.updateDisplay();
    }
    
    /**
     * 缓存 DOM 元素引用（性能优化）
     */
    _cacheElements() {
        this._displayEl = document.getElementById('timerDisplay');
        this._statusEl = document.getElementById('timerStatus');
        this._progressCircle = document.querySelector('.progress-ring-circle');
        this._startBtn = document.getElementById('startBtn');
        this._historyEl = document.getElementById('timerHistory');
    }

    bindEvents() {
        // 模式切换
        document.querySelectorAll('.mode-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                if (this.running) return;
                this.switchMode(tab.dataset.mode);
            });
        });

        // 时间设置
        const minutesInput = document.getElementById('timerMinutes');
        const secondsInput = document.getElementById('timerSeconds');
        
        if (minutesInput) {
            minutesInput.addEventListener('change', () => {
                if (!this.running) {
                    this.setCountdownTime(parseInt(minutesInput.value) || 25, parseInt(secondsInput?.value) || 0);
                }
            });
        }
        
        if (secondsInput) {
            secondsInput.addEventListener('change', () => {
                if (!this.running) {
                    this.setCountdownTime(parseInt(minutesInput?.value) || 25, parseInt(secondsInput.value) || 0);
                }
            });
        }

        // 控制按钮
        document.getElementById('startBtn')?.addEventListener('click', () => this.toggleTimer());
        document.getElementById('resetBtn')?.addEventListener('click', () => this.reset());

        // 备注输入
        document.getElementById('timerNote')?.addEventListener('input', (e) => {
            this.currentNote = e.target.value;
        });
    }

    switchMode(mode) {
        this.mode = mode;
        
        // 更新UI
        document.querySelectorAll('.mode-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.mode === mode);
        });

        // 显示/隐藏时间设置
        const timeSettings = document.getElementById('timeSettings');
        if (timeSettings) {
            timeSettings.style.display = mode === 'countdown' ? 'flex' : 'none';
        }

        // 重置显示
        if (mode === 'countdown') {
            this.seconds = this.initialSeconds;
        } else {
            this.stopwatchSeconds = 0;
        }
        this.updateDisplay();
    }

    setCountdownTime(minutes, seconds) {
        this.initialSeconds = minutes * 60 + seconds;
        this.seconds = this.initialSeconds;
        this.updateDisplay();
    }

    toggleTimer() {
        if (this.running) {
            this.pause();
        } else {
            this.start();
        }
    }

    start() {
        if (this.running) return;

        this.running = true;
        this.paused = false;

        // 更新按钮（使用缓存的元素）
        const startBtn = this._startBtn || document.getElementById('startBtn');
        if (startBtn) {
            startBtn.innerHTML = '<i class="fas fa-pause"></i>';
            startBtn.classList.add('running');
        }

        // 更新状态
        this.updateStatus(this.mode === 'countdown' ? '专注中...' : '计时中...');

        // 使用 requestAnimationFrame 替代 setInterval（性能优化）
        this._lastTickTime = performance.now();
        this._startRAFLoop();
    }
    
    /**
     * 启动 RAF 循环（性能优化）
     * 使用 requestAnimationFrame 替代 setInterval，更节能且更精确
     */
    _startRAFLoop() {
        const loop = (currentTime) => {
            if (!this.running) return;
            
            // 计算经过的时间
            const elapsed = currentTime - this._lastTickTime;
            
            // 每秒执行一次 tick
            if (elapsed >= 1000) {
                // 补偿时间偏差
                const tickCount = Math.floor(elapsed / 1000);
                for (let i = 0; i < tickCount; i++) {
                    this.tick();
                    if (!this.running) break; // tick 可能会停止计时器
                }
                this._lastTickTime = currentTime - (elapsed % 1000);
            }
            
            // 继续循环
            if (this.running) {
                this._rafId = requestAnimationFrame(loop);
            }
        };
        
        this._rafId = requestAnimationFrame(loop);
    }
    
    /**
     * 停止 RAF 循环
     */
    _stopRAFLoop() {
        if (this._rafId) {
            cancelAnimationFrame(this._rafId);
            this._rafId = null;
        }
    }

    pause() {
        this.running = false;
        this.paused = true;

        // 停止 RAF 循环
        this._stopRAFLoop();

        // 更新按钮（使用缓存的元素）
        const startBtn = this._startBtn || document.getElementById('startBtn');
        if (startBtn) {
            startBtn.innerHTML = '<i class="fas fa-play"></i>';
            startBtn.classList.remove('running');
        }

        this.updateStatus('已暂停');
    }

    reset() {
        // 保存记录
        if (this.running || this.paused) {
            this.saveRecord();
        }

        this.running = false;
        this.paused = false;

        // 停止 RAF 循环
        this._stopRAFLoop();

        // 重置时间
        if (this.mode === 'countdown') {
            this.seconds = this.initialSeconds;
        } else {
            this.stopwatchSeconds = 0;
        }

        // 更新UI（使用缓存的元素）
        const startBtn = this._startBtn || document.getElementById('startBtn');
        if (startBtn) {
            startBtn.innerHTML = '<i class="fas fa-play"></i>';
            startBtn.classList.remove('running');
        }

        this.updateDisplay();
        this.updateStatus('准备开始');
        this.updateProgress(100);
    }

    tick() {
        if (this.mode === 'countdown') {
            if (this.seconds > 0) {
                this.seconds--;
                this.updateDisplay();
                
                // 更新进度
                const progress = (this.seconds / this.initialSeconds) * 100;
                this.updateProgress(progress);
            } else {
                this.onCountdownFinished();
            }
        } else {
            this.stopwatchSeconds++;
            this.updateDisplay();
        }
    }

    onCountdownFinished() {
        this.saveRecord();
        this.playNotification();
        
        // 显示完成提示
        this.showToast('🍅 番茄完成！建议休息5分钟~');
        
        this.reset();
    }

    saveRecord() {
        let elapsed;
        let completed;

        if (this.mode === 'countdown') {
            elapsed = this.initialSeconds - this.seconds;
            completed = this.seconds === 0;
        } else {
            elapsed = this.stopwatchSeconds;
            completed = true;
        }

        if (elapsed <= 0) return;

        const record = {
            id: Date.now().toString(),
            mode: this.mode,
            duration: elapsed,
            note: this.currentNote || '',
            timestamp: new Date().toISOString(),
            completed: completed
        };

        // 保存到存储
        if (this.storage) {
            this.storage.addTimerRecord(record);
        }

        // 更新历史列表
        this.addRecordToList(record);
        
        // 触发同步
        if (window.app?.webdav) {
            window.app.webdav.markDirty();
        }
    }

    /**
     * 更新显示（使用缓存的 DOM 元素）
     */
    updateDisplay() {
        // 如果有节流版本且正在运行，使用节流版本
        if (this._throttledUpdateDisplay && this.running) {
            this._throttledUpdateDisplay();
        } else {
            this._doUpdateDisplay();
        }
    }
    
    /**
     * 实际执行显示更新（性能优化：使用缓存的 DOM 元素）
     */
    _doUpdateDisplay() {
        const display = this._displayEl || document.getElementById('timerDisplay');
        if (!display) return;

        let totalSeconds = this.mode === 'countdown' ? this.seconds : this.stopwatchSeconds;
        
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        if (hours > 0) {
            display.textContent = `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            display.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }

        // 倒计时最后10秒变红
        if (this.mode === 'countdown' && this.seconds <= 10 && this.running) {
            display.classList.add('warning');
        } else {
            display.classList.remove('warning');
        }
    }

    /**
     * 更新状态文本（使用缓存的 DOM 元素）
     */
    updateStatus(text) {
        const status = this._statusEl || document.getElementById('timerStatus');
        if (status) {
            status.textContent = text;
        }
    }

    /**
     * 更新进度环（使用缓存的 DOM 元素）
     */
    updateProgress(percent) {
        const circle = this._progressCircle || document.querySelector('.progress-ring-circle');
        if (circle) {
            const radius = circle.r.baseVal.value;
            const circumference = radius * 2 * Math.PI;
            const offset = circumference - (percent / 100) * circumference;
            circle.style.strokeDasharray = `${circumference} ${circumference}`;
            circle.style.strokeDashoffset = offset;
        }
    }
    
    /**
     * 页面隐藏时的处理（性能优化）
     * 当页面不可见时，暂停 RAF 循环以节省资源
     */
    onPageHidden() {
        if (this.running) {
            // 记录隐藏时的时间戳，用于恢复时补偿
            this._hiddenTime = performance.now();
            // 停止 RAF 循环以节省电量
            this._stopRAFLoop();
        }
    }
    
    /**
     * 页面显示时的处理（性能优化）
     * 当页面重新可见时，恢复计时并补偿隐藏期间的时间
     */
    onPageVisible() {
        if (this.running && this._hiddenTime) {
            // 计算隐藏期间经过的时间
            const hiddenDuration = performance.now() - this._hiddenTime;
            const hiddenSeconds = Math.floor(hiddenDuration / 1000);
            
            // 补偿隐藏期间的时间
            if (hiddenSeconds > 0) {
                if (this.mode === 'countdown') {
                    this.seconds = Math.max(0, this.seconds - hiddenSeconds);
                    if (this.seconds === 0) {
                        this.onCountdownFinished();
                        return;
                    }
                } else {
                    this.stopwatchSeconds += hiddenSeconds;
                }
                this.updateDisplay();
                if (this.mode === 'countdown') {
                    const progress = (this.seconds / this.initialSeconds) * 100;
                    this.updateProgress(progress);
                }
            }
            
            // 重新启动 RAF 循环
            this._lastTickTime = performance.now();
            this._startRAFLoop();
            this._hiddenTime = null;
        }
    }

    playNotification() {
        // 尝试播放声音
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2teleQAA');
            audio.play().catch(() => {});
        } catch (e) {}

        // 振动
        if ('vibrate' in navigator) {
            navigator.vibrate([200, 100, 200]);
        }
    }

    showToast(message) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    async loadHistory() {
        if (!this.storage) return;

        try {
            const allRecords = await this.storage.getTimerRecords();
            // 获取今天的记录
            const today = new Date().toISOString().split('T')[0];
            const records = allRecords.filter(r => {
                const recordDate = new Date(r.timestamp).toISOString().split('T')[0];
                return recordDate === today;
            });
            
            const list = document.getElementById('timerHistory');
            if (!list) return;

            list.innerHTML = '';
            records.slice(-10).reverse().forEach(record => {
                this.addRecordToList(record, false);
            });
        } catch (error) {
            console.error('加载计时历史失败:', error);
        }
    }

    renderHistory() {
        this.loadHistory();
    }

    render() {
        this.updateDisplay();
    }

    addRecordToList(record, prepend = true) {
        const list = document.getElementById('timerHistory');
        if (!list) return;

        const item = document.createElement('div');
        item.className = 'history-item';

        const icon = record.mode === 'countdown' ? '🍅' : '⏱';
        const time = new Date(record.timestamp);
        const timeStr = `${time.getHours().toString().padStart(2, '0')}:${time.getMinutes().toString().padStart(2, '0')}`;
        const durationStr = this.formatDuration(record.duration);

        item.innerHTML = `
            <span class="history-icon">${icon}</span>
            <span class="history-time">${timeStr}</span>
            <span class="history-duration">${durationStr}</span>
            <span class="history-note">${record.note || '无备注'}</span>
        `;

        if (prepend) {
            list.insertBefore(item, list.firstChild);
            // 限制显示数量
            while (list.children.length > 10) {
                list.removeChild(list.lastChild);
            }
        } else {
            list.appendChild(item);
        }
    }

    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }

    /**
     * 导出数据（用于同步）
     * 导出时移除移动端特有的id字段，以兼容桌面端格式
     * 桌面端格式: { mode, duration, note, timestamp, completed }
     */
    async exportData() {
        if (!this.storage) return [];
        
        try {
            const records = await this.storage.getTimerRecords();
            // 转换为桌面端兼容格式（移除id字段）
            return records.map(record => ({
                mode: record.mode,
                duration: record.duration,
                note: record.note || '',
                timestamp: record.timestamp,
                completed: record.completed !== undefined ? record.completed : true
            }));
        } catch (error) {
            console.error('导出计时记录失败:', error);
            return [];
        }
    }

    /**
     * 导入数据（用于同步）
     * 从桌面端导入时，为每条记录生成id（如果没有的话）
     * 桌面端格式: { mode, duration, note, timestamp, completed }
     * 移动端格式: { id, mode, duration, note, timestamp, completed }
     */
    async importData(records) {
        if (!this.storage || !Array.isArray(records)) return;
        
        try {
            // 清除现有记录
            await this.storage.clear('timer_records');
            
            // 导入新记录，确保每条记录都有id
            for (const record of records) {
                const normalizedRecord = {
                    // 如果没有id，基于timestamp生成一个
                    id: record.id || new Date(record.timestamp).getTime().toString(),
                    mode: record.mode || 'countdown',
                    duration: record.duration || 0,
                    note: record.note || '',
                    timestamp: record.timestamp || new Date().toISOString(),
                    completed: record.completed !== undefined ? record.completed : true
                };
                await this.storage.addTimerRecord(normalizedRecord);
            }
            
            // 刷新历史列表
            await this.loadHistory();
        } catch (error) {
            console.error('导入计时记录失败:', error);
        }
    }
}

// 导出模块
window.TimerModule = TimerModule;
