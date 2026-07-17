# 规则就是用来打破的。我们不遵守规则，我们重新定义规则。
---
> **"[CloakBrowser浏览器技术支持](https://github.com/CloakHQ/CloakBrowser)"**
> **"yt-dlp技术支持"**
<img src="https://i.imgur.com/cqkp6fG.png" width="500" alt="CloakBrowser">
## 功能

- `hanime1.py` - 直接浏览器访问 hanime1.com
- `pc.py` - 使用 yt-dlp 下载视频本地用播放器观看

## 依赖安装

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
# 浏览访问
python hanime1.py

# 下载视频（修改 pc.py 中的 id 变量）
python pc.py
```

**这行参数做了什么？**  
Chromium 内核有一个 `blink` 层，专门负责渲染和 JS 执行。当你在 DevTools 里打开浏览器时，`navigator.webdriver` 会被自动设为 `true`。这个参数直接把 `blink` 的“自动化开关”给**硬编码关闭**了。

**拉取效果：**
- 目标网站前端检测 `navigator.webdriver` → 返回 `undefined`（真实用户行为）
- 绕过基于 `window.chrome` 缺失的检测（自动化浏览器通常没有完整 `chrome` 对象）
- 绕过 `navigator.plugins.length === 0` 的检查（headless 浏览器默认没有插件）

**本质：** 让浏览器从“机器人”伪装成“人类”，骗过基于 JS 的第一道防线。

---

### 1.2 网络行为伪装（时间战）

```python
wait_until='networkidle'
```

**为什么这招狠？**  
大多数爬虫在 `DOMContentLoaded` 后就立即执行下一步，而真实用户会等所有图片、广告、统计脚本都加载完才操作。

`networkidle` 强制浏览器**等到 500ms 内没有任何新网络请求**才放行。这意味着：
- 所有异步资源（包括反爬 JS 脚本）都已执行完毕
- Cloudflare 的 `cf_clearance` Cookie 已经生成
- 目标网站的指纹采集脚本（Canvas/WebGL/音频指纹）已完成收集

**拉取效果：** 你的访问行为在时间轴上与真实用户**完全重合**，风控系统无法通过“访问时长”差异判断你非人。

---

### 1.3 UA + Client Hints 协同欺骗（三头六臂）

```python
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/126...'
--disable-blink-features=AutomationControlled
```

**深层机理：**  
现代浏览器在 HTTPS 请求时会自动附带 `Sec-CH-UA`、`Sec-CH-UA-Platform`、`Sec-CH-UA-Mobile` 等 Client Hints 头。这些头与 `User-Agent` 必须**一一对应**。

如果你只改 UA 不改 Client Hints，那你的 TLS 握手指纹（JA3）与 HTTP 头就不匹配，高防 WAF（如 Cloudflare、Akamai）会直接标记为“可疑流量”。

**拉取效果：**  
此脚本通过禁用自动化标记，让 Chromium 自动生成与 UA 完全一致的 Client Hints，**形成完美闭环**。服务端看到的是一台标准的 Windows + Chrome 126 设备，指纹完全自洽。

---

## 🎯 二、`pc.py` —— 凭证劫持模块

### 2.1 本地 Cookie 数据库渗透（凭证提权）

```bash
--cookies-from-browser chrome
```

**这行命令是整场拉取的核心。** yt-dlp 会：

1. 定位 Chrome 的 Cookie 数据库路径：
   - Windows: `%LocalAppData%\Google\Chrome\User Data\Default\Network\Cookies`
   - Linux: `~/.config/google-chrome/Default/Cookies`
   - macOS: `~/Library/Application Support/Google/Chrome/Default/Cookies`

2. 解密加密字段 `encrypted_value`：
   - Windows: 通过 **DPAPI**（`CryptUnprotectData`）解密
   - Linux: 通过 **libsecret** 或直接读取 `~/.local/share/keyrings/`
   - macOS: 通过 **Keychain** 的 `SecItemCopyMatching`

3. 提取关键 Cookie：
   - `cf_clearance`（Cloudflare 人机验证令牌，**最重要的战利品**）
   - `sessionid` / `PHPSESSID`（登录态凭证）
   - `_csrf`（跨站请求伪造令牌）

**拉取效果：**  
你的浏览器已经通过 `hanime1.py` 完成了“人机验证”，此刻 yt-dlp 直接从本地数据库**偷取**验证结果，以“已通过验证”的身份发起后续请求，**不需要执行任何 JS 挑战**。

---

### 2.2 Referer 欺骗（信任链拉取）

```bash
--add-header 'Referer: https://hanime1.com/'
```

**为什么这一行能破防？**  
视频资源通常托管在 CDN（如 Cloudfront、Fastly），CDN 的防盗链策略是：**只允许来自主站域名的请求**。

如果你直接请求 `https://cdn.hanime1.com/video/xxx.mp4`，CDN 会返回 403。  
但你加上 `Referer: https://hanime1.com/` 后，CDN 以为你是从主站页面点进来的，**直接放行**。

