import json
import re
import sys
import os
import nltk #Librería NLP
from django.shortcuts import render
from django.http import HttpResponse

def generateGeneralLanguajeModel(fileFormat, arg, listWords, listWordsInf, dictNgram, dictNgramInf, dictBackoff, dictBackoffInf): 
	#Función que crea el modelo de lenguaje general de N-gramas (con N<=5) a partir de un archivo .txt o un array JSON
	"""Parámetros de entrada:
		- fileFormat: Formato del archivo a procesar
		- arg: Archivo a procesar
		- listWords: Lista existente de palabras añadidas al diccionario de N-gramas
		- listWordsInf: Lista existente de palabras añadidas al diccionario de N-gramas de infinitivos
		- dictNgram: Diccionario existente de N-gramas
		- dictNgramInf: Diccionario existente de N-gramas de infinitivos
		- dictBackoff: Diccionario existente de backoff por bigramas
		- dictBackoffInf: Diccionario existente de backoff por bigramas de infinitivos
		Resultado:
		- listWords: Lista actualizada de palabras añadidas al diccionario de N-gramas
		- listWordsInf: Lista actualizada de palabras añadidas al diccionario de N-gramas de infinitivos
		- dictNgram: Diccionario actualizado de N-gramas
		- dictNgramInf: Diccionario actualizado de N-gramas de infinitivos
		- dictBackoff: Diccionario actualizado de backoff por bigramas
		- dictBackoffInf: Diccionario actualizado de backoff por bigramas de infinitivos"""

	keySentence = "frase" #Parámetro del array JSON que contiene la frase
	keyWeight = "frecuencia" #Parámetro del array JSON que contiene la frecuencia de ocurrencia de la frase
	valid = True #Indica si el archivo proporcionado es válido para su procesado
	maxNgramSize = 5 #Tamaño máximo de los N-gramas
	finishOperators = ['.', '?','!']  #Carácteres que identifican el final de una frase

	if fileFormat == 'txt': #Caso de archivos .txt que contienen una frase por línea
		input_file = open(arg, encoding="utf-8") #Apertura del archivo .txt con el formato de codificación de caracteres UTF-8, indicado para el uso de caracteres especiales como vocales con tilde o letra Ñ.
		input_file_filtered = replacePunctuation(input_file.read()) #Ver explicación en la función
		text_array = input_file_filtered.split('\n') #Separación del archivo en frases, a partir del caracter \n que indica una nueva línea

		for item in text_array: #Procesado de cada frase para su inclusión en el modelo de lenguaje
			words = item.split() #Se separa la frase en palabras
			wordsInf = replaceToInfinitive(words) #Se obtienen las frases pasando todos los verbos a infinitivo

			for w in words: #Se incluyen las nuevas palabras en la lista de palabras 
				if w not in listWords:
					listWords.append(w.lower())
			for wI in wordsInf: #Se incluyen las nuevas palabras en la lista de palabras que solo incluye infinitivos
				if wI not in listWordsInf:
					listWordsInf.append(wI.lower())

			weight = 1 #Para archivos .txt, se cuenta la frecuencia de N-gramas como el conteo de apariciones. Por tanto, cada aparición suma 1.

			sizeSentence = len(words) #Tamaño de la frase en número de palabras
			if(sizeSentence > 0):	#Si la frase no acaba en un signo de puntuación, se le añade uno. En este caso el punto.
				if words[sizeSentence-1] not in finishOperators:
					words.append('.') 
					wordsInf.append('.') 

			for nSize in range(maxNgramSize+1): #Se generan los N-gramas contenidos en la frase que está siendo analizada. Desde el 1-grama (diccionario de palabras) al N-grama.
				dictNgram = addSentenceToDictionary(words, weight, dictNgram, nSize)
				dictNgramInf = addSentenceToDictionary(wordsInf, weight, dictNgramInf, nSize)
			

	elif fileFormat == "json": #Caso de arrays JSON
		input_file = open(arg, encoding="utf-8") #Apertura del array JSON con el formato de codificación de caracteres UTF-8, indicado para el uso de caracteres especiales como vocales con tilde o letra Ñ.
		json_array = json.load(input_file) #Carga del array separado por objetos JSON.

		for item in json_array: 
			words = replacePunctuation(item[keySentence]).split() #Se obtiene la frase del array JSON, se separa en palabras y se procesan los signos de puntuación (ver explicación en función 'replacePunctuation')
			wordsInf = replaceToInfinitive(words) #Se obtienen las frases pasando todos los verbos a infinitivo
			
			for w in words: #Se incluyen las nuevas palabras en la lista de palabras 
				if w not in listWords:
					listWords.append(w.lower())
			for wI in wordsInf: #Se incluyen las nuevas palabras en la lista de palabras que solo incluye infinitivos
				if wI not in listWordsInf:
					listWordsInf.append(wI.lower())

			weight = item[keyWeight] #En este caso, las frases aparecen asociadas a un parámetro de frecuencia. Por tanto, se suma la apariencia de N-gramas en la frase analizada en las mismas unidades que este parámetro.

			sizeSentence = len(words) #Tamaño de la frase en número de palabras
			if(sizeSentence > 0): #Si la frase no acaba en un signo de puntuación, se le añade uno. En este caso el punto.
				if words[sizeSentence-1] not in finishOperators:
					words.append('.')
					wordsInf.append('.')

			for nSize in range(maxNgramSize+1): #Se generan los N-gramas contenidos en la frase que está siendo analizada. Desde el 1-grama (diccionario de palabras) al N-grama.
				dictNgram = addSentenceToDictionary(words, weight, dictNgram, nSize)
				dictNgramInf = addSentenceToDictionary(wordsInf, weight, dictNgramInf, nSize)

	else: #Si el formato de archivo introducido no es válido, se le indica al usuario. Además, se cambia el boolean 'valid' a falso.
		print('Formato no válido. Indique "txt" o "json".')
		valid = False

	if valid: #Se generan los diccionarios del parámetro Backoff tanto para el diccionario regular como para el de infinitivos si se ha proporcionado un archivo de entrada válido
		dictBackoff = generateDictBackoffKatz(dictNgram) 
		dictBackoffInf = generateDictBackoffKatz(dictNgramInf)

	return listWords, listWordsInf, dictNgram, dictNgramInf, dictBackoff, dictBackoffInf #Se devuelven las listas de palabras y diccionarios generados
	

