/**
 * 性能优化工具模块
 * 提供防抖、节流、DOM 操作优化等工具函数
 */

// ==================== 防抖函数 ====================
/**
 * 防抖函数 - 延迟执行，多次调用只执行最后一次
 * @param {Function} func - 要执行的函数
 * @param {number} wait - 等待时间（毫秒）
 * @param {boolean} immediate - 是否立即执行
 * @returns {Function} 防抖后的函数
 */
function debounce(func, wait = 300, immediate = false) {
    let timeout = null;
    let result;
    
    const debounced = function(...args) {
        const context = this;
        
        if (timeout) clearTimeout(timeout);
        
        if (immediate) {
            const callNow = !timeout;
            timeout = setTimeout(() => {
                timeout = null;
            }, wait);
            if (callNow) result = func.apply(context, args);
        } else {
            timeout = setTimeout(() => {
                func.apply(context, args);
            }, wait);
        }
        
        return result;
    };
    
    debounced.cancel = function() {
        if (timeout) {
            clearTimeout(timeout);
            timeout = null;
        }
    };
    
    return debounced;
}

// ==================== 节流函数 ====================
/**
 * 节流函数 - 固定时间间隔执行
 * @param {Function} func - 要执行的函数
 * @param {number} wait - 间隔时间（毫秒）
 * @param {Object} options - 配置选项
 * @returns {Function} 节流后的函数
 */
function throttle(func, wait = 100, options = {}) {
    let timeout = null;
    let previous = 0;
    const { leading = true, trailing = true } = options;
    
    const throttled = function(...args) {
        const context = this;
        const now = Date.now();
        
        if (!previous && !leading) previous = now;
        
        const remaining = wait - (now - previous);
        
        if (remaining <= 0 || remaining > wait) {
            if (timeout) {
                clearTimeout(timeout);
                timeout = null;
            }
            previous = now;
            func.apply(context, args);
        } else if (!timeout && trailing) {
            timeout = setTimeout(() => {
                previous = leading ? Date.now() : 0;
                timeout = null;
                func.apply(context, args);
            }, remaining);
        }
    };
    
    throttled.cancel = function() {
        if (timeout) {
            clearTimeout(timeout);
            timeout = null;
        }
        previous = 0;
    };
    
    return throttled;
}

// ==================== requestAnimationFrame 优化 ====================
/**
 * 使用 requestAnimationFrame 优化的节流
 * 适用于动画和频繁的 DOM 更新
 * @param {Function} func - 要执行的函数
 * @returns {Function} 优化后的函数
 */
function rafThrottle(func) {
    let rafId = null;
    let lastArgs = null;
    
    const throttled = function(...args) {
        lastArgs = args;
        
        if (rafId === null) {
            rafId = requestAnimationFrame(() => {
                func.apply(this, lastArgs);
                rafId = null;
            });
        }
    };
    
    throttled.cancel = function() {
        if (rafId !== null) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
    };
    
    return throttled;
}

// ==================== DOM 批量更新 ====================
/**
 * DOM 批量更新管理器
 * 收集多个 DOM 更新操作，在下一帧统一执行
 */
class DOMBatchUpdater {
    constructor() {
        this.updates = new Map();
        this.scheduled = false;
    }
    
    /**
     * 添加更新任务
     * @param {string} key - 任务标识（相同 key 会覆盖）
     * @param {Function} updateFn - 更新函数
     */
    add(key, updateFn) {
        this.updates.set(key, updateFn);
        this.schedule();
    }
    
    /**
     * 调度执行
     */
    schedule() {
        if (this.scheduled) return;
        
        this.scheduled = true;
        requestAnimationFrame(() => {
            this.flush();
        });
    }
    
    /**
     * 执行所有更新
     */
    flush() {
        const updates = new Map(this.updates);
        this.updates.clear();
        this.scheduled = false;
        
        updates.forEach((updateFn) => {
            try {
                updateFn();
            } catch (e) {
                console.error('DOM 更新错误:', e);
            }
        });
    }
}

