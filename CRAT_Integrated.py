#Developed by Kristopher Kyle, Linguistics, University of Oregon
import os
import re
import sys 
import platform
import shutil
import subprocess
import glob

try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET

import ktatk_py3 as ktk #this is Kris' toolkit

if platform.system() == "Darwin":
	system = "M"
elif platform.system() == "Windows":
	system = "W"
elif platform.system() == "Linux":
	system = "L"

def resource_path(relative):
	if hasattr(sys, "_MEIPASS"):
		return os.path.join(sys._MEIPASS, relative)
	return os.path.join(relative)

def call_stan_corenlp_pos(class_path, file_list, output_folder, memory, nthreads, system,parse_type = ""): #for CoreNLP 3.5.1 (most recent compatible version)
	#mac osx call:
	if system == "M":
		call_parser = "java -cp "+ class_path +"*: -Xmx" + memory + "g edu.stanford.nlp.pipeline.StanfordCoreNLP -threads "+ nthreads + " -annotators tokenize,ssplit,pos,lemma"+parse_type+" -filelist " + file_list + " -outputDirectory "+ output_folder
	#windows call:
	elif system == "W":
		call_parser = "java -cp "+ class_path +"*; -Xmx" + memory + "g edu.stanford.nlp.pipeline.StanfordCoreNLP -threads "+ nthreads + " -annotators tokenize,ssplit,pos,lemma"+parse_type+" -filelist " + file_list + " -outputDirectory "+ output_folder
	
	subprocess.call(call_parser, shell=True) #This watches the output folder until all files have been parsed


def stan_corenlp(system, stan_call,in_files, memory, nthreads):

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

	for line in list_of_files:
		line = line + "\n"	
		file_list_file.write(line)
	file_list_file.flush()
	file_list_file.close()

	stan_file_list = (input_folder + "_filelist.txt")
	
	current_directory = resource_path("./")
	stan_output_folder = "parsed_files/"
	
	stan_call(current_directory, stan_file_list, stan_output_folder, memory, nthreads, system)



print("Starting CRAT...")

#Note this was adapted from CRAT. Instead of using a single source file, it uses two (e.g., a reading and a listening passage as in TOEFL integrated writing prompts)
#Importantly, it can isolate words/phrases that occur in only one or the other passage (to track where they came from)
#Notes for Kris: This version is from CRAT_Small_1.2_F1.py. The only changes are that notes were added and unused code was deleted.
##### These files need to be defined! ######

#need to include these variables:

#folder where files are:
indir = "mydata/myfiles/" #This is an example. All .txt files in the "myfiles/" foler will be processed. Must be plain text.

#name and location of output file
outdir = "mydata/myresults.csv" #This is an example. This is the name of your outputfile

#source text name - 
# source_1 = "mydata/Leture_Source_Text.txt" #This is an example. This is the name of your first source text (it will be referred to as "listening" and/or "L" in the results)
# source_2 = "mydata/Reading_Source_Text.txt" #This is an example. This is the name of your second source text (it will be referred to as "reading" and/or "R" in the results)


source_1 = "mydata/Indy-Form1-text_Speaking.txt" #This is an example. This is the name of your first source text (it will be referred to as "listening" and/or "L" in the results)
source_2 = "mydata/Indy-Form1-text_reading.txt" #This is an example. This is the name of your second source text (it will be referred to as "reading" and/or "R" in the results)

#############################################

input_glob = indir + "/*.txt"

outf=open(outdir, "w")

key_out_dir = "/".join(outdir.split("/")[:-1])

filenames = glob.glob(input_glob)

for_stan = filenames
for_stan.append(source_1) #add primary source_text for file processing
for_stan.append(source_2) #add secondary source_text for file processing

file_number = 0
file_counter = 1 #for update_list

stan_corenlp(system, call_stan_corenlp_pos, for_stan, "3", "2") #creates pos_tag version of the text

#Kris, start here.

#### Database Import and Dictionary Building ####
print("Loading Program Databases")

print("Loading LSA Matrix...")
lsa_matrix_list = "\n".join(open(resource_path("tasa_lsa_matrix_1.txt")).read().split("\n") + open(resource_path("tasa_lsa_matrix_2.txt")).read().split("\n") + open(resource_path("tasa_lsa_matrix_3.txt")).read().split("\n") + open(resource_path("tasa_lsa_matrix_4.txt")).read().split("\n"))

print("Loading LSA Weights...")		
lsa_weights_list = open(resource_path('lsa_weights.txt'), 'r').read()

