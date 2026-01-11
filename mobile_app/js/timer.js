/**
 * 计时器模块 - 番茄钟和正计时功能
 */

class TimerModule {
    constructor() {
        this.mode = 'countdown'; // countdown | stopwatch
        this.running = false;
        this.paused = false;
        this.seconds = 25 * 60;
        this.initialSeconds = 25 * 60;
        this.stopwatchSeconds = 0;
        this.interval = null;
        this.currentNote = '';
        this.storage = null;
    }

    async init() {
        // 从全局 app 获取 storage
        this.storage = window.app?.storage;
        this.bindEvents();
        await this.loadHistory();
        this.updateDisplay();
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

        // 更新按钮
        const startBtn = document.getElementById('startBtn');
        if (startBtn) {
            startBtn.innerHTML = '<i class="fas fa-pause"></i>';
            startBtn.classList.add('running');
        }

        // 更新状态
        this.updateStatus(this.mode === 'countdown' ? '专注中...' : '计时中...');

        // 开始计时
        this.interval = setInterval(() => this.tick(), 1000);
    }

    pause() {
        this.running = false;
        this.paused = true;

        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }

        // 更新按钮
        const startBtn = document.getElementById('startBtn');
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

        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }

        // 重置时间
        if (this.mode === 'countdown') {
            this.seconds = this.initialSeconds;
        } else {
            this.stopwatchSeconds = 0;
        }

        // 更新UI
        const startBtn = document.getElementById('startBtn');
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

    updateDisplay() {
        const display = document.getElementById('timerDisplay');
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

    updateStatus(text) {
        const status = document.getElementById('timerStatus');
        if (status) {
            status.textContent = text;
        }
    }

    updateProgress(percent) {
        const circle = document.querySelector('.progress-ring-circle');
        if (circle) {
            const radius = circle.r.baseVal.value;
            const circumference = radius * 2 * Math.PI;
            const offset = circumference - (percent / 100) * circumference;
            circle.style.strokeDasharray = `${circumference} ${circumference}`;
            circle.style.strokeDashoffset = offset;
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
}

// 导出模块
window.TimerModule = TimerModule;