def replacePunctuation(text_array): #Se añade un espacio a los signos de puntuación para asegurar que no forman parte de ninguna palabra, sino que forman una independiente
	"""Parámetros de entrada:
		- text_array: frase inicial
		Resultado:
		- text_array: frase una vez separado los signos de puntuación para formar una nueva palabra"""
	text_array = text_array.replace("¿", "¿ ")
	text_array = text_array.replace("?", " ?")
	text_array = text_array.replace("¡", "¡ ")
	text_array = text_array.replace("!", " !")
	text_array = text_array.replace(".", " . ")
	text_array = text_array.replace(",", " , ")
	text_array = text_array.replace(";", " ; ")
	text_array = text_array.replace(":", " : ")

	return text_array
 
def replaceToInfinitive(words): #Función que reemplaza los verbos por su infinitivo
	"""Parámetros de entrada:
		- words: Lista de palabras
		Resultado:
		- words: Lista de palabras una vez sustituidos los verbos por sus infinitivos"""
	script_dir = os.path.dirname(__file__)
	rel_path = "es-verbs.txt"
	fileDictVerbs = os.path.join(script_dir, rel_path) 
	input_file = open(fileDictVerbs, encoding="utf-8") #Se abre el archivo que contiene todas las formas verbales de los verbos en español
	verbs_array = input_file.read().split() #Se obtiene una lista de arrays. Cada array contiene todas las conjugaciones para un mismo verbo.

	wordsInf = []
	for w in words: #Se comprueba si cada palabra evaluada existe en la lista de conjugaciones verbales
		vb = False
		for verbs in verbs_array:
			single_verbs = verbs.split(',')
			if w.lower() in single_verbs: #Si pertenece a la lista, se obtiene su infinitivo
				vb = True
				wInf = single_verbs[0]
		if vb: #Se añade el infinitivo a la lista de palabras a procesar si es un verbo
			wordsInf.append(wInf)
		else: #Si no, se mantiene la propia palabra
			wordsInf.append(w)

	return wordsInf