print("Loading LSA Matrix Dict (be patient) ...")
lsa_matrix = ktk.list_dict_builder(lsa_matrix_list,numbers="yes")

print("Loading LSA Weight Dict...")
lsa_weights = ktk.dict_builder(lsa_weights_list,2)


#Wordnet Databases
print("Loading Wordnet Databases...")
wn_verb_list = open(resource_path('wn_verb.txt'), 'r').read()
wn_verb_dict = ktk.list_dict_builder_nr(wn_verb_list)
wn_noun_list = open(resource_path('wn_noun.txt'), 'r').read()
wn_noun_dict = ktk.list_dict_builder_nr(wn_noun_list)

#### Source Summary Analysis ####
print("Processing Summary Text..")

source = open(source_1,"r").read().lower()

npar_source = ktk.n_paragraphs(source)

source_clean = ktk.text_cleaner(source) #text now string of words

#print "Source clean: ", source_clean
nwords_source = len(source_clean)

tagged_source_1 = "parsed_files/" + source_1.split("/")[-1] + ".xml"
tagged_source_2 = "parsed_files/" + source_2.split("/")[-1] + ".xml"

print("Loading Summary Text POS Lists")

source_pos_dict = ktk.content_pos_dict(tagged_source_1) #dict of pos lists
source_pos_lem_dict = ktk.content_pos_dict(tagged_source_1,lemma = "yes") #dict of pos lists

source2_pos_dict = ktk.content_pos_dict(tagged_source_2) #dict of pos lists
source2_pos_lem_dict = ktk.content_pos_dict(tagged_source_2,lemma = "yes") #dict of pos lists

#this is for creating a stop list (synonyms and lsa)
#The stoplist includes all words [and all their lemma forms] used in either prompt
source_1_content_lems = source_pos_dict["lemmer_content"]
source_2_content_lems = ktk.content_pos_dict(tagged_source_2)["lemmer_content"]

source_1_2_stoplist = []

source_1_stoplist = []
source_2_stoplist = []

for x in source_1_content_lems:
	source_1_2_stoplist.append(x)
	source_1_stoplist.append(x)
	for y in source_1_content_lems[x]:
		source_1_2_stoplist.append(y)
		source_1_stoplist.append(y)

for x in source_2_content_lems:
	source_1_2_stoplist.append(x)
	source_2_stoplist.append(x)
	for y in source_2_content_lems[x]:
		source_1_2_stoplist.append(y)
		source_2_stoplist.append(y)

source_1_2_stoplist = list(set(source_1_2_stoplist))


### End stoplist creation

print("Loading Summary Text Ngram Lists")

source_ngram_pos_dict = ktk.ngram_pos_dict(tagged_source_1)
source_ngram_pos_lem_dict = ktk.ngram_pos_dict(tagged_source_1, lemma = "yes")

source2_ngram_pos_dict = ktk.ngram_pos_dict(tagged_source_2)
source2_ngram_pos_lem_dict = ktk.ngram_pos_dict(tagged_source_2, lemma = "yes")

## More Source analysis ##
#model for keyword lists:
#simple_source_keywords = ktk.keyness(source_clean, COCA_fiction_uni_F, top_perc = .1)

#ngrams
##Listening
listening_noR_bi = ktk.ngram_constrainer(source_ngram_pos_lem_dict["bi_list"],source_2_stoplist)
listening_noR_tri = ktk.ngram_constrainer(source_ngram_pos_lem_dict["tri_list"],source_2_stoplist)
listening_noR_quad = ktk.ngram_constrainer(source_ngram_pos_lem_dict["quad_list"],source_2_stoplist)

listening_noR_n_list_bi = ktk.ngram_constrainer(source_ngram_pos_lem_dict["n_list_bi"],source_2_stoplist)
listening_noR_adj_list_bi = ktk.ngram_constrainer(source_ngram_pos_lem_dict["adj_list_bi"],source_2_stoplist)
listening_noR_v_list_bi = ktk.ngram_constrainer(source_ngram_pos_lem_dict["v_list_bi"],source_2_stoplist)
listening_noR_v_n_list_bi = ktk.ngram_constrainer(source_ngram_pos_lem_dict["v_n_list_bi"],source_2_stoplist)
listening_noR_a_n_list_bi = ktk.ngram_constrainer(source_ngram_pos_lem_dict["a_n_list_bi"],source_2_stoplist)