// 全局 DOM 批量更新器实例
const domBatchUpdater = new DOMBatchUpdater();

// ==================== 虚拟列表（简化版）====================
/**
 * 简化的虚拟滚动列表
 * 只渲染可见区域的元素
 */
class VirtualList {
    constructor(options) {
        this.container = options.container;
        this.itemHeight = options.itemHeight || 60;
        this.items = options.items || [];
        this.renderItem = options.renderItem;
        this.buffer = options.buffer || 5; // 缓冲区大小
        
        this.scrollTop = 0;
        this.containerHeight = 0;
        this.contentEl = null;
        this.listEl = null;
        
        this.init();
    }
    
    init() {
        if (!this.container) return;
        
        // 创建内容容器
        this.contentEl = document.createElement('div');
        this.contentEl.className = 'virtual-list-content';
        this.contentEl.style.position = 'relative';
        
        // 创建列表容器
        this.listEl = document.createElement('div');
        this.listEl.className = 'virtual-list-items';
        this.listEl.style.position = 'absolute';
        this.listEl.style.top = '0';
        this.listEl.style.left = '0';
        this.listEl.style.right = '0';
        
        this.contentEl.appendChild(this.listEl);
        this.container.appendChild(this.contentEl);
        
        // 绑定滚动事件
        this.handleScroll = rafThrottle(this.onScroll.bind(this));
        this.container.addEventListener('scroll', this.handleScroll, { passive: true });
        
        this.updateContainerHeight();
        this.render();
    }
    
    updateContainerHeight() {
        this.containerHeight = this.container.clientHeight;
    }
    
    setItems(items) {
        this.items = items;
        this.render();
    }
    
    onScroll() {
        this.scrollTop = this.container.scrollTop;
        this.render();
    }
    
    render() {
        if (!this.listEl || !this.items.length) {
            if (this.listEl) this.listEl.innerHTML = '';
            return;
        }
        
        const totalHeight = this.items.length * this.itemHeight;
        this.contentEl.style.height = `${totalHeight}px`;
        
        // 计算可见范围
        const startIndex = Math.max(0, Math.floor(this.scrollTop / this.itemHeight) - this.buffer);
        const endIndex = Math.min(
            this.items.length,
            Math.ceil((this.scrollTop + this.containerHeight) / this.itemHeight) + this.buffer
        );
        
        // 渲染可见项
        const fragment = document.createDocumentFragment();
        for (let i = startIndex; i < endIndex; i++) {
            const itemEl = this.renderItem(this.items[i], i);
            if (itemEl) {
                itemEl.style.position = 'absolute';
                itemEl.style.top = `${i * this.itemHeight}px`;
                itemEl.style.left = '0';
                itemEl.style.right = '0';
                fragment.appendChild(itemEl);
            }
        }
        
        this.listEl.innerHTML = '';
        this.listEl.appendChild(fragment);
    }
    
    destroy() {
        if (this.handleScroll) {
            this.container.removeEventListener('scroll', this.handleScroll);
            this.handleScroll.cancel?.();
        }
        if (this.contentEl) {
            this.contentEl.remove();
        }
    }
}

// ==================== 事件委托管理器 ====================
/**
 * 事件委托管理器
 * 统一管理容器内的事件委托
 */
class EventDelegator {
    constructor(container) {
        this.container = container;
        this.handlers = new Map();
    }
    
    /**
     * 添加事件委托
     * @param {string} eventType - 事件类型
     * @param {string} selector - CSS 选择器
     * @param {Function} handler - 事件处理函数
     */
    on(eventType, selector, handler) {
        if (!this.handlers.has(eventType)) {
            this.handlers.set(eventType, new Map());
            this.container.addEventListener(eventType, this.handleEvent.bind(this, eventType), {
                passive: eventType === 'scroll' || eventType === 'touchmove'
            });
        }
        
        const selectorHandlers = this.handlers.get(eventType);
        if (!selectorHandlers.has(selector)) {
            selectorHandlers.set(selector, []);
        }
        selectorHandlers.get(selector).push(handler);
    }
    
