# -*- coding: utf-8 -*-
import yaml
import argparse
import os
from termcolor import cprint
import json
import re
import requests
from termcolor import colored
import shutil

KEYWORD = ""
COOKIE = ""
SEARCH_PAGE = 10
OVERVIEW = {}
WEIGHTS = {}
EXTRA_KEYWORD = []

def load_custom_weights():
    global WEIGHTS
    global EXTRA_KEYWORD
    if not os.path.exists('./config.yml'):
        return

    with open('./config.yml', 'r') as f:
        config = yaml.safe_load(f)
    if 'weights' in config:
        WEIGHTS = config['weights']
    if 'extra_keywords' in config:
        EXTRA_KEYWORD.extend(config['extra_keywords'])


def is_config_file(path):
    score = 10
    suffixs = ['.yaml', '.yml', '.conf', '.cnf', '.properties', '.xml', '.json']
    for suffix in suffixs:
        if path.endswith(suffix):
            return score
    return 0


def is_language_file(path):
    score = 15
    suffixs = ['.php', '.java', '.go', '.jsp', '.py', '.sh', '.js', '.ts', '.sql', '.rust']
    for suffix in suffixs:
        if path.endswith(suffix):
            return score
    return 0

def check_one_line(line, nice_words):
    cur_page_score = 0
    if len(line) == 0:
        return cur_page_score

    for word in nice_words:
        if word in line.lower():
            # 再跟
            cur_page_score += 10
    
    for word in WEIGHTS:
        if word in line.lower():
            cur_page_score += WEIGHTS[word]

    if 'http' in line:
        # 或许是个可访问的服务
        cur_page_score += 20
    elif 'jdbc' in line:
        cur_page_score += 20
    elif 'api' in line:
        cur_page_score += 5
    elif 'test' in line:
        cur_page_score += 5
    else:
        cur_page_score += 2
    return cur_page_score

def process_one_file(config):
    repo = config['repo_nwo']
    path = config['path']
    commit = config['commit_sha']
    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    resp = requests.get(url)
    if resp.status_code != 200:
        cprint(f"[-] {url} ret {resp.status_code} {resp.text}")
        return

    content = resp.text

    # repo = 'test'
    # path = 'test.url'
    # with open('./bucket-10000-20230102-20230109.csv', 'r') as f:
    #     content = f.read()

    cur_page_score = 0
    nice_words = [
        'username:', 'password:', 'username=', 'password=',
        'mysql', 'pgsql', 'mongo', 'oracle', 'sqlserver', 'redis', 'mariadb', 'mssql'
        'aliyun', 'qcloud', 'tencentyun', 'accesskey', 'accessSecret', 'accessId', 'bucket'
        '数据库', '配置文件'
    ]
    # 整个页面的关联度有待考究, 偏差太大?
    # has_count = []
    # for want in nice_words:
    #     if want not in has_count and want in content:
    #         cur_page_score += 5
    #         has_count.append(want)

    assets = []
    if repo in OVERVIEW and 'assets' in OVERVIEW[repo]:
        assets = OVERVIEW[repo]['assets']
    emails = []
    if repo in OVERVIEW and 'emails' in OVERVIEW[repo]:
        emails = OVERVIEW[repo]['emails']

    last_line = ''
    for line in content.split('\n'):
        line = line.strip()
        if KEYWORD in line:
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            url_pattern = r'https?://[^\s]+(?:\.com|\.cn)(?:\.cn)?'
            domain_pattern = r'\b(?:[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\.)+(?:com|cn)(?:\.cn)?\b'
            email_pattern = r'\b[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\.)+(?:com|cn)(?:\.cn)?\b'

            ip_addr = re.findall(ip_pattern, line)
            for ip in ip_addr:
                if ip.startswith('10.') or ip.startswith('172.') or ip.startswith('192.') or ip.startswith('127.'):
                    continue
                if ip not in assets:
                    assets.append(ip)

            mails = re.findall(email_pattern, line)
            if len(mails) > 0:
                cur_page_score += 10
            for mail in mails:
                if mail not in emails:
                    emails.append(mail)

            if 'http' in line:
                links = re.findall(url_pattern, line)
                for link in links:
                    if KEYWORD in link and link not in assets:
                        assets.append(link)
            else:
                links = re.findall(domain_pattern, line)
                for link in links:
                    if KEYWORD in link and link not in assets:
                        assets.append(link)

            cur_page_score += check_one_line(line, nice_words)
            # 同时检查上一行
            cur_page_score += check_one_line(last_line, nice_words)

        last_line = line

    if cur_page_score > 0:
        cur_page_score += is_language_file(path)
        cur_page_score += is_config_file(path)


    if repo not in OVERVIEW:
        OVERVIEW[repo] = {
            'score': 0,
            'assets': [],
            'emails': [],
            'path': {},
        }
    OVERVIEW[repo]['path'][path] = cur_page_score
    OVERVIEW[repo]['assets'] = assets
    OVERVIEW[repo]['emails'] = emails
    OVERVIEW[repo]['score'] += cur_page_score
    # print(f"cur_page_score: {cur_page_score}")


