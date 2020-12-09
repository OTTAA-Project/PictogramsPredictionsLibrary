import json
import re
import sys
import os
import math

def viterbiNbest(sentence, maxNgram, maxNumPaths, listWords, dictNgram, dictBackoff): #Función que devuelve las listas de palabras más probables para continuar la frase inicial dada
	"""Parámetros de entrada:
		- sentence: frase inicial a continuar
		- maxNgram: máximo orden de los N-gramas a evaluar. Por defecto: 5
		- maxNumPaths: máximo número de soluciones a devolver
		- listWords: listado de todas las palabras que aparecen en el diccionario de N-gramas
		- dictNgram: diccionario de N-gramas
		- dictBackoff: diccionario de bigramas con sus parámetros de backoff

		Resultado:
		- pathsSelected: caminos más probables (en forma de lista de strings) para continuar la frase inicial
		"""
	finishOperators = ['.', '?','!'] #Carácteres que identifican el final de una frase
	sentenceWords = sentence.split() #Se transforma la frase inicial en lista de palabras
	n = min(len(sentenceWords), maxNgram-1) #Se obtiene el número de palabras iniciales sobre las que trabajar (como máximo el orden máximo del N-grama establecido menos 1 ya que hay que añadir la nueva palabra a evaluar)
	nGram = [] #Se inicializa la lista de palabras que forman un N-grama
	paths = [] #Se inicializa la lista de caminos a evaluar
	pathsActive = dict() #Se inicializa el diccionario de caminos activos
	pathsActive[""] = 0
	pathsSaved = dict() #Se inicializa el diccionario de caminos guardados
	th1 = -1.0 #Umbral 1 que evalua si el algoritmo debe parar. Se inicializa a -1.
	th2 = 0 #Umbral 2 que evalua si un camino se debe podar. Se inicializa a 0.
	minUpdate = -0.1 #Mínima actualización de Umbral 2. Se establece en -0.1 (probabilidad logarítmica).

	for i in range(n): #Se construye el N-grama inicial sobre el que trabajar
		nGram.append(sentenceWords[len(sentenceWords)-n+i])
	s = 0 #Variable que evalua la iteración del algoritmo o, el número de palabras del camino más largo.

	while 1: #Bucle recursivo infinito que solo se termina cuando se encuentra un break.
		paths = list(pathsActive.keys()) #Lista de caminos activos en forma de string
		probPaths = list(pathsActive.values()) #Lista de las probabilidades de los caminos activos
		pathsActive = dict() #Se re-iniciliza el diccionario de caminos activos
		matrixProb = [list() for i in range(max(1,len(paths)))] #Se inicializa la matriz de probabilidad; filas: caminos activos, columnas: cada palabra de la lista de palabras

		for pth in range(max(1,len(paths))): #Se recorre cada camino activo
			nGramEv = [] #Se actualiza el N-grama a evaluar con el inicial y la información del camino bajo evaluación
			for wordIni in nGram:
				nGramEv.append(wordIni)
			if s > 0: 
				newNGram = paths[pth].split()
				for k in range(len(newNGram)):
					nGramEv.append(newNGram[k])
				while len(nGram)>maxNgram:
					nGramEv.pop(0)

			for word in listWords: #Se recorre la lista de palabras para calcular su probabilidad tras el camino evaluado y se añade a la matriz de probabilidades
				prob = evaluateNgram(word, nGramEv, dictNgram, dictBackoff)
				matrixProb[pth].append(prob)

		maxProbPaths = max(matrixProb) #Se calcula la probabilidad máxima de cada camino
		maxProb = max(maxProbPaths) #Se calcula la probabilidad máxima general

		if 1.5*maxProb < minUpdate: #Se actulizar Umbral 2 que, como mínimo, se incrementa en el valor del 'minUpdate'
			th2 = th2+1.5*maxProb
		else:
			th2 = th2+minUpdate

		maxProbTot = -10000 #Se incializa el valor de la probabilidad total en un valor cercano a su límite inferior (- infinito)
		maxPath = [] #Se inicializa el camino cuya probabilidad es la máxima
		for pth in range(max(1,len(paths))): #Se recorre la matriz de probabilidades
			for w in range(len(listWords)):
				if (probPaths[pth] + matrixProb[pth][w]) >= th2: #Sólo se guardan aquellos caminos que superen Umbral 2
					newPath = paths[pth].split() 
					newWord = listWords[w]
					newPath.append(newWord) #Se crea el nuevo camino con el camino evaluado añadiendo la nueva palabra
					prob = matrixProb[pth][w] #Se obtiene la probabilidad de añadir la nueva palabra
					probTot = probPaths[pth] + prob #Se actualiza la probabilidad total como la suma de la acumulada del camino a la de la evaluación de la nueva palabra añadida

					if probTot >= maxProbTot: #Se evalúa si la probabilidad de este camino es la máxima hasta el momento. Si es así, se actualiza esta probabilidad máxima y se guarda el camino.
						maxProbTot = probTot
						maxPath = newPath

					newPathSentence = "" #Se convierte el camino de lista a string
					for j in range(len(newPath)):
						newPathSentence = newPathSentence + newPath[j] + " "

					if newWord in finishOperators: #Si el camino acaba en un signo de puntuación de fin de frase, se guarda el camino y no se sigue evaluando
						pathsSaved[newPathSentence] = probTot
					else: #Si no, se añade al diccionario de caminos activos
						pathsActive[newPathSentence] = probTot
			
		if maxPath == []: #Si ningún camino ha superado Umbral 2, se finaliza el algoritmo ya que no habrá caminos activos
			break
		elif maxProbTot < th1: #Si el camino de máxima probabilidad no supera Umbral 1, se finaliza el algoritmo
			break

		th1=(2*th1+maxProbTot)/3 #Se actualiza Umbral 1 ponderando su valor actual (2/3) con la máxima probabilidad total (1/3)

		lastWord = maxPath[len(newPath)-1] 
		if lastWord in finishOperators: #Si la última palabra del camino más probable es un signo de puntuación de fin de frase, se finaliza el algoritmo
			break

		s = s + 1 #Se añade 1 a la variable que cuenta el número de iteraciones del algoritmo


	paths = list(pathsActive.keys()) #Se obtiene la lista de caminos activos actualizada
	probPaths = list(pathsActive.values()) #Se obtiene la lista de probabilidades de los caminos activos actualizada
	for pth in range(len(paths)): #Se añaden los caminos activos al diccionario de caminos guardados tras finalizar el algoritmo
		pathsSaved[paths[pth]] = probPaths[pth]

	pathsSavedOrdered = orderDictByValue(pathsSaved) #Se ordena el diccionario de caminos guardados de mayor a menor probabilidad
	pathsSO = list(pathsSavedOrdered.keys()) #Se obtiene la lista de caminos guardados ordenada por probabilidad

	pathsSelected = list() 
	for pthSd in range(min(maxNumPaths,len(pathsSO))): #Se recogen los K caminos más probables, siendo K el número máximo de caminos a devolver
		pathsSelected.append(pathsSO[pthSd])

	return pathsSelected #Se devuelven los caminos más probables


