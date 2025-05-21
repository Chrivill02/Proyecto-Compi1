class TablaSimbolos:
    def __init__(self, padre=None):
        self.padre = padre
        self.variables = {}
        self.funciones = {}
        
    def declarar_variable(self, nombre, tipo):
        if nombre in self.variables:
            raise Exception(f"Error: La variable '{nombre}' ya ha sido declarada")
        self.variables[nombre] = {
            "tipo": tipo, 
            "es_variable": True
            }
        
    def obtener_tipo_variable(self, nombre):
        if nombre in self.variables:
            return self.variables[nombre]["tipo"]
        elif self.padre:
            return self.padre.obtener_tipo_variable(nombre)
        raise Exception(f"Error: La variable '{nombre}' no a sido declarada")
    
    def declarar_funcion(self, nombre, tipo_retorno, parametros):
        if nombre in self.funciones:
            raise Exception(f"Error: La funcion '{nombre}' ya a sido declarada")
        self.funciones[nombre] = {
            "tipo_retorno": tipo_retorno, 
            "parametros": parametros, 
            "es_funcion": True
            }
        
    def obtener_funcion(self, nombre):
        if nombre in self.funciones:
            return self.funciones[nombre]
        elif self.padre:
            return self.padre.obtener_funcion(nombre)
        raise Exception(f"Error: La funcion '{nombre}' no a sido declarada")
    
    def verificar_funcion(self, nombre, tipo_retorno, parametros):
        if nombre in self.funciones:
            funcion = self.funciones[nombre]
            if funcion["tipo_retorno"] != tipo_retorno:
                raise Exception(f"Error: La funcion '{nombre}' tiene un tipo de retorno diferente")
            if len(funcion["parametros"]) != len(parametros):
                raise Exception(f"Error: La funcion '{nombre}' tiene un numero diferente de parametros")
            for i, param in enumerate(parametros):
                if funcion["parametros"][i] != param:
                    raise Exception(f"Error: El tipo del parametro {i+1} de la funcion '{nombre}' es diferente")
                else:
                    return True
        else:
            raise Exception(f"Error: La funcion '{nombre}' no a sido declarada")
        
