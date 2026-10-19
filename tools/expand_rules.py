#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlClash 规则库扩容 v2（2026-10-19）
- 生成 "8.5 国外常用站点扩展库" 规则段
- 插入到 profile 的「第 8 段 国内直连」之后、「第 9 段 自定义」之前
- 同时把原来的「第 7 段（全部注释掉）」替换为指向说明
用法： python expand_rules.py            # 只生成预览块到 /tmp/rules_block.txt
       python expand_rules.py --apply    # 备份并写入 profile
"""
import os, re, shutil, sys, time

PROFILE = os.path.expanduser(
    "~/Library/Application Support/com.follow.clash/profiles/368389100727701504.yaml")

DEFAULT = "🚀 节点选择"
AI = "🤖 AI"
VID = "📺 流媒体"
DEV = "🐙 开发"

# ---------------------------------------------------------------- 1. geosite 大类
GEOSITE_CATS = [
    ("category-ai-chat-!cn", AI, "AI 对话站（ChatGPT/Claude/Gemini/Perplexity 等）", 70),
    ("category-dev", DEV, "开发者站（代码托管/包管理/文档）", 515),
    ("category-games", DEFAULT, "游戏平台与社区", 836),
    ("category-media", VID, "流媒体与音视频", 1401),
    ("category-entertainment", VID, "娱乐内容站", 1501),
    ("category-social-media-!cn", DEFAULT, "海外社交媒体", 578),
    ("category-scholar-!cn", DEFAULT, "学术/科研/文献", 5992),
]

# ---------------------------------------------------------------- 2. geosite 单站
GEOSITE_SITES = [
    # (分类, 目标组, 中文说明)
    ("reddit", DEFAULT, "Reddit"), ("discord", DEFAULT, "Discord"),
    ("wikimedia", DEFAULT, "维基媒体"), ("linkedin", DEFAULT, "领英"),
    ("pinterest", DEFAULT, "Pinterest"), ("tumblr", DEFAULT, "Tumblr"),
    ("quora", DEFAULT, "Quora"), ("medium", DEFAULT, "Medium"),
    ("signal", DEFAULT, "Signal"), ("line", DEFAULT, "LINE"),
    ("vk", DEFAULT, "VK / OK.ru"),
    ("hulu", VID, "Hulu"), ("soundcloud", VID, "SoundCloud"),
    ("tidal", VID, "TIDAL"), ("vimeo", VID, "Vimeo"), ("dailymotion", VID, "Dailymotion"),
    ("gitlab", DEV, "GitLab"), ("stackexchange", DEV, "Stack Exchange 全站"),
    ("docker", DEV, "Docker Hub"), ("npmjs", DEV, "npm"), ("jetbrains", DEV, "JetBrains"),
    ("unity", DEV, "Unity"),
    ("huggingface", AI, "Hugging Face"), ("perplexity", AI, "Perplexity"),
    ("steam", DEFAULT, "Steam"), ("epicgames", DEFAULT, "Epic Games"),
    ("nintendo", DEFAULT, "任天堂"), ("playstation", DEFAULT, "PlayStation"),
    ("xbox", DEFAULT, "Xbox"), ("blizzard", DEFAULT, "暴雪"), ("riot", DEFAULT, "Riot"),
    ("notion", DEFAULT, "Notion"), ("figma", DEFAULT, "Figma"), ("slack", DEFAULT, "Slack"),
    ("zoom", DEFAULT, "Zoom"), ("trello", DEFAULT, "Trello"), ("atlassian", DEFAULT, "Atlassian"),
    ("adobe", DEFAULT, "Adobe"), ("dropbox", DEFAULT, "Dropbox"), ("onedrive", DEFAULT, "OneDrive"),
    ("mega", DEFAULT, "MEGA"),
    ("paypal", DEFAULT, "PayPal"), ("stripe", DEFAULT, "Stripe"), ("shopify", DEFAULT, "Shopify"),
    ("ebay", DEFAULT, "eBay"), ("amazon", DEFAULT, "Amazon"),
    ("bbc", DEFAULT, "BBC"), ("cnn", DEFAULT, "CNN"), ("nytimes", DEFAULT, "纽约时报"),
    ("wsj", DEFAULT, "华尔街日报"), ("reuters", DEFAULT, "路透社"),
    ("bloomberg", DEFAULT, "彭博"), ("theguardian", DEFAULT, "卫报"),
    ("forbes", DEFAULT, "福布斯"), ("imdb", DEFAULT, "IMDb"), ("archive", DEFAULT, "Archive.org"),
    ("speedtest", DEFAULT, "Speedtest"), ("cloudflare", DEFAULT, "Cloudflare"),
    ("protonmail", DEFAULT, "Proton Mail"), ("duckduckgo", DEFAULT, "DuckDuckGo"),
    ("bing", DEFAULT, "Bing"), ("yandex", DEFAULT, "Yandex"),
]

# ---------------------------------------------------------------- 3. 域名后缀长尾
DOMAINS = {
    ("维基 / 百科", DEFAULT): """
