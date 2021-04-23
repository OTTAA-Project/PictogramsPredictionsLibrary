from generateGeneralLanguajeModel import replaceToInfinitive
from viterbiNbest import viterbiNbest
from viterbiNbest import conjugateSentence
from viterbiNbest import convertToJSON
import json
import time


def calcularPrediccion(sentence, maxNgram, maxNumPaths, listWords, listWordsInf, dictNgram, dictNgramInf, verbs_array, listDefaultPaths): 
	#Función que realiza la predicción a partir de una frase dada y devuelve los resultados en un array JSON. Utiliza diversas funciones creadas en el archivo 'viterbiNbest'.
	"""Parámetros de entrada:
		- sentence: frase inicial a continuar
		- maxNgram: máximo orden de los N-gramas a evaluar. Por defecto: 5
		- maxNumPaths: máximo número de soluciones a devolver
		- listWords: listado de todas las palabras que aparecen en el diccionario de N-gramas
		- listWordsInf: listado de todas las palabras que aparecen en el diccionario de N-gramas con todos los verbos en infinitivos
		- dictNgram: diccionario de N-gramas
		- dictNgramInf: diccionario de N-gramas de infinitivos
		- verbs_array: lista con todas las formas verbales de los verbos en español
		- listDefaultPaths: lista de caminos por defecto

		Resultado:
		- json_pathsConjugated: array JSON con todas las predicciones calculadas (ordenadas de mayor a menor probabilidad)
		"""
	sentenceList= sentence.split() #Se convierte la frase inicial en lista de palabras
	sentenceLower = ''
	for w in range(len(sentenceList)): #Se pasan todas las palabras a minúsculas para evitar 'case sensitive'
		sentenceLower = sentenceLower + sentenceList[w].lower() + " "

	sentenceInfList = replaceToInfinitive(sentenceLower.split()) #Se cambian los verbos por su infinitivo
	sentenceInf = ''
	for w in range(len(sentenceInfList)): #Se convierte la lista de palabras con verbos en infinitivo en string
		sentenceInf = sentenceInf + sentenceInfList[w] + " "

	pathsSelected = viterbiNbest(sentenceInf, maxNgram, maxNumPaths, listWordsInf, dictNgramInf, listDefaultPaths)  #Se ejecuta el algoritmo Viterbi para obtener las predicciones de continuación de la frase inicial

	pathsConjugated = [] #Inicialización de la lista donde se guardarán las frases cuyos verbos estarán conjugados
	for path in pathsSelected: #Conjugación de todos los verbos que aparecen en las frases resultado del algoritmo Viterbi
		pathConj = conjugateSentence(sentenceLower, path, maxNgram, dictNgram, verbs_array)
		pathsConjugated.append(pathConj)

	json_pathsConjugated = convertToJSON(pathsConjugated) #Se convierte la lista de resultados en array JSON

	return json_pathsConjugated #Se devuelve el array JSON