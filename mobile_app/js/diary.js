/**
 * 日记模块 - 管理日记功能
 * 与桌面端 diary_storage.py 数据格式兼容
 * 性能优化版本：使用事件委托、DOM 缓存、防抖渲染
 */

class DiaryModule {
    constructor(storage) {
        this.storage = storage;
        this.entries = [];
        this.currentEntry = null;
        this.currentDate = new Date();
        this.isEditing = false;
        
        // 性能优化：缓存 DOM 元素
        this._listContainer = null;
        this._editorModal = null;
        this._viewContainer = null;
        this._moodSelector = null;
        this._weatherSelector = null;
        
        // 性能优化：事件委托器
        this._listDelegator = null;
        this._moodDelegator = null;
        this._weatherDelegator = null;
        
        // 性能优化：防抖渲染
        this._debouncedRender = window.Performance?.debounce
            ? window.Performance.debounce(() => this._doRenderEntryList(), 100)
            : () => this._doRenderEntryList();
        
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
        this.renderEntryList();
        this.bindEvents();
        this.bindMarkdownToolbar();
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
        // 新建日记按钮 - 匹配 index.html 中的 newDiaryBtn
        const newBtn = document.getElementById('newDiaryBtn');
        if (newBtn) {
            newBtn.addEventListener('click', () => this.showEditor());
        }
        
        // 保存按钮 - 匹配 index.html 中的 saveDiaryBtn
        const saveBtn = document.getElementById('saveDiaryBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('点击保存按钮');
                this.saveEntry();
            });
        }
        
        // 关闭按钮 - 匹配 index.html 中的 diaryBackBtn (dialog-close)
        const closeBtn = document.getElementById('diaryBackBtn');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.hideEditor();
            });
        }
        
        // 取消按钮 - 匹配 index.html 中的 diaryCancelBtn
        const cancelBtn = document.getElementById('diaryCancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.hideEditor();
            });
        }
        
        // 删除按钮
        const deleteBtn = document.getElementById('deleteDiaryBtn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.deleteCurrentEntry());
        }
        
        // 模态框背景点击关闭 (dialog-overlay)
        const editorModal = document.getElementById('diaryEditorModal');
        if (editorModal) {
            editorModal.addEventListener('click', (e) => {
                // 只有点击模态框背景（不是内容区域）时才关闭
                if (e.target === editorModal) {
                    this.hideEditor();
                }
            });
            
            // 阻止对话框内容区域的点击事件冒泡
            const dialog = editorModal.querySelector('.dialog');
            if (dialog) {
                dialog.addEventListener('click', (e) => {
                    e.stopPropagation();
                });
            }
        }
        
        // 心情选择
        this.renderMoodSelector();
        
        // 天气选择
        this.renderWeatherSelector();
    }
    
    /**
     * 绑定富文本工具栏事件
     */
    bindMarkdownToolbar() {
        const toolbar = document.getElementById('wysiwygToolbar');
        const editor = document.getElementById('diaryContent');
        
        if (!toolbar || !editor) return;
        
        // 阻止工具栏按钮的 mousedown 事件，防止编辑器失去焦点
        toolbar.addEventListener('mousedown', (e) => {
            e.preventDefault();
        });
        
        // 阻止 touchstart 事件，防止移动端编辑器失去焦点
        toolbar.addEventListener('touchstart', (e) => {
            // 阻止默认行为以防止焦点丢失
            if (e.target.closest('.wysiwyg-btn')) {
                e.preventDefault();
                e.stopPropagation();
                
                // 在 touchstart 中直接执行命令，因为 preventDefault 会阻止 click 事件
                const btn = e.target.closest('.wysiwyg-btn');
                if (!btn) return;
                
                const command = btn.dataset.command;
                const value = btn.dataset.value || null;
                
                this.executeWysiwygCommand(command, value, editor);
            }
        }, { passive: false });
        
        // 工具栏按钮点击事件 (用于桌面端)
        toolbar.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const btn = e.target.closest('.wysiwyg-btn');
            if (!btn) return;
            
            const command = btn.dataset.command;
            const value = btn.dataset.value || null;
            
            this.executeWysiwygCommand(command, value, editor);
        });
        
        // 键盘快捷键
        editor.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key.toLowerCase()) {
                    case 'b':
                        e.preventDefault();
                        this.executeWysiwygCommand('bold', null, editor);
                        break;
                    case 'i':
                        e.preventDefault();
                        this.executeWysiwygCommand('italic', null, editor);
                        break;
                    case 'u':
                        e.preventDefault();
                        this.executeWysiwygCommand('underline', null, editor);
                        break;
                }
            }
        });
    }
    
    /**
     * 执行 WYSIWYG 命令
     */
    executeWysiwygCommand(command, value, editor) {
        // 保存当前选区（移动端点击按钮可能导致选区丢失）
        const selection = window.getSelection();
        let savedRange = null;
        
        if (selection && selection.rangeCount > 0) {
            savedRange = selection.getRangeAt(0).cloneRange();
        }
        
        // 确保编辑器获得焦点
        editor.focus();
        
        // 恢复选区
        if (savedRange) {
            selection.removeAllRanges();
            selection.addRange(savedRange);
        }
        
        // 如果没有选区或选区不在编辑器内，将光标放到编辑器末尾
        if (!selection || selection.rangeCount === 0 || !editor.contains(selection.anchorNode)) {
            const range = document.createRange();
            range.selectNodeContents(editor);
            range.collapse(false); // 折叠到末尾
            selection.removeAllRanges();
            selection.addRange(range);
        }
        
        // 对于特殊命令，需要额外处理
        if (command === 'formatBlock') {
            // 检查当前选区是否已在该标题格式
            const sel = window.getSelection();
            if (sel && sel.rangeCount > 0) {
                const range = sel.getRangeAt(0);
                const startNode = range.startContainer;
                const element = startNode.nodeType === 1 ? startNode : startNode.parentElement;
                const currentBlock = element ? element.closest(value.toUpperCase()) : null;
                
                if (currentBlock && currentBlock.tagName === value.toUpperCase()) {
                    // 已经是该格式，转换为普通段落
                    document.execCommand('formatBlock', false, 'P');
                } else {
                    // 应用新格式
                    document.execCommand('formatBlock', false, value);
                }
            } else {
                // 没有选区时，直接应用格式
                document.execCommand('formatBlock', false, value);
            }
        } else if (command === 'createLink') {
            const url = prompt('请输入链接地址:', 'https://');
            if (url) {
                document.execCommand('createLink', false, url);
            }
        } else if (command === 'insertImage') {
            const url = prompt('请输入图片地址:');
            if (url) {
                document.execCommand('insertImage', false, url);
            }
        } else {
            // 标准命令
            document.execCommand(command, false, value);
        }
        
        // 触发内容更新事件
        this.updateEditorContent();
    }
    
    /**
     * 更新编辑器内容并触发预览更新
     */
    updateEditorContent() {
        // 内容已通过 execCommand 更新，无需额外处理
        // 但可以在这里添加实时预览逻辑
    }
    
    /**
     * 在行首插入文本
     */
    insertAtLineStart(beforeText, selectedText, prefix) {
        // 找到当前行的开始位置
        const lastNewline = beforeText.lastIndexOf('\n');
        const lineStart = lastNewline + 1;
        const beforeLine = beforeText.substring(0, lineStart);
        const currentLineStart = beforeText.substring(lineStart);
        
        // 检查是否已经有该前缀
        if (currentLineStart.startsWith(prefix)) {
            // 移除前缀
            return {
                fullText: beforeLine + currentLineStart.substring(prefix.length) + selectedText,
                cursorPos: beforeText.length - prefix.length + selectedText.length
            };
        } else {
            // 添加前缀
            return {
                fullText: beforeLine + prefix + currentLineStart + selectedText,
                cursorPos: beforeText.length + prefix.length + selectedText.length
            };
        }
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
     * 渲染日记列表（使用防抖优化）
     */
    renderEntryList() {
        // 使用防抖渲染，避免频繁更新
        this._debouncedRender();
    }
    
    /**
     * 设置列表事件委托（只需设置一次）
     */
    _setupListEventDelegation() {
        if (!this._listContainer || this._listDelegator) return;
        
        // 使用 EventDelegator 进行事件委托
        if (window.Performance?.EventDelegator) {
            this._listDelegator = new window.Performance.EventDelegator(this._listContainer);
            
            // 卡片点击事件（查看详情）
            this._listDelegator.on('click', '.diary-entry-card', (e, target) => {
                // 如果点击的是按钮，不触发卡片点击
                if (e.target.closest('.entry-action-btn')) return;
                const id = target.dataset.id;
                this.loadEntry(id);
            });
            
            // 编辑按钮事件
            this._listDelegator.on('click', '.edit-btn', (e, target) => {
                e.stopPropagation();
                const id = target.dataset.id;
                const entry = this.entries.find(ent => ent.id === id);
                if (entry) {
                    this.showEditor(entry.date, entry);
                }
            });
            
            // 删除按钮事件
            this._listDelegator.on('click', '.delete-btn', (e, target) => {
                e.stopPropagation();
                const id = target.dataset.id;
                this.deleteEntry(id);
            });
        }
    }
    
    /**
     * 实际执行渲染的方法
     */
    _doRenderEntryList() {
        // 缓存 DOM 元素
        if (!this._listContainer) {
            this._listContainer = document.getElementById('diaryList');
        }
        
        const container = this._listContainer;
        if (!container) return;
        
        // 设置事件委托（只需一次）
        this._setupListEventDelegation();
        
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
        
        // 使用 DocumentFragment 批量构建 DOM
        const fragment = document.createDocumentFragment();
        const tempDiv = document.createElement('div');
        
        let html = '';
        for (const [month, entries] of Object.entries(groupedEntries)) {
            html += `<div class="diary-month-group">
                <h3 class="month-title">${month}</h3>
                <div class="diary-entries">`;
            
            entries.forEach(entry => {
                const date = new Date(entry.date);
                const mood = this.moodOptions.find(m => m.value === entry.mood);
                const weather = this.weatherOptions.find(w => w.value === entry.weather);
                
                // 获取标题（如果有）
                const title = entry.title || '';
                // 获取内容预览
                const preview = this.getContentPreview(entry.content, 80);
                // 格式化日期显示
                const dateStr = `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 ${this.getWeekdayName(date.getDay())}`;
                
                html += `
                    <div class="diary-entry-card" data-id="${entry.id}">
                        <div class="entry-header">
                            <span class="entry-date-small">${dateStr}</span>
                            <div class="entry-icons">
                                ${mood ? `<span class="mood-icon">${mood.emoji}</span>` : ''}
                                ${weather ? `<span class="weather-icon">${weather.emoji}</span>` : ''}
                            </div>
                        </div>
                        <h4 class="entry-title">${title || '无标题'}</h4>
                        <p class="entry-preview-text">${preview || '(空白日记)'}</p>
                        <div class="entry-actions">
                            <button class="entry-action-btn edit-btn" data-id="${entry.id}" title="编辑">
                                <span>✏️</span> 编辑
                            </button>
                            <button class="entry-action-btn delete-btn" data-id="${entry.id}" title="删除">
                                <span>🗑️</span> 删除
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div></div>';
        }
        
        // 使用 requestAnimationFrame 优化 DOM 更新
        if (window.requestAnimationFrame) {
            requestAnimationFrame(() => {
                container.innerHTML = html;
            });
        } else {
            container.innerHTML = html;
        }
        
        // 事件委托已在 _setupListEventDelegation 中设置，无需重复绑定
    }
    
    /**
     * 删除指定日记
     */
    async deleteEntry(id) {
        const entry = this.entries.find(e => e.id === id);
        if (!entry) return;
        
        if (!confirm('确定要删除这篇日记吗？')) {
            return;
        }
        
        try {
            await this.storage.deleteDiaryEntry(id);
            
            // 从本地列表移除
            this.entries = this.entries.filter(e => e.id !== id);
            
            this.showToast('日记已删除');
            
            // 刷新界面
            this.renderEntryList();
            
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
     * @param {string} dateStr - 日期字符串
     * @param {boolean} autoCreate - 是否在没有日记时自动打开编辑器，默认为 false
     */
    async loadEntryByDate(dateStr, autoCreate = false) {
        const entry = this.entries.find(e => e.date === dateStr);
        if (entry) {
            this.showEntry(entry);
        } else if (autoCreate) {
            // 只有在明确要求时才打开编辑器
            this.showEditor(dateStr);
        }
        // 如果没有日记且不自动创建，则什么都不做，保持在列表页面
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
        
        // 匹配 index.html 中的ID
        const editorModal = document.getElementById('diaryEditorModal');
        const diaryContainer = document.querySelector('.diary-container');
        
        // 显示编辑器模态框
        if (editorModal) editorModal.style.display = 'flex';
        
        // 设置标题
        const titleInput = document.getElementById('diaryTitle');
        if (titleInput) {
            titleInput.value = entry?.title || '';
        }
        
        // 设置内容 - 匹配 index.html 中的 diaryContent (contenteditable div)
        const contentDiv = document.getElementById('diaryContent');
        if (contentDiv) {
            // 对于 contenteditable div，使用 innerHTML 而不是 value
            contentDiv.innerHTML = entry?.content || '';
        }
        
        // 设置心情 - 匹配 index.html 中的 diaryMood
        const moodSelect = document.getElementById('diaryMood');
        if (moodSelect && entry?.mood) {
            moodSelect.value = entry.mood;
        }
        
        // 设置天气 - 匹配 index.html 中的 diaryWeather
        const weatherInput = document.getElementById('diaryWeather');
        if (weatherInput) {
            weatherInput.value = entry?.weather || '';
        }
        
        // 保存当前日期用于保存时使用
        this.currentEditDate = dateStr || entry?.date || new Date().toISOString().split('T')[0];
        
        // 聚焦内容输入框
        if (contentDiv) {
            contentDiv.focus();
        }
    }
    
    /**
     * 隐藏编辑器
     */
    hideEditor() {
        // 匹配 index.html 中的ID
        const editorModal = document.getElementById('diaryEditorModal');
        
        if (editorModal) editorModal.style.display = 'none';
        
        this.currentEntry = null;
        this.isEditing = false;
        this.currentEditDate = null;
    }
    
    /**
     * 保存日记
     */
    async saveEntry() {
        console.log('开始保存日记...');
        // 匹配 index.html 中的ID
        const titleInput = document.getElementById('diaryTitle');
        const contentDiv = document.getElementById('diaryContent');
        const moodSelect = document.getElementById('diaryMood');
        const weatherInput = document.getElementById('diaryWeather');
        
        if (!contentDiv) {
            console.error('找不到日记内容编辑框');
            this.showToast('系统错误：找不到编辑框', 'error');
            return;
        }

        // 使用 showEditor 中保存的日期
        const date = this.currentEditDate || new Date().toISOString().split('T')[0];
        const title = titleInput?.value || '';
        // 对于 contenteditable div，使用 innerHTML 而不是 value
        const content = contentDiv.innerHTML || '';
        const mood = moodSelect?.value || '';
        const weather = weatherInput?.value || '';
        
        console.log('日记内容长度:', content.length);

        // 检查内容是否为空（过滤掉空的 HTML 标签）
        const textContent = contentDiv.textContent.trim();
        const hasMedia = content.includes('<img') || content.includes('<iframe');
        
        if (!textContent && !hasMedia) {
            console.log('日记内容为空');
            this.showToast('请输入日记内容', 'warning');
            return;
        }
        
        try {
            const now = new Date().toISOString();
            
            if (this.isEditing && this.currentEntry) {
                // 更新现有日记
                const updatedEntry = {
                    ...this.currentEntry,
                    date,
                    title,
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
                        title,
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
                    // 创建新日记 - 包含与桌面端兼容的所有字段
                    const newEntry = {
                        id: this.generateId(),
                        date,
                        title,
                        content,
                        mood,
                        weather,
                        tags: [],      // 与桌面端兼容
                        images: [],    // 与桌面端兼容
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
     * 包含与桌面端兼容的所有字段
     */
    exportData() {
        return this.entries.map(entry => ({
            id: entry.id,
            date: entry.date,
            title: entry.title,
            content: entry.content,
            mood: entry.mood,
            weather: entry.weather,
            tags: entry.tags || [],      // 与桌面端兼容
            images: entry.images || [],  // 与桌面端兼容
            created_at: entry.created_at,
            updated_at: entry.updated_at
        }));
    }
    
    /**
     * 导入日记数据（用于同步）
     * 支持从桌面端导入的数据格式
     */
    async importData(entries) {
        for (const entry of entries) {
            // 确保导入的数据包含所有必要字段
            const normalizedEntry = {
                id: entry.id,
                date: entry.date || entry.created_at?.split('T')[0] || new Date().toISOString().split('T')[0],
                title: entry.title || '',
                content: entry.content || '',
                mood: entry.mood || '',
                weather: entry.weather || '',
                tags: entry.tags || [],
                images: entry.images || [],
                created_at: entry.created_at || new Date().toISOString(),
                updated_at: entry.updated_at || new Date().toISOString()
            };
            
            const existing = this.entries.find(e => e.id === normalizedEntry.id);
            if (existing) {
                // 比较更新时间，保留较新的
                if (new Date(normalizedEntry.updated_at) > new Date(existing.updated_at)) {
                    await this.storage.updateDiaryEntry(normalizedEntry);
                    const index = this.entries.findIndex(e => e.id === normalizedEntry.id);
                    if (index !== -1) {
                        this.entries[index] = normalizedEntry;
                    }
                }
            } else {
                await this.storage.addDiaryEntry(normalizedEntry);
                this.entries.push(normalizedEntry);
            }
        }
        
        // 重新排序
        this.entries.sort((a, b) => new Date(b.date) - new Date(a.date));
        
        // 刷新界面
        this.renderEntryList();
    }
}

// 导出模块
window.DiaryModule = DiaryModule;
