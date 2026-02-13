import requests
import os
import json
import base64

# 配置（这些会从 GitHub Secrets 读，不用改）
GITHUB_TOKEN = os.getenv('GH_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPOSITORY')
FILE_PATH = "links.json"

def check_backlink(url):
    """检查对方网站是否有我的回链"""
    try:
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            # 域名！
            return "828111.xyz" in response.text
        return False
    except:
        return False

def run_cleanup():
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 1. 获取最新的 links.json
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    res = requests.get(url, headers=headers).json()
    content = base64.b64decode(res['content']).decode('utf-8')
    links = json.loads(content)
    sha = res['sha']

    new_links = []
    changes_made = False

    # 2. 逐一巡检
    for link in links:
        print(f"正在检查: {link['name']}...")
        is_ok = check_backlink(link['url'])
        
        if is_ok:
            link['fail_count'] = 0 # 检查通过，重置失败计数
            new_links.append(link)
        else:
            link['fail_count'] = link.get('fail_count', 0) + 1
            print(f"⚠️ {link['name']} 没搜到回链 (第{link['fail_count']}次失败)")
            
            if link['fail_count'] < 3:
                # 失败没超过3次，留校察看
                new_links.append(link)
            else:
                # 连续3次失败，直接踢出名单
                print(f"❌ {link['name']} 连续3次失败，正式开除！")
                changes_made = True
                continue
        
        # 如果 fail_count 变了，也标记为需要更新
        if 'fail_count' in link:
            changes_made = True

    # 3. 如果有人被踢了或者失败计数更新了，写回仓库
    if changes_made:
        new_content = json.dumps(new_links, indent=2, ensure_ascii=False)
        update_data = {
            "message": "🧹 凌晨巡检：清理失效链接",
            "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
            "sha": sha
        }
        requests.put(url, headers=headers, json=update_data)
        print("✅ 仓库已更新")
    else:
        print("☕ 所有老哥都挺靠谱，今天无需清理")

if __name__ == "__main__":
    run_cleanup()
