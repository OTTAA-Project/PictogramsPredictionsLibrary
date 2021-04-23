import json
import re
import sys
import os
import math
import time

def viterbiNbest(sentence, maxNgram, maxNumPaths, listWords, dictNgram, listDefaultPaths): #Función que devuelve las listas de palabras más probables para continuar la frase inicial dada
	"""Parámetros de entrada:
		- sentence: frase inicial a continuar
		- maxNgram: máximo orden de los N-gramas a evaluar. Por defecto: 5
		- maxNumPaths: máximo número de soluciones a devolver
		- listWords: listado de todas las palabras que aparecen en el diccionario de N-gramas
		- dictNgram: diccionario de N-gramas
		- listDefaultPaths: lista de caminos por defecto

		Resultado:
		- pathsSelected: caminos más probables (en forma de lista de strings) para continuar la frase inicial
		"""
	listSign = [".", "?", "!", "¿", "¡", ",",";"] #Se indica la lista de signos de puntuación para no considerarlos en la evaluación de palabras
	sentenceWords = sentence.split() #Se transforma la frase inicial en lista de palabras
	n = min(len(sentenceWords), maxNgram-1) #Se obtiene el número de palabras iniciales sobre las que trabajar (como máximo el orden máximo del N-grama establecido menos 1 ya que hay que añadir la nueva palabra a evaluar)
	nGram = [] #Se inicializa la lista de palabras que forman un N-grama
	pathsSaved = dict() #Se inicializa el diccionario de caminos guardados
	listWordsEv = list() #Lista de palabras a evaluar

	for i in range(n): #Se construye el N-grama inicial sobre el que trabajar
		nGram.append(sentenceWords[len(sentenceWords)-n+i])

	probPaths = list() #Lista de las probabilidades de los caminos activos

	keysDict = list(dictNgram.keys()) #Se obtienen las claves del diccionario de N-gramas en forma de lista
	valuesDict= list(dictNgram.values()) #Se obtienen los valores del diccionario de N-gramas en forma de lista

	for key, value in dictNgram.items(): #Se obtienen aquellas palabras que se encuentran en las frases del diccionario que incluyen la frase inicial
		if sentence in key:
			wordsSentece = key.split()
			for w in wordsSentece:
				if w not in listWordsEv and w not in listSign: #Se guardan aquellas palabras que aún no se encuentran en la lista, no se considerando los signos de puntuación
					listWordsEv.append(w)

	try:
		listWordsEv.remove(sentenceWords[len(sentenceWords)-1]) #Se elimina la última palabra de la frase inicial para no repetirla en la predicción
	except:
		listWordsEv
					
	for word in listWordsEv: #Se recorre la lista de palabras para calcular su probabilidad y se añade a la lista de probabilidades
		prob = evaluateNgram(word, nGram, keysDict, valuesDict)
		pathsSaved[word] = prob

	pathsSavedOrdered = dict(sorted(pathsSaved.items(), key=lambda item: item[1], reverse = True)) #Se ordenan las palabras evaluadas en orden decreciente de probabilidad
	pathsSO = list(pathsSavedOrdered.keys()) #Se obtiene la lista de caminos guardados ordenada por probabilidad

	pathsSelected = list() 
	for pthSd in range(min(maxNumPaths,len(pathsSO))): #Se recogen los K caminos más probables, siendo K el número máximo de caminos a devolver
		pathsSelected.append(pathsSO[pthSd])

	ind = 0
	while len(pathsSelected) < maxNumPaths:
		pathsSelected.append(listDefaultPaths[ind])
		ind = ind + 1

	return pathsSelected #Se devuelven los caminos más probables


def evaluateNgram(word, nGram, keysDict, valuesDict): #Función que calcula la probabilidad logarítmica P(w|N-grama)
	"""Parámetros de entrada:
		- word: palabra a añadir tras el N-grama proporcionado (w)
		- nGram: N-grama inicial
		- keysDict: lista de claves del diccionario de N-gramas
		- valuesDict: lista de valores del diccionario de N-gramas

		Resultado:
		- logprob: probabilidad logarítmica P(N|(N-1)-grama)
		"""
	sentence = '' #Inicialización de la frase a evaluar
	listBigramsBO = [] #Inicialización de la lista de bigramas
	prob = 1 #Inicialización de la variable de probabilidad
	nGramEv = []

	for w in nGram: #Se añade la nueva palabra al N-grama inicial en una nueva lista
		nGramEv.append(w)
	
	nGramEv.append(word)
	for i in range(len(nGramEv)): #Se convierte el N-grama inicial, dado en forma de lista, en un string
		sentence = sentence + nGramEv[i] + " "

	try: #Si la frase aparece en el diccionario, se obtiene su probabilidad
		indexSentence = keysDict.index(sentence)
		prob = valuesDict[indexSentence][4]
		modo = "diccionario"
	except: #Si no, se debe contar con el parámetro de backoff
		modo = "backoff"
		prob = 0

	if prob>0: #Se calcula la probabilidad logarímitica; si la probabilidad fuera 0, se asigna un valor muy bajo (realmente: -inf)
		logprob = math.log(prob) 
	else:
		logprob = -10000

	return logprob #Se devuelve la probabilidad logarítmica

