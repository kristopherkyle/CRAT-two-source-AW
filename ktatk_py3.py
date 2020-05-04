# KTATK Kris' text analysis toolkit from CRAT 1.5. Version _1 fixes synonym overlap calculation issues
from __future__ import division
import os
import re
import sys 
import platform
import shutil
import subprocess
import glob
import math
from threading import Thread
from operator import itemgetter
try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET
from collections import Counter

def version():
	print("ktatk version .01")
	
#This allows for a packaged gui to find the resource files.
def indexer(index, index_name, index_list, header_list):
	index_list.append(index)
	header_list.append(index_name)
	
def resource_path(relative):
	if hasattr(sys, "_MEIPASS"):
		return os.path.join(sys._MEIPASS, relative)
	return os.path.join(relative)

def lemma_dicter(lemma_file):
	lemma_list = open((lemma_file),'rU').read().split("\n")
	lemma_dict = {}

	for line in lemma_list:
		#ignores first lines
		if line[0] is '#':
			continue
		#allows use of each line:
		entries=line.split("\t")
		#creates dictionary entry for each word in line:
		for word in entries:
			lemma_dict[word] = entries[0]
	
	return lemma_dict

def unlemmer(lem_dict,lem_list): #takes lemma dictionary and a lemmatized list. Turns lemmatized list into unlemmatized list for the constrainer (see below)
	out_list = []
	for item in lem_list:
		if item in lem_dict:
			for x in lem_dict[item]:
				out_list.append(x)
	return out_list
	
def start_watcher(def2, count, folder, dataQueue,root):
	t2 = Thread(target=def2, args =(count,folder,dataQueue,root))
	t2.start()

def watcher(count, folder, dataQueue, root):
	import glob
	import time
	counter = 1

	while count>len(glob.glob(folder+"*")):
		##print "Count ", count
		#counter = 1
		if len(glob.glob(folder+"*")) == 0:
			if counter == 1:
				output = "Starting Stanford CoreNLP..."
				counter+=1
			elif counter == 2:
				output = "Starting Stanford CoreNLP."
				counter+=1
			elif counter == 3:
				output = "Starting Stanford CoreNLP.."
				counter+=1
				counter = 1
		else:
			output = "CoreNLP has tagged " + str(len(glob.glob(folder+"*"))) + " of " + str(count) + " files."
		dataQueue.put(output)
		root.update_idletasks()
		
		time.sleep(.3) #seconds it waits before checking again
	
	final_message = "CoreNLP has tagged " + str(count) + " of " + str(count) + " files."
	dataQueue.put(output)
	root.update_idletasks()

def call_stan_corenlp_pos(class_path, file_list, output_folder, memory, nthreads, system, dataQueue,root, parse_type = ""): #for CoreNLP 3.5.1 (most recent compatible version)
	#mac osx call:
	if system == "M":
		call_parser = "java -cp "+ class_path +"*: -Xmx" + memory + "g edu.stanford.nlp.pipeline.StanfordCoreNLP -threads "+ nthreads + " -annotators tokenize,ssplit,pos,lemma"+parse_type+" -filelist " + file_list + " -outputDirectory "+ output_folder
	#windows call:
	elif system == "W":
		call_parser = "java -cp "+ class_path +"*; -Xmx" + memory + "g edu.stanford.nlp.pipeline.StanfordCoreNLP -threads "+ nthreads + " -annotators tokenize,ssplit,pos,lemma"+parse_type+" -filelist " + file_list + " -outputDirectory "+ output_folder

	count = len(file(file_list, "rU").readlines())
	folder = output_folder
	#print "starting checker"
	start_watcher(watcher, count, folder, dataQueue,root)
	
	subprocess.call(call_parser, shell=True) #This watches the output folder until all files have been parsed

def gui_stan_corenlp(system, stan_call,in_files, memory, nthreads, dataQueue,root):

	if not os.path.exists(resource_path("parsed_files/")):
		os.makedirs(resource_path("parsed_files/"))

	if not os.path.exists(resource_path("to_process/")):
		os.makedirs(resource_path("to_process/"))

	folder_list = [resource_path('parsed_files/'), resource_path('to_process/')]

	for folder in folder_list:
		for the_file in os.listdir(folder):
			file_path = os.path.join(folder, the_file)
			os.unlink(file_path)

	###End Preprocessing###
	copy_files = in_files
	###print copy_files
	for thing in copy_files:
		thing_1=thing
		if system == "M":
			thing = thing.split("/")[-1]
			thing = resource_path("to_process/") + thing
		elif system == "W":
			thing = thing.split("\\")[-1]
			thing = resource_path("to_process\\") + thing   
		###print "origin:",thing_1
		###print "Destination:", thing
		shutil.copyfile(thing_1, thing)
	input_folder = resource_path("to_process/")
	#input_folder = re.sub(" ", "\ ", input_folder)

	#write file_list:
	list_of_files = glob.glob(input_folder + "*.txt")

	file_list_file = open(input_folder + "_filelist.txt", "w")

	file_list = (input_folder + "_filelist.txt")
	###print "file list ", file_list
	for line in list_of_files:
		line = line + "\n"	
		file_list_file.write(line)
	file_list_file.flush()
	file_list_file.close()

	stan_file_list = (input_folder + "_filelist.txt")
	###print "file list ", file_list
	###print input_folder
	
	current_directory = resource_path("./")
	stan_output_folder = "parsed_files/"
	
	stan_call(current_directory, stan_file_list, stan_output_folder, memory, nthreads, system, dataQueue,root)

