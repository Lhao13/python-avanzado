Articulo = "Cada día se hace cada vez más evidente el uso de la inteligencia artificial en nuestra vida cotidiana sin embargo aún quedan muchos elementos para trabajar y organizar antes de poder realizar una verdadera implementación de la inteligencia artificial en la educación, aun así no deja de ser una gran ventaja y ayuda a la hora de impartir y generar conocimientos esto sumado a los retos del siglo XXI que buscan una integralidad y una verdadera transversalidad de la tecnología y en los diversos ejes del saber, este documento un tiene como objetivo hacer una reflexión sobre la importancia y la verdadera utilidad de la implementación y asistencia de la IA en nuestra labor docente también que permite ver claros ejemplos a nivel mundial sobre alfabetización digital que apunta a encamina a comprender más a profundidad sobre la verdadera utilidad y practicidad de la IA, también enfocar y construir verdaderas competencias pedagógicas orientadas a construir un pensamiento científico y tecnológico."

Simbolos= [".", ",", ";", ":", "!", "?"]
reemplazos = (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"))
ArticulosYPrepocisiones = ["el", "la", "los", "lo", "las", "un", "una", "unos", "unas","a", "ante", "bajo", "con", "contra", "de", "desde", "durante","en", "entre", "hacia", "hasta", "mediante", "para", "sin", "sobre", "a", "ante", "bajo", "cabe", "con", "contra", "de", "desde", "durante","en", "entre", "hacia", "hasta", "mediante", "para", "por", "segun","sin", "so", "sobre", "tras", "versus"]

SinSimbolos = Articulo.lower()
            
for s in Simbolos:
    SinSimbolos = SinSimbolos.replace(s, "")

for original, nuevo in reemplazos:
    SinSimbolos = SinSimbolos.replace(original, nuevo)

SinArticulos = SinSimbolos.split()

for p in ArticulosYPrepocisiones:
    if p in SinArticulos:
        SinArticulos = [x for x in SinArticulos if x != p]

#------------------Análisis------------------
# Cantidad de palabras
NumeroDePalabras = len(SinArticulos)

# Cantidad de palabras únicas
NumeroDePalabrasUnicas = len(set(SinArticulos))

# Palabra más larga
PalabraMasLarga = max(SinArticulos, key=len)

# Palabra con más vocales
PalabraConMasVocales = max(SinArticulos, key=lambda x: sum(1 for c in x if c in "aeiou"))

# Cadena sin artículos ni preposiciones
Cadena = " ".join(SinArticulos)
FrecuenciaLetras = {letra: Cadena.count(letra) for letra in set(Cadena) if letra.isalpha()}

# Palabras con más frecuencia
PalabrasMasComunes = {palabra: SinArticulos.count(palabra) for palabra in set(SinArticulos)}

#Palabras con más densidad (longitud/frecuencia)
PalabrasConMasDensidad = {palabra: len(palabra) / SinArticulos.count(palabra) for palabra in set(SinArticulos)}

#Longitud promedio de palabras
LongitudPromedioPalabras = sum(len(p) for p in SinArticulos) / len(SinArticulos) if SinArticulos else 0

#------------------Resultados------------------
# Número de palabras
print(f"Número de palabras: {NumeroDePalabras}")

# Número de palabras únicas
print(f"Número de palabras únicas: {NumeroDePalabrasUnicas}")

# Palabra más larga
print(f"Palabra más larga: {PalabraMasLarga}")

# Palabra con más vocales
print(f"Palabra con más vocales: {PalabraConMasVocales}")

# Frecuencia de letras
print(f"Frecuencia de letras: {FrecuenciaLetras}")

# Ordenar palabras por mayor frecuencia, solo mostrar las 5 mas altas
sorted_by_value_asc = dict(sorted(PalabrasMasComunes.items(), key=lambda item: item[1], reverse=True))
print(f"Palabras más comunes: {list(sorted_by_value_asc.items())[:5]}")

# Ordenar palabras por mayor densidad, solo mostrar las 5 mas altas
sorted_by_value_asc2 = dict(sorted(PalabrasConMasDensidad.items(), key=lambda item: item[1], reverse=True))
print(f"Palabras con más densidad: {list(sorted_by_value_asc2.items())[:5]}")

# Longitud promedio de palabras
print(f"Longitud promedio de palabras: {LongitudPromedioPalabras}")