def filter_punish():
    """降低/去除噪音"""
    global OVERVIEW
    for repo in OVERVIEW:
        has_lang = False
        # 必须要有程序语言文件, 否则只计算 60%
        for path in OVERVIEW[repo]['path']:
            if is_language_file(path) > 0:
                has_lang = True
                break
        if not has_lang:
            OVERVIEW[repo]['score'] = round(OVERVIEW[repo]['score'] * 0.6, 2)


def analysis():
    global OVERVIEW
    assets = []
    emails = []
    filter_punish()
    OVERVIEW = dict(sorted(OVERVIEW.items(), key=lambda x: x[1]['score'], reverse=True))

    for repo in OVERVIEW:
        first_line = True
        for path in OVERVIEW[repo]['path']:
            if first_line:
                print(f"{repo:<30} {path:<30} {OVERVIEW[repo]['path'][path]}")
                first_line = False
            else:
                print(f"{'':<30} {path:<30} {OVERVIEW[repo]['path'][path]}")
                first_line = False

        for one in OVERVIEW[repo]['assets']:
            if one not in assets:
                assets.append(one)

        for one in OVERVIEW[repo]['emails']:
            if one not in emails:
                emails.append(one)

        total_score = OVERVIEW[repo]['score']
        score_style = str(total_score)
        if total_score >= 60:
            score_style = f"\033[1;32;40m  {score_style}  \033[0m"
        elif total_score > 30:
            score_style = colored(score_style, 'green')
        else:
            score_style = colored(score_style, 'grey', on_color='on_white', attrs=['bold'])

        print(f"{'':<30} {'':<30} {score_style}")
        print("-" * 100)
    
    cprint(f"[*] find {len(assets)} assets", 'green', attrs=['bold'])

    save_dir = f"results/{KEYWORD}"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    result_fn = os.path.join(save_dir, 'result.json')
    assets_fn = os.path.join(save_dir, 'assets.txt')
    email_fn = os.path.join(save_dir, 'emails.txt')
    with open(assets_fn, 'w') as f:
        for one in assets:
            f.write(f"{one}\n")
    with open(email_fn, 'w') as f:
        for one in emails:
            f.write(f"{one}\n")

    # 分开存
    with open(result_fn, 'w') as f:
        json.dump(OVERVIEW, f, indent=2, ensure_ascii=False)


def process_one_page(page, keyword):
    global SEARCH_PAGE
    url = f"https://github.com/search?q={keyword}&type=code&p={page}"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Cookie": f"user_session={COOKIE}; logged_in=yes; tz=Asia%2FShanghai; has_recent_activity=1;",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers)
    result = resp.json()
    if len(result['payload']['results']) == 0:
        cprint("[!] can't fetch back github search results, maybe end", color='red', attrs=["bold"])
        SEARCH_PAGE = 0
        return

    for one in result['payload']['results']:
        process_one_file(one)


def banner():
    print("""
  _         _   _       _____ _                 _      ____             
 | |    ___| |_( )___  |_   _| |__   __ _ _ __ | | __ |  _ \  _____   __
 | |   / _ \ __|// __|   | | | '_ \ / _` | '_ \| |/ / | | | |/ _ \ \ / /
 | |__|  __/ |_  \__ \   | | | | | | (_| | | | |   <  | |_| |  __/\ V / 
 |_____\___|\__| |___/   |_| |_| |_|\__,_|_| |_|_|\_\ |____/ \___| \_/  
                                                                        
""")


def config_init():
    config_fn = './config.yml'
    if os.path.exists(config_fn):
        return

    cprint(f"[*] seem like the first run, init config.yml")
    shutil.copyfile('./config_example.yml', config_fn)


def main():
    cprint(f"[+] will fetch back {SEARCH_PAGE} pages", 'green')
    keywords = [KEYWORD]
    for one in EXTRA_KEYWORD:
        one = f"{KEYWORD} {one}"
        keywords.append(one)

    for keyword in keywords:
        for i in range(SEARCH_PAGE):
            i += 1
            cprint(f"[+] keyword: `{keyword}` process page {i}...")
            process_one_page(i, keyword)
            if i >= SEARCH_PAGE:
                break
    analysis()


if __name__ == "__main__":
    banner()
    parser = argparse.ArgumentParser(description="Let's Thank Dev!")

    parser.add_argument('-k', '--keyword', required=True, type=str, help='域名/目标')
    parser.add_argument('-s', '--session', required=True, type=str, help='github session')
    parser.add_argument('-p', '--page', type=int, help='github search page nums')
    parser.add_argument('-m', '--min', type=int, help='filter minimum score')

    args = parser.parse_args()
    KEYWORD = args.keyword
    COOKIE = args.session
    if args.page is not None:
        SEARCH_PAGE = int(args.page)

    
    load_custom_weights()
    cprint(f"[+] start to crawl github, using keyword {KEYWORD}", color='green', attrs=['bold'])
    
    main()
    # analysis()
    
    # process_one_file('')