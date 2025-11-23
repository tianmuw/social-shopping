# posts/tasks.py
from celery import shared_task
from .models import AssociatedProduct

# 导入爬虫库
import requests
from bs4 import BeautifulSoup


# def scrape_product_info(url):
#     """
#     一个 *极其简单* 的爬虫函数。
#     它只尝试抓取 <title> 和 <img> 标签。
#
#     注意：这个爬虫很脆弱，对天猫/京东 100% 会失败，
#     因为它们有反爬机制。但它足以 *验证我们的异步流程*。
#     """
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#         'Accept-Language': 'en-US,en;q=0.9',
#     }
#
#     try:
#         response = requests.get(url, headers=headers, timeout=10)
#         response.raise_for_status() # 如果是 4xx 或 5xx 错误，就抛出异常
#
#         soup = BeautifulSoup(response.text, 'html.parser')
#
#         # 1. 尝试获取标题
#         title = soup.find('title')
#         product_title = title.string.strip() if title else '标题抓取失败'
#
#         # 2. 尝试获取第一张图片 (非常不准，仅为演示)
#         image = soup.find('img')
#         product_image_url = image['src'] if image and image.get('src') else None
#
#         # 3. 尝试获取价格 (几乎不可能用通用方式抓到)
#         product_price = "价格无法抓取"
#
#         # 如果图片 URL 是相对路径 (例如 /images/pic.jpg)，尝试补全
#         if product_image_url and product_image_url.startswith('/'):
#             from urllib.parse import urljoin
#             product_image_url = urljoin(url, product_image_url)
#
#         return {
#             'title': product_title,
#             'image_url': product_image_url,
#             'price': product_price,
#         }
#
#     except requests.RequestException as e:
#         print(f"抓取失败: {e}")
#         return None


# backend/posts/tasks.py

# ... (from celery import ..., from .models import ... , import requests, from bs4 ...)

# (!!!) 用下面的代码替换你旧的 scrape_product_info 函数 (!!!)

def scrape_product_info(url):
    """
    一个 *更健壮* 的爬虫函数。
    它会尝试处理 Base64 图片和相对路径。
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 尝试获取标题
        title = soup.find('title')
        product_title = title.string.strip() if title else '标题抓取失败'

        # 2. (新!) 尝试获取第一张图片 (更健壮的逻辑)
        image = soup.find('img')
        product_image_url = None # 默认为 None
        if image and image.get('src'):
            src = image.get('src')

            if src.startswith('data:image'):
                # 这是一个 Base64 编码的图片, 我们不保存它
                product_image_url = None
            elif src.startswith('//'):
                # 像 //example.com/img.png 这样的协议相对 URL
                product_image_url = f"https:{src}"
            elif src.startswith('/'):
                # 相对 URL (例如 /images/logo.png)
                from urllib.parse import urljoin
                product_image_url = urljoin(url, src)
            elif src.startswith('http'):
                # 完整的绝对 URL
                product_image_url = src

        # 3. 尝试获取价格 (依然很难)
        product_price = "价格无法抓取"

        # (!!!) 最终保险 (!!!)
        # 在返回前，确保 URL 不会超过数据库限制
        # 我们留 20 个字符的余地，所以截断到 1000
        if product_image_url and len(product_image_url) > 1000:
            product_image_url = product_image_url[:1000]

        if product_title and len(product_title) > 500: # 顺便也保险一下 title
            product_title = product_title[:500]

        return {
            'title': product_title,
            'image_url': product_image_url,
            'price': product_price,
        }

    except requests.RequestException as e:
        print(f"抓取失败: {e}")
        return None


# 这就是 Celery 任务！
@shared_task
def task_scrape_product(product_id):
    """
    Celery 异步任务：根据 product_id 抓取商品信息
    """
    try:
        product = AssociatedProduct.objects.get(id=product_id)
    except AssociatedProduct.DoesNotExist:
        return f"Product with id {product_id} not found."

    scraped_data = scrape_product_info(product.original_url)

    if scraped_data:
        # 抓取成功，更新数据库
        product.product_title = scraped_data['title']
        product.product_image_url = scraped_data['image_url']
        product.product_price = scraped_data['price']
        product.scrape_status = AssociatedProduct.ScrapeStatus.SUCCESS
        product.save()
        return f"Success: Scraped {product.original_url}"
    else:
        # 抓取失败
        product.scrape_status = AssociatedProduct.ScrapeStatus.FAILED
        product.save()
        return f"Failed: Could not scrape {product.original_url}"