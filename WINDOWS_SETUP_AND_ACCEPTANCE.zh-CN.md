# Windows 安装、试用与验收指南

适用环境为 Windows 10/11 x64、Python 3.11 或 3.12。游戏使用 Dota 2 无边框窗口模式。

## 一、首次安装

在项目目录打开 CMD，安装依赖。已安装 Python 3.12 时，把 `py -3.11` 改成 `py -3.12`。

```bat
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-models.txt
```

模型安装需要联网。确认接受 NLLB 的 CC BY-NC 4.0 个人非商业使用条款后，运行下载脚本。模型安装完成后，程序会在本机离线识别和翻译。[NLLB 模型许可](https://huggingface.co/facebook/nllb-200-distilled-600M)

```bat
.venv\Scripts\python scripts\download_models.py --accept-nllb-license
```

首次运行 `run.bat` 时会从示例生成 `config.yaml`。

## 二、启动

1. 将 Dota 2 设置为“无边框窗口”，然后进入游戏或观战。
2. 双击 `run.bat`。程序进入 Windows 托盘，并在后台加载模型。
3. 在右下角托盘找到 **Dota SEA Translator**。折叠的图标在 `^` 菜单里。
4. 右键托盘图标，选择 **Calibrate Chat Area**。拖框圈住已经发出的聊天消息，松开鼠标保存。按 `Esc` 可取消。
5. 选择 **Debug ROI Preview**，检查完整的消息是否落在框内。
6. 保持 **Translation Enabled** 勾选。切回 Dota 2，文字可见时按一次 **F8**。

按键后，悬浮窗显示识别进度和译文。等待结果后可再次按 **F8**。切出游戏时，程序释放 F8。需要调整字幕位置时，勾选 **Move Overlay**，拖动完成后取消勾选，恢复鼠标穿透。

### 常见提示

| 屏幕上的情况 | 处理方式 |
| --- | --- |
| 启动后只看到控制台 | 在托盘的 `^` 菜单找 **Dota SEA Translator**。启动报错时，`run.bat` 会停下来显示错误。 |
| 按 F8 没有反应 | 确认 Dota 2 在前台，并检查 **Translation Enabled**。托盘提示快捷键注册失败时，检查其他程序是否占用了 F8。 |
| 「聊天区没有识别到文字」 | 等消息在屏幕上出现后再按 F8。用 **Debug ROI Preview** 检查是否需要重新框选。 |
| 「识别到了文字，但没有可翻译的外语聊天」 | 试用下方的泰语或印尼语样例。英语和中文默认跳过，无法判断语种的行也会被过滤。 |
| 「截图是黑的」 | 在 Dota 2 切换到无边框窗口，再检查聊天区。 |
| 「正在识别聊天…」停留较久 | 刚启动时模型可能仍在加载。等当前识别结束后再按 F8。 |

泰语聊天可以同时包含中文队友标签、玩家名和战队标签。泰语 OCR 可能把前缀里的中文标签或括号读成其他符号。冒号正确识别时，程序会单独翻译正文。越南语样图也观察到部分重音字符漏识别。

## 三、自动检查

关闭正在运行的程序，然后在项目目录执行：

```bat
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python scripts\security_check.py
```

- 测试最后显示 `OK`。
- 安全检查显示 `Security boundary check passed`。

## 四、Dota 实机验收

在练习房里逐条发送以下测试句。让消息显示在已校准的聊天区后按 F8。

| 语言 | 发送的文字 |
| --- | --- |
| 印尼语 | `Tolong tunggu saya sebentar.` |
| 泰语 | `อย่าไปคนเดียว` |
| 越南语 | `đợi tôi một chút` |
| 英语 | `wait for me` |
| 中文 | `等我一下` |

游戏内出现类似 `【队友】Player【TAG】: อย่าไปคนเดียว` 的消息时，预期正文译为「别一个人去」。

- [ ] 程序只显示托盘图标，没有大型主窗口。
- [ ] DPI 缩放下仍能准确框选聊天区。
- [ ] **Debug ROI Preview** 能看到完整聊天消息。
- [ ] 印尼语和带前缀的泰语消息都能显示中文译文。记录越南语重音识别的实际表现。
- [ ] 英语和中文默认不翻译。
- [ ] 一次按键只处理当时的聊天画面，等待期间没有持续截图或 OCR。
- [ ] 悬浮窗始终置顶、不抢键盘焦点，取消 **Move Overlay** 后鼠标可以穿透。
- [ ] Dota 切到后台后按快捷键不会截图，切回后可以再次触发。
- [ ] 默认每条字幕约 8 秒后开始淡出，同时最多显示 5 条译文。
- [ ] **Settings** 修改后能保存，重启后配置生效。
- [ ] 退出程序后没有保存聊天截图或聊天日志。

## 五、真实性能测试

先让一条非英语聊天保持可见。在 CMD 中运行下面的命令后，5 秒内切回 Dota：

```bat
timeout /t 5 /nobreak & .venv\Scripts\python scripts\benchmark.py
```

记录命令输出的 `Capture`、`OCR`、`LangDetect`、`Translation` 和 `Total`。此命令独立加载模型，测到的是冷启动耗时。托盘版在启动时预载模型，可以另外记录预载后从 F8 到首条字幕的时间。

把实机结果记在开发计划的 G1 和 7.3。[开发计划](DEVELOPMENT_PLAN.md)
