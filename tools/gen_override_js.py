#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从当前 FlClash profile 生成"覆写脚本 main.js"
—— 保证脚本产出的策略组/规则与现在正在跑的配置完全一致
用法: python gen_override_js.py [profile路径] [输出路径]
"""
import sys, json, re, yaml, datetime

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    '/Users/zaiquantao/Library/Application Support/com.follow.clash/profiles/368389100727701504.yaml'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'main.js'

d = yaml.safe_load(open(SRC, encoding='utf-8'))
rules = d['rules']
groups = d['proxy-groups']

TEST = dict(url="http://cp.cloudflare.com/generate_204", interval=300, lazy=False,
            timeout=8000, **{'expected-status': 204, 'max-failed-times': 3})
URLTEST = dict(TEST, tolerance=50)

# 区域组用正则动态取节点（抗改名/换批），其余组按原样引用
REGION = {
    '🇭🇰 香港优选':   ('url-test', r'🇭🇰', URLTEST),
    '🇯🇵 日本优选':   ('url-test', r'🇯🇵', URLTEST),
    '🇯🇵 日本稳定':   ('fallback', r'🇯🇵', TEST),
    '🇸🇬 新加坡优选':  ('url-test', r'🇸🇬', URLTEST),
    '🇺🇸 美国优选':   ('url-test', r'🇺🇸', URLTEST),
    '🇬🇧 英国优选':   ('url-test', r'🇬🇧', URLTEST),
    '🇯🇵 日本专线':   ('url-test', r'🇯🇵.*专线', URLTEST),
    '🇸🇬 新加坡专线':  ('url-test', r'🇸🇬.*专线', URLTEST),
    '🇭🇰 香港专线':   ('url-test', r'🇭🇰.*专线', URLTEST),
    '🇺🇸 美国流媒体':  ('url-test', r'🇺🇸.*流媒体', URLTEST),
    '🇨🇳 台湾专线':   ('url-test', r'台湾.*专线', URLTEST),
}
ALL = ('url-test', None, URLTEST)
ALL_FB = ('fallback', None, TEST)

def js(v):
    return json.dumps(v, ensure_ascii=False)

lines = []
for g in groups:
    name = g['name']
    if name in REGION:
        typ, pat, opts = REGION[name]
        lines.append(f"  grp({js(name)}, '{typ}', pick(/{pat}/), {js(opts)});")
    elif name in ('♻️ 自动选择',):
        lines.append(f"  grp({js(name)}, 'url-test', names, {js(URLTEST)});")
    elif name in ('🛡️ 故障转移',):
        lines.append(f"  grp({js(name)}, 'fallback', names, {js(TEST)});")
    else:
        mem = [m for m in g.get('proxies', []) if m != '__NODES__']
        extra = {}
        if g.get('include-all-proxies'):
            extra['include-all-proxies'] = True
        lines.append(f"  grp({js(name)}, {js(g['type'])}, {js(mem)}"
                     + (f", {js(extra)}" if extra else "") + ");")

groups_js = "\n".join(lines)
rules_js = "\n".join("  " + js(r) + "," for r in rules)
today = datetime.date.today().isoformat()

js_src = f"""// =====================================================================
//  FlClash / mihomo 覆写脚本（由已调优配置自动生成）
//  生成日期: {today}
//  作用: 剔除伪节点 → 重建 {len(groups)} 个策略组 → 覆盖 {len(rules)} 条规则 → Apple 直连
//
//  用法一（推荐，永久生效）: FlClash → 配置 → 选中订阅 → 右上角「脚本」
//                         → 粘贴本文件全文 → 保存 → 重新拉取订阅
//  用法二: 放进仓库，用 raw 链接填到脚本的 URL 栏
//
//  设计要点:
//   1. 区域组用正则从实际节点里挑（换节点/改名都不会失效）
//   2. 规则整段覆盖，不依赖机场订阅自带的规则
//   3. 兜底 = 走代理；国内由 GEOSITE,cn / .cn / GEOIP,cn 三层拦回直连
// =====================================================================

function main(config) {{
  // ---------- 1. 剔除伪节点（"剩余流量""套餐到期"这类，会被测速误选）----------
  const FAKE = /剩余流量|套餐到期|官网|过期|重置/;
  const proxies = (config.proxies || []).filter(p => p && p.name && !FAKE.test(p.name));
  config.proxies = proxies;
  const names = proxies.map(p => p.name);
  const pick = re => names.filter(n => re.test(n));

  // ---------- 2. 重建策略组 ----------
  const groups = [];
  function grp(name, type, members, extra) {{
    const g = {{ name, type, proxies: members }};
    if (extra) Object.assign(g, extra);
    // 空组会让内核报错，兜底挂第一个节点或 DIRECT
    if (!g.proxies.length) g.proxies = names.length ? [names[0]] : ['DIRECT'];
    groups.push(g);
  }}

{groups_js}

  config['proxy-groups'] = groups;

  // ---------- 3. 覆盖规则 ----------
  config.rules = RULES;

  // ---------- 4. Apple 直连补丁（DNS 侧）----------
  if (config.dns) {{
    const apple = ['*.apple.com', '*.icloud.com', '*.mzstatic.com', '*.aaplimg.com',
                   '*.cdn-apple.com', '*.icloud-content.com', '*.itunes.com', '*.me.com'];
    config.dns['fake-ip-filter'] = Array.from(new Set(
      (config.dns['fake-ip-filter'] || []).concat(apple)));
  }}

  return config;
}}

// ---------- 规则表（{len(rules)} 条）----------
const RULES = [
{rules_js}
];
"""

open(OUT, 'w', encoding='utf-8').write(js_src)
print(f'已生成 {OUT}: {len(js_src)/1024:.1f} KB | 组 {len(groups)} | 规则 {len(rules)}')
