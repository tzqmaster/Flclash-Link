# Flclash-Link

FlClash / mihomo 的**覆写脚本仓库**。只放规则和策略组，**不放任何节点、UUID、订阅地址**——节点走你自己的机场订阅。

## 链接一览（按设备选）

| 设备 | 用什么 | 链接 |
| --- | --- | --- |
| **电脑 / 安卓（FlClash）** | 覆写脚本 `main.js` | `https://raw.githubusercontent.com/tzqmaster/Flclash-Link/main/main.js` |
| **iPhone（小火箭 Shadowrocket）** | 规则配置 `.conf` | `https://raw.githubusercontent.com/tzqmaster/Flclash-Link/main/shadowrocket/Shadowrocket.conf` |
| **iPhone（ClashMi / Karing / Stash）** | 完整 yaml，**本仓库不托管** | 本地跑 `tools/make_ios_yaml.py` 生成后 AirDrop 到手机 |

raw 被墙时换 jsDelivr 镜像：把 `https://raw.githubusercontent.com/tzqmaster/Flclash-Link/main/` 换成 `https://cdn.jsdelivr.net/gh/tzqmaster/Flclash-Link@main/`。

⚠️ **两条链接不能互换**：`main.js` 是 JS 覆写脚本，只有 FlClash 认（FlClash 无 iOS 版，官方只发 Win/macOS/Linux/Android），iOS 客户端把它当订阅填进去必然解析失败。

⚠️ **iOS 的 Clash 系客户端（ClashMi / Karing / Stash）只吃「含节点的完整 yaml」**，而本仓库是公开的、且带 pre-commit 凭据拦截（`server:` / `uuid:` / 订阅地址一律拒绝入库）。所以 iOS 版走「本地生成 + 文件导入」，不托管在仓库里——避免把 53 个节点凭据公开。

```bash
# 在 Mac 上生成 iOS 版（会从当前 FlClash 配置里带出节点）
python3 tools/make_ios_yaml.py ~/Library/Application\ Support/com.follow.clash/config.yaml Clash-iOS.yaml
```

## 这个仓库解决什么

机场订阅自带的规则通常只有 100 多条，`reddit`、`wikipedia`、`discord`、`steam`、`facebook`、`linkedin`、`bbc` 这类常见站点经常没有规则，直接掉进「兜底直连」，国内直连必然打不开。

本仓库的 `main.js` 会在拉取订阅后自动做四件事：

1. 剔除伪节点（`剩余流量：xxx`、`套餐到期：xxx`，这类节点测速能过、会被误选）
2. 重建 **28 个策略组**（6 个地区线路组 + 10 个区域优选 / 专线组 + AI / Google / Telegram / 开发 / 流媒体 / 未匹配 等场景组）
3. 覆盖 **861 条规则**（Apple 直连 + 7 个 geosite 大类 + 62 个单站 + 600+ 条域名后缀）
4. 兜底改为**走代理**，国内域名由 `GEOSITE,cn` / `.cn` / `GEOIP,cn` 三层拦回直连

## 策略组怎么选（两层：场景 → 线路 → 节点）

每个场景组（🚀 节点选择 / 🎯 Google / 🐙 开发 / 🐦 X / ✈️ Telegram / 📺 流媒体 / 🌐 未匹配）都内置了 6 个**线路组**，选择路径是「先定场景走哪条线，再定这条线上哪个节点」：

| 线路组        | 内容                 | 适合场景                |
| ---------- | ------------------ | ------------------- |
| 🇭🇰 香港线路  | 香港优选（自动）+ 9 个香港节点  | 默认、GitHub / 开发、网页浏览 |
| 🇯🇵 日本线路  | 日本优选（自动）+ 15 个日本节点 | AI、YouTube、需要日区 IP  |
| 🇸🇬 新加坡线路 | 新加坡优选（自动）+ 12 个节点  | 备用、东南亚解锁            |
| 🇺🇸 美国线路  | 美国优选（自动）+ 12 个节点   | 流媒体、需要美区 IP         |
| 🇬🇧 英国线路  | 英国优选（自动）+ 4 个节点    | 英区内容                |
| 🇨🇳 台湾线路  | 台湾专线（自动）+ 1 个节点    | 中文区低延迟              |

- 每组第一项是该地区的**自动优选项**，默认不折腾就选它（会自动避开死节点）。
- 想固定某个节点，展开线路组直接点具体节点名即可。
- `🧪 节点测速` 组永远列出全部节点，用来手动逐个测延迟。

## 文件

```
main.js                      覆写脚本（贴进 FlClash，或用 raw 链接）
shadowrocket/Shadowrocket.conf  iOS 小火箭（Shadowrocket）用的规则配置
rules/规则库覆盖清单.csv      771 条规则覆盖了哪些站，逐条可查
docs/配置改动说明.md          完整的改动记录、实测数据、回滚方法
docs/手机使用说明.md          手机端（安卓 / iPhone）配置方法
tools/gen_override_js.py      从一份已调优的 yaml 反向生成 main.js
tools/make_ios_yaml.py         从同一份 yaml 生成 iOS 客户端可导入的精简 yaml（含节点，勿公开）
tools/gen_shadowrocket.py     从同一份 yaml 生成小火箭 .conf（含 GEOSITE 展开）
tools/expand_rules.py         规则库扩容脚本（幂等，可反复执行）
```

