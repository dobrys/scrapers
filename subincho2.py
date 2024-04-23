import time
import asyncio
from urllib.parse import urlparse, parse_qs

import aiohttp
from bs4 import BeautifulSoup
import json


class PageFetcher:
    # https: // subincho.com / index.php?route = account / login
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), cookie_jar=aiohttp.CookieJar())
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def login(self, login_url, username, password):

        data = {'email': username, 'password': password}

        async with self.session.post(login_url, data=data) as response:
            print(response)
            if response.status == 200:
                print(f"Logged in successfully as {username}!")
            else:
                print(f"Failed to log in as {username}!")

    async def is_loged(self, url):
        async with self.session.get(url, allow_redirects=False) as response:
            if response.headers['Location'] == 'https://subincho.com/index.php?route=account/login':
                return False
            return True

    def print_cookies(self, cookies):
        # json_object = json.dumps(cookies, indent=4)

        # Print JSON object
        # print("json cookies::", json_object)
        for cookie, details in cookies.items():
            print("cookie:", cookie, details)
            # for detail, value in details.items():
            #     print("details:", detail,value )

    def print_headers(self, headers):
        for header in headers.items():
            print("header:", header)

    async def fetch_html(self, url):
        async with self.session.get(url) as response:
            # cookies = self.session.cookie_jar.filter_cookies('https://subincho.com')
            # self.print_headers(response.headers)
            # self.print_cookies(cookies)
            # exit(44)
            return await response.text()


def fix_decimal_separator(string_value):
    fixed = string_value.replace(',', '.')
    return fixed


def __remove_extra_dot(string):
    # Проверка дали има точно две точки в стринга
    if string.count('.') == 2:

        second_dot_index = string.find('.', string.find('.') + 1)
        # Премахване на всичко след втората точка
        string_without_extra_dots = string[:second_dot_index]
        print("string_without_extra_dots:", string_without_extra_dots)
        return string_without_extra_dots
    else:
        # Ако няма точно две точки, връщаме оригиналния стринг
        return string


def remove_extra_dot(string):
    # Проверка дали има точно две точки в стринга
    if string.count('.') == 2:
        # Намиране на позицията на първата точка
        first_dot_index = string.find('.')
        # Изтриване на първата точка
        string_without_first_dot = string[:first_dot_index] + string[first_dot_index + 1:]
        return string_without_first_dot
    else:
        # Ако няма точно две точки, връщаме оригиналния стринг
        return string


def string_to_float(value):
    fl = remove_extra_dot(fix_decimal_separator(value))
    ret = float(fl)
    # print(f"string:{fl} to float:{ret}")
    return ret


async def save2json(file_name, data):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def fetch_categories(page_fetcher, url):
    print(f"Fetching categories...")
    html = await page_fetcher.fetch_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    categories_div = soup.find_all("div", {"id": "myDropdown"})
    links = soup.select('#myDropdown a')
    hrefs = [link['href'] for link in links]
    return hrefs


async def fetch_links_for_category(page_fetcher, url, base_url):
    details = []
    product_currency = 'лв.'
    off = base_url + "/"
    category_label = url.replace(off, "")
    extra = r"?limit=1200&sort=p.date_added&order=DESC"
    bokluk = '&sort=p.date_added&order=DESC&limit=1200'
    url += extra
    # print(url)

    # print("fetching pages in:", category_label)
    html = await page_fetcher.fetch_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    products = soup.find_all("div", {"class": "product-block-inner"})

    have_discount = False
    for product in products:
        if product is None:
            print("product:", product)
            exit(43)
        product_prices = product.find("p", {"class": "price"})
        product_prices_old = product_prices.find("span", {"class": "price-old"})
        product_prices_new = product_prices.find("span", {"class": "price-new"})
        # print(product_prices, "\n--------------------------\n\n")
        # print(product_prices_old, product_prices_new, "\n")
        if product_prices_old:
            try:
                price_old = string_to_float(product_prices_old.text.strip().split()[0])
                have_discount = True
            except Exception as e:
                print("product_prices_old::error:", e)
                price_old = 0
                have_discount = False
        else:
            price_old = 0
            have_discount = False
        if product_prices_new:
            try:
                price_new = string_to_float(product_prices_new.text.strip().split()[0])
            except Exception as err:
                print("product_prices_new::error:", err)
                price_new = 0
        else:
            try:
                price_new = string_to_float(product_prices.text.strip().split()[0])
                # print("A price_new:", price_new)
            except Exception as ebasi:
                print("ebasi:", ebasi)
                price_new = 0
        # print("price_old:", price_old)
        # print("price_new:", price_new)
        product_link = product.find("h4").find("a")
        product_name = product_link.text
        product_href = product_link["href"].replace(bokluk, "")
        parsed_url = urlparse(product_href)
        product_id = parse_qs(parsed_url.query)['product_id'][0]
        try:
            # img = product.find("img", {"class": "reg-image"})["src"]
            img = product.find("img", {"class": "img-responsive"})["src"]
            product_img = base_url + '/' + img
        except Exception as fuck:
            print("try::EXCEPT::Category:", category_label)
            print("try::EXCEPT::product ID:", product_id)
            print("try::EXCEPT::product name:", product_name)
            print("try::EXCEPT::url:", url)
            product_img = 'none'
            # print("fuck:", fuck)

        product_desc = product.find("p", {"class": "desc"}).text.strip()
        # print(product_name, "\n")
        # print(product_href, "\n")

        info = {
            "product_category": category_label,
            "product_id": product_id,
            "product_name": product_name,
            "product_desc": product_desc,
            "product_have_discount": have_discount,
            "product_price_new": price_new,
            "product_price_old": price_old,
            "product_currency": product_currency,
            "product_url": product_href,
            "product_image": product_img
        }
        details.append(info)

    details.sort(key=lambda x: x["product_price_new"])
    return details


async def main():
    debug = False
    for_me = False
    base_url = 'https://subincho.com'
    all_links = []
    login_url = 'https://subincho.com/index.php?route=account/login'
    user = "dobry.stoev@gmail.com"
    password = "Pti4kaViFelina"
    file = "subincho.json"

    async with PageFetcher() as page_fetcher:

        # await page_fetcher.login(login_url, "dobry.stoev@gmail.com", page_fetcher)
        if for_me:
            file = "my.subincho.json"
            is_logged = await page_fetcher.is_loged('https://subincho.com/index.php?route=account/account')
            if is_logged:
                print("Already Logged-IN")
            else:
                print("Log-In now ...")
                await page_fetcher.login(login_url, user, password)

        if debug:
            file = "debug." + file;
            all_links = await fetch_links_for_category(page_fetcher, "https://subincho.com/komputri", base_url)
            # for link in all_links:
            #     print("------------------------")
            #     for key, value in link.items():
            #         # print("product:", prod)
            #         print(f" {key} : {value}")
        else:
            categories = await fetch_categories(page_fetcher, base_url)

            links_tasks = []
            for category in categories:
                # print("preparing task for category:", category)
                links_tasks.append(fetch_links_for_category(page_fetcher, category, base_url))
            all_links = await asyncio.gather(*links_tasks)
            print(all_links)
            # for link in all_links:
            #     print("------------------------")
            #     for key, value in link.items():
            #         # print("product:", prod)
            #         print(f" {key} : {value}", type(value))

        await save2json(file, all_links)


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds.")
