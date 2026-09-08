# 启动与验收指南（Windows Setup and Acceptance）

适用环境：Windows 10/11 x64、Python 3.11 或 3.12、Dota 2 无边框窗口模式。

## 一、首次安装

在项目目录打开 CMD，依次运行：

```bat
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-models.txt
copy config.example.yaml config.yaml
.venv\Scripts\python scripts\download_models.py --accept-nllb-license
```

最后一条命令表示接受 NLLB 模型的 CC-BY-NC-4.0 条款；本项目仅按个人、非商业用途使用该模型。模型下载和转换可能需要较长时间，但只需执行一次。

## 二、启动

1. 将 Dota 2 设置为“无边框窗口”，然后进入游戏或观战。
2. 双击 `run.bat`。
3. 在 Windows 托盘（可能位于折叠菜单）找到 **Dota SEA Translator**。
4. 选择 **Calibrate Chat Area**，框选聊天文字区域并保存。
5. 用 **Debug ROI Preview** 检查截图是否只包含聊天区。
6. 保持 **Translation Enabled** 勾选。

翻译会自动显示在透明悬浮窗中。需要调整位置时勾选 **Move Overlay**，拖动完成后取消勾选，恢复鼠标穿透。

## 三、自动检查

关闭正在运行的程序，然后在项目目录执行：

```bat
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python scripts\security_check.py
```

通过标准：

- 测试最后显示 `OK`；
- 安全检查显示 `Security boundary check passed`。

## 四、Dota 实机验收

建议自己在聊天框手动发送或让队友发送以下测试句：

```text
Indonesian: jangan pergi mid dulu
Thai:       อย่าไปคนเดียว
Vietnamese: đợi tôi một chút
English:    wait for me
Chinese:    等我一下
```

逐项确认：

- [ ] 程序只显示托盘图标，没有大型主窗口。
- [ ] DPI 缩放下仍能准确框选聊天区。
- [ ] Debug Preview 能看到正常画面，没有持续黑屏。
- [ ] 印尼语、泰语、越南语能被 OCR，并显示中文翻译。
- [ ] 英语和中文默认不翻译。
- [ ] 同一条消息停留在屏幕上时不会反复翻译。
- [ ] 悬浮窗始终置顶、不抢键盘焦点，取消 **Move Overlay** 后鼠标可以穿透。
- [ ] Dota 切到后台后停止捕获，切回后恢复。
- [ ] 每条字幕最多保留约 8 秒，同时最多显示 5 条。
- [ ] **Settings** 修改后能保存；按提示重启后配置生效。
- [ ] 退出程序后没有保存聊天截图或聊天日志。

若截图持续黑屏，不要尝试 Hook 或注入；确认游戏使用无边框窗口后重新校准。

## 五、真实性能测试

先让一条非英语聊天保持可见。在 CMD 中运行下面的命令后，5 秒内切回 Dota：

```bat
timeout /t 5 /nobreak & .venv\Scripts\python scripts\benchmark.py
```

记录命令输出的 `Capture`、`ChangeDetect`、`OCR`、`LangDetect`、`Translation` 和 `Total`。首次翻译包含模型加载，明显较慢属于正常情况；同时可在任务管理器观察空闲 CPU 和内存。

完成后，把实测结果发给我；我会根据问题修复，并在 `DEVELOPMENT_PLAN.md` 中勾选 G1 和 7.3。
