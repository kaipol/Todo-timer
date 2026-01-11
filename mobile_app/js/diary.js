/**
 * 日记模块 - 管理日记功能
 * 与桌面端 diary_storage.py 数据格式兼容
 */

class DiaryModule {
    constructor(storage) {
        this.storage = storage;
        this.entries = [];
        this.currentEntry = null;
        this.currentDate = new Date();
        this.isEditing = false;
        
        // 心情选项
        this.moodOptions = [
            { value: 'happy', emoji: '😊', label: '开心' },
            { value: 'calm', emoji: '😌', label: '平静' },
            { value: 'sad', emoji: '😢', label: '难过' },
            { value: 'angry', emoji: '😠', label: '生气' },
            { value: 'anxious', emoji: '😰', label: '焦虑' },
            { value: 'excited', emoji: '🤩', label: '兴奋' },
            { value: 'tired', emoji: '😴', label: '疲惫' },
            { value: 'confused', emoji: '😕', label: '困惑' }
        ];
        
        // 天气选项
        this.weatherOptions = [
            { value: 'sunny', emoji: '☀️', label: '晴天' },
            { value: 'cloudy', emoji: '☁️', label: '多云' },
            { value: 'rainy', emoji: '🌧️', label: '雨天' },
            { value: 'snowy', emoji: '❄️', label: '雪天' },
            { value: 'windy', emoji: '💨', label: '大风' },
            { value: 'foggy', emoji: '🌫️', label: '雾天' },
            { value: 'stormy', emoji: '⛈️', label: '暴风雨' }
        ];
    }
    
    /**
     * 初始化日记模块
     */
    async init() {
        await this.loadEntries();
        this.renderCalendar();
        this.renderEntryList();
        this.bindEvents();
        this.loadTodayEntry();
    }
    
    /**
     * 加载所有日记条目
     */
    async loadEntries() {
        try {
            this.entries = await this.storage.getAllDiaryEntries();
            // 按日期排序，最新的在前
            this.entries.sort((a, b) => new Date(b.date) - new Date(a.date));
        } catch (error) {
            console.error('加载日记失败:', error);
            this.entries = [];
        }
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 新建日记按钮
        const newBtn = document.getElementById('new-diary-btn');
        if (newBtn) {
            newBtn.addEventListener('click', () => this.showEditor());
        }
        
        // 保存按钮
        const saveBtn = document.getElementById('save-diary-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveEntry());
        }
        
        // 取消按钮
        const cancelBtn = document.getElementById('cancel-diary-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideEditor());
        }
        
        // 删除按钮
        const deleteBtn = document.getElementById('delete-diary-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.deleteCurrentEntry());
        }
        
        // 月份导航
        const prevMonth = document.getElementById('prev-month');
        const nextMonth = document.getElementById('next-month');
        if (prevMonth) {
            prevMonth.addEventListener('click', () => this.navigateMonth(-1));
        }
        if (nextMonth) {
            nextMonth.addEventListener('click', () => this.navigateMonth(1));
        }
        
        // 心情选择
        this.renderMoodSelector();
        
        // 天气选择
        this.renderWeatherSelector();
    }
    
    /**
     * 渲染心情选择器
     */
    renderMoodSelector() {
        const container = document.getElementById('mood-selector');
        if (!container) return;
        
        container.innerHTML = this.moodOptions.map(mood => `
            <button type="button" class="mood-option" data-mood="${mood.value}" title="${mood.label}">
                ${mood.emoji}
            </button>
        `).join('');
        
        container.querySelectorAll('.mood-option').forEach(btn => {
            btn.addEventListener('click', (e) => {
                container.querySelectorAll('.mood-option').forEach(b => b.classList.remove('selected'));
                e.target.classList.add('selected');
            });
        });
    }
    