def addSentenceToDictionary(words, weight, dictNgram, nSize): #Se añade la frase al modelo de lenguaje general en forma de N-gramas
	"""Parámetros de entrada:
		- words: lista de palabras que contiene la frase
		- weight: peso de la frase a procesar. Para los archivos .txt = 1; para los archivos .json = frecuencia.
		- dictNgram: diccionario de N-gramas
		- nSize: tamaño de los N-gramas 
		Resultado:
		- Diccionario de N-gramas:
			Clave: El N-grama completo
			Valor: lista con los siguientes datos:
				a. Palabra N: Componente N del N-grama
				b. (N-1)-grama: Array de palabras del N-grama desde la 1 hasta la N-1
				c. Número de ocurrencias de la Palabra N tras el (N-1)-grama
				d. Número de ocurrencias del (N-1)-grama
				e. Probabilidad de ocurrencia de la Palabra N respecto al (N-1)-grama: P(N|(N-1)-grama)
			
	Ejemplo de componente en el diccionario:
	N-grama: Vamos a comer arroz
	
	Clave: 'Vamos a comer arroz'
	Valor: ['arroz', ['Vamos', 'a', 'comer'], 2, 8, 0.25]
		a. Palabra N: 'arroz'
		b. (N-1)-grama: ['Vamos', 'a', 'comer']
		c. Ocurrencias de la Palabra N: 2
		d. Ocurrencias del (N-1)-grama: 8
		e. Probabilidad P(N|(N-1)-grama): 25%"""


	listWords = []
	wordsLower = []
	for w in words: #Se ponen todas las palabras en minúsculas antes de añadir al diccionario para evitar 'case sensitive' 
		wordsLower.append(w.lower())

	for i in wordsLower: #Se recorren las palabras contenidas en la frase
		indexList = wordsLower.index(i) #Nueva palabra a procesar
		listWords.append(i)  #Se añade la palabra a la lista de palabras que han aparecido anteriormente en la frase
		listDict = []
		if indexList >= (nSize-1): #Para recoger un N-grama, la frase debe conetener, al menos, las mismas palabras que el tamaño del mismo
			keyDict = ""
			for k in range(nSize): #La clave del diccionario será el propio N-grama, que es único. Está formado por la palabra y las N-1 anteriores.
				keyDict = wordsLower[indexList-k] + " " + keyDict
			listDict.append(i) #Se añade el primer parámetro de la lista de valores (Palabra N)
			listPrev = wordsLower[(indexList-(nSize-1)):indexList:1]
			listDict.append(listPrev) #Se añade el segundo parámetro de la lista de valores: (N-1)-grama

			[num, numTot, per, dictNgram] = updateDict(listPrev, keyDict, weight, dictNgram) #Se actualiza el diccionario tras el procesado del nuevo N-grama

			listDict.append(num) #Se añade el tercer parámetro de la lista de valores: ocurrencias de la Palabra N tras el (N-1)-grama
			listDict.append(numTot) #Se añade el cuarto parámetro de la lista de valores: ocurrencias del (N-1)-grama
			listDict.append(per) #Se añade el quinto parámetro de la lista de valores: probabilidad P(N|(N-1)-grama)
			dictNgram[keyDict] = listDict #Se adjunta la lista de valores a la clave del diccionario

	return dictNgram #Se devuelve el diccionario actualizado