def safe_divide(numerator, denominator):
	if denominator == 0:
		index = 0
	else: index = numerator/denominator
	return index

def simple_list_dict_builder(database_file, delimiter):
	dict ={}
	
	data_file = open(database_file, "rU").read().lower().split("\n")
	
	for entries in data_file:
		if entries[0] == "#":
			continue
		entries = entries.split(delimiter)
		dict[entries[0]]=entries[1:]
	return dict

def list_dict_builder(database_file, delimiter = "\t", numbers = "no"):
	dict = {}
	data_file = database_file.lower().split("\n")
	
	for lines in data_file:
		if lines == "":
			continue
		line = lines.split(delimiter)
		if numbers == "no":
			dict[line[0]] = line[1:]
		if numbers == "yes":
			key = line[0]
			value = []
			for item in line[1:]:
				item = float(item)
				value.append(item)
			dict[key] = value
	
	return dict

def list_dict_builder_nr(database_file, delimiter = "\t", numbers = "no"): #non-repeating version
	dict = {}
	data_file = database_file.lower().split("\n")
	
	for lines in data_file:
		if lines == "":
			continue
		line = lines.split(delimiter)
		if numbers == "no":
			clean_line = []
			for x in line[1:]:
				if x == line[0]:
					continue
				else:
					clean_line.append(x)
			dict[line[0]] = clean_line
		if numbers == "yes":
			key = line[0]
			value = []
			for item in line[1:]:
				item = float(item)
				value.append(item)
			dict[key] = value
	
	return dict


def lsa_list_dict_builder(database_file, grab_list, delimiter = "\t"):
	dict = {}
	data_file = database_file.lower().split("\n")
	
	number = 0
	for lines in data_file:
		#print number
		if lines == "":
			number+=1
			continue
		if number in grab_list:
			line = lines.split(delimiter)
			dict[line[0]] = line[1:]
			number +=1
		else:
			number +=1
			continue

	return dict

def dict_builder(database_file, number, log = "n", delimiter = "\t"): #builds dictionaries from database files
	dict ={}
	data_file = database_file.lower().split("\n")
	for entries in data_file:  
		if entries == "":
			continue
		if entries[0] == '#': #ignores first line which contains category information
			continue
			
		entries = entries.split(delimiter)
		if log == "n": 
			dict[entries[0]]=float(entries[number])
		if log == "y": 
			if not entries[number] == '0':
				dict[entries[0]]=math.log10(float(entries[number]))

	return dict

def dict_builder_constrained(database_file, number, log = "n", delimiter = "\t", constraint = 50000, ): #builds dictionaries from database files
	dict ={}
	data_file = database_file.lower().split("\n")
	for entries in data_file[:constraint]:  
		if entries == "":
			continue
		if entries[0] == '#': #ignores first line which contains category information
			continue
			
		entries = entries.split(delimiter)
		if log == "n": 
			dict[entries[0]]=entries[number]
		if log == "y": 
			if not entries[number] == '0':
				dict[entries[0]]=math.log10(float(entries[number]))

	return dict

def constrainer(text, constraint): #both are lists
	new_text=[]
	for word in text:
		if word in constraint:
			continue
		else:
			new_text.append(word)
	return new_text

def ngram_constrainer(text, constraint): #both are lists
	new_text=[]
	violation = []
	for ngram in text:
		wrds = ngram.split(" ")
		for x in wrds:
			if x in constraint:
				violation.append(ngram)
	for ngram in text:
		if ngram in violation:
			continue
		else:
			new_text.append(ngram)
	return new_text

def simple_sum(text,data_dict,types,null_item,index_list=None,index_name=None,header_list=None): #input is list of lists
	counter = 0
	nitems = (len(text))
	for items in text:
		counter+=DataDict_counter(items, data_dict,types,null_item, min = "yes")
	
	outvar = safe_divide(counter,nitems)
	
	if header_list == None:
		return outvar
	else:
		index_list.append(outvar)
		header_list.append(index_name)		
		
		