listening_noR_n_list_tri = ktk.ngram_constrainer(source_ngram_pos_lem_dict["n_list_tri"],source_2_stoplist)
listening_noR_adj_list_tri = ktk.ngram_constrainer(source_ngram_pos_lem_dict["adj_list_tri"],source_2_stoplist)
listening_noR_v_list_tri = ktk.ngram_constrainer(source_ngram_pos_lem_dict["v_list_tri"],source_2_stoplist)
listening_noR_v_n_list_tri = ktk.ngram_constrainer(source_ngram_pos_lem_dict["v_n_list_tri"],source_2_stoplist)
listening_noR_a_n_list_tri = ktk.ngram_constrainer(source_ngram_pos_lem_dict["a_n_list_tri"],source_2_stoplist)

listening_noR_n_list_quad = ktk.ngram_constrainer(source_ngram_pos_lem_dict["n_list_quad"],source_2_stoplist)
listening_noR_adj_list_quad = ktk.ngram_constrainer(source_ngram_pos_lem_dict["adj_list_quad"],source_2_stoplist)
listening_noR_v_list_quad = ktk.ngram_constrainer(source_ngram_pos_lem_dict["v_list_quad"],source_2_stoplist)
listening_noR_v_n_list_quad = ktk.ngram_constrainer(source_ngram_pos_lem_dict["v_n_list_quad"],source_2_stoplist)
listening_noR_a_n_list_quad = ktk.ngram_constrainer(source_ngram_pos_lem_dict["a_n_list_quad"],source_2_stoplist)

#ngrams
##Reading
reading_noL_bi = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["bi_list"],source_1_stoplist)
reading_noL_tri = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["tri_list"],source_1_stoplist)
reading_noL_quad = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["quad_list"],source_1_stoplist)

reading_noL_n_list_bi = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["n_list_bi"],source_1_stoplist)
reading_noL_adj_list_bi = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["adj_list_bi"],source_1_stoplist)
reading_noL_v_list_bi = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["v_list_bi"],source_1_stoplist)
reading_noL_v_n_list_bi = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["v_n_list_bi"],source_1_stoplist)
reading_noL_a_n_list_bi = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["a_n_list_bi"],source_1_stoplist)

reading_noL_n_list_tri = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["n_list_tri"],source_1_stoplist)
reading_noL_adj_list_tri = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["adj_list_tri"],source_1_stoplist)
reading_noL_v_list_tri = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["v_list_tri"],source_1_stoplist)
reading_noL_v_n_list_tri = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["v_n_list_tri"],source_1_stoplist)
reading_noL_a_n_list_tri = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["a_n_list_tri"],source_1_stoplist)

reading_noL_n_list_quad = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["n_list_quad"],source_1_stoplist)
reading_noL_adj_list_quad = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["adj_list_quad"],source_1_stoplist)
reading_noL_v_list_quad = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["v_list_quad"],source_1_stoplist)
reading_noL_v_n_list_quad = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["v_n_list_quad"],source_1_stoplist)
reading_noL_a_n_list_quad = ktk.ngram_constrainer(source2_ngram_pos_lem_dict["a_n_list_quad"],source_1_stoplist)



### End Source Summary Analysis

nfiles = len(filenames)

syn_n_t = open(key_out_dir +"/syn_noun_overlap.txt","w")
syn_v_t = open(key_out_dir +"/syn_verb_overlap.txt","w")
	
### Begin Iteration Through Summary Responses ###
for filename in filenames:
	header_list = ["Filename"]
	index_list = []
	
