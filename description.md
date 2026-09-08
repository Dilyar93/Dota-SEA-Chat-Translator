# Dota 2 SEA 实时聊天翻译器

## Codex 开发规格说明书

项目暂定名称：

**Dota SEA Chat Translator**

目标平台：

**Windows 10 / Windows 11 x64**

项目性质：

**个人使用、完全免费、本地优先、不开启任何游戏自动化功能。**

---

# 1. 项目目标

开发一个专门用于 Dota 2 SEA 区游戏的实时文字聊天翻译工具。

用户在 Dota 2 游戏过程中，经常遇到东南亚玩家使用以下语言聊天：

* Indonesian / 印尼语
* Malay / 马来语
* Tagalog / 菲律宾语
* Thai / 泰语
* Vietnamese / 越南语
* English / 英语

用户能够理解中文和基本英语，因此主要目标是：

> 自动识别 Dota 2 屏幕中下方聊天区域中新出现的非英语聊天，将其翻译为简体中文，并通过透明悬浮窗实时显示。

整个过程不应要求用户频繁按快捷键。

理想体验：

```text
Dota 玩家输入：
jangan pergi mid dulu

程序检测：
Indonesian / Malay

悬浮翻译：
先别去中路。
```

或者：

```text
Dota 玩家输入泰语：
อย่าไปคนเดียว

悬浮翻译：
别一个人去。
```

---

# 2. 最重要的安全边界

这是整个项目最高优先级的开发原则。

程序只能操作 Windows 桌面层，不与 Dota 2 游戏内部数据交互。

## 严格禁止

不得：

* ReadProcessMemory
* OpenProcess 后读取 Dota 内存
* DLL Injection
* Hook Dota 内部函数
* 修改 dota2.exe
* 修改游戏 DLL
* 修改游戏文件
* 读取游戏内部对象
* 读取战争迷雾信息
* 读取网络包获取游戏数据
* 使用驱动访问游戏
* 模拟玩家鼠标操作
* 模拟玩家键盘操作
* 自动发送聊天
* 自动执行指令
* 自动施法
* 自动移动
* 使用任何作弊相关 SDK

不要设计任何未来可能演变为游戏辅助/作弊的接口。

## 允许

程序只能：

```text
Windows 屏幕截图
        ↓
OCR
        ↓
语言检测
        ↓
文本翻译
        ↓
Windows 透明悬浮窗
```

可以通过 Windows API：

* 获取显示器信息
* 获取前台窗口
* 获取 Dota 窗口坐标
* 获取 DPI
* 判断 Dota 是否处于前台

但不得读取 Dota 进程内存。

Dota 2 使用 VAC。Valve 曾明确针对读取 Dota 客户端内部、正常游戏不可见数据的第三方程序采取封禁措施。因此本项目必须始终保持纯屏幕 OCR 架构。

代码中增加注释：

```text
SECURITY BOUNDARY:
This application only observes pixels already visible to the user.
Never add process memory reading, DLL injection, game hooks,
input automation, packet inspection, or game file modification.
```

---

# 3. 核心架构

整体数据流：

```text
Dota 2
  │
  │ visible screen pixels only
  ↓
Screen Capture
  │
  ↓
ROI 裁剪
  │
  ↓
Change Detection
  │
  ├── 无变化 → 不执行 OCR
  │
  └── 有变化
          ↓
     Image Preprocess
          ↓
        OCR
          ↓
     Line Reconstruction
          ↓
      Message Dedup
          ↓
    Language Detection
          ↓
    Translation Cache
          │
          ├── 命中 → 直接显示
          │
          └── 未命中
                 ↓
          Local Translation
                 ↓
              Overlay
```

---

# 4. 推荐技术栈

优先使用 Python 开发 MVP。

推荐：

```text
Python 3.11+
PySide6
mss
numpy
opencv-python
PaddleOCR
PaddlePaddle
fastText
CTranslate2
Transformers
SentencePiece
RapidFuzz
pywin32
```

不要为了追求架构复杂度而使用 Electron、WebView 或客户端/服务器架构。

这是单机工具。

---

# 5. UI 技术

GUI 使用：

**PySide6**

需要三个主要 UI：

1. System Tray
2. ROI Calibration Window
3. Translation Overlay