def DataDict_counter(in_text, data_dict,types,null_item,index_list=None,index_name=None,header_list=None, min = "no"):
	
	if types == "cw":
		text = []
		for words in in_text:
			if words in fw_stop_list:
				continue
			else: 
				text.append(words)
		in_text = text
	
	if types == "fw":
		text = []
		for words in in_text:
			if words not in fw_stop_list:
				continue
			else: 
				text.append(words)
		in_text = text			
	
	if min == "no":
		counter = 0
		sum_counter = 0
		for word in in_text:
			if word in data_dict and data_dict[word] != null_item:
				counter+=1
				sum_counter+=float(data_dict[word])
			else:
				if word in lemma_dict and lemma_dict[word] in data_dict and data_dict[lemma_dict[word]] != null_item:
					counter+=1
					sum_counter+=float(data_dict[lemma_dict[word]])
	
	if min == "yes":
		counter = 1
		for word in in_text:
			if word in data_dict and data_dict[word] != null_item:
				try:
					if float(data_dict[word]) < sum_counter:
						sum_counter = float(data_dict[word])
				except NameError:
					sum_counter = float(data_dict[word])
					
			else:
				if word in lemma_dict and lemma_dict[word] in data_dict and data_dict[lemma_dict[word]] != null_item:
					try:
						if float(data_dict[lemma_dict[word]]) < sum_counter:
							sum_counter = float(data_dict[lemma_dict[word]])
					except NameError:
						sum_counter = float(data_dict[lemma_dict[word]])

	try:
		sum_counter = sum_counter
	except UnboundLocalError:
		sum_counter = 0
					
	if header_list == None:
		return sum_counter
	
	else:
		index = safe_divide(sum_counter,counter)
		index_list.append(index)
		header_list.append(index_name)

def Mixed_DataDict_counter(in_text, data_dict,types,index_list,index_name,header_list):
	counter = 0
	sum_counter = 0
	position = 0
	
	if types == "cw":
		text = []
		for words in in_text:
			if words in fw_stop_list:
				continue
			else: 
				text.append(words)
		in_text = text
	
	if types == "fw":
		text = []
		for words in in_text:
			if words not in fw_stop_list:
				continue
			else: 
				text.append(words)
		in_text = text			
	
	if types == "cw" or types == "fw":
		for word in in_text:
			if word in data_dict and data_dict[word] is not "0":
				counter+=1
				sum_counter+=float(data_dict[word])
			else:
				if word in lemma_dict and lemma_dict[word] in data_dict and data_dict[lemma_dict[word]] is not "0":
					counter+=1
					sum_counter+=float(data_dict[lemma_dict[word]])
	
	if types == "aw":
		for item in in_text:
			if position > len(in_text)-1:
				continue
			word = in_text[position]
				
			if len(in_text[position:]) == 1:
				if word in data_dict and data_dict[word] is not "0":
					counter+=1
					sum_counter+=float(data_dict[word])
					position+=1
					continue
				elif word in lemma_dict and lemma_dict[word] in data_dict and data_dict[lemma_dict[word]] is not "0":
						counter+=1
						sum_counter+=float(data_dict[lemma_dict[word]])
						position += 1
						continue
				else: position+=1
				
			else:
				bigram = " ".join(in_text[position:position +1])
				if bigram in data_dict and data_dict[bigram] is not "0":
					counter+= 1
					sum_counter += float(data_dict[bigram])
					position +=2
				else:
					if word in data_dict and data_dict[word] is not "0":
						counter+=1
						sum_counter+=float(data_dict[word])
						position+=1
					elif word in lemma_dict and lemma_dict[word] in data_dict and data_dict[lemma_dict[word]] is not "0":
							counter+=1
							sum_counter+=float(data_dict[lemma_dict[word]])
							position += 1
					else: position+=1				
	
	index = safe_divide(sum_counter,counter)
	index_list.append(index)
	header_list.append(index_name)

def ListDict_counter(in_text, data_dict,index_list,index_name):
	counter = 0
	nwords = len(in_text)

	for word in in_text:
		if word in data_dict:
			counter+=1
		else:
			if word in lemma_dict and lemma_dict[word] in data_dict:
				counter+=1
	index = safe_divide(counter,nwords)
	index_list.append(index)
	header_list.append(index_name)

def Ngram_ListDict_counter(in_text, data_dict,index_list,index_name):
	counter = 0
	nwords = len(in_text)
	position = 0
	
	def single_count(word):
		key = 0
		if word in data_dict:
			key=1
		elif word in lemma_dict and lemma_dict[word] in data_dict:
				key =1
		return key
	
	def ngram_count(gram,n):
		yes = 0
		if gram in data_dict:
			yes +=n
		return yes
		
	for item in in_text:
		#This section ensures the text (or remaining portion of the text) is long enough to look for fiv-grams, etc.
		if position > len(in_text)-1: continue
		word = in_text[position]
		if len(in_text[position:]) < 2:
			if single_count(word) == 1:
				counter+=1
				position+=1
			else: position+=1
		
		bigram = " ".join(in_text[position:position +1])
		if len(in_text[position:]) < 3:
			yes = ngram_count(bigram,2)
			if yes > 0:
				counter+=yes
				position+=yes
				continue
			if single_count(word) == 1:
				counter+=1
				position+=1
			else: position+=1
							
		trigram = " ".join(in_text[position:position +2])
		if len(in_text[position:]) < 4:
			yes = ngram_count(trigram,3)
			if yes > 0:
				counter+=yes
				position+=yes
				continue
			yes = ngram_count(bigram,2)
			if yes > 0:
				counter+=yes
				position+=yes
				continue
			if single_count(word) == 1:
				counter+=1
				position+=1
			else: position+=1
								
		quadgram = " ".join(in_text[position:position +3])
		if len(in_text[position:]) < 5:
			yes = ngram_count(quadgram,4)
			if yes > 0:
				counter+=yes
				position+=yes
				continue
			yes = ngram_count(trigram,3)
			if yes > 0:
				counter+=yes
				position+=yes
				continue
			yes = ngram_count(bigram,2)
			if yes > 0:
				counter+=yes
				position+=yes
				continue
			if single_count(word) == 1:
				counter+=1
				position+=1
			else: position+=1				
		
		#This functions on most of the text. It checks for five-grams. If none, quad-grams, etc.
		fivegram = " ".join(in_text[position:position +4])
		if len(in_text[position:]) > 4:
			yes = ngram_count(fivegram,4)
			if yes > 0:
				counter+=yes
				position+=yes
				continue
			yes = ngram_count(quadgram,4)
			if yes > 0:
				counter+=yes
				position+=yes
				continue
			yes = ngram_count(trigram,3)
			if yes > 0:
				counter+=yes
				position+=yes
				continue
			yes = ngram_count(bigram,2)
			if yes > 0:
				counter+=yes
				position+=yes
				continue
			if single_count(word) == 1:
				counter+=1
				position+=1
			else: position+=1
						
	index = safe_divide(counter,nwords)
	index_list.append(index)
	header_list.append(index_name)			

