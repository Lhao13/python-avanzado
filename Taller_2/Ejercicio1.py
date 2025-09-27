#primera parte
#Crea una claseMatrizSymbolica que represente matrices con elementos simbólicos.

class MatrizSymbolica:

    def __init__(self):
        self.matriz = []
        self.filas = 0
        self.columnas = 0

    def agregar_fila(self, fila):
        self.matriz.append(fila)
        self.filas += 1
        self.columnas = len(fila)
    
    def es_numerico(self, elemento):
        """Verifica si un elemento es numérico"""
        try:
            float(elemento)
            return True
        except (ValueError, TypeError):
            return False
    
    def es_matriz_numerica(self):
        """Verifica si toda la matriz contiene solo números"""
        for fila in self.matriz:
            for elemento in fila:
                if not self.es_numerico(elemento):
                    return False
        return True
    
    # Representacion de la matriz
    def __repr__(self):
        return "\n".join(["[" + "  ,  ".join(fila) + "]" for fila in self.matriz])

    #suma
    def __add__(self, otra):
        if self.filas != otra.filas or self.columnas != otra.columnas:
            raise ValueError("Las matrices deben tener las mismas dimensiones para sumar.")
        resultado = MatrizSymbolica()
        for i in range(self.filas):
            fila_resultado = []
            for j in range(self.columnas):
                elem1 = self.matriz[i][j]
                elem2 = otra.matriz[i][j]
                # Si ambos elementos son numéricos, hacer el cálculo
                if self.es_numerico(elem1) and self.es_numerico(elem2):
                    suma = float(elem1) + float(elem2)
                    # Si es entero, mostrarlo como entero
                    if suma.is_integer():
                        fila_resultado.append(str(int(suma)))
                    else:
                        fila_resultado.append(str(suma))
                else:
                    fila_resultado.append(f"({elem1}) + ({elem2})")
            resultado.agregar_fila(fila_resultado)
        return resultado
    
    #resta
    def __sub__(self, otra):
        if self.filas != otra.filas or self.columnas != otra.columnas:
            raise ValueError("Las matrices deben tener las mismas dimensiones para restar.")
        resultado = MatrizSymbolica()
        for i in range(self.filas):
            fila_resultado = []
            for j in range(self.columnas):
                elem1 = self.matriz[i][j]
                elem2 = otra.matriz[i][j]
                # Si ambos elementos son numéricos, hacer el cálculo
                if self.es_numerico(elem1) and self.es_numerico(elem2):
                    resta = float(elem1) - float(elem2)
                    # Si es entero, mostrarlo como entero
                    if resta.is_integer():
                        fila_resultado.append(str(int(resta)))
                    else:
                        fila_resultado.append(str(resta))
                else:
                    fila_resultado.append(f"({elem1}) - ({elem2})")
            resultado.agregar_fila(fila_resultado)
        return resultado
    
    #multiplicacion
    def __mul__(self, otra):
        if self.columnas != otra.filas:
            raise ValueError("El número de columnas de la primera matriz debe ser igual al número de filas de la segunda.")
        resultado = MatrizSymbolica()
        for i in range(self.filas):
            fila_resultado = []
            for j in range(otra.columnas):
                # Verificar si todos los elementos involucrados son numéricos
                todos_numericos = True
                suma_numerica = 0
                suma_simbolica = ""
                
                for k in range(self.columnas):
                    elem1 = self.matriz[i][k]
                    elem2 = otra.matriz[k][j]
                    
                    if self.es_numerico(elem1) and self.es_numerico(elem2):
                        # Calcular producto numérico
                        producto = float(elem1) * float(elem2)
                        suma_numerica += producto
                        
                        # También mantener versión simbólica por si acaso
                        termino = f"({elem1})*({elem2})"
                        suma_simbolica += termino if suma_simbolica == "" else f" + {termino}"
                    else:
                        todos_numericos = False
                        termino = f"({elem1})*({elem2})"
                        suma_simbolica += termino if suma_simbolica == "" else f" + {termino}"
                
                # Usar resultado numérico si todos los elementos son numéricos
                if todos_numericos:
                    if suma_numerica.is_integer():
                        fila_resultado.append(str(int(suma_numerica)))
                    else:
                        fila_resultado.append(str(suma_numerica))
                else:
                    fila_resultado.append(suma_simbolica)
            resultado.agregar_fila(fila_resultado)
        return resultado
    
    #transpuesta (matrices 2x2 y 3x3)
    def transponer(self):
        resultado = MatrizSymbolica()
        for j in range(self.columnas):
            fila_transpuesta = []
            for i in range(self.filas):
                fila_transpuesta.append(self.matriz[i][j])
            resultado.agregar_fila(fila_transpuesta)
        return resultado
    
    #determinante (matrices 2x2 y 3x3)
    def determinante(self):
        if self.filas != self.columnas:
            raise ValueError("La matriz debe ser cuadrada para calcular el determinante.")
        
        if self.filas == 2:
            a, b = self.matriz[0]
            c, d = self.matriz[1]
            
            # Si todos son numéricos, calcular directamente
            if (self.es_numerico(a) and self.es_numerico(b) and 
                self.es_numerico(c) and self.es_numerico(d)):
                det = float(a) * float(d) - float(b) * float(c)
                return str(int(det)) if det.is_integer() else str(det)
            else:
                return f"({a})*({d}) - ({b})*({c})"
                
        elif self.filas == 3:
            a, b, c = self.matriz[0]
            d, e, f = self.matriz[1]
            g, h, i = self.matriz[2]
            
            # Si todos son numéricos, calcular directamente
            elementos = [a, b, c, d, e, f, g, h, i]
            if all(self.es_numerico(elem) for elem in elementos):
                det = (float(a)*float(e)*float(i) + float(b)*float(f)*float(g) + 
                       float(c)*float(d)*float(h) - float(c)*float(e)*float(g) - 
                       float(b)*float(d)*float(i) - float(a)*float(f)*float(h))
                return str(int(det)) if det.is_integer() else str(det)
            else:
                return (f"({a})*({e})*({i}) + ({b})*({f})*({g}) + ({c})*({d})*({h}) - "
                        f"(({c})*({e})*({g}) + ({b})*({d})*({i}) + ({a})*({f})*({h}))")
        else:
            raise NotImplementedError("El cálculo del determinante solo está implementado para matrices 2x2 y 3x3.")
    
    #inversa sinmbolica (matrices 2x2 y 3x3)
    def inversa(self):
        if self.filas != self.columnas:
            raise ValueError("La matriz debe ser cuadrada para calcular la inversa.")
        
        det = self.determinante()
        
        # Verificar si el determinante es 0 para matrices numéricas
        if self.es_matriz_numerica() and float(det) == 0:
            raise ValueError("La matriz no tiene inversa (determinante = 0)")
        
        if self.filas == 2:
            a, b = self.matriz[0]
            c, d = self.matriz[1]
            resultado = MatrizSymbolica()
            
            # Si la matriz es completamente numérica, calcular valores directamente
            if self.es_matriz_numerica():
                det_num = float(det)
                fila1 = [str(float(d)/det_num), str(-float(b)/det_num)]
                fila2 = [str(-float(c)/det_num), str(float(a)/det_num)]
                
                # Convertir a enteros si es posible
                for i in range(len(fila1)):
                    if float(fila1[i]).is_integer():
                        fila1[i] = str(int(float(fila1[i])))
                for i in range(len(fila2)):
                    if float(fila2[i]).is_integer():
                        fila2[i] = str(int(float(fila2[i])))
                
                resultado.agregar_fila(fila1)
                resultado.agregar_fila(fila2)
            else:
                # Mantener operaciones simbólicas
                resultado.agregar_fila([f"({d})/({det})", f"-({b})/({det})"])
                resultado.agregar_fila([f"-({c})/({det})", f"({a})/({det})"])
            
            return resultado
            
        elif self.filas == 3:
            a, b, c = self.matriz[0]
            d, e, f = self.matriz[1]
            g, h, i = self.matriz[2]
            resultado = MatrizSymbolica()
            
            # Si la matriz es completamente numérica, calcular valores directamente
            if self.es_matriz_numerica():
                det_num = float(det)
                
                # Calcular cofactores numéricamente
                c11 = (float(e)*float(i) - float(f)*float(h)) / det_num
                c12 = -(float(b)*float(i) - float(c)*float(h)) / det_num
                c13 = (float(b)*float(f) - float(c)*float(e)) / det_num
                
                c21 = -(float(d)*float(i) - float(f)*float(g)) / det_num
                c22 = (float(a)*float(i) - float(c)*float(g)) / det_num
                c23 = -(float(a)*float(f) - float(c)*float(d)) / det_num
                
                c31 = (float(d)*float(h) - float(e)*float(g)) / det_num
                c32 = -(float(a)*float(h) - float(b)*float(g)) / det_num
                c33 = (float(a)*float(e) - float(b)*float(d)) / det_num
                
                # Convertir a string y a enteros si es posible
                cofactores = [c11, c12, c13, c21, c22, c23, c31, c32, c33]
                cofactores_str = []
                for cf in cofactores:
                    if cf == int(cf):
                        cofactores_str.append(str(int(cf)))
                    else:
                        cofactores_str.append(str(cf))
                
                resultado.agregar_fila(cofactores_str[0:3])
                resultado.agregar_fila(cofactores_str[3:6])
                resultado.agregar_fila(cofactores_str[6:9])
            else:
                # Mantener operaciones simbólicas
                resultado.agregar_fila([
                    f"(({e})*({i}) - ({f})*({h}))/({det})",
                    f"-(({b})*({i}) - ({c})*({h}))/({det})",
                    f"(({b})*({f}) - ({c})*({e}))/({det})"
                ])
                resultado.agregar_fila([
                    f"-(({d})*({i}) - ({f})*({g}))/({det})",
                    f"(({a})*({i}) - ({c})*({g}))/({det})",
                    f"-(({a})*({f}) - ({c})*({d}))/({det})"
                ])
                resultado.agregar_fila([
                    f"(({d})*({h}) - ({e})*({g}))/({det})",
                    f"-(({a})*({h}) - ({b})*({g}))/({det})",
                    f"(({a})*({e}) - ({b})*({d}))/({det})"
                ])
            
            return resultado
        else:
            raise NotImplementedError("El cálculo de la inversa solo está implementado para matrices 2x2 y 3x3.")
    
    # Método para sustituir variables simbólicas por valores numéricos
    def sustituir(self, variables):
        """
        Sustituye las variables simbólicas por valores numéricos.
        variables: diccionario donde las claves son las variables (strings) y los valores son números
        """
        resultado = MatrizSymbolica()
        for i in range(self.filas):
            fila_nueva = []
            for j in range(self.columnas):
                elemento = str(self.matriz[i][j])
                # Sustituir cada variable en el elemento
                for var, valor in variables.items():
                    elemento = elemento.replace(str(var), str(valor))
                # Evaluar la expresión resultante de forma segura
                try:
                    elemento_evaluado = eval(elemento)
                    fila_nueva.append(str(elemento_evaluado))
                except:
                    fila_nueva.append(elemento)  # Si no se puede evaluar, mantener como string
            resultado.agregar_fila(fila_nueva)
        return resultado
    
    
    