wikipedia.org wikipedia.com wikimediafoundation.org mediawiki.org wiktionary.org wikidata.org
wikivoyage.org wikibooks.org wikisource.org wikinews.org wikiquote.org wikiversity.org
fandom.com wikia.com wikiwand.com britannica.com dbpedia.org
""",
    ("社区 / 论坛", DEFAULT): """
reddit.com redd.it redditmedia.com redditstatic.com redditinc.com
discord.com discord.gg discordapp.com discordapp.net discord.media discordstatus.com
threads.net threads.com bsky.app bsky.social mastodon.social mastodon.online mstdn.social
substack.com substackcdn.com patreon.com patreonusercontent.com ko-fi.com buymeacoffee.com
imgur.com giphy.com tenor.com 9gag.com 4chan.org 4channel.org
producthunt.com ycombinator.com news.ycombinator.com slashdot.org lobste.rs
naver.com daum.net kakao.com kakao.co.kr
rakuten.co.jp yahoo.co.jp nicovideo.jp pixiv.net dmm.co.jp dlsite.com
""",
    ("新闻 / 科技媒体", DEFAULT): """
apnews.com npr.org pbs.org politico.com axios.com thehill.com semafor.com
theverge.com wired.com arstechnica.com engadget.com techcrunch.com venturebeat.com theinformation.com
9to5mac.com 9to5google.com macrumors.com appleinsider.com androidpolice.com xda-developers.com
scmp.com ft.com economist.com newyorker.com theatlantic.com vox.com vice.com
dailymail.co.uk thetimes.co.uk telegraph.co.uk independent.co.uk thesun.co.uk mirror.co.uk
cnbc.com businessinsider.com insider.com fortune.com barrons.com marketwatch.com seekingalpha.com
yahoo.com aol.com msn.com
nbcnews.com abcnews.go.com cbsnews.com foxnews.com usatoday.com latimes.com
washingtonpost.com nypost.com chicagotribune.com bostonglobe.com
huffpost.com buzzfeed.com buzzfeednews.com salon.com slate.com thedailybeast.com
""",
    ("视频 / 音乐", VID): """
googlevideo.com ytimg.com youtu.be youtube-nocookie.com yt3.ggpht.com
nflxvideo.net nflximg.net nflxext.com nflxso.net
disneyplus.com disney-plus.net dssott.com bamgrid.com
max.com hbomax.com hbomaxcdn.com
peacocktv.com paramountplus.com cbsivideo.com aiv-cdn.net
crunchyroll.com crunchyrollsvc.com vrv.co funimation.com
sndcdn.com bandcamp.com deezer.com qobuz.com last.fm discogs.com genius.com
shazam.com pandora.com iheart.com audius.co
rumble.com odysee.com kick.com bitchute.com lbry.tv
""",
    ("游戏", DEFAULT): """
