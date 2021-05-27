# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 08:46:08 2021

@author: Juanma
"""

import os
import json

usuarios_dir = "D:/OTTAA - Lixi/PictogramsPredictionsLibrary/nabu/20210228_GenerateLanguageModels/frases_usuarios_30_11_2020"
lista_usuarios = os.listdir(usuarios_dir)

total = 0
files_not_read = []
for user in lista_usuarios:
    with open(usuarios_dir + "/" + user, "r") as json_file:
        
        try: 
            json_dir = json.load(json_file)
            json_file.close()
            
            total += len(json_dir)
            
        except:
            files_not_read.append(user)