def updateDict(listPrev, keyDict, weight, dictNgram): #Función que actualiza el diccionario tras el procesado de un nuevo N-grama
	"""Parámetros de entrada:
		- listPrev: lista de palabras que componen el (N-1)-grama a procesar
		- keyDict: clave del diccionario correspondiente al N-grama a procesar (el propio N-grama)
		- weight: peso del nuevo N-grama 
		- dictNgram: diccionario de N-gramas

		Resultado:
		- num: número de ocurrencias totales de la palabra N tras el (N-1)-grama tras el procesado del nuevo N-grama
		- numTot: número de ocurrencias totales del (N-1)-grama tras el procesado del nuevo N-grama
		- per: porcentaje actualizado 'num'/'numTot', equivalente a P(N|(N-1)-grama)
		- dictNgram: diccionario actualizado
		"""

	keysDictExt = list(dictNgram.keys()) #Se obtiene la lista de claves del diccionario
	if len(keysDictExt) > 0: #Se comprueba que el diccionario no está vacío
		valuesDictExt = list(dictNgram.values()) #Se obtiene la lista de valores del diccionario
		valuesDictExtTras = list(zip(*valuesDictExt)) #Se traspone la lista de valores del diccionario para obtener cada uno de los datos
		valuesPrev = valuesDictExtTras[1] #Obtención de los (N-1)-grama en forma de lista de palabras
		numTotPrev = valuesDictExtTras[3] #Obtención del dato 'numTot' o número de ocurrencias de cada (N-1)-grama
		if listPrev in valuesPrev: #Caso de que el (N-1)-grama exista
			indexPrev = valuesPrev.index(listPrev) #Se obtiene el índice donde se encuentra el (N-1)-grama
			numTot = numTotPrev[indexPrev] + weight #Se actualizad el parámetro 'numTot'  del (N-1)-grama
			for indexEv in range(len(keysDictExt)):
				if(listPrev == valuesPrev[indexEv]): #Se actualizan los parámetros 'numTot' y 'per' de todos los N-gramas del diccionario que comparten el mismo (N-1)-grama debido al incrementeo del 'numTot'
					keyChange = keysDictExt[indexEv] 
					numPrev = dictNgram[keyChange][2]
					dictNgram[keyChange][3] = numTot
					dictNgram[keyChange][4] = numPrev / numTot
		else: #Si el (N-1)-grama no existe, se inicializa
			numTot = weight

		if keyDict in dictNgram: #Si el N-grama ya existía, se actualiza su ocurrencia 'num'
			num = dictNgram[keyDict][2] + weight
		else: #Si el N-grama no existía, se inicializa su ocurrencia 'num'
			num = weight
	else: #El primer N-grama se añade al diccionario siendo 'num' y 'numTot' el peso del N-grama 
		num = weight
		numTot = weight

	per = num / numTot #Cálculo de la probabilidad de ocurrencia N|(N-1)-grama

	return num, numTot, per, dictNgram #Se devuelven los valores 'num', 'numTot' y 'per' del N-grama procesado además del diccionario actualizado

def generateDictBackoffKatz(dictNgram): #Función que genera el diccionario de parámetros backoff asociados a los bigramas incluídos en el diccionario de N-gramas proporcionado
	"""Parámetros de entrada:
		- dictNgram: diccionario de N-gramas

		Resultado:
		- dictBackoff: diccionario de bigramas con sus parámetros de backoff
			Clave: El bigrama completo
			Valor: lista con los siguientes datos:
				a. Palabra 'i': Componente 'i' del bigrama o segunda palabra
				b. Palabra 'i-1': Componente 'i-1' del bigrama o primera palabra
				c. Parámetro 'c_katz' del bigrama analizado
				d. #umatorio de los 'c_katz' que comparten la primera palabra, 'w_{i-1}', del bigrama analizado
				e. #Probabilidad de backoff del bigrama analizado: P_backoff(wi_{i-1}) = p_katz(w_i|w_{i-1})
			"""
	
	dictBackoff = {} #Inicialización del diccionario de parámetro backoff
	keysDictExt = list(dictNgram.keys())  #Se extraen las claves del diccionario de N-gramas

	for nGram in keysDictExt: #Se recorre el diccionario de N-gramas en busca de bigramas con el objetivo de calcular su parámetro de backoff y añadirlos a este diccionario
		listWords = nGram.split()
		if len(listWords)==2:
			dictBackoff = addBigramToDictBackoffKatz(nGram, dictNgram, dictBackoff)
			
	return dictBackoff #Se devuelve el diccionario de bigramas con sus parámetros de backoff actualizado