程序启动后默认进入系统托盘，不打开大型主窗口。

托盘菜单：

```text
Dota SEA Translator
--------------------
✓ Translation Enabled
Calibrate Chat Area
Settings
Test OCR
Pause
Exit
```

---

# 6. 屏幕捕获

首选：

**python-mss**

原因：

* 免费
* MIT License
* Windows 支持
* 可以只抓指定 ROI
* 能直接转换 NumPy
* 不需要游戏注入

原则：

**绝对不要持续截取整个屏幕再 OCR。**

只截聊天区域。

推荐捕获流程：

```python
screen_roi = {
    "left": ...,
    "top": ...,
    "width": ...,
    "height": ...
}
```

然后：

```python
frame = capture(screen_roi)
```

目标轮询频率：

```text
4～6 FPS
```

即约：

```text
每 170～250 ms 获取一次 ROI
```

这里“获取截图”可以频繁，但 OCR 不可以每帧运行。

---

# 7. Dota 显示模式

首选支持：

**Borderless Window / 无边框窗口**

启动时如果截图连续黑屏，应：

1. 提示用户切换 Dota 为无边框窗口；
2. 不尝试绕过 DirectX；
3. 不使用 DLL / Hook 解决。

未来可以考虑 Desktop Duplication API，但不是 MVP 必需功能。

---

# 8. ROI 聊天区域校准

不要写死：

```text
x = 600
y = 900
width = 1200
height = 300
```

因为用户可能使用：

* 1920×1080
* 2560×1440
* 3440×1440
* 4K
* 不同 HUD Scale
* Windows DPI Scale

必须制作 ROI Calibration。

用户点击：

**Calibrate Chat Area**

程序：

1. 截取当前屏幕；
2. 全屏显示半透明截图；
3. 用户鼠标拖动矩形；
4. 提示：

```text
请选择 Dota 2 屏幕中下方聊天消息出现的区域
```

5. 保存区域。

保存时尽量不要保存绝对像素。

建议转换为相对于 Dota Client Area 的比例：

```text
left_ratio
top_ratio
width_ratio
height_ratio
```

例如：

```yaml
roi:
  left: 0.18
  top: 0.60
  width: 0.62
  height: 0.25
```

因此分辨率变化时仍然基本可用。

---

# 9. Dota 窗口检测

使用 Windows API / pywin32。

允许：

```text
EnumWindows
GetForegroundWindow
GetWindowText
GetClientRect
ClientToScreen
```

目的只有：

* 判断 Dota 是否运行
* 判断 Dota 是否是当前前台窗口
* 获取客户区屏幕位置

不要：

```text
OpenProcess
ReadProcessMemory
VirtualQueryEx
```

当 Dota 不在前台时：

```text
暂停截图
暂停 OCR
暂停翻译
```

降低系统资源占用。

---

# 10. Change Detection

这是性能优化的核心。

不要：

```text
截图 → OCR
截图 → OCR
截图 → OCR
截图 → OCR
```

应当：

```text
截图
 ↓
图像变化检测
 ↓
只有变化明显才 OCR
```

## 第一阶段变化检测

将 ROI：

1. 转灰度；
2. 缩小到例如 1/4；
3. Gaussian Blur；
4. 比较前一帧。

例如：

```python
diff = cv2.absdiff(previous, current)
score = np.mean(diff)
```

设置 configurable threshold。

初始：

```text
change_threshold = 3～8
```

由实际测试调整。

## Debounce

Dota 聊天文字出现时可能有透明度动画。

因此第一次检测到变化后：

```text
等待约 100～180 ms
```

再执行 OCR。

防止 OCR 识别到半透明动画中的文字。

---

# 11. OCR

使用：

**PaddleOCR PP-OCRv5 Mobile Models**

重点支持：

```text
Indonesian
Malay
Tagalog
Vietnamese
Thai
English
```

这里存在两个主要文字体系：

### Latin Script

使用：

```text
latin_PP-OCRv5_mobile_rec
```

用于：

* Indonesian
* Malay
* Tagalog
* Vietnamese
* English

### Thai Script

使用：

```text
th_PP-OCRv5_mobile_rec
```

用于：

* Thai
* English

不要使用大型 server OCR 模型作为默认模型。

目标是：

**小 ROI + Mobile OCR + CPU。**

