# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 14:41:41 2021

@author: Juanma
"""

#Link for subt: http://es.tvsubtitles.net/tvshow-357-10.html
    
import os
import numpy as np

subt_dir = "D:/OTTAA - Lixi/PictogramsPredictionsLibrary/L&OSubt"
line_list = []

for file_name in os.listdir(subt_dir):
    if ".srt" in file_name: #Only get srt files
        file = open(subt_dir + "/" + file_name, "r")
        
        for line in file:
            line_array = line.split(" ") #get each word of the phrase on a list
            if ("-->" in line_array) or (line_array[0] == "\n") or ("P r e s e n t a" in line) or ("P R E S E N T A" in line) or ("wWw.Subs-Team.Tv" in line) or ("tvsubtitles" in line) or ("Law & Order: SVU" in line): #filter lines that has this elements
                pass
            else:
                try:
                    int(line_array[0]) #if the first element is a number, filter it since its the numbering of subtitles
                except:
                    line_list.append(line.split("\n")[0].split("<i>")[-1].split("</i>")[0].split("<b>")[-1].split("</b")[0].split("--")[0].split("- ")[-1]) #clear this elements of this line (but not filter it)
        
        file.close()
    
        
list_path = "D:/OTTAA - Lixi/PictogramsPredictionsLibrary/frasesL&O.txt"
max_phrase_no = 22420

if len(line_list) > max_phrase_no:
    line_list = [line_list[rand] for rand in np.random.randint(0, len(line_list), size = max_phrase_no)] #reduce the list of phrases to a max_number
        
try:
    temp_f = open(list_path, "r")
    temp_f.close()
    os.remove(list_path)
except Exception as e:
    print(e)
    pass

w_file = open(list_path, "a", encoding="utf-8")
for line in line_list[:-1]:
    w_file.write(line + "\n")
w_file.write(line_list[-1])
    
w_file.close() 