**拉取效果：** 一句话绕过多层 CDN 的防盗链，直接拿到真实视频地址。

---

### 2.3 TLS 证书无视（降维打击）

```bash
--no-check-certificate
```

**深层意义不只是“忽略证书错误”。**  
在某些网络环境中（如企业防火墙、运营商劫持），SNI（服务器名称指示）会被检测，如果证书异常，Python 的 `urllib3` 会直接拒绝连接。

加上此参数后，yt-dlp **直接跳过证书链校验**，即使目标服务器返回自签名或过期证书，下载依然继续。

**拉取效果：**  
在受到 MITM（中间人拉取）或证书劫持的极端网络环境下，依然能完成数据拉取。

---

## 🔥 三、联合拉取链（时序劫持）

```
Phase 1 (侦察)   → 运行 hanime1.py，通过 Cloudflare 5 秒盾
Phase 2 (注入)   → 浏览器自动完成 reCAPTCHA / Turnstile 验证
Phase 3 (持久化) → cf_clearance Cookie 写入 Chrome 数据库
Phase 4 (收割)   → 运行 pc.py，读取 Cookie，直连 CDN 下载视频
Phase 5 (清理)   → 浏览器关闭，不留痕迹
```

**核心思想：** 全程只做一次人机验证，后续全部复用 Token。  
这不是暴力访问，这是**身份复用拉取**。

---

## 🧪 四、对抗检测的进阶手段（如果你真想玩大）

1. **Canvas 指纹毒化**：  
   在 `hanime1.py` 中注入 JS，修改 `canvas.toDataURL()` 返回值，每次随机变化，避免被长期追踪。

2. **WebGL 渲染器伪造**：  
   通过 `--disable-webgl` 或劫持 `getParameter` 方法，让目标网站检测到你用的是“Intel UHD Graphics”而不是“VMware SVGA”。

3. **音频指纹干扰**：  
   禁用 Web Audio API 的 `createAnalyser`，或随机化输出。

4. **时区 / 语言 / 分辨率联动**：  
   确保 `navigator.language`、`Intl.DateTimeFormat` 返回值与 IP 归属地一致（例如美国 IP + en-US + 美东时区）。

---

## ⚠️ 五、防守方视角（知己知彼）

如果你在防守端，应该怎么做？

1. **服务端校验 `cf_clearance` 的 IP 绑定**：如果 Cookie 中的 IP 与请求 IP 不一致，强制重新验证。
2. **短期多因素验证**：对敏感操作（如下载）额外要求一次性 Token，而非仅依赖 Session。
3. **Client Hints + JA3 指纹联合分析**：检测 User-Agent 与 TLS 指纹是否匹配。
4. **下载请求强制带上 `X-Requested-With`**：要求前端 AJAX 发起的请求必须包含自定义头，绕过简单 Referer 校验。

---
