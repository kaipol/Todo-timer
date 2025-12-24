# Time Tracker

Time Tracker 是一款基于 PyQt6 的桌面番茄钟与应用使用时间追踪工具，专为 Windows 平台设计。它可以实时监控前台程序，记录每个应用的使用时长，并提供番茄钟、备忘录、日历与周统计等效率管理功能。

## 功能特性
- **番茄钟与正计时**：支持倒计时/正计时切换，可添加备注并自动保存历史记录。
- **应用使用监控**：通过前台窗口监控记录应用使用时长，展示今日/每周统计，支持图标展示与子窗口聚合。
- **日历视图**：以卡片式日历查看每日番茄记录与应用使用，支持一键清理指定日期数据。
- **周统计面板**：展示本周总时长、日均、Top 应用列表、每日展开详情等信息。
- **备忘录与提醒**：内置待办、提醒、今日待办同步，完成项可批量清理。
- **日记模块**：支持按日记录、编辑与今日摘录。
- **个性化样式**：自定义背景图、渐变、颜色、模糊、透明度及应用图标。
- **单例运行**：使用 `QLocalServer` 保证只启动一个实例。
- **迷你悬浮窗**：主窗体可最小化为小窗，方便随时查看当前任务。

## 开发环境
- Python 3.12（推荐使用 Conda/Miniforge 环境）
- 系统：Windows 10/11
- 依赖：详见 `requirements.txt`

## 快速开始
```bash
# 安装依赖
pip install -r requirements.txt

# 运行开发版本
python main.py
```

首次运行会在用户目录下创建配置与数据文件夹 `~/.time_tracker`，存储如下数据：
- `config.json`：界面与背景配置
- `timer_records.json`：计时记录
- `memos.json`：备忘录
- `usage/`：应用使用统计
- `diary/`：日记数据

## 目录结构
```
core/            # 核心逻辑（配置、监控、存储、工具）
core/storage/    # 各类数据存储类（计时、应用、备忘录、日记）
ui/              # PyQt UI 组件（主窗体、日历、备忘录、日记等）
TimeTracker.spec # PyInstaller 构建配置
main.py          # 程序入口
```

## 编译为 EXE
项目已携带 `TimeTracker.spec`，可直接使用 PyInstaller 构建。
```bash
# 确保已安装依赖
pip install -r requirements.txt

# 生成 exe（dist/TimeTracker.exe）
pyinstaller TimeTracker.spec
```
构建完成后，可在 `dist/TimeTracker.exe` 运行单文件版本。如需自定义图标、单文件/多文件模式等，可修改 `TimeTracker.spec`。

## 常见问题
1. **为何没有界面显示/报错缺少 Qt DLL？**
   - 请确认通过 `pip install PyQt6` 安装完成，且未被杀毒软件阻止。
2. **如何清理历史数据？**
   - 在日历面板点击 `🗑️ 清理`，可删除指定日期的计时与应用记录；或直接删除 `~/.time_tracker` 对应数据文件。
3. **如何更换背景/图标？**
   - 打开设置面板，选择背景类型与图片；或在 `core/config.py` 中设置默认值。
4. **是否支持 WebDAV 同步？**
   - 代码中提供 `core/webdav_sync.py` 模块，UI 中的设置面板可配置 WebDAV 备份与恢复。

## 构建与测试
- 本地测试：运行 `python main.py` 手动验证 UI 与功能。
- 自动化测试：暂无专用脚本，可使用 PyInstaller 构建成功作为基本验证。

欢迎根据实际需求扩展功能或优化 UI，若需二次开发建议在虚拟环境中操作以保持依赖一致性。祝使用愉快！
