/**
 * 待办事项模块
 * 与桌面端 memo_storage.py 数据格式兼容
 * 性能优化版本：使用事件委托、防抖、DOM 批量更新
 */

class MemoManager {
    constructor(storage) {
        this.storage = storage;
        this.memos = [];
        this.currentFilter = 'all'; // all, active, completed
        this.currentSort = 'priority'; // priority, created, deadline
        
        // 性能优化：事件委托器
        this.eventDelegator = null;
        // 性能优化：渲染防抖
        this._debouncedRender = null;
        // 性能优化：缓存 DOM 元素
        this._containerEl = null;
        this._statsEl = null;
        // 性能优化：HTML 转义缓存
        this._escapeCache = new Map();
    }

    /**
     * 初始化待办事项模块
     */
    async init() {
        // 缓存 DOM 元素引用
        this._containerEl = document.getElementById('memoList');
        this._statsEl = document.getElementById('memoStats');
        
        // 初始化防抖渲染
        if (window.Performance?.debounce) {
            this._debouncedRender = window.Performance.debounce(() => this._doRender(), 100);
        }
        
        // 初始化事件委托
        this._setupEventDelegation();
        
        await this.loadMemos();
        this.setupEventListeners();
        this.render();
    }
    
    /**
     * 设置事件委托（性能优化）
     */
    _setupEventDelegation() {
        if (!this._containerEl) return;
        
        // 使用事件委托管理器（如果可用）
        if (window.Performance?.EventDelegator) {
            this.eventDelegator = new window.Performance.EventDelegator(this._containerEl);
            
            // 复选框点击
            this.eventDelegator.on('click', '.memo-checkbox', (e, target) => {
                e.stopPropagation();
                const item = target.closest('.memo-item');
                if (item) this.toggleComplete(item.dataset.id);
            });
            
            // 编辑按钮
            this.eventDelegator.on('click', '.memo-edit-btn', (e, target) => {
                e.stopPropagation();
                const item = target.closest('.memo-item');
                if (item) this.showEditDialog(item.dataset.id);
            });
            
            // 删除按钮
            this.eventDelegator.on('click', '.memo-delete-btn', (e, target) => {
                e.stopPropagation();
                const item = target.closest('.memo-item');
                if (item) this.deleteMemo(item.dataset.id);
            });
            
            // 点击展开详情
            this.eventDelegator.on('click', '.memo-item', (e, target) => {
                // 如果点击的是按钮，不展开
                if (e.target.closest('.memo-checkbox, .memo-edit-btn, .memo-delete-btn')) return;
                target.classList.toggle('expanded');
            });
        }
    }

    /**
     * 加载待办事项
     */
    async loadMemos() {
        this.memos = await this.storage.getMemos();
        // 按优先级和创建时间排序
        this.sortMemos();
    }

    /**
     * 排序待办事项
     */
    sortMemos() {
        this.memos.sort((a, b) => {
            // 未完成的排在前面
            if (a.completed !== b.completed) {
                return a.completed ? 1 : -1;
            }
            
            switch (this.currentSort) {
                case 'priority':
                    // 优先级高的排前面 (数字越小优先级越高)
                    if (a.priority !== b.priority) {
                        return a.priority - b.priority;
                    }
                    return new Date(b.created_at) - new Date(a.created_at);
                    
                case 'created':
                    return new Date(b.created_at) - new Date(a.created_at);
                    
                case 'deadline':
                    if (!a.deadline && !b.deadline) return 0;
                    if (!a.deadline) return 1;
                    if (!b.deadline) return -1;
                    return new Date(a.deadline) - new Date(b.deadline);
                    
                default:
                    return 0;
            }
        });
    }