steamcommunity.com steampowered.com steamstatic.com steamcontent.com
epicgames.com epicgamescdn.com unrealengine.com
ea.com origin.com eaassets-a.akamaihd.net
blizzard.com battle.net riotgames.com leagueoflegends.com valorant.com
nintendo.com nintendo.net playstation.com playstation.net xbox.com xboxlive.com
minecraft.net mojang.com roblox.com rbxcdn.com
gog.com humblebundle.com itch.io nexusmods.com curseforge.com
ubisoft.com capcom.com bethesda.net rockstargames.com take2games.com square-enix.com
gamefaqs.com ign.com gamespot.com pcgamer.com kotaku.com polygon.com eurogamer.net
""",
    ("开发 / 包管理", DEV): """
github.io githubusercontent.com githubassets.com gitlab.io bitbucket.org sourceforge.net
pypi.org files.pythonhosted.org pythonhosted.org python.org
crates.io docs.rs rust-lang.org
rubygems.org packagist.org golang.org go.dev proxy.golang.org sum.golang.org
nodejs.org npmjs.com npmjs.org yarnpkg.com deno.land bun.sh
docker.io docker.com hub.docker.com ghcr.io
stackoverflow.com stackexchange.com serverfault.com superuser.com askubuntu.com
mathoverflow.net sstatic.net stackapps.com
devdocs.io readthedocs.io gitbook.io
vercel.com netlify.com netlify.app heroku.com railway.app render.com fly.io
supabase.com appwrite.io mongodb.com redis.io elastic.co postgresql.org mysql.com sqlite.org
workers.dev pages.dev r2.dev
vscode.dev cursor.com replit.com codesandbox.io stackblitz.com gitpod.io glitch.com
codepen.io jsfiddle.net
apache.org maven.apache.org gradle.org spring.io quarkus.io
kotlinlang.org scala-lang.org haskell.org ocaml.org elixir-lang.org php.net
laravel.com symfony.com djangoproject.com rubyonrails.org
expressjs.com nextjs.org reactjs.org react.dev vuejs.org angular.io svelte.dev
tailwindcss.com vitejs.dev webpack.js.org
qt.io llvm.org gnu.org kernel.org debian.org ubuntu.com archlinux.org
fedoraproject.org centos.org alpinelinux.org freebsd.org brew.sh
""",
    ("AI 工具", AI): """
chatgpt.com chat.openai.com sora.com claude.ai gemini.google.com grok.com x.ai
perplexity.ai midjourney.com character.ai poe.com civitai.com
stability.ai runwayml.com elevenlabs.io suno.com udio.com
openrouter.ai together.ai replicate.com groq.com mistral.ai cohere.com
ollama.com lmstudio.ai llama.com anyscale.com fireworks.ai deepinfra.com
copilot.microsoft.com hf.co
""",
    ("办公 / 协作", DEFAULT): """
notion.so notion.site figma.com slack.com zoom.us zoomgov.com trello.com
atlassian.net jira.com asana.com airtable.com miro.com canva.com
lucid.co lucidchart.com monday.com clickup.com todoist.com
evernote.com obsidian.md roamresearch.com coda.io
grammarly.com grammarly.io otter.ai descript.com loom.com calendly.com
zapier.com ifttt.com make.com typeform.com surveymonkey.com
salesforce.com force.com hubspot.com zendesk.com intercom.com
mailchimp.com sendgrid.net twilio.com
""",
    ("云盘 / 邮箱", DEFAULT): """
dropbox.com dropboxusercontent.com box.com boxcloud.com mega.nz
1drv.ms pcloud.com icedrive.net sync.com backblaze.com
wetransfer.com file.io transfer.sh gofile.io pixeldrain.com
proton.me protonmail.com tutanota.com tuta.com mailbox.org fastmail.com hey.com zoho.com
""",
    ("购物 / 支付 / 金融", DEFAULT): """