def simple_proportion(target_text,ref_text,type,index_name= None,index_list = None,header_list = None): #each text is a list
	length = len(target_text)
	counter = 0
	not_counter = 0
	for items in target_text:
		if items in ref_text:
			counter+=1
		else:
			not_counter+=1
			
	if type == "perc":
		outvar = safe_divide(counter,length)
	if type == "prop":
		outvar = safe_divide(counter,not_counter)

	if header_list is not None:
		header_list.append(index_name)
		index_list.append(outvar)
	
	if header_list is None:
		return outvar
		
		
	
def proportion_counter(in_text,data_dict,index_list,index_name):
	count = len(in_text)
	in_list = 0
	for items in in_text:
		##print items
		if items in data_dict:
			##print items
			in_list +=1
	
	index = safe_divide(in_list,count)
	index_list.append(index)
	header_list.append(index_name)				

def content_pos_dict(xml_file, lemma = "no"):
	if lemma == "no":
		token_get = 0
	if lemma == "yes":
		token_get = 1
	
	def mini_lem_lister(input): #input is a list of lists [[lemma_form,raw_form],[lemma_form,raw_form]]
		mini_dict = {}
		for items in input:
			lem = items[0]
			raw = items[1]
			if lem in mini_dict:
				if raw not in mini_dict[lem]:
					mini_dict[lem].append(raw)
			else:
				mini_dict[lem] = [raw]
		
		return mini_dict
	
		
	dict = {}

	tree = ET.ElementTree(file=xml_file)

	noun_tags = ["NN", "NNS", "NNP", "NNPS"] #consider whether to identify gerunds
	proper_n = ["NNP", "NNPS"]
	no_proper = ["NN", "NNS"]
	pronouns = ["PRP", "PRP$"]
	adjectives = ["JJ", "JJR", "JJS"]
	verbs = ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ", "MD"]
	adverbs = ["RB", "RBR", "RBS"]
	content = ["NN", "NNS", "NNP", "NNPS","JJ", "JJR", "JJS","VB", "VBD", "VBG", "VBN", "VBP", "VBZ", "MD","RB", "RBR", "RBS"]
	
	pos_word_list = []

	s_noun_text = []
	s_proper_n_text = []
	s_no_proper_text = []
	s_pronoun_text = []
	s_adjective_text = []
	s_verb_text = []
	s_verb_noun_text = []
	s_adverb_text = []
	s_content_text = []
	s_function_text = []	
	s_all_text = []
	
	lem_raw_noun = []
	lem_raw_verb = []
	lem_raw_all = []
	lem_raw_content = []
	
	for sentences in tree.iter("sentence"):
		noun_text = []
		proper_n_text = []
		no_proper_text = []
		pronoun_text = []
		adjective_text = []
		verb_text = []
		verb_noun_text = []
		adverb_text = []
		content_text = []
		function_text = []
		all_text = []
		
		for tokens in sentences.iter("token"):
			if tokens[4].text in punctuation:
				continue
			all_text.append(tokens[token_get].text.lower())
			lem_raw_all.append([tokens[1].text.lower(),tokens[0].text.lower()])

			if tokens[4].text in noun_tags:
				noun_text.append(tokens[token_get].text.lower())
				verb_noun_text.append(tokens[token_get].text.lower())
				lem_raw_noun.append([tokens[1].text.lower(),tokens[0].text.lower()])
			if tokens[4].text in proper_n:
				proper_n_text.append(tokens[token_get].text.lower())
			if tokens[4].text in no_proper:
				no_proper_text.append(tokens[token_get].text.lower())
			if tokens[4].text in pronouns:
				pronoun_text.append(tokens[token_get].text.lower())
			if tokens[4].text in adjectives:
				adjective_text.append(tokens[token_get].text.lower())
			if tokens[4].text in verbs:
				verb_text.append(tokens[token_get].text.lower())
				verb_noun_text.append(tokens[token_get].text.lower())
				lem_raw_noun.append([tokens[1].text.lower(),tokens[0].text.lower()])
			if tokens[4].text in adverbs:
				adverb_text.append(tokens[token_get].text.lower())
			if tokens[4].text in content and tokens[1].text != "be":
				content_text.append(tokens[token_get].text.lower())
				lem_raw_content.append([tokens[1].text.lower(),tokens[0].text.lower()])
			if tokens[4].text not in content or tokens[1].text == "be":
				function_text.append(tokens[token_get].text.lower())
		
		s_noun_text.append(noun_text)
		s_proper_n_text.append(proper_n_text)
		s_no_proper_text.append(no_proper_text)
		s_pronoun_text.append(pronoun_text)
		s_adjective_text.append(adjective_text)
		s_verb_text.append(verb_text)
		s_verb_noun_text.append(verb_noun_text)
		s_adverb_text.append(adverb_text)
		s_content_text.append(content_text)
		s_function_text.append(function_text)	
		s_all_text.append(all_text)

	all_content = [item for sublist in s_content_text for item in sublist]
	all_noun = [item for sublist in s_noun_text for item in sublist]
	all_proper_n = [item for sublist in s_proper_n_text for item in sublist]
	all_no_proper = [item for sublist in s_no_proper_text for item in sublist]
	all_pronoun = [item for sublist in s_pronoun_text for item in sublist]
	all_adjective = [item for sublist in s_adjective_text for item in sublist]
	all_verb = [item for sublist in s_verb_text for item in sublist]
	all_verb_noun = [item for sublist in s_verb_noun_text for item in sublist]
	all_adverb = [item for sublist in s_adverb_text for item in sublist]
	all_function = [item for sublist in s_function_text for item in sublist]
	all_all = [item for sublist in s_all_text for item in sublist]
	
	#dict["s_content"]= s_content_text
	#dict["s_noun"] = s_noun_text
	#dict["s_adj"] = s_adjective_text
	#dict["s_verb"] = s_verb_text
	#dict["s_adv"] = s_adverb_text
	#dict["s_function"] = s_function_text
	
	
	dict["s_all"] = s_all_text

	dict["content"]= all_content
	dict["noun"] = all_noun
	dict["proper_n"] = all_proper_n
	dict["no_proper"] = all_no_proper
	dict["pronoun"] = all_pronoun
	dict["adj"] = all_adjective
	dict["verb"] = all_verb
	dict["verb_noun"] = all_verb_noun
	dict["adv"] = all_adverb
	dict["function"] = all_function
	dict["all"] = all_all
	dict["lemmer_noun"] = mini_lem_lister(lem_raw_noun)
	dict["lemmer_verb"] = mini_lem_lister(lem_raw_verb)
	dict["lemmer_all"] = mini_lem_lister(lem_raw_all)
	dict["lemmer_content"] = mini_lem_lister(lem_raw_content)
	
	return dict