    /**
     * 移除事件委托
     * @param {string} eventType - 事件类型
     * @param {string} selector - CSS 选择器
     * @param {Function} handler - 事件处理函数（可选）
     */
    off(eventType, selector, handler) {
        const selectorHandlers = this.handlers.get(eventType);
        if (!selectorHandlers) return;
        
        if (handler) {
            const handlers = selectorHandlers.get(selector);
            if (handlers) {
                const index = handlers.indexOf(handler);
                if (index > -1) handlers.splice(index, 1);
            }
        } else {
            selectorHandlers.delete(selector);
        }
    }
    
    /**
     * 处理事件
     */
    handleEvent(eventType, event) {
        const selectorHandlers = this.handlers.get(eventType);
        if (!selectorHandlers) return;
        
        selectorHandlers.forEach((handlers, selector) => {
            const target = event.target.closest(selector);
            if (target && this.container.contains(target)) {
                handlers.forEach(handler => {
                    try {
                        handler.call(target, event, target);
                    } catch (e) {
                        console.error('事件处理错误:', e);
                    }
                });
            }
        });
    }
    
    /**
     * 销毁
     */
    destroy() {
        this.handlers.forEach((_, eventType) => {
            this.container.removeEventListener(eventType, this.handleEvent);
        });
        this.handlers.clear();
    }
}

// ==================== 内存缓存 ====================
/**
 * 简单的内存缓存，带 TTL
 */
class MemoryCache {
    constructor(defaultTTL = 60000) {
        this.cache = new Map();
        this.defaultTTL = defaultTTL;
    }
    
    set(key, value, ttl = this.defaultTTL) {
        const expiry = Date.now() + ttl;
        this.cache.set(key, { value, expiry });
    }
    
    get(key) {
        const item = this.cache.get(key);
        if (!item) return undefined;
        
        if (Date.now() > item.expiry) {
            this.cache.delete(key);
            return undefined;
        }
        
        return item.value;
    }
    
    has(key) {
        return this.get(key) !== undefined;
    }
    
    delete(key) {
        this.cache.delete(key);
    }
    
    clear() {
        this.cache.clear();
    }
    
    // 清理过期项
    cleanup() {
        const now = Date.now();
        this.cache.forEach((item, key) => {
            if (now > item.expiry) {
                this.cache.delete(key);
            }
        });
    }
}

// ==================== HTML 转义（优化版）====================
/**
 * 高性能 HTML 转义
 * 使用查找表而非正则替换
 */
const htmlEscapeMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
};

function escapeHtml(str) {
    if (!str) return '';
    if (typeof str !== 'string') str = String(str);
    
    let result = '';
    for (let i = 0; i < str.length; i++) {
        const char = str[i];
        result += htmlEscapeMap[char] || char;
    }
    return result;
}

// ==================== 性能监控 ====================
/**
 * 简单的性能监控
 */
class PerformanceMonitor {
    constructor() {
        this.marks = new Map();
        this.measures = [];
    }
    
    mark(name) {
        this.marks.set(name, performance.now());
    }
    
    measure(name, startMark, endMark) {
        const start = this.marks.get(startMark);
        const end = endMark ? this.marks.get(endMark) : performance.now();
        
        if (start !== undefined) {
            const duration = end - start;
            this.measures.push({ name, duration, timestamp: Date.now() });
            
            if (duration > 16) { // 超过一帧的时间
                console.warn(`[性能警告] ${name}: ${duration.toFixed(2)}ms`);
            }
            
            return duration;
        }
        return 0;
    }
    
    getReport() {
        return this.measures.slice(-100); // 最近 100 条记录
    }
    
    clear() {
        this.marks.clear();
        this.measures = [];
    }
}

// 全局性能监控实例
const perfMonitor = new PerformanceMonitor();

// ==================== 导出 ====================
window.Performance = {
    debounce,
    throttle,
    rafThrottle,
    DOMBatchUpdater,
    domBatchUpdater,
    VirtualList,
    EventDelegator,
    MemoryCache,
    escapeHtml,
    PerformanceMonitor,
    perfMonitor
};