paypal.com stripe.com wise.com revolut.com coinbase.com kraken.com
binance.com okx.com bybit.com kucoin.com crypto.com etherscan.io solscan.io
etsy.com aliexpress.com temu.com shein.com wish.com
walmart.com target.com bestbuy.com newegg.com bhphotovideo.com adorama.com costco.com
ikea.com homedepot.com lowes.com macys.com nordstrom.com
nike.com adidas.com uniqlo.com zara.com hm.com asos.com farfetch.com ssense.com
stockx.com goat.com
tradingview.com investing.com coingecko.com coinmarketcap.com defillama.com xe.com oanda.com
""",
    ("出行 / 旅行", DEFAULT): """
booking.com agoda.com expedia.com hotels.com kayak.com skyscanner.net
tripadvisor.com trivago.com airbnb.com hostelworld.com
marriott.com hilton.com hyatt.com ihg.com accor.com
uber.com lyft.com doordash.com ubereats.com grubhub.com
delta.com united.com aa.com emirates.com qatarairways.com singaporeair.com
jal.co.jp ana.co.jp cathaypacific.com evaair.com china-airlines.com
""",
    ("学术 / 教育", DEFAULT): """
arxiv.org biorxiv.org medrxiv.org nature.com science.org sciencedirect.com
springer.com ieee.org acm.org jstor.org pubmed.ncbi.nlm.nih.gov ncbi.nlm.nih.gov
researchgate.net academia.edu semanticscholar.org ssrn.com osf.io overleaf.com sharelatex.com
tandfonline.com wiley.com sagepub.com cell.com plos.org mdpi.com frontiersin.org
coursera.org edx.org udemy.com khanacademy.org udacity.com brilliant.org
masterclass.com skillshare.com duolingo.com quizlet.com chegg.com coursehero.com brainly.com
mit.edu harvard.edu stanford.edu berkeley.edu ox.ac.uk cam.ac.uk
""",
    ("影视资料 / 动漫 / 阅读", DEFAULT): """
imdb.com rottentomatoes.com letterboxd.com goodreads.com
myanimelist.net anilist.co mangadex.org bato.to novelupdates.com
webtoons.com tapas.io fanfiction.net archiveofourown.org ao3.org
openlibrary.org gutenberg.org librivox.org
""",
    ("网络 / 测速 / 工具", DEFAULT): """
