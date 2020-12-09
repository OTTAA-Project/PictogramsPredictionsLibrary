from generateGeneralLanguajeModel import generateGeneralLanguajeModel
from generateGeneralLanguajeModel import replaceToInfinitive
import json


#Script que crea los modelos de lenguaje a partir de los archivos (.txt o .json) proporcionados

#Se especifican los archivos con los que crear los modelos de lenguaje en dos listas: fileFormat (formato de los archivos) y file (archivo)
#Como ejemplo, se propone un archivo .txt y otro .json
fileFormat = []
file = []
fileFormat.append('txt')
file.append('frasesTest.txt')
fileFormat.append('json')
file.append('test.json')

#Luego, se inicializan las listas y diccionarios a generar. Son los siguientes:
listWords = ['.', '?','!'] #Lista de palabras incluídas en el diccionario, inicializada con los signos de puntuación de fin de frase
listWordsInf = ['.', '?','!'] #Lista de palabras incluídas en el diccionario de infinitivos, inicializada con los signos de puntuación de fin de frase
dictNgram = {} #Diccionario de N-gramas
dictNgramInf = {} #Diccionario de N-gramas con verbos en infinitivo
dictBackoff = {} #Diccionario de parámetro backoff
dictBackoffInf = {} #Diccionario de parámetro backoff con verbos en infinitivo

for i in range(len(file)): #Para todos los archivos especificados, se generan los modelos de lenguaje añadiendo los datos recursivamente
	[listWords, listWordsInf, dictNgram, dictNgramInf, dictBackoff, dictBackoffInf] = generateGeneralLanguajeModel(fileFormat[i], file[i], listWords, listWordsInf, dictNgram, dictNgramInf, dictBackoff, dictBackoffInf)


#Se guardan todos los datos (listas y diccionarios), cada uno en un archivo .txt
f = open("listWords.txt", "w")
for word in listWords:
    f.write(word+'\n')
f.close()

f = open("listWordsInf.txt", "w")
for word in listWordsInf:
    f.write(word+'\n')
f.close()

f = open("dictNgram.txt", "w")
json.dump(dictNgram, f)
f.close()

f = open("dictNgramInf.txt", "w")
json.dump(dictNgramInf, f)
f.close()

f = open("dictBackoff.txt", "w")
json.dump(dictBackoff, f)
f.close()

f = open("dictBackoffInf.txt", "w")
json.dump(dictBackoffInf, f)
f.close()