    /**
     * 设置事件监听
     */
    setupEventListeners() {
        // 添加按钮 - 支持两种ID格式
        const addBtn = document.getElementById('add-memo-btn') || document.getElementById('addMemoBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showAddDialog());
        }

        // 筛选按钮
        document.querySelectorAll('.memo-filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.memo-filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentFilter = e.target.dataset.filter;
                this.render();
            });
        });

        // 排序选择
        const sortSelect = document.getElementById('memo-sort');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.currentSort = e.target.value;
                this.sortMemos();
                this.render();
            });
        }
    }

    /**
     * 获取筛选后的待办事项
     */
    getFilteredMemos() {
        switch (this.currentFilter) {
            case 'active':
                return this.memos.filter(m => !m.completed);
            case 'completed':
                return this.memos.filter(m => m.completed);
            default:
                return this.memos;
        }
    }

    /**
     * 渲染待办事项列表（性能优化版）
     * 使用防抖和事件委托减少 DOM 操作
     */
    render() {
        // 如果有防抖渲染函数，使用防抖
        if (this._debouncedRender) {
            this._debouncedRender();
        } else {
            this._doRender();
        }
    }
    
    /**
     * 实际执行渲染（内部方法）
     */
    _doRender() {
        const container = this._containerEl || document.getElementById('memoList');
        if (!container) return;

        const filteredMemos = this.getFilteredMemos();
        
        if (filteredMemos.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <p>${this.currentFilter === 'all' ? '暂无待办事项' :
                         this.currentFilter === 'active' ? '没有进行中的任务' : '没有已完成的任务'}</p>
                </div>
            `;
            this.updateStats();
            return;
        }

        // 使用 DocumentFragment 批量更新 DOM（性能优化）
        const fragment = document.createDocumentFragment();
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = filteredMemos.map(memo => this.renderMemoItem(memo)).join('');
        
        while (tempDiv.firstChild) {
            fragment.appendChild(tempDiv.firstChild);
        }
        
        container.innerHTML = '';
        container.appendChild(fragment);

        // 如果没有事件委托器，使用传统方式绑定事件（兼容性）
        if (!this.eventDelegator) {
            container.querySelectorAll('.memo-item').forEach(item => {
                const id = item.dataset.id;
                
                // 复选框
                item.querySelector('.memo-checkbox')?.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleComplete(id);
                });

                // 编辑
                item.querySelector('.memo-edit-btn')?.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showEditDialog(id);
                });

                // 删除
                item.querySelector('.memo-delete-btn')?.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteMemo(id);
                });

                // 点击展开详情
                item.addEventListener('click', () => {
                    item.classList.toggle('expanded');
                });
            });
        }
        // 如果有事件委托器，事件已在 _setupEventDelegation 中统一处理

        // 更新统计
        this.updateStats();
    }

    /**
     * 渲染单个待办事项
     */
    renderMemoItem(memo) {
        const priorityLabels = ['紧急', '高', '中', '低'];
        const priorityColors = ['#e74c3c', '#e67e22', '#3498db', '#95a5a6'];
        
        const deadlineStr = memo.deadline ? this.formatDeadline(memo.deadline) : '';
        const isOverdue = memo.deadline && !memo.completed && new Date(memo.deadline) < new Date();
        
        return `
            <div class="memo-item ${memo.completed ? 'completed' : ''} ${isOverdue ? 'overdue' : ''}" 
                 data-id="${memo.id}">
                <div class="memo-main">
                    <div class="memo-checkbox ${memo.completed ? 'checked' : ''}">
                        ${memo.completed ? '✓' : ''}
                    </div>
                    <div class="memo-content">
                        <div class="memo-title">${this.escapeHtml(memo.content)}</div>
                        <div class="memo-meta">
                            <span class="memo-priority" style="background: ${priorityColors[memo.priority]}">
                                ${priorityLabels[memo.priority]}
                            </span>
                            ${memo.category ? `<span class="memo-category">${this.escapeHtml(memo.category)}</span>` : ''}
                            ${deadlineStr ? `<span class="memo-deadline ${isOverdue ? 'overdue' : ''}">${deadlineStr}</span>` : ''}
                        </div>
                    </div>
                    <div class="memo-actions">
                        <button class="memo-edit-btn" title="编辑">✏️</button>
                        <button class="memo-delete-btn" title="删除">🗑️</button>
                    </div>
                </div>
                ${memo.notes ? `
                    <div class="memo-notes">
                        <p>${this.escapeHtml(memo.notes)}</p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * 格式化截止日期
     */
    formatDeadline(deadline) {
        const date = new Date(deadline);
        const now = new Date();
        const diff = date - now;
        const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
        
        if (days < 0) {
            return `已过期 ${Math.abs(days)} 天`;
        } else if (days === 0) {
            return '今天截止';
        } else if (days === 1) {
            return '明天截止';
        } else if (days <= 7) {
            return `${days} 天后截止`;
        } else {
            return date.toLocaleDateString('zh-CN');
        }
    }

    /**
     * 更新统计信息
     */
    updateStats() {
        const total = this.memos.length;
        const completed = this.memos.filter(m => m.completed).length;
        const active = total - completed;
        
        const statsEl = document.getElementById('memoStats');
        if (statsEl) {
            statsEl.innerHTML = `
                <span>总计: ${total}</span>
                <span>进行中: ${active}</span>
                <span>已完成: ${completed}</span>
            `;
        }
    }

    /**
     * 显示添加对话框
     */
    showAddDialog() {
        this.showMemoDialog();
    }

    /**
     * 显示编辑对话框
     */
    showEditDialog(id) {
        const memo = this.memos.find(m => m.id === id);
        if (memo) {
            this.showMemoDialog(memo);
        }
    }

    /**
     * 显示待办事项对话框
     */
    showMemoDialog(memo = null) {
        const isEdit = memo !== null;
        const currentPriority = isEdit ? memo.priority : 2;
        const currentCategory = isEdit && memo.category ? memo.category : '';
        
        // 预设分类
        const categories = ['工作', '学习', '生活', '健康', '其他'];
        
        // 创建对话框
        const dialog = document.createElement('div');
        dialog.className = 'dialog-overlay';
        dialog.innerHTML = `
            <div class="dialog">
                <div class="dialog-header">
                    <h3>${isEdit ? '编辑待办' : '添加待办'}</h3>
                    <button class="dialog-close">×</button>
                </div>
                <div class="dialog-body">
                    <div class="form-group">
                        <label>📝 待办内容 <span class="required">*</span></label>
                        <input type="text" id="memo-input-content"
                               value="${isEdit ? this.escapeHtml(memo.content) : ''}"
                               placeholder="今天要做什么？" required>
                    </div>
                    
                    <div class="form-group">
                        <label>🎯 优先级</label>
                        <div class="priority-selector">
                            <div class="priority-option urgent">
                                <input type="radio" name="priority" id="priority-0" value="0"
                                       ${currentPriority === 0 ? 'checked' : ''}>
                                <label for="priority-0">
                                    <span class="priority-icon">🔥</span>
                                    <span class="priority-text">紧急</span>
                                </label>
                            </div>
                            <div class="priority-option high">
                                <input type="radio" name="priority" id="priority-1" value="1"
                                       ${currentPriority === 1 ? 'checked' : ''}>
                                <label for="priority-1">
                                    <span class="priority-icon">⭐</span>
                                    <span class="priority-text">高</span>
                                </label>
                            </div>
                            <div class="priority-option medium">
                                <input type="radio" name="priority" id="priority-2" value="2"
                                       ${currentPriority === 2 ? 'checked' : ''}>
                                <label for="priority-2">
                                    <span class="priority-icon">📌</span>
                                    <span class="priority-text">中</span>
                                </label>
                            </div>
                            <div class="priority-option low">
                                <input type="radio" name="priority" id="priority-3" value="3"
                                       ${currentPriority === 3 ? 'checked' : ''}>
                                <label for="priority-3">
                                    <span class="priority-icon">📝</span>
                                    <span class="priority-text">低</span>
                                </label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>📁 分类</label>
                        <input type="text" id="memo-input-category"
                               value="${this.escapeHtml(currentCategory)}"
                               placeholder="选择或输入分类">
                        <div class="category-shortcuts">
                            ${categories.map(cat => `
                                <span class="category-chip ${currentCategory === cat ? 'active' : ''}"
                                      data-category="${cat}">${cat}</span>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>⏰ 截止时间</label>
                        <div class="deadline-shortcuts">
                            <span class="deadline-chip" data-days="0">今天</span>
                            <span class="deadline-chip" data-days="1">明天</span>
                            <span class="deadline-chip" data-days="7">一周后</span>
                            <span class="deadline-chip" data-days="-1">无</span>
                        </div>
                        <input type="datetime-local" id="memo-input-deadline"
                               value="${isEdit && memo.deadline ? memo.deadline.slice(0, 16) : ''}">
                    </div>
                    
                    <div class="form-group">
                        <label>💬 备注</label>
                        <textarea id="memo-input-notes" rows="2"
                                  placeholder="添加更多细节...">${isEdit && memo.notes ? this.escapeHtml(memo.notes) : ''}</textarea>
                    </div>
                </div>
                <div class="dialog-footer">
                    <button class="btn btn-secondary dialog-cancel">取消</button>
                    <button class="btn btn-primary dialog-confirm">${isEdit ? '💾 保存' : '✨ 添加'}</button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // 聚焦输入框
        setTimeout(() => {
            document.getElementById('memo-input-content')?.focus();
        }, 100);

        // 关闭对话框
        const closeDialog = () => {
            dialog.classList.add('closing');
            setTimeout(() => dialog.remove(), 200);
        };

        dialog.querySelector('.dialog-close').addEventListener('click', closeDialog);
        dialog.querySelector('.dialog-cancel').addEventListener('click', closeDialog);
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) closeDialog();
        });

        // 分类快捷选择
        dialog.querySelectorAll('.category-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const category = chip.dataset.category;
                const input = document.getElementById('memo-input-category');
                
                // 切换选中状态
                dialog.querySelectorAll('.category-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                input.value = category;
            });
        });

        // 截止日期快捷选择
        dialog.querySelectorAll('.deadline-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const days = parseInt(chip.dataset.days);
                const input = document.getElementById('memo-input-deadline');
                
                // 切换选中状态
                dialog.querySelectorAll('.deadline-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                
                if (days === -1) {
                    input.value = '';
                } else {
                    const date = new Date();
                    date.setDate(date.getDate() + days);
                    date.setHours(18, 0, 0, 0); // 默认设置为下午6点
                    input.value = date.toISOString().slice(0, 16);
                }
            });
        });

        // 确认
        dialog.querySelector('.dialog-confirm').addEventListener('click', async () => {
            const content = document.getElementById('memo-input-content').value.trim();
            if (!content) {
                // 添加抖动效果
                const input = document.getElementById('memo-input-content');
                input.style.borderColor = 'var(--danger)';
                input.style.animation = 'shake 0.3s ease';
                setTimeout(() => {
                    input.style.borderColor = '';
                    input.style.animation = '';
                }, 300);
                return;
            }

            // 获取选中的优先级
            const priorityInput = dialog.querySelector('input[name="priority"]:checked');
            const priority = priorityInput ? parseInt(priorityInput.value) : 2;

            const memoData = {
                content,
                priority,
                category: document.getElementById('memo-input-category').value.trim(),
                deadline: document.getElementById('memo-input-deadline').value || null,
                notes: document.getElementById('memo-input-notes').value.trim()
            };

            if (isEdit) {
                await this.updateMemo(memo.id, memoData);
            } else {
                await this.addMemo(memoData);
            }

            closeDialog();
        });
    }

    /**
     * 添加待办事项
     * 包含与桌面端兼容的所有字段
     */
    async addMemo(data) {
        const memo = {
            id: this.generateId(),
            content: data.content,
            priority: data.priority || 2,
            category: data.category || '默认',
            deadline: data.deadline,
            notes: data.notes || '',
            completed: false,
            completed_at: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            // 与桌面端兼容的提醒相关字段
            reminder_enabled: data.reminder_enabled || false,
            reminder_datetime: data.reminder_datetime || null,
            reminder_repeat: data.reminder_repeat || 'none',  // none, daily, weekly, monthly
            reminder_notified: false
        };

        this.memos.push(memo);
        this.sortMemos();
        await this.storage.saveMemo(memo);
        this.render();
        
        // 触发同步
        if (window.app?.webdav) {
            window.app.webdav.markDirty();
        }
    }

    /**
     * 更新待办事项
     */
    async updateMemo(id, data) {
        const index = this.memos.findIndex(m => m.id === id);
        if (index === -1) return;

        this.memos[index] = {
            ...this.memos[index],
            ...data,
            updated_at: new Date().toISOString()
        };

        this.sortMemos();
        await this.storage.saveMemo(this.memos[index]);
        this.render();
        
        if (window.app?.webdav) {
            window.app.webdav.markDirty();
        }
    }

    /**
     * 切换完成状态
     */
    async toggleComplete(id) {
        const memo = this.memos.find(m => m.id === id);
        if (!memo) return;

        memo.completed = !memo.completed;
        memo.completed_at = memo.completed ? new Date().toISOString() : null;
        memo.updated_at = new Date().toISOString();

        this.sortMemos();
        await this.storage.saveMemo(memo);
        this.render();
        
        if (window.app?.webdav) {
            window.app.webdav.markDirty();
        }
    }

    /**
     * 删除待办事项
     */
    async deleteMemo(id) {
        if (!confirm('确定要删除这个待办事项吗？')) return;

        const index = this.memos.findIndex(m => m.id === id);
        if (index === -1) return;

        this.memos.splice(index, 1);
        await this.storage.deleteMemo(id);
        this.render();
        
        if (window.app?.webdav) {
            window.app.webdav.markDirty();
        }
    }

    /**
     * 清除已完成的待办事项
     */
    async clearCompleted() {
        if (!confirm('确定要清除所有已完成的待办事项吗？')) return;

        const completedIds = this.memos.filter(m => m.completed).map(m => m.id);
        
        for (const id of completedIds) {
            await this.storage.deleteMemo(id);
        }
        
        this.memos = this.memos.filter(m => !m.completed);
        this.render();
        
        if (window.app?.webdav) {
            window.app.webdav.markDirty();
        }
    }

    /**
     * 生成唯一ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 导出数据（用于同步）
     * 包含与桌面端兼容的所有字段
     */
    exportData() {
        return this.memos.map(memo => ({
            id: memo.id,
            content: memo.content,
            completed: memo.completed,
            created_at: memo.created_at,
            completed_at: memo.completed_at,
            priority: memo.priority,
            category: memo.category || '默认',
            // 与桌面端兼容的提醒相关字段
            reminder_enabled: memo.reminder_enabled || false,
            reminder_datetime: memo.reminder_datetime || null,
            reminder_repeat: memo.reminder_repeat || 'none',
            reminder_notified: memo.reminder_notified || false,
            // 移动端额外字段
            deadline: memo.deadline,
            notes: memo.notes,
            updated_at: memo.updated_at
        }));
    }

    /**
     * 导入数据（用于同步）
     * 支持从桌面端导入的数据格式
     */
    async importData(memos) {
        const normalizedMemos = memos.map(memo => ({
            id: memo.id,
            content: memo.content,
            completed: memo.completed || false,
            created_at: memo.created_at || new Date().toISOString(),
            completed_at: memo.completed_at || null,
            priority: memo.priority || 2,
            category: memo.category || '默认',
            // 与桌面端兼容的提醒相关字段
            reminder_enabled: memo.reminder_enabled || false,
            reminder_datetime: memo.reminder_datetime || null,
            reminder_repeat: memo.reminder_repeat || 'none',
            reminder_notified: memo.reminder_notified || false,
            // 移动端额外字段
            deadline: memo.deadline || null,
            notes: memo.notes || '',
            updated_at: memo.updated_at || new Date().toISOString()
        }));
        
        this.memos = normalizedMemos;
        for (const memo of normalizedMemos) {
            await this.storage.saveMemo(memo);
        }
        this.sortMemos();
        this.render();
    }
}

// 导出
window.MemoManager = MemoManager;
