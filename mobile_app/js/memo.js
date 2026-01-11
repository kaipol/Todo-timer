/**
 * 待办事项模块
 * 与桌面端 memo_storage.py 数据格式兼容
 */

class MemoManager {
    constructor(storage) {
        this.storage = storage;
        this.memos = [];
        this.currentFilter = 'all'; // all, active, completed
        this.currentSort = 'priority'; // priority, created, deadline
    }

    /**
     * 初始化待办事项模块
     */
    async init() {
        await this.loadMemos();
        this.setupEventListeners();
        this.render();
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
        // 添加按钮
        const addBtn = document.getElementById('add-memo-btn');
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
     * 渲染待办事项列表
     */
    render() {
        const container = document.getElementById('memo-list');
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
            return;
        }

        container.innerHTML = filteredMemos.map(memo => this.renderMemoItem(memo)).join('');

        // 绑定事件
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
        
        const statsEl = document.getElementById('memo-stats');
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
                        <label>内容 *</label>
                        <input type="text" id="memo-input-content" 
                               value="${isEdit ? this.escapeHtml(memo.content) : ''}" 
                               placeholder="输入待办内容..." required>
                    </div>
                    <div class="form-group">
                        <label>优先级</label>
                        <select id="memo-input-priority">
                            <option value="0" ${isEdit && memo.priority === 0 ? 'selected' : ''}>紧急</option>
                            <option value="1" ${isEdit && memo.priority === 1 ? 'selected' : ''}>高</option>
                            <option value="2" ${(!isEdit || memo.priority === 2) ? 'selected' : ''}>中</option>
                            <option value="3" ${isEdit && memo.priority === 3 ? 'selected' : ''}>低</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>分类</label>
                        <input type="text" id="memo-input-category" 
                               value="${isEdit && memo.category ? this.escapeHtml(memo.category) : ''}" 
                               placeholder="如：工作、学习、生活...">
                    </div>
                    <div class="form-group">
                        <label>截止日期</label>
                        <input type="datetime-local" id="memo-input-deadline" 
                               value="${isEdit && memo.deadline ? memo.deadline.slice(0, 16) : ''}">
                    </div>
                    <div class="form-group">
                        <label>备注</label>
                        <textarea id="memo-input-notes" rows="3" 
                                  placeholder="添加备注...">${isEdit && memo.notes ? this.escapeHtml(memo.notes) : ''}</textarea>
                    </div>
                </div>
                <div class="dialog-footer">
                    <button class="btn btn-secondary dialog-cancel">取消</button>
                    <button class="btn btn-primary dialog-confirm">${isEdit ? '保存' : '添加'}</button>
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

        // 确认
        dialog.querySelector('.dialog-confirm').addEventListener('click', async () => {
            const content = document.getElementById('memo-input-content').value.trim();
            if (!content) {
                alert('请输入待办内容');
                return;
            }

            const memoData = {
                content,
                priority: parseInt(document.getElementById('memo-input-priority').value),
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
     */
    async addMemo(data) {
        const memo = {
            id: this.generateId(),
            content: data.content,
            priority: data.priority || 2,
            category: data.category || '',
            deadline: data.deadline,
            notes: data.notes || '',
            completed: false,
            completed_at: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
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
     */
    exportData() {
        return this.memos;
    }

    /**
     * 导入数据（用于同步）
     */
    async importData(memos) {
        this.memos = memos;
        for (const memo of memos) {
            await this.storage.saveMemo(memo);
        }
        this.sortMemos();
        this.render();
    }
}

// 导出
window.MemoManager = MemoManager;
