# -*- coding: utf-8 -*-
import bs4
import requests

from bs4 import BeautifulSoup
from threading import Thread


class YueDu88:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 8.0.0; "
                                      "Pixel 2 XL Build/OPD1.170816.004) "
                                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                                      "Chrome/86.0.4240.198 Mobile Safari/537.36"}
        self.book_name = ""
        self.first_chapter_id = 0
        self.last_chapter_id = 0
        self.download = {}

    def get_soup(self, url):
        """
        解析页面, 返回BeautifulSoup对象
        :param url: 页面连接
        :return: BeautifulSoup对象
        """
        response = requests.get(url=url, headers=self.headers)
        if response.status_code == 200:
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "lxml")
            return soup
        else:
            print(f"url:{url}下载失败:{response.reason}")

    def get_parsed_text(self, chapter_url):
        """
        解析某一页小说页面内容
        :param chapter_url: 输入章节连接，例如：http://www.yuedu88.com/ndxnfwnds/63601.html
        :return: 返回 章节名和内容
        """
        soup = self.get_soup(chapter_url)

        if soup:
            # 章节名
            title = soup.find("h1").text.strip()

            # 内容
            text_list = soup.find("div", attrs={"id": "BookText"})
            text = get_all_text(text_list)[1]

            chapter_id = chapter_url.split("/")[-1].split(".")[0]  # 提取出数字63601
            chapter = title + "\n\n" + text

            # 用多线程下载，先存到一个字典
            self.download.update({int(chapter_id): chapter})
            print(f"章节:{title}下载成功，id:{chapter_id}")
            return chapter

    def get_chapters(self, book_url):
        """
        获取第一章节到最后章节的ID

        :param book_url: 书的连接 http://www.yuedu88.com/ndxnfwnds
        :return: 第一章节到最后章节的ID (63600, 63644)
        """
        soup = self.get_soup(book_url)
        # 书名
        self.book_name = soup.find("h1").text

        # 有些书的章节分开几页存放，有的书没有分页按钮
        page_urls = soup.find("div", attrs={"class": "pagebar"}).find_all("a")
        if page_urls:
            first_page_url = page_urls[0]["href"]
            last_page_url = page_urls[-1]["href"]
        else:
            first_page_url = book_url
            last_page_url = book_url

        first_chapter_id = self._get_first_chapter_id(first_page_url)
        last_chapter_id = self._get_last_chapter_id(last_page_url)

        self.first_chapter_id = first_chapter_id
        self.last_chapter_id = last_chapter_id
        print(f"获取章节ID成功，first:{first_chapter_id}, last:{last_chapter_id}")
        return first_chapter_id, last_chapter_id

    def _get_first_chapter_id(self, book_url):
        """
        获取页面最前面的章节的ID
        :param book_url: http://www.yuedu88.com/ndxnfwnds
        :return:
        """
        soup = self.get_soup(book_url)

        # 页面最前面的章节的连接
        link = str(soup.find("li").a["href"])  # http://www.yuedu88.com/ndxnfwnds/63600.html
        first_chapter = link.split("/")[-1].split(".")[0]  # 提取出数字63600 这是第一章的页面
        return int(first_chapter)

    def _get_last_chapter_id(self, book_url):
        """
        获取页面最后面的章节的ID
        :param book_url: http://www.yuedu88.com/ndxnfwnds/2/
        :return:
        """
        soup = self.get_soup(book_url)

        # 页面最后面的章节的连接
        link = str(soup.find_all("li")[-1].a["href"])  # http://www.yuedu88.com/ndxnfwnds/63644.html
        last_chapter = link.split("/")[-1].split(".")[0]  # 提取出数字63644 这是最后章的页面
        return int(last_chapter)

    def download_book(self, book_url):
        # 多线程任务
        tasks = []
        self.get_chapters(book_url)
        for i in range(self.first_chapter_id, self.last_chapter_id + 1):
            url = f"{book_url}/{str(i)}.html"
            tasks.append(Thread(target=self.get_parsed_text, args=(url,)))
        # 执行多线程下载
        [t.start() for t in tasks]
        [t.join() for t in tasks]
        print(f"下载完成，共下载{len(self.download)}章节")

    def save_to_file(self, file_name=""):
        if not file_name:
            file_name = self.book_name + ".txt"
        with open(file_name, mode="w", encoding="utf-8") as f:
            for i in range(self.first_chapter_id, self.last_chapter_id + 1):
                # 判断是否有下载失败的章节
                if self.download.get(i):
                    f.write(self.download.get(i) + "\n\n\n\n\n")
                else:
                    print(f"章节{i}丢失, 所有章节{self.download.keys()}")
        print(f"文件保存成功，文件名:{file_name}")


def get_all_text(soup):
    """
    传入tag，循环取出所有的文本
    flag: 网页最下面有个“在线阅读网” 说明已经到底，停止执行循环
    :param soup: 传入tag节点
    :return:
    """
    flag = False
    text = ""
    for s in soup:
        if isinstance(s, bs4.element.Tag):
            t = get_all_text(s)
            if t[0]:
                break
            text += t[1]
        elif isinstance(s, bs4.element.NavigableString):
            if s.replace(" ", "").startswith("在线"):
                flag = True
                break
            elif s.strip():
                text += f"\n    {s.strip()}"
    return flag, text


if __name__ == "__main__":
    yd = YueDu88()
    yd.download_book("http://www.yuedu88.com/ndxnfwnds")  # 最后面不要有斜杠/
    yd.save_to_file()
