# Time Tracker 移动端应用

一个整合了日记、待办事项、计时器和使用时间统计的移动端应用，支持通过 WebDAV 与桌面端同步数据。

## 功能特性

### 📝 待办事项 (Memo)
- 添加、编辑、删除待办事项
- 设置优先级（普通、重要、紧急）
- 分类管理
- 提醒功能
- 标记完成状态
- 筛选查看（全部/未完成/已完成）

### 📔 日记 (Diary)
- Markdown 格式支持
- 心情记录（😊 开心、😐 平静、😢 难过、😠 生气、😰 焦虑）
- 天气记录
- 标签管理
- 日历视图
- 按日期浏览

### ⏱️ 计时器 (Timer)
- 倒计时模式（番茄钟）
- 正计时模式（秒表）
- 自定义时长
- 计时记录保存
- 历史记录查看

### 📊 统计 (Stats)
- 计时统计（今日/本周/本月）
- 待办完成率
- 日记写作统计
- 可视化图表

### ☁️ WebDAV 同步
- 支持任意 WebDAV 服务器
- 与桌面端数据格式兼容
- 手动同步（上传/下载）
- 备份管理

## 技术栈

- **前端**: HTML5 + CSS3 + JavaScript (ES6+)
- **存储**: IndexedDB (本地持久化)
- **同步**: WebDAV 协议
- **打包**: Capacitor (Android/iOS)

## 快速开始

### 1. 安装依赖

```bash
cd mobile_app
npm install
```

### 2. 本地开发

直接在浏览器中打开 `index.html` 进行开发测试：

```bash
# 使用 VS Code Live Server 插件
# 或者使用 Python 简单服务器
python -m http.server 8080

# 或者使用 Node.js 服务器
npx serve .
```

### 3. 构建 Android APK

#### 安装 Capacitor

```bash
npm install @capacitor/core @capacitor/cli @capacitor/android
npx cap init "Time Tracker" "com.timetracker.app"
```

#### 添加 Android 平台

```bash
npx cap add android
```

#### 复制 Web 资源

```bash
# 确保 capacitor.config.json 中 webDir 设置为 "."
npx cap copy android
```

#### 打开 Android Studio

```bash
npx cap open android
```

#### 构建 APK

在 Android Studio 中：
1. 选择 `Build` > `Build Bundle(s) / APK(s)` > `Build APK(s)`
2. APK 文件将生成在 `android/app/build/outputs/apk/debug/`

### 4. 构建 iOS 应用 (需要 macOS)

```bash
npm install @capacitor/ios
npx cap add ios
npx cap copy ios
npx cap open ios
```

## 配置 WebDAV

1. 打开应用，进入「设置」页面
2. 填写 WebDAV 服务器信息：
   - 服务器地址（如：`https://dav.example.com/`）
   - 用户名
   - 密码
   - 同步路径（如：`/timetracker/`）
3. 点击「测试连接」验证配置
4. 保存设置

### 支持的 WebDAV 服务

- 坚果云
- Nextcloud
- ownCloud
- 群晖 NAS
- 其他标准 WebDAV 服务

## 数据格式

应用使用 JSON 格式存储数据，与桌面端完全兼容：

### 待办事项 (memos.json)
```json
{
  "items": [
    {
      "id": "uuid",
      "content": "待办内容",
      "priority": 0,
      "category": "默认",
      "completed": false,
      "created_at": "2024-01-01T00:00:00.000Z",
      "completed_at": null
    }
  ]
}
```

### 日记 (diary_entries.json)
```json
{
  "entries": [
    {
      "id": "uuid",
      "date": "2024-01-01",
      "content": "日记内容（Markdown）",
      "mood": "happy",
      "weather": "sunny",
      "tags": ["标签1", "标签2"],
      "created_at": "2024-01-01T00:00:00.000Z"
    }
  ]
}
```

### 计时记录 (timer_records.json)
```json
{
  "records": [
    {
      "id": "uuid",
      "type": "countdown",
      "duration": 1500,
      "note": "备注",
      "started_at": "2024-01-01T00:00:00.000Z",
      "ended_at": "2024-01-01T00:25:00.000Z"
    }
  ]
}
```

## 项目结构

```
mobile_app/
├── index.html          # 主页面
├── package.json        # 项目配置
├── README.md           # 说明文档
├── css/
│   └── styles.css      # 样式文件
└── js/
    ├── app.js          # 主应用逻辑
    ├── storage.js      # 本地存储模块
    ├── webdav.js       # WebDAV 同步模块
    ├── timer.js        # 计时器模块
    ├── memo.js         # 待办事项模块
    ├── diary.js        # 日记模块
    └── stats.js        # 统计模块
```

## 与桌面端同步

1. 确保桌面端和移动端使用相同的 WebDAV 配置
2. 在桌面端进行「上传备份」
3. 在移动端进行「下载备份」
4. 数据将自动合并（以最新修改为准）

## 注意事项

- 首次使用请先配置 WebDAV 设置
- 建议定期进行数据同步
- 同步前请确保网络连接正常
- 冲突数据以最后修改时间为准

## 开发说明

### 添加新功能

1. 在对应模块文件中添加功能逻辑
2. 在 `index.html` 中添加 UI 元素
3. 在 `styles.css` 中添加样式
4. 在 `app.js` 中注册事件监听

### 调试

- 使用浏览器开发者工具进行调试
- IndexedDB 数据可在 Application > Storage > IndexedDB 中查看
- 网络请求可在 Network 面板中监控

## 许可证

MIT License

## 更新日志

### v1.0.0 (2024-01-10)
- 初始版本发布
- 实现待办事项、日记、计时器、统计功能
- 支持 WebDAV 同步
