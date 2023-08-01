import requests
from bs4 import BeautifulSoup

# 设置查询关键词和搜索引擎列表
keyword = "定增保底协议效力"
search_engines = ["https://www.baidu.com/s", "https://www.sogou.com/web"]

# 遍历搜索引擎列表，查询关键词
for engine in search_engines:
    # 构造查询参数
    params = {"wd": keyword}

    # 发送 GET 请求，并解析返回的 HTML 页面
    response = requests.get(engine, params=params)
    print(response.text)
    soup = BeautifulSoup(response.text, "html.parser")

    # 提取搜索结果条目中的标题和链接
    for item in soup.select(".result"):
        title = item.select_one("h3").get_text().strip()
        link = item.select_one(".c-showurl").get_text().strip()

        # 输出结果
        print(f"{title}\\n{link}\\n")