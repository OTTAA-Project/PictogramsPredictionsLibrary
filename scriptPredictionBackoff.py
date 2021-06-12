from calcularPrediccionBackoff import calcularPrediccion
import json
import time
import os
import re

#Script donde se especifica una frase y se obtienen las predicciones
timeStart = time.time() 
#Datos de entrada:
sentence = "Los átomos" #Frase inicial sobre la que calcular la predicción
maxNgram = 5 #Máximo orden del N-grama
maxNumPaths = 4 #Máximo número de caminos devueltos tras la ejecución del algoritmo

#Carga de todos los archivos que forman los modelos de lenguaje (normal y de infinitivos)
f = open("listWords.txt", "r")
content = f.read()
listWords = content.split("\n")
f.close()

f = open("listWordsInf.txt", "r")
content = f.read()
listWordsInf = content.split("\n")
f.close()

f = open("dictNgram.txt", "r")
dictNgram = json.load(f)
f.close()

f = open("dictNgramInf.txt", "r")
dictNgramInf = json.load(f)
f.close()

f = open("dictBackoff.txt", "r")
dictBackoff = json.load(f)
f.close()

f = open("dictBackoffInf.txt", "r")
dictBackoffInf = json.load(f)
f.close()

#Carga de formas verbales en español
script_dir = os.path.dirname(__file__)
rel_path = "es-verbs.txt"
fileDictVerbs = os.path.join(script_dir, rel_path) 
verbForms = open(fileDictVerbs, encoding="utf-8") #Se abre el archivo que contiene todas las formas verbales de los verbos en español
verbs_array = verbForms.read().split() #Se obtiene una lista de arrays. Cada array contiene todas las conjugaciones para un mismo verbo.

#Carga de lista de caminos por defecto (a utilizar con aquella frases iniciales que no existan en el diccionario)
f = open("listDefaultPaths.txt", "r", encoding="utf-8")
content = f.read()
listDefaultPaths = content.split("\n")
f.close()

time1 = time.time() - timeStart
print("Abrir archivos:",time1)

#print("frase inicial:",sentence)
#Una vez recopilados todos los datos, se calcula la predicción basada en el algoritmo Viterbi
json_pathsConjugated = calcularPrediccion(sentence, maxNgram, maxNumPaths, listWords, listWordsInf, dictNgram, dictNgramInf, dictBackoff, dictBackoffInf, verbs_array, listDefaultPaths)
#Impresión de los resultados
timeFin = time.time() - timeStart
print(sentence, ": ", json_pathsConjugated,"tiempo:",timeFin)
timeStart2 = time.time()
json_pathsConjugated2 = calcularPrediccion(sentence, maxNgram, maxNumPaths, listWords, listWordsInf, dictNgram, dictNgramInf, dictBackoff, dictBackoffInf, verbs_array, listDefaultPaths)
timeFin2 = time.time() - timeStart2
print(sentence, ": ", json_pathsConjugated2,"tiempo sin apertura:",timeFin2)