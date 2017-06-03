# -*- coding: utf-8 -*-

import sys
sys.path.append("utils")
from flask import request, render_template, Blueprint
import json
import sqlite3
import time
import nlp
import cambridge_crawler
import database

# Phonetic Transcription Interpreter

# 创建 Blueprint
bp_pti = Blueprint("Phonetic Transcription Interpreter", __name__)

# 提交文本的页面
@bp_pti.route('/phonetic_transcription_interpreter', methods=['GET'])
def submit():
	return render_template('pti_submit.html')

# 处理数据并返回结果页面
@bp_pti.route('/phonetic_transcription_interpreter', methods=['POST'])
def processing():
	start_time = time.time()  # 计时起点
	# 读取用于拼写检查的超级单词表
	with open("data/words.txt") as fd:
		ultra_word_list = fd.read().split()
	text = request.form["text"]
	# 断句分词
	matrix = []  # 每行都是句子被分词之后产生的单词列表
	for sentence in nlp.nltk_sentence_tokenizer(text):
		matrix.append(nlp.nltk_word_tokenizer(sentence))
	'''
	生成参考字典，其格式如下：
	refer_dict = '{
		"word1":{"pos_pron":["pos1:pron1", "pos2:pron2,pron3"], "index":0},
		"word2":{"pos_pron":["pos1:pron1", "pos2:pron2,pron3"], "index":0},
		"word3":{"pos_pron":["pos1:pron1", "pos2:pron2,pron3"], "index":0}
	}'
	'''
	# refer_dict 用于转为 json 字符串并写入 HTML 页面供 JavaScript 使用
	refer_dict = {}
	# wait_to_save 用于暂时存储将要写入数据库的新词数据：{"word":"pos_pron",...}
	wait_to_save = {}
	db = database.DatabaseManager()
	db.open()
	for row in matrix: # 一行
		for word in row: # 行中某个词
			print("Current Word: %s" %word)
			# 首先检测 word 是不是英语单词
			if word.lower() not in ultra_word_list:
				refer_dict[word.lower()] = {"pos_pron":[":"], "index":0}
				print("%s 不是英语单词" %word)
				continue
			pos_pron_str = db.query(word.lower())
			if pos_pron_str is not None:
				# 数据库查出的是字符串，要转为list类型
				pos_pron = json.loads(pos_pron_str)
				print("Hit in DB cache.")
			else:
				pos_pron = cambridge_crawler.crawler(word.lower())
				# 传给数据库时保证键值都是字符串类型
				wait_to_save[word.lower()] = json.dumps(pos_pron)
				print("Crawl from URL.")
			# pos_pron 是一个list，存储了该单词每个词性的音标
			refer_dict[word.lower()] = {"pos_pron":pos_pron, "index":0}
	
	# 将新的数据保存到数据库
	db.save_to_db(wait_to_save)
	db.close()
	
	# 组装 HTML 片段
	content_block = ""
	text_wc = 0
	for row in matrix: # 一行
		# 行首加一格空的div，以便换行
		content_block += "<div class=\"no-data\"></div>"		
		for word in row: # 行中某个词
			pos_pron_element = refer_dict[word.lower()]["pos_pron"][0]
			pos = pos_pron_element.split(":")[0]
			pron = pos_pron_element.split(":")[1]
			content_block += "<div class=\"group\" title=\"%s\">\n"	\
			                  "\t<p class=\"word\">%s</p>"		\
			                  "\t<p class=\"pronunciation\">%s</p>"	\
			                  "</div>\n"				\
			                  %(pos, word, pron)
			text_wc += 1
		# 一行拼接完成
	# 循环完成后，HTML 片段生成完毕

	# 字典转json字符串
	refer_dict_str = json.dumps(refer_dict)

	# print(refer_dict_str)
	end_time = time.time()  # 计时终点
	elapsed_time = end_time-start_time
	content_block = ("<h5>输入词汇数: %d</h5>" %text_wc) \
		+ ("<h5>执行时间: %f</h5>" %elapsed_time) \
	        + content_block
	return render_template('pti_result.html',
	                       refer_dict_str=refer_dict_str,
	                       content_block=content_block)