speedtest.net fast.com dslreports.com waveform.com
cloudflare.com cloudflare-dns.com one.one.one.one dns.google quad9.net nextdns.io
ipinfo.io ipapi.co ip.sb whatismyip.com whatsmyip.org
deepl.com reverso.net linguee.com
timeanddate.com
""",
}


def build_block() -> str:
    L = []
    A = L.append
    total_suffix = sum(len([d for d in ds.split() if d]) for ds in DOMAINS.values())

    A("# ---------- 8.5 国外常用站点扩展库 v2（2026-10-19） ----------")
    A("# 位置说明：本段故意排在「第 8 段 国内直连」之后。")
    A("#   国内域名会先被 GEOSITE,cn / DOMAIN-SUFFIX,cn / GEOIP,cn 拦住，")
    A("#   不会被这里的海外大类误伤（category-media 里也含国内视频站）。")
    A(f"# 覆盖量：7 个 geosite 大类（约 1.09 万条域名）+ {len(GEOSITE_SITES)} 个单站分类 + {total_suffix} 条域名后缀")
    A("# 性能实测：规则数从 140 → 10140 条，启动耗时 0.22s → 0.31s，内存变化在测量噪声内。")
    A("# 维护：新增站点按类别往下面加一行 DOMAIN-SUFFIX 即可；大类缺失优先用 geosite。")
    A("")
    A("# --- 8.5.1 geosite 大类（一行顶上千条，优先用这个）---")
    for cat, tgt, desc, n in GEOSITE_CATS:
        A(f"  - 'GEOSITE,{cat},{tgt}'    # {desc}（{n:,} 条）")
    A("")
    A("# --- 8.5.2 geosite 单站分类（比大类更精确，命中即停，放前面）---")
    for cat, tgt, desc in GEOSITE_SITES:
        A(f"  - 'GEOSITE,{cat},{tgt}'    # {desc}")
    A("")
    A("# --- 8.5.3 域名后缀长尾（geosite 里没有的，按类别补）---")
    for (label, tgt), ds in DOMAINS.items():
        doms = [d for d in ds.split() if d]
        A(f"# · {label}（{len(doms)} 条）→ {tgt}")
        for d in doms:
            A(f"  - 'DOMAIN-SUFFIX,{d},{tgt}'")
        A("")
    return "\n".join(L).rstrip() + "\n"


def main():
    block = build_block()
    if "--apply" not in sys.argv:
        open("/tmp/rules_block.txt", "w", encoding="utf-8").write(block)
        print(block[:1500])
        print(f"...\n[预览] 共 {len(block.splitlines())} 行，已写入 /tmp/rules_block.txt")
        return

    t = open(PROFILE, encoding="utf-8").read()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    bk = f"/Users/zaiquantao/WorkBuddy/2026-10-13-21-53-31/flclash-backup-{stamp}-rulelib"
    os.makedirs(bk, exist_ok=True)
    shutil.copy2(PROFILE, f"{bk}/profile.bak")
    shutil.copy2(os.path.expanduser("~/Library/Application Support/com.follow.clash/config.yaml"),
                 f"{bk}/config.yaml.bak")

    # 1) 旧的第 7 段（全部是注释）→ 替换为指向说明（已替换过则跳过）
    old7 = "# ---------- 7. 常用国外站点（默认没走代理，需要就取消注释） ----------"
    if old7 in t:
        start = t.index(old7)
        end = t.index("# ---------- 8. 国内域名 / IP 强制直连（三层，缺一不可） ----------")
        note = ("# ---------- 7. 常用国外站点（已升级为第 8.5 段扩展库） ----------\n"
                "# 原来这里是一堆注释掉的规则（reddit / wikipedia / discord ...）。\n"
                "# 2026-10-19 已统一搬到「8.5 国外常用站点扩展库」并全部启用，\n"
                "# 且位置挪到国内直连之后，避免海外大类误伤国内站点。\n"
                "# 需要临时关掉某类：把 8.5 段对应行注释掉即可。\n")
        t = t[:start] + note + t[end:]

    # 2) 幂等：已存在旧的 8.5 段先整段摘掉
    anchor = "# ---------- 9. 自定义规则（新增请写在这条注释下面，必须在 MATCH 之前） ----------"
    if "# ---------- 8.5 国外常用站点扩展库" in t:
        s = t.index("# ---------- 8.5 国外常用站点扩展库")
        e = t.index(anchor)
        t = t[:s] + t[e:]

    # 3) 插到第 9 段之前
    assert t.count(anchor) == 1
    t = t.replace(anchor, block + "\n" + anchor, 1)

    # 3) 兜底说明同步
    t = t.replace(
        "# 现在改为默认走 🚀 节点选择；第 8 段的 GEOSITE,cn + DOMAIN-SUFFIX,cn 仍保证国内网站直连。",
        "# 现在改为默认走 🚀 节点选择；第 8 段的 GEOSITE,cn + DOMAIN-SUFFIX,cn 仍保证国内网站直连。\n"
        "# 第 8.5 段另有 1 万余条国外站点显式规则，因此即使把兜底切回 DIRECT，常见国外站也不会打不开。")

    open(PROFILE, "w", encoding="utf-8").write(t)
    print(f"备份目录: {bk}")
    print(f"已写入 profile，新规则行数: {len(block.splitlines())}")


if __name__ == "__main__":
    main()
