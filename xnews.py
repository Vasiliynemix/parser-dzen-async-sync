import requests, time, json, re, shutil, os, datetime
from bs4 import BeautifulSoup

s = requests.session()
x = s.post('https://dzen.ru/news/rubric/auto?issue_tld=ru').text
soup = BeautifulSoup(x, "html.parser")
# print(x)
all_scripts = soup.find_all('script')[5].text
# print(all_scripts)
# datas = re.search(r"window.Ya.Neo.dataSource='(.*)'", all_scripts).group(1)
script = all_scripts.split("top", 1)[1]
script = script[2:]
xxa = script.split("window.Ya.Neo.dataSource", 1)[0]

# convert to dictionary
# data = json.loads(script[100:])
# print(xxa)
rx2 = r'(?<="url":)[^,]*'
res2 = re.findall(rx2, xxa)

# print(gf)
x = [n.encode().decode("unicode-escape") for n in res2]
x = x[21:-1]
# xx = re.findall(r'(url?[^\s]+")', xxa)
print('--- first method ---')
# data = json.loads(xxa)
# print(xx)
# items = [
#     item for item in soup.find_all(class_="mg-card__title")
# ]
# get = [ item.get('href') for item in items]
dd = 0
for i in x:
    now = datetime.datetime.now()
    news_data = {}
    news_data['datetime'] = str(now)
    news_data["link"] = i
    dd += 1
    p = requests.post(i.replace('"', '')).text
    soupk = BeautifulSoup(p, "html.parser")
    all_script = soupk.find_all('script')[5].text
    src = r'(?<="src":)[^,]*'

    res4r = re.findall(src, all_script)
    ssa = [n.encode().decode("unicode-escape") for n in res4r]

    full_image = ssa[0].replace('"', '')
    if 'https:' not in full_image:
        continue
    full_image = full_image[:full_image.rfind('/')]
    news_data["preview"] = full_image + '/366x183'
    news_data['image'] = full_image + '/800x400'
    print(full_image)
    data = requests.get(full_image + '/800x400', stream=True)
    data2 = requests.get(full_image + '/366x183', stream=True)

    # full_image = driver.find_element(By.CSS_SELECTOR, "#neo-page > div > div > div > div.news-app-layout__content-and-rubric.news-app-layout__content-and-rubric_with-new-layout > div.news-app__content.news-app__content_with-new-layout > div.mg-grid__row.mg-grid__row_gap_8.news-app__layout > div > div > div.mg-grid__col.mg-grid__col_xs_8 > div > article > div.mg-story__body > div.mg-media-block.news-story__media-block > div.mg-scroll.mg-scroll_is-prev-hidden.mg-media-block__previews > div > div:nth-child(2) > button > div > div:nth-child(1) > img")
    # Opening a new file named img with extension .jpg
    # This file would store the data of the image file
    xx = datetime.datetime.strftime(now, "%Y%m%d%H%M%S%f")
    os.makedirs(os.path.dirname(f'images/{xx}'), exist_ok=True)
    path = os.path.join(os.getcwd(), f'images/{xx}')
    os.mkdir(path)
    with open(f'images/{xx}/image.jpg', 'wb') as f:
        shutil.copyfileobj(data.raw, f)
    with open(f'images/{xx}/preview.jpg', 'wb') as fa:
        shutil.copyfileobj(data2.raw, fa)

        # news_data["preview"] = full_image+'/366x183'
    # news_data['image'] = full_image+'/800x400'
    title = soupk.find_all(class_='mg-story__title')
    title = title[0].text
    print(title)
    news_data["main_title"] = title

    print('==============================================================')
    other_titles = soupk.find_all(class_='mg-snippet__text')
    other_titles_text = [title.text for title in other_titles]
    news_data["subtitle"] = other_titles_text

    print(other_titles_text)
    print('==============================================================')

    more_event_titles = soupk.find_all(class_='mg-snippet__title')
    more_event_titles_text = [title.text for title in more_event_titles]
    news_data["subtitle_other"] = more_event_titles_text

    print(more_event_titles_text)
    print('==============================================================')

    patha = os.path.join(os.getcwd(), f'json/{xx}')
    os.mkdir(patha)

    # Возвращаемся на страницу со списком новостей
    # driver.back()

    with open(f"json/{xx}/parsed_news.json", "w", encoding="utf-8") as json_file:
        json.dump(news_data, json_file, ensure_ascii=False, indent=4)
    json_file.close()