    /**
     * 渲染天气选择器
     */
    renderWeatherSelector() {
        const container = document.getElementById('weather-selector');
        if (!container) return;
        
        container.innerHTML = this.weatherOptions.map(weather => `
            <button type="button" class="weather-option" data-weather="${weather.value}" title="${weather.label}">
                ${weather.emoji}
            </button>
        `).join('');
        
        container.querySelectorAll('.weather-option').forEach(btn => {
            btn.addEventListener('click', (e) => {
                container.querySelectorAll('.weather-option').forEach(b => b.classList.remove('selected'));
                e.target.classList.add('selected');
            });
        });
    }
    
    /**
     * 渲染日历视图
     */
    renderCalendar() {
        const container = document.getElementById('diary-calendar');
        if (!container) return;
        
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        
        // 更新月份标题
        const monthTitle = document.getElementById('current-month');
        if (monthTitle) {
            monthTitle.textContent = `${year}年${month + 1}月`;
        }
        
        // 获取当月第一天和最后一天
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        
        // 获取当月第一天是星期几
        const startDayOfWeek = firstDay.getDay();
        
        // 获取有日记的日期
        const datesWithEntries = new Set(
            this.entries
                .filter(e => {
                    const d = new Date(e.date);
                    return d.getFullYear() === year && d.getMonth() === month;
                })
                .map(e => new Date(e.date).getDate())
        );
        
        // 生成日历HTML
        let html = `
            <div class="calendar-header">
                <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
            </div>
            <div class="calendar-body">
        `;
        
        // 填充空白天
        for (let i = 0; i < startDayOfWeek; i++) {
            html += '<span class="calendar-day empty"></span>';
        }
        
        // 填充日期
        const today = new Date();
        for (let day = 1; day <= lastDay.getDate(); day++) {
            const isToday = today.getFullYear() === year && 
                           today.getMonth() === month && 
                           today.getDate() === day;
            const hasEntry = datesWithEntries.has(day);
            
            let classes = 'calendar-day';
            if (isToday) classes += ' today';
            if (hasEntry) classes += ' has-entry';
            
            html += `<span class="${classes}" data-date="${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}">${day}</span>`;
        }
        
        html += '</div>';
        container.innerHTML = html;
        
        // 绑定日期点击事件
        container.querySelectorAll('.calendar-day:not(.empty)').forEach(dayEl => {
            dayEl.addEventListener('click', (e) => {
                const date = e.target.dataset.date;
                this.loadEntryByDate(date);
            });
        });
    }
    
    /**
     * 导航月份
     */
    navigateMonth(delta) {
        this.currentDate.setMonth(this.currentDate.getMonth() + delta);
        this.renderCalendar();
    }
    
