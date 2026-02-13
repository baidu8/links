import requests
import os
import json
import base64

# 配置（这些会从 GitHub Secrets 读）
GITHUB_TOKEN = os.getenv('GH_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPOSITORY')
FILE_PATH = "links.json"

def normalize_url(url):
    """【新增】标准化链接：去掉末尾斜杠并转小写"""
    return url.strip().rstrip('/').lower()

def check_backlink(url):
    """检查对方网站是否有我的回链"""
    try:
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            # 匹配你的域名
            return "828111.xyz" in response.text
        return False
    except:
        return False

def run_cleanup():
    if not GITHUB_TOKEN:
        print("❌ 错误：找不到 GH_TOKEN，请检查 Secret 设置")
        return

    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 1. 获取最新的 links.json
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    res = requests.get(url, headers=headers).json()
    
    if 'content' not in res:
        print(f"❌ 无法获取文件内容，GitHub 返回：{res.get('message', '未知错误')}")
        return

    content = base64.b64decode(res['content']).decode('utf-8')
    links = json.loads(content)
    sha = res['sha']

    new_links = []
    seen_urls = set() # 用于去重
    changes_made = False

    # 2. 逐一巡检
    for link in links:
        raw_url = link['url']
        norm_url = normalize_url(raw_url)

        # --- ✨ 新增：去重逻辑 ---
        if norm_url in seen_urls:
            print(f"🗑️ 发现重复项: {link['name']} ({raw_url})，已自动清理")
            changes_made = True
            continue # 跳过这个重复的
        
        print(f"正在检查: {link['name']}...")
        is_ok = check_backlink(raw_url)
        
        if is_ok:
            if link.get('fail_count', 0) > 0:
                link['fail_count'] = 0 # 检查通过，重置失败计数
                changes_made = True
            new_links.append(link)
            seen_urls.add(norm_url) # 记录已经处理过的链接
        else:
            link['fail_count'] = link.get('fail_count', 0) + 1
            print(f"⚠️ {link['name']} 没搜到回链 (第{link['fail_count']}次失败)")
            changes_made = True
            
            if link['fail_count'] < 3:
                # 失败没超过3次，留校察看
                new_links.append(link)
                seen_urls.add(norm_url)
            else:
                # 连续3次失败，直接踢出名单
                print(f"❌ {link['name']} 连续3次失败，正式开除！")
                continue

    # 3. 如果有变动（有人被踢、计数更新、或者清理了重复项），写回仓库
    if changes_made:
        new_content = json.dumps(new_links, indent=2, ensure_ascii=False)
        update_data = {
            "message": "🧹 凌晨巡检：清理失效链接及重复项",
            "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
            "sha": sha
        }
        put_res = requests.put(url, headers=headers, json=update_data)
        if put_res.status_code == 200:
            print("✅ 仓库已更新")
        else:
            print(f"❌ 更新失败：{put_res.json().get('message')}")
    else:
        print("☕ 所有老哥都挺靠谱，今天无需清理")

if __name__ == "__main__":
    run_cleanup()
