#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 FlClash profile 的 771 条 Clash 规则，转换成 Shadowrocket(小火箭) 可直接导入的 .conf
关键点：
  1. 小火箭不认 GEOSITE，用 GEOSITE.dat 反解析成真实域名展开
  2. 小火箭没有多策略组引用，所有代理组统一折叠为 PROXY（当前选中节点）
  3. GEOSITE,cn 有 11 万条，不展开，改用 GEOIP,CN + DOMAIN-SUFFIX,cn
  4. 在前部补一段国内主流域名直连，防止 category-media 把 B 站/爱奇艺送去代理
"""
import re
import os
import sys

PROFILE = os.path.expanduser('~/Library/Application Support/com.follow.clash/profiles/368389100727701504.yaml')
GEOSITE = '/tmp/mihomo_test/GEOSITE.dat'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shadowrocket', 'Shadowrocket.conf')

PROXY_TARGETS = {'🚀 节点选择', '🐙 开发', '📺 流媒体', '🤖 AI', '🎯 Google',
                 '✈️ Telegram', '🐦 X/Twitter', '🧪 节点测速', '🌐 未匹配', '♻️ 自动选择'}


# ---------------- GEOSITE.dat 解析 ----------------
def varint(b, i):
    r = 0
    s = 0
    while True:
        c = b[i]
        i += 1
        r |= (c & 0x7f) << s
        s += 7
        if not c & 0x80:
            return r, i


def fields(b):
    i = 0
    n = len(b)
    while i < n:
        k, i = varint(b, i)
        fn = k >> 3
        wt = k & 7
        if wt == 0:
            v, i = varint(b, i)
            yield fn, 0, v
        elif wt == 2:
            ln, i = varint(b, i)
            yield fn, 2, b[i:i + ln]
            i += ln
        elif wt == 5:
            yield fn, 5, b[i:i + 4]
            i += 4
        elif wt == 1:
            yield fn, 1, b[i:i + 8]
            i += 8
        else:
            raise ValueError('wiretype %d' % wt)


def load_geosite(path):
    d = open(path, 'rb').read()
    sites = {}
    for fn, wt, val in fields(d):
        if fn != 1:
            continue
        code = None
        doms = []
        for f2, w2, v2 in fields(val):
            if f2 == 1:
                try:
                    code = v2.decode('utf-8').lower()
                except Exception:
                    pass
            elif f2 == 2:
                typ = 0
                name = ''
                for f3, w3, v3 in fields(v2):
                    if f3 == 1 and w3 == 0:
                        typ = v3
                    elif f3 == 2:
                        name = v3.decode('utf-8', 'ignore')
                # 0=plain 2=rootdomain 3=full ；1=regex 丢掉
                if typ in (0, 2, 3) and name:
                    doms.append((typ, name.lower().strip('.')))
        if code:
            sites[code] = doms
    return sites


# ---------------- 国内直连兜底（防误伤） ----------------
CN_KEEP_DIRECT = """
bilibili.com b23.tv bilivideo.com hdslb.com
iqiyi.com iqiyipic.com qiyipic.com youku.com tudou.com
qq.com qpic.com qqmusic.com gtimg.com tencent.com tencent-cloud.com myqcloud.com
weixin.qq.com wechat.com servicewechat.com
taobao.com tmall.com alipay.com alicdn.com aliyun.com aliyuncs.com taobao.net
jd.com 360buyimg.com jd.hk
baidu.com bdstatic.com bdimg.com baidupcs.com
weibo.com weibo.cn sinaimg.cn sina.com.cn
douyin.com douyinvod.com bytedance.com toutiao.com ixigua.com snssdk.com
163.com 126.net 127.net
zhihu.com zhimg.com douban.com doubanio.com
kuaishou.com gifshow.com kwimgs.com
meituan.com meituan.net dianping.com
pinduoduo.com yangkeduo.com
ctrip.com ctripstatic.com qunar.com 12306.cn
amap.com autonavi.com
xiaomi.com mi.com miui.com huawei.com hicloud.com
oppo.com vivo.com realme.com
csdn.net cnblogs.com gitee.com oschina.net
56smart.com apiv1.56smart.com
""".split()


def main():
    # ---- 1. 读 profile 规则 ----
    txt = open(PROFILE, encoding='utf-8').read().split('\n')
    in_rules = False
    clash_rules = []
    for L in txt:
        if re.match(r'^rules:', L):
            in_rules = True
            continue
        if in_rules and re.match(r'^[a-zA-Z]', L):
            break
        if in_rules:
            m = re.search(r"- '(.*?)'", L)
            if m:
                clash_rules.append(m.group(1).strip())

    sites = load_geosite(GEOSITE)
    # 国内域名全集：展开国外分类时剔掉，防止 category-media 之类把 B 站/爱奇艺送去代理
    cn_set = set(d for _, d in sites.get('cn', []))

    # ---- 2. 转换 ----
    out = []          # (rule_line, comment)
    seen = set()      # 去重键
    stat = {'direct': 0, 'proxy': 0, 'reject': 0, 'geo': 0, 'skip': 0,
            'geo_expand': 0, 'dup': 0, 'cn_filtered': 0}

    CN_CORE_IPS = [
        'IP-CIDR,10.0.0.0/8,DIRECT,no-resolve',
        'IP-CIDR,172.16.0.0/12,DIRECT,no-resolve',
        'IP-CIDR,192.168.0.0/16,DIRECT,no-resolve',
        'IP-CIDR,127.0.0.0/8,DIRECT,no-resolve',
        'IP-CIDR,100.64.0.0/10,DIRECT,no-resolve',
        'IP-CIDR,169.254.0.0/16,DIRECT,no-resolve',
        'IP-CIDR,224.0.0.0/4,DIRECT,no-resolve',
        'IP-CIDR,255.255.255.255/32,DIRECT,no-resolve',
        'IP-CIDR6,::1/128,DIRECT,no-resolve',
        'IP-CIDR6,fc00::/7,DIRECT,no-resolve',
        'IP-CIDR6,fe80::/10,DIRECT,no-resolve',
    ]

    def target(p):
        if p == 'DIRECT':
            return 'DIRECT'
        if p == 'REJECT':
            return 'REJECT'
        if p in PROXY_TARGETS:
            return 'PROXY'
        return 'PROXY'

    def push(line, key=None):
        k = key or line.split(',')[0] + '|' + line.split(',')[1] if line.count(',') >= 1 else line
        if k in seen:
            stat['dup'] += 1
            return False
        seen.add(k)
        out.append(line)
        return True

    cn_geo = [False]

    # 私网直连先落
    for r in CN_CORE_IPS:
        push(r, 'IP|' + r.split(',')[1])

    for raw in clash_rules:
        parts = [x.strip() for x in raw.split(',')]
        typ = parts[0]

        # --- MATCH ---
        if typ == 'MATCH':
            continue  # FINAL 最后统一加

        # --- GEOSITE ---
        if typ == 'GEOSITE':
            name = parts[1].lower()
            pol = parts[2] if len(parts) > 2 else 'DIRECT'
            tgt = target(pol)

            if name == 'private':
                continue  # 已用 IP 段覆盖
            if name in ('cn',):
                cn_geo[0] = True
                stat['geo'] += 1
                continue
            if name in ('apple',):
                # apple 全集 1818 条太大，只展 apple-cn + icloud，其余靠 GEOIP,CN
                merged = sites.get('apple-cn', []) + sites.get('icloud', [])
                cnt = 0
                for t, d in merged:
                    if d.startswith('.'):
                        d = d.lstrip('.')
                    if t == 3:
                        line = 'DOMAIN,%s,%s' % (d, tgt)
                    else:
                        line = 'DOMAIN-SUFFIX,%s,%s' % (d, tgt)
                    if push(line, 'D|' + d):
                        cnt += 1
                stat['geo_expand'] += cnt
                continue

            doms = sites.get(name, [])
            if not doms:
                stat['skip'] += 1
                continue
            cap = 35
            cnt = 0
            for t, d in doms:
                if cnt >= cap:
                    break
                if d.startswith('.'):
                    d = d.lstrip('.')
                if d in cn_set:
                    stat['cn_filtered'] += 1
                    continue
                if t == 3:
                    line = 'DOMAIN,%s,%s' % (d, tgt)
                else:
                    line = 'DOMAIN-SUFFIX,%s,%s' % (d, tgt)
                if push(line, 'D|' + d):
                    cnt += 1
            stat['geo_expand'] += cnt
            continue

        # --- 普通规则 ---
        if typ in ('DOMAIN', 'DOMAIN-SUFFIX', 'IP-CIDR', 'IP-CIDR6', 'GEOIP'):
            name = parts[1]
            pol = parts[2] if len(parts) > 2 else 'DIRECT'
            extra = parts[3] if len(parts) > 3 else None
            tgt = target(pol)
            line = '%s,%s,%s' % (typ, name, tgt)
            if extra and extra.lower() == 'no-resolve':
                line += ',no-resolve'
            if typ == 'IP-CIDR' or typ == 'GEOIP':
                key = typ + '|' + name
            else:
                key = 'D|' + name.lower()
            if push(line, key):
                stat[tgt.lower() if tgt in ('DIRECT', 'REJECT') else 'proxy'] += 1
            continue

        stat['skip'] += 1

    # ---- 3. 组装 conf ----
    header = """#!MANAGED-CONFIG https://raw.githubusercontent.com/tzqmaster/Flclash-Link/main/shadowrocket/Shadowrocket.conf interval=86400