class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = {}
        self.ambito_actual = "global"
        self.tipo_actual = None
        self.funciones = {}

    def analizar(self, ast):
        # Pasar por el árbol AST y analizar cada nodo
        for nodo in ast:
            self.analizar_nodo(nodo)

    def analizar_nodo(self, nodo):
        if nodo is None:
            return

        tipo_nodo = nodo.__class__.__name__

        if tipo_nodo == "Programa":
            self.analizar_programa(nodo)
        elif tipo_nodo == "Declaracion":
            self.analizar_declaracion(nodo)
        elif tipo_nodo == "Asignacion":
            self.analizar_asignacion(nodo)
        elif tipo_nodo == "ExpresionBinaria":
            return self.analizar_expresion_binaria(nodo)
        elif tipo_nodo == "Identificador":
            return self.analizar_identificador(nodo)
        elif tipo_nodo == "Literal":
            return self.analizar_literal(nodo)
        elif tipo_nodo == "DeclaracionFuncion":
            self.analizar_declaracion_funcion(nodo)
        elif tipo_nodo == "LlamadaFuncion":
            return self.analizar_llamada_funcion(nodo)
        elif tipo_nodo == "Retorno":
            self.analizar_retorno(nodo)
        elif tipo_nodo == "Si":
            self.analizar_si(nodo)
        elif tipo_nodo == "Mientras":
            self.analizar_mientras(nodo)
        elif tipo_nodo == "Para":
            self.analizar_para(nodo)
        elif tipo_nodo == "Bloque":
            self.analizar_bloque(nodo)
        else:
            # Si es un nodo no reconocido, imprimir una advertencia
            print(f"Tipo de nodo no implementado: {tipo_nodo}")

    def analizar_programa(self, programa):
        for nodo in programa.nodos:
            self.analizar_nodo(nodo)

    def analizar_declaracion(self, declaracion):
        tipo = declaracion.tipo
        nombre = declaracion.nombre
        valor_inicial = declaracion.valor

        # Verificar si la variable ya está declarada en el ámbito actual
        clave = f"{self.ambito_actual}.{nombre}"
        if clave in self.tabla_simbolos:
            raise Exception(f"Error semántico: La variable '{nombre}' ya está declarada en el ámbito '{self.ambito_actual}'")

        # Agregar a la tabla de símbolos
        self.tabla_simbolos[clave] = {
            "tipo": tipo,
            "ambito": self.ambito_actual
        }

        # Si hay un valor inicial, validar que sea del tipo correcto
        if valor_inicial:
            tipo_valor = self.analizar_nodo(valor_inicial)
            if tipo_valor != tipo and tipo_valor is not None:
                raise Exception(f"Error semántico: No se puede asignar un valor de tipo '{tipo_valor}' a una variable de tipo '{tipo}'")

    def analizar_asignacion(self, asignacion):
        nombre = asignacion.objetivo
        valor = asignacion.valor

        # Verificar si la variable existe
        clave_global = f"global.{nombre}"
        clave_local = f"{self.ambito_actual}.{nombre}"
        
        if clave_local in self.tabla_simbolos:
            tipo_variable = self.tabla_simbolos[clave_local]["tipo"]
        elif clave_global in self.tabla_simbolos:
            tipo_variable = self.tabla_simbolos[clave_global]["tipo"]
        else:
            raise Exception(f"Error semántico: La variable '{nombre}' no está declarada")

        # Verificar que el valor sea del tipo correcto
        tipo_valor = self.analizar_nodo(valor)
        if tipo_valor != tipo_variable and tipo_valor is not None:
            raise Exception(f"Error semántico: No se puede asignar un valor de tipo '{tipo_valor}' a una variable de tipo '{tipo_variable}'")

    def analizar_expresion_binaria(self, expresion):
        tipo_izq = self.analizar_nodo(expresion.izquierda)
        tipo_der = self.analizar_nodo(expresion.derecha)
        
        # Si alguno de los operandos es None (error previo), no continuar con la validación
        if tipo_izq is None or tipo_der is None:
            return None
            
        # Verificar compatibilidad de tipos
        if expresion.operador in ['+', '-', '*', '/']:
            # Para operaciones aritméticas
            if tipo_izq not in ['int', 'float'] or tipo_der not in ['int', 'float']:
                raise Exception(f"Error semántico: Operador '{expresion.operador}' no aplicable a tipos '{tipo_izq}' y '{tipo_der}'")
                
            # Determinar el tipo resultante (float si alguno es float)
            if tipo_izq == 'float' or tipo_der == 'float':
                return 'float'
            else:
                return 'int'
                
        elif expresion.operador in ['==', '!=', '<', '>', '<=', '>=']:
            # Para operaciones de comparación
            if tipo_izq != tipo_der:
                raise Exception(f"Error semántico: No se pueden comparar tipos diferentes: '{tipo_izq}' y '{tipo_der}'")
            return 'int'  # Las comparaciones retornan un valor booleano (representado como int en C)
            
        elif expresion.operador in ['&&', '||']:
            # Para operaciones lógicas
            if tipo_izq != 'int' or tipo_der != 'int':
                raise Exception(f"Error semántico: Operador '{expresion.operador}' requiere operandos de tipo 'int'")
            return 'int'
            
        return None

    def analizar_identificador(self, identificador):
        nombre = identificador.nombre

        # Buscar en ámbito local primero, luego en global
        clave_local = f"{self.ambito_actual}.{nombre}"
        clave_global = f"global.{nombre}"
        
        if clave_local in self.tabla_simbolos:
            return self.tabla_simbolos[clave_local]["tipo"]
        elif clave_global in self.tabla_simbolos:
            return self.tabla_simbolos[clave_global]["tipo"]
        else:
            raise Exception(f"Error semántico: La variable '{nombre}' no está declarada")

    def analizar_literal(self, literal):
        valor = literal.valor
        
        if isinstance(valor, int):
            return 'int'
        elif isinstance(valor, float):
            return 'float'
        elif isinstance(valor, str):
            if len(valor) == 1:  # Si es un carácter
                return 'char'
            else:
                return 'string'
        else:
            return None

    def analizar_declaracion_funcion(self, funcion):
        nombre = funcion.nombre
        tipo_retorno = funcion.tipo_retorno
        parametros = funcion.parametros
        cuerpo = funcion.cuerpo
        
        # Verificar si la función ya está declarada
        if nombre in self.funciones:
            raise Exception(f"Error semántico: La función '{nombre}' ya está declarada")
            
        # Registrar la función
        self.funciones[nombre] = {
            "tipo_retorno": tipo_retorno,
            "parametros": [(param.tipo, param.nombre) for param in parametros]
        }
        
        # Cambiar al ámbito de la función
        ambito_anterior = self.ambito_actual
        self.ambito_actual = nombre
        
        # Registrar los parámetros en la tabla de símbolos
        for param in parametros:
            clave = f"{self.ambito_actual}.{param.nombre}"
            self.tabla_simbolos[clave] = {
                "tipo": param.tipo,
                "ambito": self.ambito_actual
            }
            
        # Analizar el cuerpo de la función
        self.analizar_nodo(cuerpo)
        
        # Volver al ámbito anterior
        self.ambito_actual = ambito_anterior

    def analizar_llamada_funcion(self, nodo):
        nombre = nodo.nombre
        argumentos = nodo.argumentos
        
        # Verificar si la función existe
        if nombre not in self.funciones:
            raise Exception(f"Error semántico: La función '{nombre}' no está declarada")
            
        # Obtener información de la función
        info_funcion = self.funciones[nombre]
        
        # Verificar el número de argumentos
        if len(argumentos) != len(info_funcion["parametros"]):
            raise Exception(f"Error semántico: La función '{nombre}' espera {len(info_funcion['parametros'])} argumentos, pero se proporcionaron {len(argumentos)}")
            
        # Verificar el tipo de cada argumento
        for i, arg in enumerate(argumentos):
            tipo_esperado = info_funcion["parametros"][i][0]
            tipo_proporcionado = self.analizar_nodo(arg)
            
            if tipo_proporcionado != tipo_esperado:
                raise Exception(f"Error semántico: El argumento {i+1} de la función '{nombre}' debe ser de tipo '{tipo_esperado}', pero se proporcionó '{tipo_proporcionado}'")
                
        # Retornar el tipo de retorno de la función
        return info_funcion["tipo_retorno"]

    def analizar_retorno(self, nodo):
        # Verificar si estamos en una función
        if self.ambito_actual == "global":
            raise Exception("Error semántico: Instrucción 'return' fuera de una función")
            
        # Verificar el tipo de retorno
        tipo_retorno_esperado = self.funciones[self.ambito_actual]["tipo_retorno"]
        
        if nodo.expresion is None:
            if tipo_retorno_esperado != "void":
                raise Exception(f"Error semántico: La función '{self.ambito_actual}' debe retornar un valor de tipo '{tipo_retorno_esperado}'")
        else:
            tipo_retorno_actual = self.analizar_nodo(nodo.expresion)
            if tipo_retorno_actual != tipo_retorno_esperado:
                raise Exception(f"Error semántico: La función '{self.ambito_actual}' debe retornar un valor de tipo '{tipo_retorno_esperado}', pero retorna '{tipo_retorno_actual}'")

    def analizar_si(self, nodo):
        # Analizar la condición
        tipo_condicion = self.analizar_nodo(nodo.condicion)
        if tipo_condicion != 'int':
            raise Exception("Error semántico: La condición de una sentencia 'if' debe ser de tipo entero/booleano")
            
        # Analizar los bloques de código
        self.analizar_nodo(nodo.entonces)
        if nodo.sino:
            self.analizar_nodo(nodo.sino)

    def analizar_mientras(self, nodo):
        # Analizar la condición
        tipo_condicion = self.analizar_nodo(nodo.condicion)
        if tipo_condicion != 'int':
            raise Exception("Error semántico: La condición de un bucle 'while' debe ser de tipo entero/booleano")
            
        # Analizar el cuerpo del bucle
        self.analizar_nodo(nodo.cuerpo)

    def analizar_para(self, nodo):
        # Crear un nuevo ámbito para el bucle for
        ambito_anterior = self.ambito_actual
        self.ambito_actual = f"{ambito_anterior}_for"
        
        # Analizar inicialización, condición y actualización
        if nodo.inicializacion:
            self.analizar_nodo(nodo.inicializacion)
            
        if nodo.condicion:
            tipo_condicion = self.analizar_nodo(nodo.condicion)
            if tipo_condicion != 'int':
                raise Exception("Error semántico: La condición de un bucle 'for' debe ser de tipo entero/booleano")
                
        if nodo.actualizacion:
            self.analizar_nodo(nodo.actualizacion)
            
        # Analizar el cuerpo del bucle
        self.analizar_nodo(nodo.cuerpo)
        
        # Restaurar ámbito anterior
        self.ambito_actual = ambito_anterior

    def analizar_bloque(self, nodo):
        # Analizar cada instrucción en el bloque
        for instruccion in nodo.instrucciones:
            self.analizar_nodo(instruccion)