# Analyze source-text use in integrated production tasks

### Overview
This program is adapted from the [Constructed Response Analysis Tool (CRAT)](https://www.linguisticanalysistools.org/crat.html). This version allows users to analyze the use of two sources (as in TOEFL integrated writing tasks). Importantly, it provides overlap indices for each source (and controls for overlap between the two sources). It also makes some modification to the way that synonym overlap is calculated (it differentiates between word overlap and synonym overlap). See Kyle (forthcoming) for more information about the indices.

If you use this program in your research, please cite the following article:

Kyle, K. (forthcoming). The relationship between features of source text use and integrated writing quality. *Assessing Writing*.

### To Use
This program was written and tested in Python 3 (3.7.3). It also makes use of Stanford CoreNLP (version 3.5.1), which is written in Java and requires the Java Development Kit (tested using JDK 8).

To use, download the entire repository. Then:
- place your files (e.g., essays) in the "mydata/myfiles/" folder
- place both our your source texts in the "mydata/" folder
- open the "CRAT_Integrated.py" file
- Replace the sample filenames on lines 110 and 111 with your source text filenames (note that the output will refer to the first one as the "listening passage or "L" and the second one as the "reading passage" or "R")
- Save and close the "CRAT_Integrated.py"
- If Python 3 and JDK are installed on your system properly, you should now be able to change your working directory to the folder that contains the "CRAT_Integrated.py" file and type "python CRAT_Integrated.py"
- Your results will be located in the "mydata/" folder. By default, the results file is named "myresults.csv"
