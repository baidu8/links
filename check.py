import requests
import json
import os


MY_URL = "828111.xyz"

def check_backlink(url):
    try:
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        return MY_URL in response.text
    except:
        return False

# 1. 加载数据
with open('links.json', 'r', encoding='utf-8') as f:
    links = json.load(f)
with open('blacklist.json', 'r', encoding='utf-8') as f:
    blacklist = json.load(f)

new_links = []

# 2. 开始判决
for link in links:
    # 检查黑名单
    if any(b in link['url'] for b in blacklist):
        print(f"黑名单命中: {link['name']}，直接开除！")
        continue
    
    # 检查回链
    has_link = check_backlink(link['url'])
    
    # 缓刑逻辑：利用 json 里的 fail_count 字段
    fail_count = link.get('fail_count', 0)
    
    if has_link:
        link['fail_count'] = 0 # 表现良好，重置次数
        new_links.append(link)
    else:
        fail_count += 1
        if fail_count < 3:
            print(f"警告: {link['name']} 未检测到回链 ({fail_count}/3)")
            link['fail_count'] = fail_count
            new_links.append(link)
        else:
            print(f"判决: {link['name']} 连续3次未检测到回链，正式剔除！")

# 3. 保存结果
with open('links.json', 'w', encoding='utf-8') as f:
    json.dump(new_links, f, ensure_ascii=False, indent=2)