---

# 12. OCR 策略

聊天区域存在：

* 玩家名称
* 英雄/队伍颜色
* UI 阴影
* 半透明背景
* 淡入淡出
* 聊天行上下移动

因此不要假设 OCR 一次就完美。

图片预处理模块：

```text
Original ROI
   ↓
2x upscale
   ↓
grayscale / HSV candidate
   ↓
contrast enhancement
   ↓
optional sharpening
   ↓
OCR
```

至少实现三种 preprocessing preset：

```text
normal
high_contrast
light_text
```

设置页可以切换。

默认使用 normal。

不要默认强二值化，因为：

* Thai 字符细节容易损失
* Vietnamese 重音符容易损失

建议：

```python
cv2.resize(..., fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
```

然后轻微 CLAHE / contrast。

---

# 13. Latin + Thai OCR 策略

MVP 推荐：

每次 OCR 事件首先运行 Latin OCR。

如果满足任一条件：

```text
Latin OCR confidence 很低
Latin OCR 返回为空
检测到聊天区域明显变化但没有可靠文字
```

则运行 Thai OCR fallback。

更稳健版本可以：

```text
Latin OCR
Thai OCR
    ↓
比较 confidence
    ↓
选择合理结果
```

但避免每帧运行双模型。

---

# 14. OCR 行重建

PaddleOCR 返回：

```text
bounding box
text
confidence
```

需要根据 y 坐标组合聊天行。

算法：

1. 按 bounding box center_y 排序；
2. y 差小于动态阈值的归为一行；
3. 同一行按 x 排序；
4. 拼接文字。

结果：

```python
OCRLine(
    text="PlayerName: jangan pergi mid dulu",
    confidence=0.91,
    bbox=...
)
```

---

# 15. 玩家名和消息拆分

Dota 聊天通常形式类似：

```text
PlayerName: message
```

也可能出现：

```text
[Allies] PlayerName: message
```

不要翻译玩家名称。

优先：

```python
speaker, message = split_first_reasonable_colon(text)
```

如果无法可靠拆分：

```text
整句翻译
```

不要因为无法解析名字而丢弃消息。

---

# 16. 消息去重

这是另一个核心功能。

因为同一条 Dota 消息会在屏幕上停留多秒。

OCR 会反复看到：

```text
jangan pergi mid dulu
```

只能翻译和显示一次。

维护：

```python
recent_messages = deque(maxlen=100)
```

每条记录：

```python
{
    "normalized_text": ...,
    "timestamp": ...,
    "source_lang": ...
}
```

Normalize：

```text
lowercase
trim spaces
collapse repeated spaces
normalize punctuation
```

首先精确比较 hash。

然后使用 RapidFuzz 做模糊去重。

例如：

```text
jangan pergi mid dulu
jangan pergi mid dulu.
jangan pergl mid dulu
```

应该尽量识别为同一句。

建议：

```text
similarity >= 90
且
timestamp < 15 秒
```

认为重复。

具体阈值通过测试调整。

---

# 17. 新消息检测

不要把整个当前聊天框 OCR 输出作为一句翻译。

例如屏幕现在有：

```text
Player1: go rosh
Player2: jangan mid
Player3: push bot
```

下一次：

```text
Player1: go rosh
Player2: jangan mid
Player3: push bot
Player4: tunggu
```

只处理：

```text
Player4: tunggu
```

已有三条不重新翻译。

---

# 18. 语言检测

使用：

**fastText lid.176**

输入：

```text
OCR 后的 message 部分
```

不要把：

```text
PlayerName:
[Allies]
```

传进去。

支持重点：

```text
id = Indonesian
ms = Malay
tl = Tagalog
th = Thai
vi = Vietnamese
en = English
zh = Chinese
```

但短游戏聊天的语言识别天然不稳定，因此必须结合规则。

---

# 19. 语言检测规则

优先级：

## Rule 1：Unicode Script

如果包含大量 Thai Unicode：

```text
Thai
```

不依赖 fastText。

## Rule 2：中文

如果主要是 CJK：

```text
skip translation
```

## Rule 3：英语

fastText 高置信度判定：

```text
English
```

默认：

```text
skip translation
```

因为用户可以看懂英语。

设置中：

```text
Translate English
```