def addBigramToDictBackoffKatz(bigram, dictNgram, dictBackoff): #Función que calcula el parámetro de backoff para un bigrama según el método de Katz
	"""Parámetros de entrada:
			- bigram: bigrama sobre el que calcular su backoff y añadir al diccionario
			- dictNgram: diccionario de N-gramas
			- dictBacoff: diccionario de bigramas con sus parámetros de backoff

			Resultado:
			- dictBackoff: diccionario actualizado de bigramas con sus parámetros de backoff 
				Clave: El bigrama completo
				Valor: lista con los siguientes datos:
					a. Palabra 'i': Componente 'i' del bigrama o segunda palabra
					b. Palabra 'i-1': Componente 'i-1' del bigrama o primera palabra
					c. Parámetro 'c_katz' del bigrama analizado
					d. #umatorio de los 'c_katz' que comparten la primera palabra, 'w_{i-1}', del bigrama analizado
					e. #Probabilidad de backoff del bigrama analizado: P_backoff(wi_{i-1}) = p_katz(w_i|w_{i-1})
			"""
	k = 5 #Katz recomienda utilizar el parámetro 'k' con valor 5
	#Inicialización de parámetros de la función
	nr = 0 
	nr1 = 0
	n1 = 0
	nk1 = 0

	listWords = bigram.split() #Se separa el bigrama en 'w0' ('w_i') y 'w1' ('w_{i-1}')
	w0 = listWords[1]
	w1 = listWords[0] 

	keysDictExt = list(dictNgram.keys())  #Se extraen las claves del diccionario de N-gramas
	if len(keysDictExt) > 0: #Si el diccionario de N-gramas tiene valores, se obtienen (explicados en la función 'addSentenceToDictionary')
		valuesDictExt = list(dictNgram.values()) 
		valuesDictExtTras = list(zip(*valuesDictExt)) 
		values = valuesDictExtTras[0]
		valuesPrev = valuesDictExtTras[1]
		valuesNum = valuesDictExtTras[2]
		valuesNumTot = valuesDictExtTras[3]
		prob = valuesDictExtTras[4]
	
	ind = keysDictExt.index(bigram) #Se obtiene el índice del diccionario de N-gramas donde se encuentra el bigrama analizado
	r = valuesNum[ind] #Se obtiene el número de ocurrencias del bigrama analizado
	for i in range(len(valuesNum)): #Se calculan los parámetros del método de Katz:
		if valuesNum[i] == r: #Número de N-gramas en el diccionario que ocurren las mismas veces, 'r', que el bigrama analizado
			nr = nr + 1
		elif valuesNum[i] == (r+1): #Número de N-gramas en el diccionario que ocurren una vez más, 'r+1', que el bigrama analizado
			nr1 = nr1 + 1 

		if valuesNum[i] == (k+1): #Número de N-gramas en el diccionario que ocurren una vez más, 'k+1', que el parámetro 'k' definido al inicio
			nk1 = nk1 + 1
		if valuesNum[i] == 1: #Número de N-gramas en el diccionario que ocurren una vez
			n1 = n1 + 1

	r1= (r+1)*nr1/nr #Cálculo del parámetro r*
	#Cálculo del parámetro dr
	numDr = r1/r - (k+1)*nk1/n1 
	denDr = 1 - (k+1)*nk1/n1
	dr = numDr/denDr 

	cKatz = dr*r #Cálculo del valor 'c_katz(wi_{i-1})'
	cKatzTotal = getCKatzTotal(w1, cKatz, dictBackoff) #Obtención del sumatorio de todos los 'c_katz(wi_{i-1})' que comparten el mismo 'w_{i-1}' o primera palabra del bigrama
	dictBackoff = updateCKatzTotal(w1, cKatzTotal, dictBackoff) #Se actualiza el diccionario de backoff tras el procesado del nuevo bigrama

	#Se calcula la probabilidad de backoff, 
	if cKatzTotal == 0: #En caso de que el denominador sea 0, esta probabilidad es cero
		probBackoff = 0 
	else:  #En caso contrario, se calcula la probabilidad de backoff como 'P_backoff(wi_{i-1}) = p_katz(w_i|w_{i-1}) = c_katz(wi_{i-1})/SUM_{w_i}[c_katz(wi_{i-1})]' 
		probBackoff = cKatz/cKatzTotal #O, explicado de otro modo, dividiendo el parámetro 'c_katz' del bigrama analizado entre el sumatorio de los 'c_katz' de todos los bigramas que comparten su primera palabra ('w_{i-1}')

	keyDict = bigram #Se añade el bigrama analizado al diccionario de backoff; su clave es el propio bigrama y sus valores los siguientes:
	listDict = []
	listDict.append(w0) #Segunda palabra del bigrama: 'w_i'
	listDict.append(w1) #Primera palabra del bigrama: 'w_{i-1}'
	listDict.append(cKatz) #Parámetro 'c_katz' del bigrama analizado
	listDict.append(cKatzTotal) #Sumatorio de los 'c_katz' que comparten la primera palabra, 'w_{i-1}', del bigrama analizado
	listDict.append(probBackoff) #Probabilidad de backoff del bigrama analizado
	dictBackoff[keyDict] = listDict

	return dictBackoff #Se devuelve el diccionario de backoff actualizado