if __name__ == "__main__":
    # Crear dos matrices simbólicas
    A = MatrizSymbolica()
    A.agregar_fila(["A", "2"])
    A.agregar_fila(["A", "A"])

    B = MatrizSymbolica()
    B.agregar_fila(["4", "5"])
    B.agregar_fila(["6", "7"])

    #suma
    C = A + B
    print("Matriz C (A + B):")
    print(C)

    #resta
    R = A - B
    print("\nMatriz R (A - B):")
    print(R)

    #multiplicacion
    F = A * B
    print("\nMatriz F (A * B):")
    print(F)

    #transpuesta
    At = A.transponer()
    print("\nMatriz At (Transpuesta de A):")
    print(At)

    Bt = B.transponer()
    print("\nMatriz Bt (Transpuesta de B):")
    print(Bt)

    #determinante
    det_A = A.determinante()
    det_B = B.determinante()
    print("\nDeterminante de A:")
    print(det_A)
    print("\nDeterminante de B:")
    print(det_B)

    #inversa
    inv_A = A.inversa()
    inv_B = B.inversa()
    print("\nInversa de A:")
    print(inv_A)
    print("\nInversa de B:")
    print(inv_B)

    # Sustituir variables en una matriz simbólica
    A_sustituida = A.sustituir({"A": 10})
    print("\nMatriz A sustituida:")
    print(A_sustituida)
    
  
    