def evaluateNgram(word, nGram, dictNgram, dictBackoff): #Función que calcula la probabilidad logarítmica P(w|N-grama)
	"""Parámetros de entrada:
		- word: palabra a añadir tras el N-grama proporcionado (w)
		- nGram: N-grama inicial
		- dictNgram: diccionario de N-gramas
		- dictBackoff: diccionario de bigramas con sus parámetros de backoff

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

	keysDict = list(dictNgram.keys()) #Se obtienen las claves del diccionario de N-gramas en forma de lista
	valuesDict= list(dictNgram.values()) #Se obtienen los valores del diccionario de N-gramas en forma de lista

	if sentence in keysDict: #Si la frase aparece en el diccionario, se obtiene su probabilidad
		indexSentence = keysDict.index(sentence)
		prob = valuesDict[indexSentence][4]
		modo = "diccionario"
	else: #Si no, se debe contar con el parámetro de backoff
		modo = "backoff"
		k = 1
		sentenceSh = sentence
		while sentenceSh not in keysDict: #Se separa la parte de la frase que existe en el diccionario de la que debe ser evaluada por backoff
										  #La parte inicial de la frase es la que se evalua por backoff y la final por diccionario de N-gramas
			m = len(nGramEv) - k
			sentenceSh = ''
			sentenceBO = ''
			for i in range(m):
				sentenceSh = sentenceSh + nGramEv[len(nGramEv)-m+i] + " "
			for i in range(k+1):
				sentenceBO = sentenceBO + nGramEv[i] + " "

			if k == len(nGramEv)-1 or len(sentenceSh.split())<=1:
				break
			else:
				k = k + 1

		if sentenceSh != '' and len(sentenceSh.split())>1: #Se obtiene la probabilidad de la parte final de la frase que existe en el diccionario de N-gramas
			indexSentence = keysDict.index(sentenceSh)
			prob = valuesDict[indexSentence][4]

		wordsSentenceBO = sentenceBO.split()
		if len(wordsSentenceBO)>1:
			for p in range(len(wordsSentenceBO)-1): #Se separa la parte inicial de la frase en bigramas
				bigram = wordsSentenceBO[len(wordsSentenceBO)-p-2] + " " + wordsSentenceBO[len(wordsSentenceBO)-p-1]
				listBigramsBO.append(bigram)

			for big in listBigramsBO: #Se calcula la probabilidad acumulada a partir de todos los bigramas de la parte inicial de la frase
				prob = prob*calculateBackoffKatz(big,dictNgram,dictBackoff)

	if prob>0: #Se calcula la probabilidad logarímitica; si la probabilidad fuera 0, se asigna un valor muy bajo (realmente: -inf)
		logprob = math.log(prob) 
	else:
		logprob = -10000


	return logprob #Se devuelve la probabilidad logarítmica

def calculateBackoffKatz(bigram, dictNgram, dictBackoff): #Función que calcula la probabilidad de backoff de un bigrama dado
	"""Parámetros de entrada:
		- bigrama: bigrama a calcular su probabilidad de backoff
		- dictNgram: diccionario de N-gramas
		- dictBackoff: diccionario de bigramas con sus parámetros de backoff

		Resultado:
		- probBackoff: probabilidad de backoff del bigrama proporcionado
		"""
	keysDictExt = list(dictNgram.keys()) #Se extraen las claves del diccionario de N-gramas
	keysDictBO = list(dictBackoff.keys()) #Se extraen las claves del diccionario de backoff
	listBigram = bigram.split() #Se separa el bigrama en 'w0' ('w_i') y 'w1' ('w_{i-1}')
	w0 = listBigram[1]
	w = w0 + " " #Se añade un espacio a la palabra 'w0' ('w_i') para su búsqueda en el diccionario de N-gramas
	w1 = listBigram[0] 
	list1gram = [] #Se crea una lista que incluye el componente 'w1' ('w_{i-1}') o primera palabra del bigrama
	list1gram.append(w1)

	if len(keysDictExt) > 0: #Si el diccionario de N-gramas tiene valores, se obtienen (explicados en la función 'addSentenceToDictionary')
		valuesDictExt = list(dictNgram.values()) 
		valuesDictExtTras = list(zip(*valuesDictExt)) 
		values = valuesDictExtTras[0]
		valuesPrev = valuesDictExtTras[1]
		valuesNum = valuesDictExtTras[2]
		prob = valuesDictExtTras[4]
	if len(keysDictBO) > 0:#Si el diccionario de backoff tiene valores, se obtienen (explicados en las funciones 'generateDictBackoffKatz' y 'addBigramToDictBackoffKatz')
		valuesDictBO = list(dictBackoff.values()) 
		valuesDictBOTras = list(zip(*valuesDictBO))
		valuesPrevBO = valuesDictBOTras[1]
		valuesCK = valuesDictBOTras[2]
		valuesCKTot = valuesDictBOTras[3]
		probK = valuesDictBOTras[4]

	if bigram in keysDictBO: #Si el bigrama definido se encuentra en el diccionario de backoff, se obtiene su probabilidad del propio diccionario
		ind = keysDictBO.index(bigram)
		probBackoff = probK[ind] 
	else: #Si no, se debe calcular tal y como se explica en el método de Katz
		if w in keysDictExt: #En primer lugar, se obtiene la probabilidad de máxima verosimilitud de la segunda palabra del bigrama, 'w0' ('w_i'), a partir del valor de probabilidad de este unigrama registrado el diccionario de N-gramas
			ind2 = keysDictExt.index(w)
			probML = prob[ind2] 
		else: #Si esta palabra, definida como unigrama, no esta incluída en el diccionario de N-gramas, su pobabilidad es 0
			probML = 0

		#A continuación, se debe obtener el parámetro alfa asociado a la primera palabra del bigrama: 'alfa(w_{i-1})'
		#Para ello, se necesitan dos valores: 'probMLTot' y 'probKatzTot'

		#'probMLTot' es el sumatorio de las probabilidades de todas las palabras que aparecen en segunda posición ('w_i') en el diccionario de N-gramas formando un bigrama con la misma primera palabra ('w_{i-1}') que el bigrama analizado
		probMLTot = 0
		listValues = []
		if list1gram in valuesPrev: #Se recorre el diccionario de N-gramas en busca de los bigramas que compartan la misma palabra 'w_{i-1}'
			for j in range(len(valuesPrev)):
				if list1gram == valuesPrev[j]: #Si se encuentra, se recoge la primera palabra 'w_i' y se obtiene su probabilidad como unigrama, sumándose a la probabilidad acumulada 'probMLTot'
					val = values[j]
					valKey = val + " "
					indVal = keysDictExt.index(valKey)
					probMLTot = probMLTot + prob[indVal]
		else: #Si no se encuentra ningún bigrama en el diccionario de N-gramas que comparta la misma primera palabra 'w_{i-1}', se asigna 0 al valor de 'probMLTot'
			probMLTot = 0

		#'probKatzTot' es el sumatorio de todas las probabilidades de Katz, 'p_katz(w_i|w_{i-1})', de los bigramas que comparten la misma primera palabra 'w_{i-1}'
		probKatzTot = 0
		valCK = 0
		valCKTot = 0
		if w1 in valuesPrevBO: #Se recorre el diccionario de backoff, en busca de todos estos bigramas
			indCK = valuesPrevBO.index(w1)
			valCKTot = valuesCKTot[indCK] #El valor del sumatorio 'c_katz(wi_{i-1})' de todos los bigramas que comparten la misma palabra 'w_{i-1}', se puede obtener del valor recogido en uno de estos bigramas ya que es el mismo para todos ellos
			for k in range(len(valuesPrevBO)): #Se añade el valor 'c_katz(wi_{i-1})'de cda uno de estos bigramas al total acumulado
				if w1 == valuesPrevBO[k]:
					valCK = valCK + valuesCK[k]

		valCKNew = getCKatzNew(dictNgram) #Se obtiene el valor 'c_katz(wi_{i-1})' del bigrama analizado si se añadiera al diccionario
		valCKTot = valCKTot + valCKNew #Se añade este valor al denominador únicamente al denominador 'valCKTot' del cálculo del sumatorio probabilidad de Katz ya que este bigrama no existe en el diccionario de backoff
		probKatzTot = valCK/valCKTot

		if probMLTot == 1: #Se asegura que el denominador en el cálculo del parámetro 'alfa' no sea 0. Si lo fuera, se fija 'alfa' = 0
			alfa = 0
		else: #Si no es cero, se calcula el parámetro 'alfa' según se define en el método de Katz
			alfa = (1-probKatzTot)/(1-probMLTot)

		cKatz = alfa*probML #Se calcula el valor 'c_katz(wi_{i-1})' del bigrama definido como la multiplicación de los parámetros 'alfa', asociado a su primera palbra 'w_{i-1}', y 'probML', asociado a su segunda palabra 'w_i'
	
		if w1 in valuesPrevBO: #Para completar el cálculo de la probabilidad de backoff del bigrama en cuestión, se obtiene el valor del parámetro 'cKatzTotal'. Es decir, el sumatorio los valores 'c_katz(wi_{i-1})' para todos los bigramas que comparten la misma primera palabra, 'w_{i-1}', que el definido
			ind3 = valuesPrevBO.index(w1)
			cKatzTotal = valuesCKTot[ind3] #El sumatorio de los valores 'c_katz(wi_{i-1})' se encuentra en cualquier bigrama que comparta su primera palabra, 'w_{i-1}'
			if cKatzTotal>0: #Se completa el cálculo de la probabilidad de backoff para el bigrama dado
				probBackoff = cKatz/cKatzTotal 
			else:
				probBackoff = 0
		else: #Si no se encuentra ningún bigrama en el diccionario cuya primera palabra 'w_{i-1}' sea la misma que la del bigrama definido, su probabilidad de backoff será 0
			probBackoff = 0

	return probBackoff #Se devuelve la probabilidad de backoff calculada para el bigrama dado


def getCKatzNew(dictNgram): #Función que obtiene el valor 'c_katz(wi_{i-1})' si se añadiera un nuevo bigrama al diccionario de backoff
	"""Parámetros de entrada:
		- dictNgram: diccionario de N-gramas

		Resultado:
		- cKatz: valor 'c_katz(wi_{i-1})' si se añadiera un nuevo bigrama al diccionario de backoff
		"""
	k = 5 #Katz recomienda utilizar el parámetro 'k' con valor 5
	#Inicialización de parámetros de la función
	nr = 0
	nr1 = 0
	n1 = 0
	nk1 = 0

	keysDictExt = list(dictNgram.keys()) #Se obtiene el índice del diccionario de N-gramas donde se encuentra el bigrama analizado
	if len(keysDictExt) > 0: #Si el diccionario de N-gramas tiene valores, se obtienen (explicados en la función 'addSentenceToDictionary')
		valuesDictExt = list(dictNgram.values())
		valuesDictExtTras = list(zip(*valuesDictExt))
		values = valuesDictExtTras[0]
		valuesPrev = valuesDictExtTras[1]
		valuesNum = valuesDictExtTras[2]
		valuesNumTot = valuesDictExtTras[3]
		prob = valuesDictExtTras[4]
	
	r = 1 #El párámetro 'r', que indica el número de ocurrencias de un bigrama se inicializa a 1 ya que sería la primera vez que se procesara
	for i in range(len(valuesNum)): #Se calculan los parámetros del método de Katz:
		if valuesNum[i] == r: #Número de N-gramas en el diccionario que ocurren las mismas veces, 'r', que el bigrama analizado -en este caso 1-
			nr = nr + 1
		elif valuesNum[i] == (r+1): #Número de N-gramas en el diccionario que ocurren una vez más, 'r+1', que el bigrama analizado
			nr1 = nr1 + 1 

		if valuesNum[i] == (k+1): #Número de N-gramas en el diccionario que ocurren una vez más, 'k+1', que el parámetro 'k' definido al inicio
			nk1 = nk1 + 1
		if valuesNum[i] == 1: #Número de N-gramas en el diccionario que ocurren una vez
			n1 = n1 + 1

	r1= (r+1)*nr1/nr#Cálculo del parámetro r*
	#Cálculo del parámetro dr
	numDr = r1/r - (k+1)*nk1/n1
	denDr = 1 - (k+1)*nk1/n1
	dr = numDr/denDr

	cKatz = dr*r #Cálculo del valor 'c_katz(wi_{i-1})'

	return cKatz #Se devuelve el valor 'c_katz(wi_{i-1})'

def orderDictByValue(pathsSaved): #Función que ordena un diccionario en función de su valor de probabilidad (de mayor a menor)
	"""Parámetros de entrada:
		- pathsSaved: diccionario inicial

		Resultado:
		- pathsSavedOrdered: diccionario ordenado
		"""
	pathsSavedOrdered = dict() #Declaración del diccionario ordenado
	paths = list(pathsSaved.keys()) #Se obtienen las claves del diccionario inicial en forma de lista
	probPaths = list(pathsSaved.values()) #Se obtienen los valores del diccionario inicial en forma de lista

	pathsOrdered = list() #Se declara la lista de claves ordenadas en función de su valor
	probPathsOrdered = list() #Se declara la lista de valores ordenados
	continueEv = True #Se crea una variable booleana que indica si se continua evaluando la lista ordenada

	pathsOrdered.append(paths[0]) #Se inicializa la lista de claves ordenadas con la primera del diccionario inicial
	probPathsOrdered.append(probPaths[0]) #Se inicializa la lista de valores ordenados con el primero del diccionario inicial
	for i in range(1,len(paths)): #Se recorren todas las claves del diccionario inicial
		indexList = max(0,len(pathsOrdered)) #Se inicializa la posición a colocar la nueva clave / el nuevo valor a la última de la lista
		continueEv = True #Se restablece el valor de la variable booleana en cada iteración
		for j in range(len(pathsOrdered)): #Se recorre la lista de valores ya ordenados
			if probPaths[i] > probPathsOrdered[j] and continueEv: #Se establece el índice de la lista donde colocar el nuevo valor en cuanto se supere uno de la lista ordenada
				indexList = j
				continueEv = False

		if indexList < (len(pathsOrdered)): #Si no es el valor más bajo de los evaluados, se reordenan las lista ordenadas
			prevPath = pathsOrdered[indexList] #Se guardan la clave y el valor a reemplazar
			prevProb = probPathsOrdered[indexList]
			pathsOrdered[indexList] = paths[i] #Se guarda la nueva clave y el valor en la posición determinada previamente
			probPathsOrdered[indexList] = probPaths[i] 
			prevPath2 = prevPath #Se guarda la clave y el valor reemplazados en nuevas variables
			prevProb2 = prevProb
			for k in range((indexList+1),len(pathsOrdered)): #Se recorren las listas desde la posición actualizada hasta el final
				prevPath = pathsOrdered[k] #Se guardan la clave y el valor a reemplazar
				prevProb = probPathsOrdered[k]
				pathsOrdered[k] = prevPath2 #Se actualiza la clave y el valor de una posición por la clave y el valor que había en la posición anterior
				probPathsOrdered[k] =prevProb2
				prevPath2 = prevPath #Se guardan la clave y el valor reemplazados para actualizarlos en la siguiente iteración
				prevProb2 = prevProb
			pathsOrdered.append(prevPath2) #El valor más bajo de los evaluados y su clave asociadas, se añade de nuevo a las listas de valor y cave ordenadas respectivamente
			probPathsOrdered.append(prevProb2)
		else: #En caso de que sea el menor valor de los evaluados, se añaden clave y valor a sus respectivas listas ordenadas
			pathsOrdered.append(paths[i])
			probPathsOrdered.append(probPaths[i])

	for pth in range(len(pathsOrdered)): #Las listas de clave y valor ordenados forman el diccioanrio ordenado
		pathsSavedOrdered[pathsOrdered[pth]] = probPathsOrdered[pth]

	return pathsSavedOrdered #Se devuelve el diccionario ordenado

def conjugateSentence(sentence, path, maxNgram, dictNgram, dictBackoff):#Función que sustituye los verbos (en infinitivo) de una frase dada por su conjugación más probable
	"""Parámetros de entrada:
		- sentence: frase inicial
		- path: frase final a procesar
		- maxNgram: máximo orden de los N-gramas a evaluar. Por defecto: 5
		- dictNgram: diccionario de N-gramas
		- dictBackoff: diccionario de bigramas con sus parámetros de backoff

		Resultado:
		- final_sentence: frase conjugada
		"""
	wordsSentece = sentence.split() #Se convierte la frase inicial en lista de palabras
	lenIni = len(wordsSentece) #Se obtiene el número de palabras de la frase inicial
	final_path = wordsSentece #Inicialización de la lista de palabras que formarán la frase final

	script_dir = os.path.dirname(__file__)
	rel_path = "es-verbs.txt"
	fileDictVerbs = os.path.join(script_dir, rel_path) 
	input_file = open(fileDictVerbs, encoding="utf-8") #Se abre el archivo que contiene todas las formas verbales de los verbos en español
	verbs_array = input_file.read().split() #Se obtiene una lista de arrays. Cada array contiene todas las conjugaciones para un mismo verbo.

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
				prob = evaluateNgram(verb, nGram, dictNgram, dictBackoff)
				probList.append(prob)

			maxProb = max(probList) #Se calcula la máxima probabilidad de entre todas las formas verbales evaluadas
			indexMax = probList.index(maxProb) #Y se obtiene el índice donde ha acontecido esta máxima probabilidad 

			wordConj = conj[indexMax] #Finalmente, se recoge esta forma verbal
			final_path.append(wordConj) #Y se añade a la lista final de palabras
		else: #Si no, se añade a la lista final tal cual
			final_path.append(word)


	for i in range(lenIni): #Se eliminan las palabras de la frase inicial del resultado
		final_path.pop(0)

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