默认关闭。

## Rule 4：Latin SEA Languages

候选：

```text
Indonesian
Malay
Tagalog
Vietnamese
English
```

使用 fastText。

如果 confidence 很低：

仍可使用 Top-1，但在内部标记：

```text
low_confidence = true
```

不要因此丢掉消息。

---

# 20. 特殊说明：Malay 与 Indonesian

Malay 与 Indonesian 很接近。

游戏短句中：

```text
fastText 可能难以准确区分
```

这是正常现象。

不要投入大量开发时间追求完美语言分类。

翻译目标是：

> 玩家能理解队友想表达什么。

不是语言学分类。

如果 Malay / Indonesian confidence 接近：

选择最高者即可。

以后可以增加 SEA 游戏词典辅助判断。

---

# 21. 翻译架构

翻译必须设计成接口：

```python
class Translator:
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str = "zh"
    ) -> str:
        ...
```

不要把具体模型写死到业务代码。

实现：

```text
translation/
    base.py
    nllb.py
```

未来可以增加：

```text
argos.py
deepl.py
google.py
openai.py
```

但 MVP 不使用任何付费 API。

---

# 22. MVP 本地翻译模型

默认：

**facebook/nllb-200-distilled-600M**

目标语言：

```text
zho_Hans
```

语言映射：

```python
NLLB_LANG_MAP = {
    "id": "ind_Latn",
    "ms": "zsm_Latn",
    "tl": "tgl_Latn",
    "th": "tha_Thai",
    "vi": "vie_Latn",
    "en": "eng_Latn",
    "zh": "zho_Hans",
}
```

优先使用：

**CTranslate2**

而不是始终使用完整 PyTorch Transformers 推理。

原因：

* CPU inference
* int8 quantization
* 更低内存
* 更适合桌面常驻程序

默认：

```text
device = cpu
compute_type = int8
```

如果检测到 NVIDIA GPU，未来可以提供：

```text
device = cuda
compute_type = float16
```

但 GPU 不是必须设备。

---

# 23. 模型许可证提示

NLLB-200-distilled-600M：

```text
CC-BY-NC-4.0
```

因此 README 必须写：

```text
The default NLLB translation model is intended for personal,
non-commercial use in this project.

Do not assume the model license permits commercial redistribution.
Review and replace the model before any commercial release.
```

程序架构必须允许以后替换翻译模型。

---

# 24. Translation Cache

游戏聊天存在大量重复短句：

```text
go
back
wait
push
mid
don't go
jangan
tunggu
```

实现缓存：

```python
cache[(source_lang, normalized_text)] = translated_text
```

至少保留整个程序运行期间。

未来可以持久化 SQLite。

MVP 使用内存缓存即可。

---

# 25. Dota / SEA 术语保护

普通翻译模型可能把游戏术语错误翻译。

建立 glossary：

```yaml
dota_terms:
  rosh: Roshan
  roshan: Roshan
  aegis: Aegis
  mid: 中路
  bot: 下路
  top: 上路
  b: 撤
  back: 撤
  push: 推进
  gank: 抓人
  smoke: 开雾
  ward: 眼
  deward: 排眼
  tp: TP
  tormentor: 魔方
```

不要机械把所有词替换成中文。

第一版可采用：

```text
翻译前 placeholder
翻译后 restore
```

例如：

```text
Roshan → __DOTA_ROSHAN__
```

避免模型误翻专有名词。

词典单独：

```text
resources/dota_glossary.yaml
```

方便以后修改。

---

# 26. Overlay 悬浮窗

翻译结果不要覆盖原 Dota 聊天内容。

建议位置：

```text
聊天区域上方
或者
聊天区域右侧偏上
```

默认：

```text
屏幕中下偏右
```

用户应该可以拖动。

Overlay 必须：

* Always On Top
* Frameless
* Transparent background
* Mouse click-through
* 不抢键盘焦点
* 不影响 Dota 鼠标
* 不进入 Alt+Tab 主窗口列表最好
* 支持 DPI Scaling

建议 PySide6：

```text
Qt.Tool
Qt.FramelessWindowHint
Qt.WindowStaysOnTopHint
Qt.WindowTransparentForInput
```

具体组合由 Codex测试。

---

# 27. Overlay 显示效果

显示格式：