# ============================================================
# Shadowrocket 规则覆写配置（由 Clash 771 条规则自动转换）
# 生成时间：__DATE__
# 规则总数：__N__ 条
#
# 用法（iOS 小火箭）：
#   首页右上「+」→ 类型选「Subscribe」填机场订阅链接 → 保存（先拿到节点）
#   底部「配置」→ 右上「+」→ 类型「URL」→ 粘贴本文件链接 → 下载
#   回到配置页，点一下导入的配置，使其生效
#
# 说明：小火箭不支持 Clash 的多策略组，这里所有代理组
#   （🚀节点选择 / 🎬流媒体 / 🤖AI / 🐙开发 / 🎯Google …）统一折叠为 PROXY，
#   即全部走你在首页选中的那个节点；DIRECT = 直连；REJECT = 拦截。
# ============================================================

[General]
bypass-system = true
skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, localhost, *.local, captive.apple.com
tun-excluded-routes = 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 224.0.0.0/4, 255.255.255.255/32
dns-server = 223.5.5.5, 119.29.29.29, 1.0.0.1
dns-fallback-system = false
dns-direct-system = false
private-ip-answer = true
icmp-auto-reply = true
always-reject-url-rewrite = false
bypass-tun = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12
internet-test-url = http://www.gstatic.com/generate_204
proxy-test-url = http://www.gstatic.com/generate_204
geoip-maxmind = false

[Rule]
"""

    # 国内大站直连插到最前（在私网之后、国外规则之前）
    cn_lines = []
    for d in CN_KEEP_DIRECT:
        if not d:
            continue
        cn_lines.append('DOMAIN-SUFFIX,%s,DIRECT' % d)

    body = list(out)
    private_part = body[:11]
    rest = body[11:]
    tail = []
    if cn_geo[0]:
        tail.append('GEOIP,CN,DIRECT')
    tail.append('FINAL,PROXY')
    final = private_part + cn_lines + rest + tail

    import datetime
    header = header.replace('__DATE__', datetime.date.today().isoformat())
    header = header.replace('__N__', str(len(final)))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(final))
        f.write('\n')

    print('输出:', OUT)
    print('规则条数:', len(final), '（私网 %d + 国内直连 %d + 其余 %d）'
          % (len(private_part), len(cn_lines), len(rest)))
    print('统计:', stat)
    print('文件大小: %.1f KB' % (os.path.getsize(OUT) / 1024.0))


if __name__ == '__main__':
    main()