## 怎么用

**方式一：贴到 App 里（最稳）**

FlClash → 配置 → 选中订阅 → 右上角「脚本」→ 把 `main.js` 全文粘进去 → 保存 → 重新拉取订阅。

**方式二：填 raw 链接（可自动更新）**

```
https://raw.githubusercontent.com/tzqmaster/Flclash-Link/main/main.js
```

填到脚本的 URL 栏。以后本仓库更新，设备重新拉订阅时自动用新版，不用再动。

**节点怎么来**：FlClash → 配置 → `+` → 从 URL 导入 → 填你自己的机场订阅链接。节点由机场维护，UUID 轮换也不影响。

## ⚠️ iOS 不能用 main.js（重要）

`main.js` 是 **FlClash 的覆写脚本（JavaScript）**，raw 链接返回的是 `text/plain` 的 JS 源码。
FlClash 官方**没有 iOS 版**（只发 Windows / macOS / Linux / Android），所以 iPhone 上任何客户端
（ClashMi / Karing / Stash / ClashX）把它填进「订阅 / 配置 URL」都会解析失败——客户端要的是 YAML，拿到的是 JS。

iPhone 三条可行路线：

| 路线 | 客户端 | 用什么 | 说明 |
| --- | --- | --- | --- |
| A | 小火箭 Shadowrocket | 本仓库 `shadowrocket/Shadowrocket.conf` | 规则已转好，见下一节 |
| B | ClashMi / Karing / Stash | **一份 yaml**（本仓库不放，因为含节点凭据） | 用 `tools/make_ios_yaml.py` 从已调优的 yaml 生成后 AirDrop 到手机 |
| C | 任意 iOS 客户端 | 直接导入机场订阅 | 节点自动更新，但规则退回机场默认（100~500 条，很多站没有规则） |

生成 iOS 版 yaml：

```bash
python3 tools/make_ios_yaml.py ~/Library/Application\ Support/com.follow.clash/config.yaml Clash-iOS.yaml
# 先用真实内核校验（可选）
mihomo -t -f Clash-iOS.yaml -d /tmp/mihomo_check
```

## iOS 小火箭（Shadowrocket）

小火箭不认 `main.js`，也不支持 `GEOSITE`，所以单独提供一份转好的规则配置：

```
https://raw.githubusercontent.com/tzqmaster/Flclash-Link/main/shadowrocket/Shadowrocket.conf
```

导入步骤：**首页右上「+」→ Subscribe → 填机场订阅链接**（先拿到节点）→ **底部「配置」→ 右上「+」→ URL → 粘贴上面这行** → 下载后点一下启用。

差异说明：

- Clash 的 861 条规则在这里转成 2320 条小火箭规则。`GEOSITE` 用 `GEOSITE.dat` 反解析成真实域名，规则库里国内域名已剔除，不会把 B 站 / 爱奇艺送进代理。
- 小火箭没有多策略组引用，`🚀节点选择 / 📺流媒体 / 🤖AI / 🐙开发 / 🎯Google` 全部折叠成 `PROXY`（即首页当前选中的节点），另保留 `DIRECT` / `REJECT`。
- 兜底顺序：私网 → 国内大站直连 → 国外显式规则 → `GEOIP,CN,DIRECT` → `FINAL,PROXY`。
- 文件头带 `#!MANAGED-CONFIG ... interval=86400`，小火箭会每天自动拉一次，仓库更新后设备自动生效。

> 节点仍然只来自机场订阅。这份 `.conf` 只改规则，不含任何节点或凭据。

## 更新规则

```bash
# 改完 rules 或策略组后重新生成
python3 tools/gen_override_js.py <已调优的 yaml> main.js
```

脚本会自动备份、替换，重复执行不会叠加。

## 实测：规则多了会不会卡

| 规则数    | 启动就绪   | 常驻内存   | 请求耗时中位（n=15） |
| ------ | ------ | ------ | ------------ |
| 140    | 0.22 s | 157 MB | 58.6 ms      |
| 771    | 0.47 s | 155 MB | 58.9 ms      |
| 10,140 | 0.31 s | 145 MB | —            |

`DOMAIN-SUFFIX` / `GEOSITE` / `IP-CIDR` 都走字典树，匹配成本只跟域名长度有关，跟规则条数无关。真正会卡的三种写法（`GEOIP` 不写 `no-resolve`、大量 `DOMAIN-KEYWORD`、`RULE-SET` 远程订阅）本仓库一条都没用。

## 注意

- 本仓库**不含任何节点或凭据**，克隆下来也无法直接上网，必须配合自己的订阅。
- 兜底默认走代理；想临时全局直连，在面板把「🌐 未匹配」切成 `DIRECT`。
- iPhone 用不了 FlClash（无 iOS 版），需换 Stash / Karing，详见 `docs/手机使用说明.md`。
