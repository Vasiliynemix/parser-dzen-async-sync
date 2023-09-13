import shutil
import uuid
from datetime import datetime

import json
import os
import aiohttp
import asyncio
from bs4 import BeautifulSoup


class AsyncParse:
    result_json_file = 'result_data.json'
    path_to_images = 'images'
    path_to_images_news = 'images/news'
    path_to_json = 'json'
    line_label_in_script = 'window.Ya.Neo.dataSource'

    def __init__(self):
        self.url = 'https://dzen.ru/news/rubric/auto?issue_tld=ru'
        self.news_data = {}
        self.content = {}
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.session.__aexit__(exc_type, exc_value, traceback)

    async def __create_images_folder(self):
        if not os.path.exists(self.path_to_images):
            os.mkdir(self.path_to_images)
        if os.path.exists(self.path_to_images_news):
            shutil.rmtree(self.path_to_images_news)
        os.mkdir(self.path_to_images_news)

    async def __create_json_folder(self):
        if os.path.exists(self.path_to_json):
            shutil.rmtree(self.path_to_json)
        os.mkdir(self.path_to_json)

    async def __save_json_static(self):
        path = f'{self.path_to_json}'
        if not os.path.exists(path):
            os.mkdir(path)

        with open(f'{path}/{self.news_data["datetime"]}.json', 'a') as file:
            json.dump(self.news_data, file, indent=4, ensure_ascii=False)

    async def __save_images_static(self):
        path = f'{self.path_to_images_news}/{self.news_data["datetime"]}'
        if not os.path.exists(path):
            os.mkdir(path)

        try:
            async with self.session.get(self.content['image']) as big_image:
                async with self.session.get(self.content['preview']) as small_image:
                    with open(f'{path}/{uuid.uuid4()}.jpg', 'wb') as file:
                        file.write(await big_image.read())

                    with open(f'{path}/{uuid.uuid4()}.jpg', 'wb') as file:
                        file.write(await small_image.read())

        except Exception as ex:
            print(ex)

    async def __get_json_info(self, url: str) -> dict:
        async with self.session.post(url=url) as response:
            content = await response.text()
            soup = BeautifulSoup(content, 'lxml')
            all_scripts = soup.find_all('script')
            for script in all_scripts:
                text = str(script)
                if self.line_label_in_script in text:
                    json_data = json.loads(text.split('window.Ya.Neo.dataSource')[1][1:-1])
                    return json_data.get('news')

    def __full_image_is_none(self, url: str) -> bool:
        if url is None:
            self.content['preview'] = 'Нет изображения'
            self.content['image'] = 'Нет изображения'
            return False
        return True

    def __save_image_content(self, item: dict):
        full_image_url = item.get('mediaContent')
        if not self.__full_image_is_none(url=full_image_url):
            return

        full_image_url = full_image_url.get('additionalSizes')
        if not self.__full_image_is_none(url=full_image_url):
            return

        full_image_url = full_image_url.get('square-big')
        if not self.__full_image_is_none(url=full_image_url):
            return

        full_image_url = full_image_url.get('src')
        if not self.__full_image_is_none(url=full_image_url):
            return

        count = len(full_image_url.split('/')[-1])
        image_url = full_image_url[:-count]
        self.content['preview'] = image_url + '366x183'
        self.content['image'] = image_url + '800x400'

    def __sub_data_is_none(self, sub_data: dict) -> bool:
        if sub_data is None:
            self.content['subtitle'] = []
            return False
        return True

    async def __save_content(self, item: dict) -> dict:
        self.content['title'] = item.get('title').replace('\xa0', ' ')
        self.content['link'] = item.get('url')

        self.__save_image_content(item=item)

        data = await self.__get_json_info(url=self.content.get('link'))

        subtitle_other_list = []
        subtitle_list = []
        if data.get('story').get('tail'):
            for subtitles_other in data.get('story').get('tail'):
                subtitle_other_list.append(subtitles_other.get('title').replace('\xa0', ' '))
        self.content['subtitles_other'] = subtitle_other_list

        sub_data = data.get('story')
        if not self.__sub_data_is_none(sub_data=sub_data):
            return self.content

        sub_data = sub_data.get('summarization')
        if not self.__sub_data_is_none(sub_data=sub_data):
            return self.content

        sub_data = sub_data.get('items')
        if not self.__sub_data_is_none(sub_data=sub_data):
            return self.content

        for subtitle in sub_data:
            subtitle_list.append(subtitle.get('text').replace('\xa0', ' '))
        self.content['subtitle'] = subtitle_list
        return self.content

    async def __save_item(self, item: dict):
        time = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S%f")
        self.news_data['datetime'] = time
        content = await self.__save_content(item=item)
        self.news_data['content'] = [content]
        print(self.content['title'])
        print(self.content['link'])
        print(self.content['subtitles_other'])
        print(self.content['subtitle'])
        print('*' * 100)
        print('\n')

    async def __get_data(self, data: dict, value: str):
        news = data.get(value)
        for item in news:
            await asyncio.gather(
                self.__save_item(item=item),
                self.__save_json_static(),
                self.__save_images_static()
            )

    async def parse(self):
        print('=============================---parser start---=============================')
        await self.__create_images_folder()
        await self.__create_json_folder()

        data = await self.__get_json_info(url=self.url)

        await self.__get_data(data=data, value='top')
        await self.__get_data(data=data, value='feed')
        print('=============================---parser stop---=============================')


async def main():
    async with AsyncParse() as async_parse:
        await async_parse.parse()

if __name__ == "__main__":
    asyncio.run(main())