def conjugateSentence(sentence, path, maxNgram, dictNgram, verbs_array):#Función que sustituye los verbos (en infinitivo) de una frase dada por su conjugación más probable
	"""Parámetros de entrada:
		- sentence: frase inicial
		- path: frase final a procesar
		- maxNgram: máximo orden de los N-gramas a evaluar. Por defecto: 5
		- dictNgram: diccionario de N-gramas
		- verbForms: archivo que contiene todas las formas verbales de los verbos en español

		Resultado:
		- final_sentence: frase conjugada
		"""
	wordsSentece = sentence.split() #Se convierte la frase inicial en lista de palabras
	lenIni = len(wordsSentece) #Se obtiene el número de palabras de la frase inicial
	final_path = wordsSentece #Inicialización de la lista de palabras que formarán la frase final

	keysDict = list(dictNgram.keys()) #Se obtienen las claves del diccionario de N-gramas en forma de lista
	valuesDict= list(dictNgram.values()) #Se obtienen los valores del diccionario de N-gramas en forma de lista

	infinitives_array = [] #Se inicializa la lista de infinitivos
	for verbs in verbs_array: #Se recorren todos los verbos para adjuntar a la lista sus infinitivos (primera posición del array donde aparecen todas las conjugaciones para cada verbo)
		single_verbs = verbs.split(',')
		infinitives_array.append(single_verbs[0].lower())

	sentenceWords = path.split() #Se convierte la frase inicial en una lista de palabras
	for word in sentenceWords: #Se comprueba si cada palabra es un infinitivo
		if word in infinitives_array: #Si lo es, se intercambia por su conjugación más probable
			indexVerb = infinitives_array.index(word) #Primero, se identifica el verbo encontrado
			conj = verbs_array[indexVerb].split(',') #Para recoger todas sus formas verbales en una lista
			nGram = final_path #Luego, se forma el N-grama anterior al verbo encontrado. 
			while len(nGram) > maxNgram: #Si es mayor que la longitud máxima, se van eliminando las palabras iniciales hasta ajustar su longitud
				nGram.pop(0)

			probList = []
			for verb in conj: #Posteriormente, se evalúa cada forma verbal tras el N-grama anterior
				prob = evaluateNgram(verb, nGram, keysDict, valuesDict)
				probList.append(prob)

			maxProb = max(probList) #Se calcula la máxima probabilidad de entre todas las formas verbales evaluadas
			indexMax = probList.index(maxProb) #Y se obtiene el índice donde ha acontecido esta máxima probabilidad 

			wordConj = conj[indexMax] #Finalmente, se recoge esta forma verbal
			final_path.append(wordConj) #Y se añade a la lista final de palabras
		else: #Si no, se añade a la lista final tal cual
			final_path.append(word)


	for i in range(lenIni): #Se eliminan las palabras de la frase inicial del resultado
		try:
			final_path.pop(0)
		except:
			final_path

	final_sentence = " ".join(final_path) #Se convierte la lista de palabras en un string que conforma la frase final

	return final_sentence #Se devuelve la frase con los verbos conjugados

def convertToJSON(paths):#Función que convierte en objeto JSON una lista de strings
	"""Parámetros de entrada:
		- paths: lista de strings

		Resultado:
		- json_paths: objeto json cuya clave es el número de orden y su valor el string
		"""
	dictPaths = dict() #Se crea un diccionario como paso previo a la creación del objeto JSON
	ind = 1 #Se inicializa el índice que servirá como clave del diccionario

	for p in paths: #Se recorre la lista de strings para asignarlas como valor al diccionario cuya clave es el orden o posición en la lista
		dictPaths[ind] = p
		ind = ind + 1
 
	json_data = json.dumps(dictPaths) #Se convierte el diccionario en un string JSON
	json_paths = json.loads(json_data) # Se crea el objeto JSON
 
	return json_paths #Se devuelve el objeto JSON creado 