```text
[印尼] 先别去中路
[泰语] 等一下
[马来] 推下路
```

玩家名称如果可靠识别：

```text
Player123
先别去中路
```

不要显示：

```text
原文 + 中文 + language confidence + OCR confidence
```

那会太乱。

正常模式只显示中文。

Debug 模式才显示：

```text
ID 0.82 | OCR 0.91
jangan pergi mid dulu
→ 先别去中路
```

---

# 28. 消息生命周期

Overlay 最多显示：

```text
4～5 条
```

默认每条：

```text
8 秒
```

后淡出。

新消息从底部出现或顶部出现均可，但保持一致。

设置：

```yaml
overlay:
  max_messages: 5
  display_seconds: 8
  font_size: 20
  opacity: 0.88
```

---

# 29. Overlay 样式

目标：

**像字幕，不像大型应用窗口。**

例如：

```text
┌─────────────────────────────┐
│ [印尼] 先别去中路           │
│ [泰语] 等一下，我在过来     │
└─────────────────────────────┘
```

背景：

```text
半透明黑色
```

文字：

```text
白色
```

但不要硬编码主题到业务逻辑。

---

# 30. 快捷键

不要占用 Dota 常见按键。

建议：

```text
Ctrl + Alt + T = Toggle Translator
Ctrl + Alt + R = Recalibrate ROI
Ctrl + Alt + D = Debug Mode
```

允许用户修改。

不使用：

```text
F1-F12
Alt
Ctrl
Space
数字键
```

作为单独快捷键。

---

# 31. Settings

配置文件：

```text
config.yaml
```

示例：

```yaml
general:
  enabled: true
  pause_when_dota_inactive: true

capture:
  fps: 5
  change_threshold: 5.0
  debounce_ms: 150

roi:
  left: 0.20
  top: 0.58
  width: 0.60
  height: 0.27

ocr:
  upscale: 2.0
  latin_model: latin_PP-OCRv5_mobile_rec
  thai_model: th_PP-OCRv5_mobile_rec
  confidence_threshold: 0.55

language:
  skip_english: true
  skip_chinese: true

translation:
  backend: nllb
  device: cpu
  compute_type: int8
  target: zho_Hans

overlay:
  max_messages: 5
  display_seconds: 8
  font_size: 20
  opacity: 0.88

privacy:
  save_screenshots: false
  save_chat_logs: false

debug:
  enabled: false
```

---

# 32. Privacy

默认：

```text
不保存截图
不保存聊天记录
不上传屏幕
不上传 OCR 文本
```

所有：

```text
Screenshot
OCR
Language ID
Translation
```

均本地完成。

Debug Mode 开启以后才允许：

```text
保存 ROI screenshot
保存 OCR output
```

而且明确提示：

```text
Debug mode may save chat screenshots locally.
```

---

# 33. 推荐项目结构

```text
dota-sea-translator/
│
├─ README.md
├─ LICENSE
├─ requirements.txt
├─ config.example.yaml
├─ run.bat
│
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ config.py
│  ├─ logging_config.py
│  │
│  ├─ capture/
│  │  ├─ __init__.py
│  │  ├─ screen_capture.py
│  │  ├─ dota_window.py
│  │  ├─ roi.py
│  │  └─ change_detector.py
│  │
│  ├─ ocr/
│  │  ├─ __init__.py
│  │  ├─ base.py
│  │  ├─ paddle_backend.py
│  │  ├─ preprocessing.py
│  │  └─ line_reconstruction.py
│  │
│  ├─ language/
│  │  ├─ __init__.py
│  │  ├─ detector.py
│  │  └─ language_codes.py
│  │
│  ├─ translation/
│  │  ├─ __init__.py
│  │  ├─ base.py
│  │  ├─ nllb.py
│  │  ├─ cache.py
│  │  └─ glossary.py
│  │
│  ├─ messages/
│  │  ├─ parser.py
│  │  ├─ normalizer.py
│  │  └─ deduplicator.py
│  │
│  └─ ui/
│     ├─ overlay.py
│     ├─ calibrator.py
│     ├─ settings.py
│     └─ tray.py
│
├─ resources/
│  ├─ dota_glossary.yaml
│  └─ languages.yaml
│
├─ scripts/
│  ├─ download_models.py
│  └─ benchmark.py
│
└─ tests/
   ├─ test_change_detector.py
   ├─ test_message_parser.py
   ├─ test_deduplicator.py
   ├─ test_language_detector.py
   └─ fixtures/
```