def ngram_pos_dict(xml,lemma = "no"):
	if lemma == "no":
		token_get = 0
	if lemma == "yes":
		token_get = 1
	
	def dict_add(dict, list, name, sent = "no"):
		if sent == "yes":
			if name in dict:
				dict[name].append(list)
			else:
				dict[name] = [list]
		if sent == "no":
			if name in dict:
				for items in list:
					dict[name].append(items)
			else:
				dict[name] = list

	
	frequency_dict = {}

	tree = ET.ElementTree(file=xml) #The file is opened by the XML parser

	uni_list = []
	bi_list = []
	tri_list = []
	quad_list = []
	
	n_list_bi= []
	adj_list_bi= []
	v_list_bi= []
	v_n_list_bi= []
	a_n_list_bi= []

	n_list_tri= []
	adj_list_tri= []
	v_list_tri= []
	v_n_list_tri= []
	a_n_list_tri= []

	n_list_quad= []
	adj_list_quad= []
	v_list_quad= []
	v_n_list_quad= []
	a_n_list_quad= []


	for sentences in tree.iter("sentence"):
		
		def lemma_lister(constraint = None):
			list = []
			for tokens in sentences.iter("token"):
				try:
					str(tokens[token_get].text)
				except UnicodeEncodeError:
					continue
				if tokens[token_get].text in punctuation:
					continue
				if constraint == None:
					list.append(tokens[token_get].text.lower())
				else:
					if tokens[4].text in constraint:
						list.append(tokens[token_get].text.lower())
					else:
						list.append("x")
			return list
			
		word_list = lemma_lister()
		
		for items in word_list:
			uni_list.append(items)
				
		n_list = lemma_lister(nouns)
		adj_list = lemma_lister(adjectives)
		v_list = lemma_lister(verbs)
		v_n_list = lemma_lister(verbs_nouns)
		a_n_list = lemma_lister(nouns_adjectives)
		
		
		n_grammer(word_list,2,bi_list)
		n_grammer(word_list,3,tri_list)
		n_grammer(word_list,4,quad_list)
		
		n_grammer(n_list, 2, n_list_bi)
		n_grammer(adj_list, 2, adj_list_bi)
		n_grammer(v_list, 2, v_list_bi)
		n_grammer(v_n_list, 2, v_n_list_bi)
		n_grammer(a_n_list, 2, a_n_list_bi)
		
		n_grammer(n_list, 3, n_list_tri)
		n_grammer(adj_list, 3, adj_list_tri)
		n_grammer(v_list, 3, v_list_tri)
		n_grammer(v_n_list, 3, v_n_list_tri)
		n_grammer(a_n_list, 3, a_n_list_tri)

		n_grammer(n_list, 4, n_list_quad)
		n_grammer(adj_list, 4, adj_list_quad)
		n_grammer(v_list, 4, v_list_quad)
		n_grammer(v_n_list, 4, v_n_list_quad)
		n_grammer(a_n_list, 4, a_n_list_quad)
		
		#dict_add(frequency_dict,n_grammer(word_list,2),"s_bi_list","no")
		#dict_add(frequency_dict,n_grammer(word_list,3),"s_tri_list","no")
		#dict_add(frequency_dict,n_grammer(word_list,4),"s_quad_list","no")

		#dict_add(frequency_dict,n_grammer(n_list, 2),"s_n_list_bi","no")
		#dict_add(frequency_dict,n_grammer(adj_list, 2),"s_adj_list_bi","no")
		#dict_add(frequency_dict,n_grammer(v_list, 2),"s_v_list_bi","no")
		#dict_add(frequency_dict,n_grammer(v_n_list, 2),"s_v_n_list_bi","no")
		#dict_add(frequency_dict,n_grammer(a_n_list, 2),"s_a_n_list_bi","no")

		#dict_add(frequency_dict,n_grammer(n_list, 3),"s_n_list_tri","no")
		#dict_add(frequency_dict,n_grammer(adj_list, 3),"s_adj_list_tri","no")
		#dict_add(frequency_dict,n_grammer(v_list, 3),"s_v_list_tri","no")
		#dict_add(frequency_dict,n_grammer(v_n_list, 3),"s_v_n_list_tri","no")
		#dict_add(frequency_dict,n_grammer(a_n_list, 3),"s_a_n_list_tri","no")

		#dict_add(frequency_dict,n_grammer(n_list, 4),"s_n_list_quad","no")
		#dict_add(frequency_dict,n_grammer(adj_list, 4),"s_adj_list_quad","no")
		#dict_add(frequency_dict,n_grammer(v_list, 4),"s_v_list_quad","no")
		#dict_add(frequency_dict,n_grammer(v_n_list, 4),"s_v_n_list_quad","no")
		#dict_add(frequency_dict,n_grammer(a_n_list, 4),"s_a_n_list_quad","no")

	dict_add(frequency_dict, bi_list, "bi_list")
	dict_add(frequency_dict, tri_list, "tri_list")
	dict_add(frequency_dict, quad_list, "quad_list")

	dict_add(frequency_dict, n_list_bi, "n_list_bi")
	dict_add(frequency_dict, adj_list_bi, "adj_list_bi")
	dict_add(frequency_dict, v_list_bi, "v_list_bi")
	dict_add(frequency_dict, v_n_list_bi, "v_n_list_bi")
	dict_add(frequency_dict, a_n_list_bi, "a_n_list_bi")

	dict_add(frequency_dict, n_list_tri, "n_list_tri")
	dict_add(frequency_dict, adj_list_tri, "adj_list_tri")
	dict_add(frequency_dict, v_list_tri, "v_list_tri")
	dict_add(frequency_dict, v_n_list_tri, "v_n_list_tri")
	dict_add(frequency_dict, a_n_list_tri, "a_n_list_tri")

	dict_add(frequency_dict, n_list_quad, "n_list_quad")
	dict_add(frequency_dict, adj_list_quad, "adj_list_quad")
	dict_add(frequency_dict, v_list_quad, "v_list_quad")
	dict_add(frequency_dict, v_n_list_quad, "v_n_list_quad")
	dict_add(frequency_dict, a_n_list_quad, "a_n_list_quad")
	
	return frequency_dict
	
	
	