#updates Program Status
	filename1 = ("Processing: " + str(file_counter) + " of " + str(nfiles) + " files")
	print(filename1)
	file_counter+=1
	
	text= open(filename, 'rU').read().lower()

	clean_text = ktk.text_cleaner(text)
	coca_text = ktk.coca_texter(clean_text)
	
	nwords_text = len(clean_text)
	npar_text = ktk.n_paragraphs(text)			
	ktk.indexer(nwords_text, "nwords", index_list, header_list)
	ktk.indexer(npar_text, "nparagraphs", index_list, header_list)
	tagged_text_name = "parsed_files/" + filename.split("/")[-1] + ".xml"

	pos_dict = ktk.content_pos_dict(tagged_text_name)
	pos_lem_dict = ktk.content_pos_dict(tagged_text_name,lemma = "yes")
	ngram_pos_dict = ktk.ngram_pos_dict(tagged_text_name)
	ngram_pos_lem_dict = ktk.ngram_pos_dict(tagged_text_name, lemma = "yes")
	
	#content words with content stoplist words removed:
	content_raw_stopremoved = []
	for x in pos_dict["content"]:
		if x in source_1_2_stoplist:
			continue
		else:
			content_raw_stopremoved.append(x)
	# end list creation
	
	parsed_nwords = len(pos_dict["all"])
	ktk.indexer(parsed_nwords, "parsed_nwords",index_list,header_list)

	ktk.indexer(len(pos_dict["s_all"]),"nsentences",index_list,header_list)
	

	ktk.lsa_similarity(source_pos_dict["content"],content_raw_stopremoved,lsa_matrix,lsa_weights,index_list,"lsa_content_rwd_nosourceL",header_list,"rwd")
	ktk.lsa_similarity(source_pos_dict["content"],content_raw_stopremoved,lsa_matrix,lsa_weights,index_list,"lsa_content_fwd_nosourceL",header_list,"fwd")
	ktk.lsa_similarity(source_pos_dict["content"],content_raw_stopremoved,lsa_matrix,lsa_weights,index_list,"lsa_content_normal_nosourceL",header_list,"normal")

	ktk.lsa_similarity(source2_pos_dict["content"],content_raw_stopremoved,lsa_matrix,lsa_weights,index_list,"lsa_content_rwd_nosourceR",header_list,"rwd")
	ktk.lsa_similarity(source2_pos_dict["content"],content_raw_stopremoved,lsa_matrix,lsa_weights,index_list,"lsa_content_fwd_nosourceR",header_list,"fwd")
	ktk.lsa_similarity(source2_pos_dict["content"],content_raw_stopremoved,lsa_matrix,lsa_weights,index_list,"lsa_content_normal_nosourceR",header_list,"normal")


#no stoplist words		
	nostop_noun = ktk.constrainer(pos_dict["noun"],source_1_2_stoplist)
	nostop_verb = ktk.constrainer(pos_dict["verb"],source_1_2_stoplist) 

	ktk.syn_overlap(nostop_noun, source_pos_dict["noun"], wn_noun_dict,index_list,"syn_overlap_nouns_nosourceL",header_list)
	ktk.syn_overlap(nostop_verb, source_pos_dict["verb"], wn_verb_dict,index_list,"syn_overlap_verbs_nosourceL",header_list)

	ktk.syn_overlap(nostop_noun, source2_pos_dict["noun"], wn_noun_dict,index_list,"syn_overlap_nouns_nosourceR",header_list)
	ktk.syn_overlap(nostop_verb, source2_pos_dict["verb"], wn_verb_dict,index_list,"syn_overlap_verbs_nosourceR",header_list)

	noun_syn_overlap = ktk.syn_overlap(nostop_noun, source_pos_dict["noun"], wn_noun_dict, wlist = "yes")
	verb_syn_overlap = ktk.syn_overlap(nostop_verb, source_pos_dict["verb"], wn_verb_dict, wlist = "yes")
	
	index_list.append(ktk.safe_divide((noun_syn_overlap[0]+verb_syn_overlap[0]),(noun_syn_overlap[1]+verb_syn_overlap[1])))
	header_list.append("syn_overlap_verbs_nouns_nosource")
	
	#ktk.syn_overlap_list(nokw_noun, source_pos_dict["noun"], wn_noun_dict)
	syn_n_t.write("\n".join(ktk.syn_overlap_list(nostop_noun, source_pos_dict["noun"], wn_noun_dict))+"\n")
	syn_v_t.write("\n".join(ktk.syn_overlap_list(nostop_verb, source_pos_dict["verb"], wn_verb_dict))+"\n")

				