---

# 34. 多线程架构

绝对不要在 Qt UI Thread 中运行：

```text
OCR
NLLB
```

线程结构建议：

```text
UI Thread
    │
    ├── Overlay
    ├── Tray
    └── Settings

Capture Worker
    │
    └── Frame Change Detection

OCR Worker
    │
    └── PaddleOCR

Translation Worker
    │
    └── NLLB
```

使用 Queue：

```text
capture_queue
ocr_queue
translation_queue
overlay_queue
```

Queue 必须有限长度。

例如：

```text
maxsize = 2～5
```

如果积压：

```text
丢掉旧截图
保留最新截图
```

游戏翻译没有必要处理两秒以前过时的 frame。

---

# 35. 性能原则

性能目标：

正常没有聊天时：

```text
CPU 使用应非常低
```

原因：

只执行：

```text
ROI screenshot
downscale
image diff
```

出现新聊天才：

```text
OCR
Language Detection
Translation
```

禁止：

```text
每 200ms 跑 NLLB
```

Translation 必须严格由“新消息事件”触发。

---

# 36. 模型懒加载

程序启动时：

```text
不要立即把所有模型加载到 RAM
```

建议：

```text
OCR 模型启动后初始化

Translation 模型第一次真正需要翻译
或者
后台低优先级初始化
```

但不能因此冻结 UI。

显示：

```text
Loading translation model...
```

首次初始化成功后：

```text
Translator Ready
```

---

# 37. 模型下载

制作：

```text
scripts/download_models.py
```

首次运行检测：

```text
models/
```

不存在则提示：

```text
Required local AI models are not installed.

[Download Models]
```

下载完成后：

```text
以后可离线运行
```

不得要求：

```text
OpenAI API Key
Google API Key
DeepL API Key
```

MVP 全本地。

---

# 38. 网络策略

运行时默认：

```text
不需要网络
```

只有首次：

```text
下载模型
```

才访问网络。

设置中提供：

```text
Offline Mode
```

开启后禁止程序主动联网。

---

# 39. 错误处理

任何 AI 模块失败都不能让整个应用崩溃。

例如：

```text
OCR failed
```

记录错误，不显示。

```text
Language detection failed
```

fallback 到 unknown。

```text
Translation failed
```

不显示该条或显示原文。

```text
Dota window unavailable
```

暂停。

```text
ROI invalid
```

提示重新 Calibration。

---

# 40. Logging

默认只记录：

```text
application start
model load
errors
performance
```

不记录聊天正文。

例如：

```text
OCR event: 182ms
Translation event: 420ms
New messages: 2
```

而不是：

```text
Player123 said xxxx
```

Debug Mode 才允许详细记录。

---

# 41. 开发阶段

请严格分阶段，不要一次把所有东西堆在一起。

## Phase 1：Screen Capture Prototype

完成：

```text
Dota 窗口识别
ROI Calibration
ROI Screenshot
Change Detection
```

暂时不要 OCR。

提供：

```text
debug ROI preview
```

验收：

聊天出现时 console：

```text
CHAT REGION CHANGED
```

聊天没有变化时不不断触发。

---

## Phase 2：OCR Prototype

加入 PaddleOCR。

Console 输出：

```text
OCR:
Player123: jangan pergi mid dulu
```

确保：

* Latin chat 能识别
* Vietnamese accents 不严重丢失
* Thai 能识别

创建：

```text
Test OCR
```

让用户可以在实际 Dota 截图上调参数。

---

## Phase 3：Message Dedup

实现：

```text
line reconstruction
message parser
normalizer
deduplicator
```

验收：

一条消息在屏幕停留 8 秒：

```text
只产生一次 NewMessage event
```

---

## Phase 4：Language Detection

加入 fastText。

输出：

```text
[id 0.81] jangan pergi mid dulu
[th 0.99] อย่าไปคนเดียว
```

英文：

```text
skip
```

中文：

```text
skip
```

---

## Phase 5：Translation

加入：

```text
NLLB
CTranslate2
```

输出：