def coca_texter(clean_text):
	coca_text=[]
	
	for words in clean_text:
		if "'" in words:
				##print words
				words = words.replace("n't"," n't")
				##print words
				words = words. split(" ")
				##print words
				#words = re.sub("'", " '",words)
				for items in words:
						coca_text.append(items)
		else: coca_text.append(words)
	return coca_text

def text_cleaner(text, lister = "yes"):
	for items in punctuation:
		text = text.replace(items, " ")
	text = text.replace("\n"," ")
	while "  " in text:
		text = text.replace("  ", " ")
	
	if lister == 'yes':
		text = text.split(" ")
		text_list2 = []
		for item in text:
			if item == "":
				continue
			else:
				text_list2.append(item)
		text = text_list2
	
	return text

def n_grammer(text, length, list = None):
	counter = 0
	ngram_text = []
	for word in text:
		ngram = text[counter:(counter+length)]
		if len(ngram)> (length-1):
			ngram_text.append(" ".join(str(x) for x in ngram))		
		counter+=1
	if list is not None:
		for item in ngram_text:
			##print item
			list.append(item)
	else:
		return ngram_text

def n_paragraphs(text):
	while "\n\n" in text:
		text = text.replace("\n\n", "\n")
	if text[0] == "\n":
		text = text[1:]
	if text[-1] == "\n":
		text = text[:-1]
	n_par = len(text.split("\n"))

	return n_par