#keyword similarity percentage
	
	content_only_lecture = ktk.constrainer(source_pos_lem_dict["content"],source_2_stoplist)
	content_only_reading = ktk.constrainer(source2_pos_lem_dict["content"],source_1_stoplist)
	
	ktk.simple_proportion(pos_lem_dict["content"],content_only_lecture, "perc", "content_word_overlap_lecture_noR", index_list, header_list)
	ktk.simple_proportion(pos_lem_dict["content"],content_only_reading, "perc", "content_word_overlap_reading_noL", index_list, header_list)
	ktk.simple_proportion(pos_lem_dict["content"],source_1_2_stoplist, "perc", "content_word_overlap_all", index_list, header_list)
	
	ktk.simple_proportion(ngram_pos_lem_dict["bi_list"],listening_noR_bi, "perc", "listening_noR_bi_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["tri_list"],listening_noR_tri, "perc", "listening_noR_tri_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["quad_list"],listening_noR_quad, "perc", "listening_noR_quad_percentage", index_list, header_list)

	ktk.simple_proportion(ngram_pos_lem_dict["n_list_bi"],listening_noR_n_list_bi, "perc", "listening_noR_n_bi_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["adj_list_bi"],listening_noR_adj_list_bi, "perc", "listening_noR_adj_bi_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_list_bi"],listening_noR_v_list_bi, "perc", "listening_noR_v_bi_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_n_list_bi"],listening_noR_v_n_list_bi, "perc", "listening_noR_v_n_bi_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["a_n_list_bi"],listening_noR_a_n_list_bi, "perc", "listening_noR_a_n_bi_percentage", index_list, header_list)

	ktk.simple_proportion(ngram_pos_lem_dict["n_list_tri"],listening_noR_n_list_tri, "perc", "listening_noR_n_tri_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["adj_list_tri"],listening_noR_adj_list_tri, "perc", "listening_noR_adj_tri_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_list_tri"],listening_noR_v_list_tri, "perc", "listening_noR_v_tri_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_n_list_tri"],listening_noR_v_n_list_tri, "perc", "listening_noR_v_n_tri_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["a_n_list_tri"],listening_noR_a_n_list_tri, "perc", "listening_noR_a_n_tri_percentage", index_list, header_list)

	ktk.simple_proportion(ngram_pos_lem_dict["n_list_quad"],listening_noR_n_list_quad, "perc", "listening_noR_n_quad_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["adj_list_quad"],listening_noR_adj_list_quad, "perc", "listening_noR_adj_quad_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_list_quad"],listening_noR_v_list_quad, "perc", "listening_noR_v_quad_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_n_list_quad"],listening_noR_v_n_list_quad, "perc", "listening_noR_v_n_quad_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["a_n_list_quad"],listening_noR_a_n_list_quad, "perc", "listening_noR_a_n_quad_percentage", index_list, header_list)
	
	ktk.simple_proportion(ngram_pos_lem_dict["bi_list"],reading_noL_bi, "perc", "reading_noL_bi_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["tri_list"],reading_noL_tri, "perc", "reading_noL_tri_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["quad_list"],reading_noL_quad, "perc", "reading_noL_quad_percentage", index_list, header_list)

	ktk.simple_proportion(ngram_pos_lem_dict["n_list_bi"],reading_noL_n_list_bi, "perc", "reading_noL_n_bi_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["adj_list_bi"],reading_noL_adj_list_bi, "perc", "reading_noL_adj_bi_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_list_bi"],reading_noL_v_list_bi, "perc", "reading_noL_v_bi_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_n_list_bi"],reading_noL_v_n_list_bi, "perc", "reading_noL_v_n_bi_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["a_n_list_bi"],reading_noL_a_n_list_bi, "perc", "reading_noL_a_n_bi_percentage", index_list, header_list)

	ktk.simple_proportion(ngram_pos_lem_dict["n_list_tri"],reading_noL_n_list_tri, "perc", "reading_noL_n_tri_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["adj_list_tri"],reading_noL_adj_list_tri, "perc", "reading_noL_adj_tri_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_list_tri"],reading_noL_v_list_tri, "perc", "reading_noL_v_tri_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_n_list_tri"],reading_noL_v_n_list_tri, "perc", "reading_noL_v_n_tri_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["a_n_list_tri"],reading_noL_a_n_list_tri, "perc", "reading_noL_a_n_tri_percentage", index_list, header_list)

	ktk.simple_proportion(ngram_pos_lem_dict["n_list_quad"],reading_noL_n_list_quad, "perc", "reading_noL_n_quad_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["adj_list_quad"],reading_noL_adj_list_quad, "perc", "reading_noL_adj_quad_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_list_quad"],reading_noL_v_list_quad, "perc", "reading_noL_v_quad_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["v_n_list_quad"],reading_noL_v_n_list_quad, "perc", "reading_noL_v_n_quad_percentage", index_list, header_list)
	ktk.simple_proportion(ngram_pos_lem_dict["a_n_list_quad"],reading_noL_a_n_list_quad, "perc", "reading_noL_a_n_quad_percentage", index_list, header_list)



###write phase of program ###	
	index_string_list=[] 
	
	if file_number == 0:
		#print "header string should print"
		header_string = ",".join(header_list)
		outf.write ('{0}\n'
		.format(header_string))
			
	for items in index_list:
		index_string_list.append(str(items))
	string = ",".join(index_string_list)

	outf.write ('{0},{1}\n'
	.format(filename.split("/")[-1],string))
	
	file_number+=1
	
outf.flush()#flushes out buffer to clean output file
outf.close()#close output file	
syn_n_t.flush()
syn_n_t.close()
syn_v_t.flush()
syn_v_t.close()
		
finishmessage = ("Processed " + str(nfiles) + " Files")
print(finishmessage)