def getCKatzTotal(w1, cKatz, dictBackoff): #Función que obtiene el sumatorio de todos los 'c_katz(wi_{i-1})' que comparten la misma palabra w_{i-1}
	"""Parámetros de entrada:
			- w1: Primera palabra del bigrama analizado,'w_{i-1}'
			- cKatz: Valor 'c_katz(wi_{i-1})' del bigrama analizado
			- dictBackoff: diccionario de bigramas con sus parámetros de backoff

			Resultado:
			- cKatzTotal: sumatorio de todos los 'c_katz(wi_{i-1})' que comparten la misma palabra 'w_{i-1}'
			"""
	keysDictBO = list(dictBackoff.keys()) #Se extraen las claves del diccionario de backoff
	if len(keysDictBO) > 0: #Si el diccionario de backoff tiene valores, se obtienen (explicados en las funciones 'generateDictBackoffKatz' y 'addBigramToDictBackoffKatz')
		valuesDictBO = list(dictBackoff.values()) 
		valuesDictBOTras = list(zip(*valuesDictBO))
		valuesBO = valuesDictBOTras[0]
		valuesPrevBO = valuesDictBOTras[1]
		valuesCK = valuesDictBOTras[2]
		valuesCKTot = valuesDictBOTras[3]
		probK = valuesDictBOTras[4]
	
		if w1 in valuesPrevBO: #Si la palabra 'w1' ('w_{i-1}') ya ha sido utilizado en otro bigrama incluido en el diccionario, se obtiene el valor actual de 'cKatzTotal'
			ind = valuesPrevBO.index(w1)
			cKatzTotal = valuesCKTot[ind]
		else: #Si no, se inicializa a cero
			cKatzTotal = 0

		cKatzTotal = cKatzTotal + cKatz #Se añade el valor 'cKatz' del bigrama analizado a 'cKatzTotal'

	else: #Si el diccionario está vacío, el valor de 'cKatzTotal' será el valor de 'cKatz' del bigrama bajo análisis ya que será su primer valor
		cKatzTotal = cKatz

	return cKatzTotal #Se devuelve el valor 'cKatzTotal' de los bigramas que comparten la misma palabra 'w1' ('w_{i-1}') que el bigrama analizado

def updateCKatzTotal(w1, cKatzTotal, dictBackoff): 
	"""Se actualiza el diccionario de backoff tras el procesado de un nuevo bigrama.
		Se deben actualizar los valores 'cKatzTotal' y 'probBackoff' de todos los bigramas que compartan la misma primera palabra, 'w1' ('w_{i-1}'), que el bigrama procesado
		Parámetros de entrada:
			- w1: primera palabra, 'w1' ('w_{i-1}'), del bigrama analizado
			- cKatzTotal: valor 'cKatzTotal' de los bigramas que comparten la misma palabra 'w1' ('w_{i-1}')
			- dictBackoff: diccionario de bigramas con sus parámetros de backoff

			Resultado:
			- dictBackoff:  diccionario actualizado de bigramas con sus parámetros de backoff
			"""
	keysDictBO = list(dictBackoff.keys()) #Se extraen las claves del diccionario de backoff
	if len(keysDictBO) > 0: #Si el diccionario de backoff tiene valores, se obtienen (explicados en las funciones 'generateDictBackoffKatz' y 'addBigramToDictBackoffKatz')
		valuesDictBO = list(dictBackoff.values()) 
		valuesDictBOTras = list(zip(*valuesDictBO)) 
		valuesBO = valuesDictBOTras[0]
		valuesPrevBO = valuesDictBOTras[1]
		valuesCK = valuesDictBOTras[2]
		valuesCKTot = valuesDictBOTras[3]
		probK = valuesDictBOTras[4]

		for i in range(len(valuesPrevBO)): #Se evalúa el diccionario de backoff en busca de los bigramas que compartan la misma primera palabra, 'w1' ('w_{i-1}')
			if w1 == valuesPrevBO[i]:
				cKatzAct = valuesCK[i] #Se obtiene el valor 'cKatz' del bigrama encontrado
				keyChange = keysDictBO[i]
				dictBackoff[keyChange][3] = cKatzTotal #Se guarda el nuevo valor de 'cKatzTotal'
				if cKatzTotal == 0: #Se asegura que el denominador no sea 0
					probAct = 0
				else:
					probAct = cKatzAct / cKatzTotal #Se calcula la nueva probabilidad de backoff del bigrama encontrado
				dictBackoff[keyChange][4] = probAct #Se guarda el valor actualizado de la probabilidad de backoff del bigrama encontrado

	return dictBackoff #Se devuelve el diccionario de backoff actualizado