def syn_overlap(target_text, reference_text, syn_dict,index_list = None,index_name= None,header_list = None, wlist = "no"):
	#this was revised on 2018-10-15
	target = [] #holder for text version
	reference = [] #holder for reference version
	reference_check = []
	nwords = len(target_text) #length of target text
	
	for item in target_text: #iterate through target text
		if item in lemma_dict: #if word in lemma dict: convert to lemma
			lemma = lemma_dict[item]
		else: lemma = item #else, the "lemma" is the item
		target.append([item,lemma]) #append [raw_word, lemma] to target
	
	for item in reference_text: #iterate through the reference text
		if item in lemma_dict: #convert to lemma if possible
			lemma = lemma_dict[item]
			reference_check.extend([item,lemma]) #this is for checking that a synonym is not a repeat of word in reference	
		else:
			lemma = item #otherwise, don't
			reference_check.append(item) #same here
		add_list = []

		if item in syn_dict: #if the item is in the syn_dict: (but not the lemma form...)
			add_list.extend(syn_dict[item]) #get synonyms of words
			
		if lemma in syn_dict:
			add_list.extend(syn_dict[lemma]) #get synonyms of words
		
		reference.extend(list(set(add_list))) #extend add_list the add_list to target (but only unique items)
		
	counter = 0 #counter for synonym overlap
	for words in target: #iterate through synonym lists in target
		if (words[0] in reference or words[1] in reference) and (words[0] not in reference_check and words[1] not in reference_check): #if word or lemma in reference (and is not a repeat of another word in the reference): add one to counter
			#print(words[0],words[1]) #this line added for examples
			counter+= 1
	
	if wlist == "yes":
		outvar = [counter,nwords]
	
	if wlist == "no":
		outvar = safe_divide(counter,nwords)
	
	if header_list is not None:
		header_list.append(index_name)
		index_list.append(outvar)
	
	if header_list == None:
		return outvar

def syn_overlap_list(target_text, reference_text, syn_dict):
	#this was revised on 2018-10-15
	target = [] #holder for text version
	reference = [] #holder for reference version
	reference_check = []
	nwords = len(target_text) #length of target text
	syn_list = []
	
	for item in target_text: #iterate through target text
		if item in lemma_dict: #if word in lemma dict: convert to lemma
			lemma = lemma_dict[item]
		else: lemma = item #else, the "lemma" is the item
		target.append([item,lemma]) #append [raw_word, lemma] to target
	
	for item in reference_text: #iterate through the reference text
		if item in lemma_dict: #convert to lemma if possible
			lemma = lemma_dict[item]
			reference_check.extend([item,lemma]) #this is for checking that a synonym is not a repeat of word in reference	
		else:
			lemma = item #otherwise, don't
			reference_check.append(item) #same here
		add_list = []
		if item in syn_dict: #if the item is in the syn_dict: (but not the lemma form...)
			add_list.extend(syn_dict[item]) #get synonyms of words
		if lemma in syn_dict:
			add_list.extend(syn_dict[lemma])
		
		reference.extend(list(set(add_list))) #extend add_list the add_list to target (but only unique items)
		
	counter = 0 #counter for synonym overlap
	for words in target: #iterate through synonym lists in target
		if (words[0] in reference or words[1] in reference) and (words[0] not in reference_check and words[1] not in reference_check): #if word or lemma in reference (and is not a repeat of another word in the reference): add one to counter
			syn_list.append(words[0])
	
	#print(syn_list)
	return syn_list

def lsa_similarity(text_list_1,text_list_2,lsa_matrix_dict,lsa_weights_dict,index_list = None,index_name= None,header_list = None,lsa_type = "rwd",nvectors = 300):
	
	def vector_av(text_list):
		n_items = 0
		l = []
		for i in range(nvectors):
			l.append(0)
		
		for items in text_list:
			if items not in lsa_matrix_dict:
				continue
			else:
				n_columns = 0
				n_items+=1
				for vector in lsa_matrix_dict[items]:
					if lsa_type == 'rwd':
						l[n_columns] += vector*lsa_weights_dict[items]
						n_columns +=1
					elif lsa_type == 'fwd':
						l[n_columns] += vector
						n_columns +=1
					elif lsa_type == 'normal':
						l[n_columns] += vector*(1-lsa_weights_dict[items])
						n_columns +=1

		#n_columns = 0
		#for items in l:
		#	l[n_columns] = l[n_columns]/n_items
	
		sum_count = 0
		for items in l:
			sum_count += math.pow(items,2)
		sqrt_sum = math.sqrt(sum_count)
			
		
		return [l, sqrt_sum]
		
	list1 = vector_av(text_list_1)
	list2 = vector_av(text_list_2)
	
	try:
		sum_count_2 = 0
		for items in range(len(list1[0])):
			sum_count_2+= (list1[0][items]*list2[0][items])


		cosine_sim = sum_count_2/(list1[1]*list2[1])
	
	except ZeroDivisionError:
		cosine_sim = "null"
		
	if header_list is not None:
		header_list.append(index_name)
		index_list.append(cosine_sim)
	
	if header_list is None:
		return cosine_sim