```text
[id]
jangan pergi mid dulu
→ 先别去中路
```

---

## Phase 6：Overlay

实现透明悬浮字幕。

验收：

* 不抢 Dota 焦点
* 鼠标可以穿透
* 不影响点击
* 始终位于游戏上层
* 用户可调整位置

---

## Phase 7：Optimization

测量：

```text
Capture latency
OCR latency
Language ID latency
Translation latency
Total latency
```

提供：

```text
scripts/benchmark.py
```

输出例如：

```text
Capture:       2.3 ms
ChangeDetect:  0.8 ms
OCR:         145.2 ms
LangDetect:    1.7 ms
Translation: 380.4 ms
Total:       530.4 ms
```

不要伪造 benchmark。

使用真实机器测量。

---

# 42. MVP 验收标准

必须满足以下条件才算 MVP 完成。

## 功能

### 1

启动程序后不需要每条聊天手动按快捷键。

### 2

用户可以框选 Dota 中下聊天区域。

### 3

聊天出现新内容后自动 OCR。

### 4

已出现过的聊天不会持续重复翻译。

### 5

支持至少：

```text
Indonesian
Malay
Tagalog
Vietnamese
Thai
```

### 6

自动翻译成简体中文。

### 7

英文默认不翻译。

### 8

中文默认不翻译。

### 9

结果自动显示在透明 Overlay。

### 10

Dota 不在前台时自动暂停。

---

# 43. 安全验收

代码仓库搜索不得出现用于 Dota 的：

```text
ReadProcessMemory
WriteProcessMemory
CreateRemoteThread
DLL injection
memory offsets
entity list
game state reader
packet sniffing
input automation
```

如果第三方 dependency 内部存在 Windows API 不算此规则。

本项目自己的业务代码不得使用这些技术与 Dota 交互。

---

# 44. 性能验收

目标，不作为绝对硬限制：

### Idle

没有聊天变化时：

```text
CPU 尽量 < 3～5%
```

### Memory

尽量避免无意义复制大模型。

### Latency

出现聊天至显示翻译：

```text
目标 < 1.5 秒
```

可以接受普通 CPU 第一次模型加载更慢。

模型加载完成后的正常聊天翻译应尽量：

```text
< 1 秒
```

如果 CPU 无法达到，不牺牲稳定性强求。

---

# 45. 防重复特别测试

必须制作单元测试：

输入时间序列：

```text
0s:
A: jangan mid

1s:
A: jangan mid

2s:
A: jangan mid

3s:
A: jangan mid
B: tunggu

4s:
A: jangan mid
B: tunggu
```

预期事件：

```text
0s → jangan mid
3s → tunggu
```

不能：

```text
每秒产生 jangan mid
```

---

# 46. OCR 错误模糊去重测试

输入：

```text
jangan pergi mid dulu
jangan pergl mid dulu
jangan pergi mid dulu.
```

在短时间窗口内：

```text
尽量视为同一句
```

避免 OCR 微小变化造成重复翻译。

---

# 47. 实际 Dota 测试素材

项目应建立：

```text
tests/fixtures/dota_chat/
```

不要把真实玩家私人聊天长期放进公开仓库。

可以使用人工生成测试图：

```text
FakePlayer1: jangan mid
FakePlayer2: tunggu
FakePlayer3: jangan pergi sendiri
```

Thai 测试：

```text
FakePlayer4: อย่าไปคนเดียว
```

Vietnamese：

```text
FakePlayer5: đừng đi một mình
```

---

# 48. 游戏黑话问题

翻译模型遇到 Dota SEA 聊天时可能遇到：

```text
拼写错误
缩写
英文夹 Indonesian
Malay + English
Tagalog + English
脏话
Dota terminology
```

目标不是产生文学翻译。

目标是：

```text
快速、足够准确地告诉用户队友想干什么。
```

因此翻译风格优先：

```text
简短
口语
保持游戏术语
```

不需要：

```text
正式书面中文
```

---

# 49. 第二阶段可以开发但 MVP 不做

以下功能明确放到 Future，不要阻塞 MVP：

### A. 双向翻译

```text
中文输入
→ Indonesian / Malay / English
```

但不自动发送 Dota。

只允许：

```text
复制到剪贴板
```

### B. SEA 游戏术语词典学习

