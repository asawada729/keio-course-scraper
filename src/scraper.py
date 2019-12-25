import requests
#from requests.auth import HTTPBasicAuth
import urllib.request
#import time
import json
#import re
#import pandas as pd
from bs4 import BeautifulSoup

class KeioScraper: 
	def __init__(self) :
		self.LIST_URL = "https://gslbs.adst.keio.ac.jp/list/List_Kamoku.php"
		self.COURSE_BASE_URL = "https://gslbs.adst.keio.ac.jp/lecture/View_Lecture.php"
		self.payload_pagenav = {
			"hid_nowpage": "1",
			"hid_pagemode": "no_edit",
			"hid_sortname_now": "lec・day・tea",
			"hid_sortmode_now": "asc・asc・asc",
			"hid_sidemode": "0",
		}

		#self.course_df = pd.DataFrame()
		#self.course_df.to_csv("course_list.csv")

	def set_boundaries(self, soup_first_page) :
		self.NUM_COURSES_QUERIED = int(soup_first_page.find(class_="hit_count").font.string)
		self.LAST_PAGE_NUM = (self.NUM_COURSES_QUERIED // 50) + 1

	def scrape_all(self, payload) :
		self.payload = payload

		soup_first_page = self.soupify_post(self.LIST_URL, self.payload)
		self.set_boundaries(soup_first_page)
		print("Scraping ", self.LAST_PAGE_NUM, " pages with ", self.NUM_COURSES_QUERIED, " courses...\n")

		soup_current_page = soup_first_page
		for page_num in range(1, self.LAST_PAGE_NUM + 1) :
			print("Going to page ", page_num, " ...")
			self.scrape_page(soup_current_page.find(id="list_table_header").find_all("a", href="#")[6:])

			self.payload_pagenav["hid_nowpage"] = page_num + 1
			soup_current_page = self.soupify_post(self.LIST_URL, self.payload_pagenav)

	def scrape_page(self, soup_a_tags) :
		print(soup_a_tags[0])

	def soupify_post(self, url, payload) :
		response = requests.post(url=url, data=payload)
		return BeautifulSoup(response.text, "html.parser")

#########################
## Scraper starts here ##
#########################

# Set up macro, syllabus url, and post parameters
PER_PAGE = 100 # 10, 20, 50, or 100
PAGE_INIT = 1

payload = {"sel_year": "2019",
			"chk_campus[]": "05",
			"chk_day[]": "月",
			"txt_kamoku": "",
			"sel_sort": "lecture",
			"sel_lessonlang": "0",
			"sel_view": "j",
			"hid_sidemode": "0",
			"hid_pagemode": "2",
			"hid_backlink": "../menu/Slt_Kamoku.php",
			"hid_student_menu": "0",
			"hid_nowpage": "",
           }

k = KeioScraper()
k.scrape_all(payload)		