    /**
     * 渲染日记列表
     */
    renderEntryList() {
        const container = document.getElementById('diary-list');
        if (!container) return;
        
        if (this.entries.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">📔</span>
                    <p>还没有日记</p>
                    <p class="empty-hint">点击"写日记"开始记录</p>
                </div>
            `;
            return;
        }
        
        // 按月份分组
        const groupedEntries = {};
        this.entries.forEach(entry => {
            const date = new Date(entry.date);
            const key = `${date.getFullYear()}年${date.getMonth() + 1}月`;
            if (!groupedEntries[key]) {
                groupedEntries[key] = [];
            }
            groupedEntries[key].push(entry);
        });
        
        let html = '';
        for (const [month, entries] of Object.entries(groupedEntries)) {
            html += `<div class="diary-month-group">
                <h3 class="month-title">${month}</h3>
                <div class="diary-entries">`;
            
            entries.forEach(entry => {
                const date = new Date(entry.date);
                const mood = this.moodOptions.find(m => m.value === entry.mood);
                const weather = this.weatherOptions.find(w => w.value === entry.weather);
                
                // 获取内容预览
                const preview = this.getContentPreview(entry.content, 50);
                
                html += `
                    <div class="diary-entry-item" data-id="${entry.id}">
                        <div class="entry-date">
                            <span class="day">${date.getDate()}</span>
                            <span class="weekday">${this.getWeekdayName(date.getDay())}</span>
                        </div>
                        <div class="entry-content">
                            <div class="entry-meta">
                                ${mood ? `<span class="mood">${mood.emoji}</span>` : ''}
                                ${weather ? `<span class="weather">${weather.emoji}</span>` : ''}
                            </div>
                            <p class="entry-preview">${preview || '(空白日记)'}</p>
                        </div>
                    </div>
                `;
            });
            
            html += '</div></div>';
        }
        
        container.innerHTML = html;
        
        // 绑定点击事件
        container.querySelectorAll('.diary-entry-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = item.dataset.id;
                this.loadEntry(id);
            });
        });
    }
    
    /**
     * 获取星期名称
     */
    getWeekdayName(day) {
        const names = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        return names[day];
    }
    
    /**
     * 获取内容预览
     */
    getContentPreview(content, maxLength) {
        if (!content) return '';
        // 移除Markdown标记
        const text = content
            .replace(/#{1,6}\s/g, '')
            .replace(/\*\*|__/g, '')
            .replace(/\*|_/g, '')
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
            .replace(/`{1,3}[^`]*`{1,3}/g, '')
            .replace(/\n/g, ' ')
            .trim();
        
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    /**
     * 加载今天的日记
     */
    async loadTodayEntry() {
        const today = new Date().toISOString().split('T')[0];
        await this.loadEntryByDate(today);
    }
    
    /**
     * 按日期加载日记
     */
    async loadEntryByDate(dateStr) {
        const entry = this.entries.find(e => e.date === dateStr);
        if (entry) {
            this.showEntry(entry);
        } else {
            // 没有该日期的日记，显示新建界面
            this.showEditor(dateStr);
        }
    }
    
    /**
     * 按ID加载日记
     */
    async loadEntry(id) {
        const entry = this.entries.find(e => e.id === id);
        if (entry) {
            this.showEntry(entry);
        }
    }
    
    /**
     * 显示日记详情
     */
    showEntry(entry) {
        this.currentEntry = entry;
        
        const viewContainer = document.getElementById('diary-view');
        const editorContainer = document.getElementById('diary-editor');
        const listContainer = document.getElementById('diary-list-container');
        
        if (viewContainer) {
            const date = new Date(entry.date);
            const mood = this.moodOptions.find(m => m.value === entry.mood);
            const weather = this.weatherOptions.find(w => w.value === entry.weather);
            
            viewContainer.innerHTML = `
                <div class="diary-view-header">
                    <button class="back-btn" id="back-to-list">
                        <span class="icon">←</span>
                    </button>
                    <h2>${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日</h2>
                    <button class="edit-btn" id="edit-diary-btn">
                        <span class="icon">✏️</span>
                    </button>
                </div>
                <div class="diary-view-meta">
                    ${mood ? `<span class="mood-tag">${mood.emoji} ${mood.label}</span>` : ''}
                    ${weather ? `<span class="weather-tag">${weather.emoji} ${weather.label}</span>` : ''}
                </div>
                <div class="diary-view-content markdown-body">
                    ${this.renderMarkdown(entry.content)}
                </div>
            `;
            
            viewContainer.style.display = 'block';
            
            // 绑定返回按钮
            document.getElementById('back-to-list').addEventListener('click', () => {
                viewContainer.style.display = 'none';
                listContainer.style.display = 'block';
            });
            
            // 绑定编辑按钮
            document.getElementById('edit-diary-btn').addEventListener('click', () => {
                this.showEditor(entry.date, entry);
            });
        }
        
        if (editorContainer) editorContainer.style.display = 'none';
        if (listContainer) listContainer.style.display = 'none';
    }
    
    /**
     * 显示编辑器
     */
    showEditor(dateStr = null, entry = null) {
        this.isEditing = !!entry;
        this.currentEntry = entry;
        
        const viewContainer = document.getElementById('diary-view');
        const editorContainer = document.getElementById('diary-editor');
        const listContainer = document.getElementById('diary-list-container');
        
        if (viewContainer) viewContainer.style.display = 'none';
        if (listContainer) listContainer.style.display = 'none';
        if (editorContainer) editorContainer.style.display = 'block';
        
        // 设置日期
        const dateInput = document.getElementById('diary-date');
        if (dateInput) {
            dateInput.value = dateStr || entry?.date || new Date().toISOString().split('T')[0];
        }
        
        // 设置内容
        const contentInput = document.getElementById('diary-content');
        if (contentInput) {
            contentInput.value = entry?.content || '';
        }
        
        // 设置心情
        const moodSelector = document.getElementById('mood-selector');
        if (moodSelector) {
            moodSelector.querySelectorAll('.mood-option').forEach(btn => {
                btn.classList.remove('selected');
                if (entry?.mood && btn.dataset.mood === entry.mood) {
                    btn.classList.add('selected');
                }
            });
        }
        
        // 设置天气
        const weatherSelector = document.getElementById('weather-selector');
        if (weatherSelector) {
            weatherSelector.querySelectorAll('.weather-option').forEach(btn => {
                btn.classList.remove('selected');
                if (entry?.weather && btn.dataset.weather === entry.weather) {
                    btn.classList.add('selected');
                }
            });
        }
        
        // 显示/隐藏删除按钮
        const deleteBtn = document.getElementById('delete-diary-btn');
        if (deleteBtn) {
            deleteBtn.style.display = this.isEditing ? 'block' : 'none';
        }
        
        // 聚焦内容输入框
        if (contentInput) {
            contentInput.focus();
        }
    }
    
    /**
     * 隐藏编辑器
     */
    hideEditor() {
        const editorContainer = document.getElementById('diary-editor');
        const listContainer = document.getElementById('diary-list-container');
        
        if (editorContainer) editorContainer.style.display = 'none';
        if (listContainer) listContainer.style.display = 'block';
        
        this.currentEntry = null;
        this.isEditing = false;
    }
    
    /**
     * 保存日记
     */
    async saveEntry() {
        const dateInput = document.getElementById('diary-date');
        const contentInput = document.getElementById('diary-content');
        const moodSelector = document.getElementById('mood-selector');
        const weatherSelector = document.getElementById('weather-selector');
        
        const date = dateInput?.value;
        const content = contentInput?.value || '';
        const mood = moodSelector?.querySelector('.mood-option.selected')?.dataset.mood || '';
        const weather = weatherSelector?.querySelector('.weather-option.selected')?.dataset.weather || '';
        
        if (!date) {
            this.showToast('请选择日期', 'error');
            return;
        }
        
        try {
            const now = new Date().toISOString();
            
            if (this.isEditing && this.currentEntry) {
                // 更新现有日记
                const updatedEntry = {
                    ...this.currentEntry,
                    date,
                    content,
                    mood,
                    weather,
                    updated_at: now
                };
                
                await this.storage.updateDiaryEntry(updatedEntry);
                
                // 更新本地列表
                const index = this.entries.findIndex(e => e.id === this.currentEntry.id);
                if (index !== -1) {
                    this.entries[index] = updatedEntry;
                }
                
                this.showToast('日记已更新');
            } else {
                // 检查是否已有该日期的日记
                const existingEntry = this.entries.find(e => e.date === date);
                if (existingEntry) {
                    // 更新现有日记
                    const updatedEntry = {
                        ...existingEntry,
                        content,
                        mood,
                        weather,
                        updated_at: now
                    };
                    
                    await this.storage.updateDiaryEntry(updatedEntry);
                    
                    const index = this.entries.findIndex(e => e.id === existingEntry.id);
                    if (index !== -1) {
                        this.entries[index] = updatedEntry;
                    }
                    
                    this.showToast('日记已更新');
                } else {
                    // 创建新日记
                    const newEntry = {
                        id: this.generateId(),
                        date,
                        content,
                        mood,
                        weather,
                        created_at: now,
                        updated_at: now
                    };
                    
                    await this.storage.addDiaryEntry(newEntry);
                    this.entries.unshift(newEntry);
                    
                    this.showToast('日记已保存');
                }
            }
            
            // 重新排序
            this.entries.sort((a, b) => new Date(b.date) - new Date(a.date));
            
            // 刷新界面
            this.renderCalendar();
            this.renderEntryList();
            this.hideEditor();
            
            // 触发同步
            if (window.app?.webdav) {
                window.app.webdav.markDirty();
            }
            
        } catch (error) {
            console.error('保存日记失败:', error);
            this.showToast('保存失败: ' + error.message, 'error');
        }
    }
    
    /**
     * 删除当前日记
     */
    async deleteCurrentEntry() {
        if (!this.currentEntry) return;
        
        if (!confirm('确定要删除这篇日记吗？')) {
            return;
        }
        
        try {
            await this.storage.deleteDiaryEntry(this.currentEntry.id);
            
            // 从本地列表移除
            this.entries = this.entries.filter(e => e.id !== this.currentEntry.id);
            
            this.showToast('日记已删除');
            
            // 刷新界面
            this.renderCalendar();
            this.renderEntryList();
            this.hideEditor();
            
            // 触发同步
            if (window.app?.webdav) {
                window.app.webdav.markDirty();
            }
            
        } catch (error) {
            console.error('删除日记失败:', error);
            this.showToast('删除失败: ' + error.message, 'error');
        }
    }
    
    /**
     * 简单的Markdown渲染
     */
    renderMarkdown(text) {
        if (!text) return '<p class="empty-content">暂无内容</p>';
        
        return text
            // 转义HTML
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            // 标题
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            // 粗体
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/__(.+?)__/g, '<strong>$1</strong>')
            // 斜体
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/_(.+?)_/g, '<em>$1</em>')
            // 代码
            .replace(/`(.+?)`/g, '<code>$1</code>')
            // 链接
            .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>')
            // 列表
            .replace(/^\- (.+)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            // 换行
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            // 包装段落
            .replace(/^(.+)$/gm, (match) => {
                if (match.startsWith('<h') || match.startsWith('<ul') || match.startsWith('<li')) {
                    return match;
                }
                return `<p>${match}</p>`;
            });
    }
    
    /**
     * 生成唯一ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
    
    /**
     * 显示提示消息
     */
    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }
    
    /**
     * 导出日记数据（用于同步）
     */
    exportData() {
        return this.entries.map(entry => ({
            id: entry.id,
            date: entry.date,
            content: entry.content,
            mood: entry.mood,
            weather: entry.weather,
            created_at: entry.created_at,
            updated_at: entry.updated_at
        }));
    }
    
    /**
     * 导入日记数据（用于同步）
     */
    async importData(entries) {
        for (const entry of entries) {
            const existing = this.entries.find(e => e.id === entry.id);
            if (existing) {
                // 比较更新时间，保留较新的
                if (new Date(entry.updated_at) > new Date(existing.updated_at)) {
                    await this.storage.updateDiaryEntry(entry);
                    const index = this.entries.findIndex(e => e.id === entry.id);
                    if (index !== -1) {
                        this.entries[index] = entry;
                    }
                }
            } else {
                await this.storage.addDiaryEntry(entry);
                this.entries.push(entry);
            }
        }
        
        // 重新排序
        this.entries.sort((a, b) => new Date(b.date) - new Date(a.date));
        
        // 刷新界面
        this.renderCalendar();
        this.renderEntryList();
    }
}

// 导出模块
window.DiaryModule = DiaryModule;