### C. 用户自定义词典

### D. 多显示器自动识别

### E. OCR 自动寻找聊天框

### F. 在线翻译 Backend

### G. GPU 加速

### H. Windows Installer

---

# 50. 明确不开发

永远不开发：

```text
自动读取敌方信息
自动读英雄数据
自动读技能 CD
自动判断游戏状态
自动读取物品
自动分析敌方位置
自动 ping
自动聊天
自动回复
自动点击
自动控制英雄
```

这个项目始终只是：

**“屏幕上已经显示出来的文字 → 中文字幕。”**

---

# 51. README 必须说明

README 首页明确写：

```text
Dota SEA Chat Translator is an independent accessibility/
translation utility.

It only captures a user-selected region of visible screen pixels.

It does not read Dota 2 process memory, inject DLLs,
modify game files, inspect network packets, or automate input.

Dota 2 and related trademarks belong to Valve Corporation.
This project is not affiliated with or endorsed by Valve.
```

同时注明：

```text
Use third-party software at your own discretion.
No software can guarantee how future anti-cheat policies
or implementations may change.
```

不要宣传：

```text
100% VAC Safe
```

因为无法做这种保证。

应该说：

```text
Designed to minimize anti-cheat interaction by remaining
a screen-only OCR application.
```

---

# 52. 第一轮 Codex 交付要求

第一轮不要追求 EXE 打包。

先提供源码运行版本。

Codex 第一轮需要完成：

```text
1. 创建完整项目结构
2. requirements / dependency setup
3. run.bat
4. PySide6 tray
5. Dota foreground detection
6. ROI calibration
7. mss region capture
8. image change detection
9. PaddleOCR
10. console 输出新 OCR 行
11. message dedupe
12. 基础测试
```

第一轮暂时可以不完成 NLLB Overlay。

先证明：

> Dota 聊天出现 → 自动可靠地产生一次新的 OCR 消息事件。

这是整个项目最关键的技术验证。

---

# 53. 第二轮 Codex 交付要求

在 Phase 1 稳定以后：

```text
1. fastText Language Detection
2. NLLB / CTranslate2
3. Translation Cache
4. Dota Glossary
5. PySide6 Overlay
6. Settings
7. Model Downloader
8. Performance benchmark
```

---

# 54. 开发原则

请 Codex 遵循：

```text
KISS
```

优先：

```text
稳定
可调试
模块化
低延迟
低资源
```

其次才是：

```text
漂亮 UI
安装包
复杂配置
```

不要：

```text
过度设计
微服务
HTTP server
数据库服务
Docker
Web frontend
Electron
```

这是 Windows 单机游戏翻译工具。

---

# 55. Codex 开始开发时的具体指令

请从 Phase 1 开始实际创建代码，而不是只继续输出设计文档。

开发流程：

1. 初始化项目。
2. 创建虚拟环境说明。
3. 创建 requirements。
4. 实现 Windows 前台 Dota 检测。
5. 实现 ROI Calibration。
6. 实现 ROI Capture。
7. 实现 Change Detector。
8. 创建 Debug Preview。
9. 添加单元测试。
10. 给出运行方法。

每完成一个 Phase：

```text
运行测试
修复明显错误
再进入下一阶段
```

不要一次生成几千行未经运行的代码。

如果某个第三方库 API 与本规格中的示例发生版本变化：

```text
以当前官方 API 为准
```

但不得改变以下架构原则：

```text
Screen Pixels Only
No Dota Memory Access
No Injection
No Input Automation
Local-first Translation
Event-driven OCR
Message Deduplication
```

---

# 56. 最终产品体验

用户期望最终流程：

```text
第一次使用
    ↓
安装程序
    ↓
下载本地 OCR / Translation 模型
    ↓
启动 Dota
    ↓
点击 Calibrate
    ↓
框选屏幕中下聊天区
    ↓
开始游戏
```

之后：

```text
SEA 玩家发送本地语言
          ↓
无需用户按键
          ↓
约 0.5～1.5 秒
          ↓
中文翻译字幕自动出现
```

整个过程中：

```text
不需要额外设备
不需要手机
不需要第二台电脑
不需要 API Key
不需要付费订阅
正常运行不需要互联网
```

这就是项目 MVP 的最终目标。