def keyness(target_list, frequency_list_dict, top_perc = None,out_dir = "",keyname = ""): #note that frequency_list_dict should be normed
	list = []
	target_freq = Counter(target_list)
	comp_freq = frequency_list_dict
	xxxx_list = "x x,x x x,x x x x".split(",")	
	for item in target_freq:
		if item == "":
			continue
		freq = target_freq[item]
		if freq < 2:
			continue
			
		tf = target_freq[item]/len(target_list)
		ref_item = item.lower()
		try:
			#print "Item: ",item
			#print "Value: ", comp_freq[item]
			rf = comp_freq[ref_item]/1000000
			perc_dif = ((tf - rf)*100)/rf
			#print "in: ", item
		except KeyError:
			#print "out: ", item
			tf_idf = 1000000 #this will be, in effect, "infinity"
			perc_dif = 1000000 #this will be, in effect, "infinity"

		list.append([item,perc_dif,tf])
	
	final_list = sorted(list, key=itemgetter(1,2), reverse=True)
	
	if top_perc == None:
		return_list = final_list
	
	else:
		return_list = []
		perc = int(len(set(target_list))*top_perc)
		##print perc
		final_list = final_list[:perc]
		for items in final_list:
			if items[0] in xxxx_list:
				continue
			return_list.append(items[0])
	
	if out_dir !="":
		key_folder = out_dir+"/"+"key_lists"+"/"
		if not os.path.exists(key_folder):
			os.makedirs(key_folder)
		
		outfilename = key_folder + keyname
		key_write = open(outfilename, "w")
		for item in return_list:
			writestring = item + "\n"
			key_write.write(writestring)
		key_write.flush()
		key_write.close()

	return return_list

def dep_counter(list, structure,var_name,variable_list,header_list):
	counter = 0
	construct_counter = 0
	if structure == None:
		for items in list:
			construction = items.split("\t")[1]
			counter += (len(construction.split("_"))-1)
			construct_counter+=1
	else:
		for items in list:
			construction = items.split("\t")[1]
			deps = construction.split("-")
			if structure == "conj" or structure == "prep":
				fine_grain_list = []
				for items in deps:
					items =items.split("_")
					for x in items:
						fine_grain_list.append(x)
				deps = fine_grain_list
			counter+= deps.count(structure)
			construct_counter+=1
	outvar = safe_divide(counter,construct_counter)
	header_list.append(var_name)
	variable_list.append(outvar)

def std_dev_calc(list, var_name,variable_list,header_list):
	counter = 0
	construct_counter = 0
	mean_diff_counter=0
	for items in list:
		construction = items.split("\t")[1]
		counter += (len(construction.split("_"))-1)
		construct_counter+=1
	mean = safe_divide(counter, construct_counter)
	for items in list:
		construction = items.split("\t")[1]
		mean_diff_counter+= math.pow(((len(construction.split("_"))-1) - mean),2)
	std_dev = math.sqrt(safe_divide(mean_diff_counter,mean))
	
	header_list.append(var_name)
	variable_list.append(std_dev)


def ttr(list,var_name,variable_list,header_list):
	header_list.append(var_name)
	outvar = safe_divide(len(set(list)),len(list))
	variable_list.append(outvar)


##### Default Arguments (used often)
punctuation = ("*",".","!","?",",",":",";","'",'"',"-","--","@","#",'$',"%","^","&","+","=","_",")","(","/","\\","-rrb-","-lrb-")

noun_tags = ["NN", "NNS", "NNP", "NNPS"] #consider whether to identify gerunds
nouns = ["NN", "NNS", "NNP", "NNPS"]
adjectives = ["JJ", "JJR", "JJS"]
verbs = ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ", "MD"]
adverbs = ["RB", "RBR", "RBS"]
content = ["NN", "NNS", "NNP", "NNPS","JJ", "JJR", "JJS","VB", "VBD", "VBG", "VBN", "VBP", "VBZ", "MD","RB", "RBR", "RBS"]
verbs_nouns = ["NN", "NNS", "NNP", "NNPS","VB", "VBD", "VBG", "VBN", "VBP", "VBZ", "MD"]
nouns_adjectives = ["NN", "NNS", "NNP", "NNPS","JJ", "JJR", "JJS"]


lemma_dict = lemma_dicter(resource_path('e_lemma_lower_clean.txt'))#default lemma dict
fw_stop_list = open('function_word_stop_list.txt', 'rU').read().split("\t")
