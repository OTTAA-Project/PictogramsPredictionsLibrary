from calcularPrediccion import calcularPrediccion
import json


#Script donde se especifica una frase y se obtienen las predicciones

#Datos de entrada:
sentence = "Me voy a" #Frase inicial sobre la que calcular la predicción
maxNgram = 5 #Máximo orden del N-grama
maxNumPaths = 5 #Máximo número de caminos devueltos tras la ejecución del algoritmo

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

#Una vez recopilados todos los datos, se calcula la predicción basada en el algoritmo Viterbi
json_pathsConjugated = calcularPrediccion(sentence, maxNgram, maxNumPaths, listWords, listWordsInf, dictNgram, dictNgramInf, dictBackoff, dictBackoffInf)
#Impresión de los resultados
print(sentence, ": ", json_pathsConjugated)