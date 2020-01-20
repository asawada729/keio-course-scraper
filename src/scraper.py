import requests
#from requests.auth import HTTPBasicAuth
import urllib.request
import time
import json
import pandas as pd
from bs4 import BeautifulSoup
from bs4.diagnose import diagnose
import re

class KeioScraper: 
	def __init__(self) :
		self.LIST_URL = "https://gslbs.adst.keio.ac.jp/list/List_Kamoku.php"
		self.INSTANCE_URL = "https://gslbs.adst.keio.ac.jp/lecture/View_Lecture.php"
		self.payload_pagenav = {
			"hid_nowpage": "",
			"hid_pagemode": "no_edit",
			"hid_sortname_now": "lec・day・tea",
			"hid_sortmode_now": "asc・asc・asc",
			"hid_sidemode": "0",
		}
		self.payload_instance = {
			"hid_nowpage": "",
			"hid_lessoncd": "",
			"hid_tourokubango": "",
			"hid_sortname_now": "lec・day・tea",
			"hid_sortmode_now": "asc・asc・asc",
			"hid_sidemode": "0",
		}
		# self.campuses = ["01", "02", "03", "04", "05", "06"]
		self.req = requests.Session()

		self.course_df = pd.DataFrame()
		self.course_df.to_csv("course_list.csv")

	def set_boundaries(self, soup_first_page) :
		self.NUM_COURSES_QUERIED = int(soup_first_page.find(class_="hit_count").font.string)
		self.LAST_PAGE_NUM = (self.NUM_COURSES_QUERIED // 50) + 1

	def scrape_all(self, payload) :
		self.payload = payload

		# self.start = time.time()
		soup_first_page = self.soupify_post(self.LIST_URL, self.payload)
		# print("Took", time.time()-self.start, "s to load a page")
		self.set_boundaries(soup_first_page)
		print("Scraping ", self.LAST_PAGE_NUM, " pages with ", self.NUM_COURSES_QUERIED, " courses...\n")

		soup_current_page = soup_first_page
		for page_num in range(1, self.LAST_PAGE_NUM + 1) :
			print("Going to page ", page_num, " ...")
			self.scrape_page(list(filter(lambda item: item != "\n", soup_current_page.find(id="list_table_header").contents[2:])))

			self.payload_pagenav["hid_nowpage"] = page_num + 1
			# self.start = time.time()
			soup_current_page = self.soupify_post(self.LIST_URL, self.payload_pagenav)
			# print("Took", time.time()-self.start, "s to load a page")

	def scrape_page(self, soup_course_bundles) :
		#print(soup_course_bundles[0])
		# self.page_start = time.time()
		self.payload_instance["hid_nowpage"] = self.payload_pagenav["hid_nowpage"]
		for course_bundle in soup_course_bundles :
			#print(course_bundle)
			self.scrape_bundle(course_bundle.find(class_="ListTbl_in"))

		# print("Took", time.time()-self.page_start, "ms to scrape this page")

		# Append one page of courses to disk
		current_course_df = pd.read_csv("course_list.csv", index_col=0)
		pd.concat([current_course_df, self.course_df]).reset_index(drop=True).to_csv("course_list.csv")
		self.course_df = pd.DataFrame()

	def scrape_bundle(self, course_bundle) :
		for course in course_bundle.find_all("tr") :
			self.scrape_course(course)

	def scrape_course(self, course) :
		info_list = []
		for course_info in course.find_all("td") :
			info_list.append(course_info.get_text(strip=True))

		data = {}
		data["degree"] = info_list[0]
		data["faculty"] = info_list[1]
		data["major"] = info_list[2]
		data["specializations"] = info_list[3]
		data["semester"] = info_list[5]
		data["day_period"] = info_list[6]

		course_id = re.findall(r"\d+", course.find(href="#")["onclick"])
		assert len(course_id) == 2
		self.payload_instance["hid_lessoncd"] = course_id[0]
		self.payload_instance["hid_tourokubango"] = course_id[1]
		# start = time.time()
		course_page = self.soupify_post(self.INSTANCE_URL, self.payload_instance)
		# print("Took", time.time()-start, "s to load a course")

		# start = time.time()
		data["id"] = course_id[1]
		data["course_code"] = course_id[0]

		lecture_cont3 = course_page.find(class_="lecture_cont03")
		data["title_others"] = [string for string in lecture_cont3.stripped_strings]

		lecture_cont2 = [x.get_text(strip=True) for x in course_page.find_all(class_="lecture_cont02")]
		# data["year_semester"] = lecture_cont2[0]
		data["credits"] = lecture_cont2[1]
		data["campus"] = lecture_cont2[2]
		# data["faculty"] = lecture_cont2[3]

		# data["day_period"] = course_page.find(class_="lecture_cont02_youbi").get_text(strip=True)
		
		data["lecturers"] = [lecturer for lecturer in course_page.find(class_="teacher_name").stripped_strings]

		# lecture_cont = [x.get_text(strip=True) for x in course_page.find_all(class_="lecture_cont")]
		data["subtitle"] = course_page.find_all(class_="lecture_cont")[0].get_text(strip=True)
		# data["degree"] = lecture_cont[len(lecture_cont) - 1]

		self.course_df = self.course_df.append(data, ignore_index=True)
		# print("Took", time.time()-start, "s to scrape a course")

	def soupify_post(self, url, payload) :
		response = self.req.post(url=url, data=payload)
		return BeautifulSoup(response.text, "lxml")

#########################
## Scraper starts here ##
#########################

# Set up macro, syllabus url, and post parameters
PER_PAGE = 100 # 10, 20, 50, or 100
PAGE_INIT = 1

payload = {"sel_year": "2019",
			"chk_campus[]": ["01", "02", "04", "05", "06", "09"],
			"chk_day[]": "",
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
