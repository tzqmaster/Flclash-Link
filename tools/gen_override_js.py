#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从一份已调优的 FlClash / mihomo 配置反向生成覆写脚本 main.js
—— 保证脚本产出的策略组/规则与那份配置完全一致

用法:
  python gen_override_js.py [profile路径] [输出路径]
"""
import sys, json, yaml, datetime

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    '/Users/zaiquantao/Library/Application Support/com.follow.clash/profiles/368389100727701504.yaml'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'main.js'

d = yaml.safe_load(open(SRC, encoding='utf-8'))
rules = d['rules']
groups = d['proxy-groups']

TEST = {"url": "http://cp.cloudflare.com/generate_204", "interval": 300, "lazy": False,
        "timeout": 8000, "expected-status": 204, "max-failed-times": 3}
URLTEST = dict(TEST, tolerance=50)

# 区域组：用正则从实际节点里挑，换节点 / 改名都不会失效
REGION = {
    '🇭🇰 香港优选':  ('url-test', r'🇭🇰', URLTEST),
    '🇯🇵 日本优选':  ('url-test', r'🇯🇵', URLTEST),
    '🇯🇵 日本稳定':  ('fallback', r'🇯🇵', TEST),
    '🇸🇬 新加坡优选': ('url-test', r'🇸🇬', URLTEST),
    '🇺🇸 美国优选':  ('url-test', r'🇺🇸', URLTEST),
    '🇬🇧 英国优选':  ('url-test', r'🇬🇧', URLTEST),
    '🇯🇵 日本专线':  ('url-test', r'🇯🇵.*专线', URLTEST),
    '🇸🇬 新加坡专线': ('url-test', r'🇸🇬.*专线', URLTEST),
    '🇭🇰 香港专线':  ('url-test', r'🇭🇰.*专线', URLTEST),
    '🇺🇸 美国流媒体': ('url-test', r'🇺🇸.*流媒体', URLTEST),
    '🇨🇳 台湾专线':  ('url-test', r'台湾.*专线', URLTEST),
}
ALL_GROUP = '♻️ 自动选择'
FB_GROUP = '🛡️ 故障转移'


def js(v):
    return json.dumps(v, ensure_ascii=False)


lines = []
for g in groups:
    name = g['name']
    if name in REGION:
        typ, pat, opts = REGION[name]
        lines.append("  grp(%s, '%s', pick(/%s/), %s);" % (js(name), typ, pat, js(opts)))
    elif name == ALL_GROUP:
        lines.append("  grp(%s, 'url-test', names.slice(), %s);" % (js(name), js(URLTEST)))
    elif name == FB_GROUP:
        lines.append("  grp(%s, 'fallback', names.slice(), %s);" % (js(name), js(TEST)))
    else:
        extra = {"include-all-proxies": True} if g.get('include-all-proxies') else None
        lines.append("  grp(%s, %s, %s%s);" % (
            js(name), js(g['type']), js(g.get('proxies', [])),
            (", " + js(extra)) if extra else ""))
GROUPS_JS = "\n".join(lines)
RULES_JS = "\n".join("  " + js(r) + "," for r in rules)
TODAY = datetime.date.today().isoformat()

TEMPLATE = """// =====================================================================
//  FlClash / mihomo 覆写脚本（由已调优配置自动生成）
//  生成日期: @TODAY@
//  作用: 剔除伪节点 -> 重建 @NG@ 个策略组 -> 覆盖 @NR@ 条规则 -> Apple 直连
//
//  用法一（最稳）: FlClash -> 配置 -> 选中订阅 -> 右上角「脚本」
//                -> 粘贴本文件全文 -> 保存 -> 重新拉取订阅
//  用法二: 填 raw 链接，设备拉订阅时自动获取最新版
//          https://raw.githubusercontent.com/tzqmaster/Flclash-Link/main/main.js
//
//  设计要点:
//   1. 区域组用正则从实际节点里挑，换节点 / 改名都不会失效
//   2. 规则整段覆盖，不依赖机场订阅自带的规则
//   3. 兜底 = 走代理；国内由 GEOSITE,cn / .cn / GEOIP,cn 三层拦回直连
//   4. 全文 ES5 写法（var / function / 无箭头函数），兼容各版本脚本引擎
// =====================================================================

function main(config) {
  // ---------- 1. 剔除伪节点（"剩余流量""套餐到期"这类会被测速误选）----------
  var FAKE = /剩余流量|套餐到期|官网|过期|重置/;
  var proxies = (config.proxies || []).filter(function (p) {
    return p && p.name && !FAKE.test(p.name);
  });
  config.proxies = proxies;

  var names = [];
  for (var i = 0; i < proxies.length; i++) names.push(proxies[i].name);

  function pick(re) {
    return names.filter(function (n) { return re.test(n); });
  }

  // ---------- 2. 重建策略组 ----------
  var groups = [];
  function grp(name, type, members, extra) {
    var g = { name: name, type: type, proxies: members };
    if (extra) {
      for (var k in extra) { if (extra.hasOwnProperty(k)) g[k] = extra[k]; }
    }
    if (!g.proxies.length) g.proxies = names.length ? [names[0]] : ['DIRECT'];
    groups.push(g);
  }

@GROUPS@

  config['proxy-groups'] = groups;

  // ---------- 3. 覆盖规则 ----------
  config.rules = RULES;

  // ---------- 4. Apple 直连补丁（DNS 侧）----------
  if (config.dns) {
    var apple = ['*.apple.com', '*.icloud.com', '*.mzstatic.com', '*.aaplimg.com',
                 '*.cdn-apple.com', '*.icloud-content.com', '*.itunes.com', '*.me.com'];
    var cur = config.dns['fake-ip-filter'] || [];
    for (var j = 0; j < apple.length; j++) {
      if (cur.indexOf(apple[j]) < 0) cur.push(apple[j]);
    }
    config.dns['fake-ip-filter'] = cur;
  }

  return config;
}

// ---------- 规则表（@NR@ 条）----------
var RULES = [
@RULES@
];
"""

out = (TEMPLATE.replace('@TODAY@', TODAY)
              .replace('@NG@', str(len(groups)))
              .replace('@NR@', str(len(rules)))
              .replace('@GROUPS@', GROUPS_JS)
              .replace('@RULES@', RULES_JS))

open(OUT, 'w', encoding='utf-8').write(out)
print('已生成 %s: %.1f KB | 组 %d | 规则 %d' % (OUT, len(out) / 1024, len(groups), len(rules)))
