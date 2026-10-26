#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把一份「已调优的 mihomo/Clash yaml」压成 iOS 客户端能直接导入的精简版。

为什么需要它：
  main.js 是 FlClash 的覆写脚本（JavaScript），只有 FlClash（Android/桌面）认。
  官方没有 iOS 版 FlClash，iPhone 上的 ClashMi / Karing / Stash / ClashX 只能吃
  YAML 配置，把 main.js 当订阅填进去会解析失败。

用法：
  python3 tools/make_ios_yaml.py <源 yaml> [输出文件]

输出文件包含 53~55 个内嵌节点 → 带凭据，只能放本机/手机，不要提交到公开仓库。
"""

import os
import sys

import yaml

# 保留的顶层键（iOS 客户端不认的监听/控制类键全部丢弃）
KEEP_SCALARS = [
    'mode', 'log-level', 'ipv6', 'unified-delay', 'tcp-concurrent',
    'keep-alive-interval', 'find-process-mode', 'global-client-fingerprint',
    'geodata-mode', 'geo-auto-update', 'geo-update-interval',
]
DROP_DNS_KEYS = ['listen']

HEADER = """# =====================================================================
#  Clash / mihomo 配置 —— iOS 专用（ClashMi / Karing / Stash / ClashX 均可导入）
#  由 tools/make_ios_yaml.py 生成   |   节点: {n_proxies} 内嵌 / 策略组: {n_groups} / 规则: {n_rules}
#
#  ⚠️ 本文件含节点凭据：只放手机本地（AirDrop / 文件 App / iCloud），
#     不要上传到任何公开仓库或公开网盘。
#
#  导入：ClashMi / Karing → 配置 → 右上 + → 从文件导入 → 选本文件 → 启用
#        再打开 VPN / TUN 开关授权。
#  ⚠️ 节点是导出当时的快照，机场轮换 UUID 后需要重新跑一次本脚本。
# =====================================================================
"""


def build(src_path, out_path):
    with open(src_path, encoding='utf-8') as f:
        d = yaml.safe_load(f)

    proxies = d.get('proxies') or []
    groups = d.get('proxy-groups') or []
    rules = d.get('rules') or []
    if not proxies:
        raise SystemExit('源配置里没有 proxies，无法生成（不能拿纯规则文件当配置用）')

    out = {
        'mixed-port': 7890,
        'allow-lan': False,
        'bind-address': '*',
    }
    for k in KEEP_SCALARS:
        if k in d:
            out[k] = d[k]
    out.setdefault('mode', 'rule')
    out.setdefault('log-level', 'warning')

    dns = d.get('dns')
    if dns:
        for k in DROP_DNS_KEYS:
            dns.pop(k, None)
        out['dns'] = dns

    out['proxies'] = proxies
    out['proxy-groups'] = groups
    out['rules'] = rules

    header = HEADER.format(n_proxies=len(proxies), n_groups=len(groups), n_rules=len(rules))
    body = yaml.safe_dump(out, allow_unicode=True, sort_keys=False,
                          width=4096, default_flow_style=False)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(header + body)
    return len(proxies), len(groups), len(rules)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else 'Clash-iOS.yaml'
    n_p, n_g, n_r = build(src, out)
    size = os.path.getsize(out) / 1024
    print('已生成 %s  %.1f KB  |  节点 %d / 组 %d / 规则 %d' % (out, size, n_p, n_g, n_r))
    print('提示：用 mihomo -t -f %s -d /tmp/x 可先做一次语法校验' % out)


if __name__ == '__main__':
    main()
