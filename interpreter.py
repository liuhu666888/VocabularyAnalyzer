# -*- coding: utf-8 -*-

from flask import Flask, request, render_template
import re
import os
import json
import sqlite3
import nlp
import cambridge_crawler

# Phonetic Transcription Interpreter

app = Flask(__name__)
app.static_folder = 'static'
@app.route('/phonetic_transcription_interpreter', methods=['GET'])
def submit_page():
	return render_template('submit.html')

@app.route('/phonetic_transcription_interpreter', methods=['POST'])
def processing():
	text = request.form["text"]
	# 断句分词
	matrix = []  # 每行都是句子被分词之后的
	for sentence in nlp.sentence_tokenizer(text):
		matrix.append(nlp.regex_tokenizer(sentence))
	'''
	生成字典，其对应的json字符串如下：
	refer_dict_str = '{
		"word1":{"pos_pron":["pos1:pron1", "pos2:pron2,pron3"], "index":0},
		"word2":{"pos_pron":["pos1:pron1", "pos2:pron2,pron3"], "index":0},
		"word3":{"pos_pron":["pos1:pron1", "pos2:pron2,pron3"], "index":0}
	}'
	'''
	refer_dict = {}
	for row in matrix: # 一行
		for word in row: # 行中某个词
			pos_pron = cambridge_crawler.crawler(word)
			# pos_pron 是一个list，存储了该单词每个词性的音标
			refer_dict[word] = {"pos_pron":pos_pron, "index":0}
	
	# 字典转json字符串
	refer_dict_str = json.dumps(refer_dict)

	# 组装 HTML 片段
	content_block = ""
	for row in matrix: # 一行
		# 行首加一格空的div，以便换行
		content_block += "<div class=\"no-data\"></div>"		
		for word in row: # 行中某个词
			pos_pron = refer_dict[word]["pos_pron"]
			content_block += \
				"<div class=\"group\">\n" +\
				"\t<p class=\"word\">" + word + "</p>" +\
				"\t<p class=\"pronunciation\">" + pos_pron[0] + "</p>" +\
				"</div>\n"
		# 一行拼接完成
	# 循环完成后，HTML 片段生成完毕
	print(refer_dict_str)
	return render_template('result.html',
	                       refer_dict_str=refer_dict_str,
	                       content_block=content_block)

if __name__ == '__main__':
	app.run()
	#interpreter('source_text.txt')