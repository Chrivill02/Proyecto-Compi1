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
        self.tabla_global = TablaSimbolos()
        self.tabla_actual = self.tabla_global
        self.funcion_actual = None
        
    def analizar(self, nodo):
        metodo = f"analizar_{type(nodo).__name__}"
        if hasattr(self, metodo):
            return getattr(self, metodo)(nodo)
        else:
            return None
        
    def analizar_nodoPrograma(self, nodo):
        for funcion in nodo.funciones:
            self.analizar(funcion)
        
        if not nodo.tiene_main():
            raise Exception("Error: No se encontro la funcion main")
        
    def analizar_nodoFuncion(self, nodo):
        self.tabla_global.declarar_funcion(
            nodo.nombre,
            nodo.tipo,
            [(p.tipo, p.nombre) for p in nodo.parametros]
        )
        
        ambito_funcion = TablaSimbolos(padre=self.tabla_global)
        self.tabla_actual = ambito_funcion
        self.funcion_actual = nodo.nombre
        
        for param in nodo.parametros:
            self.tabla_actual.declarar_variable(param.nombre, param.tipo)
            
        for instruccion in nodo.cuerpo:
            self.analizar(instruccion)
            
        self.tabla_actual = self.tabla_global
        self.funcion_actual = None
        
    def analizar_nodoParametro(self, nodo):
        self.tabla_actual.declarar_variable(nodo.nombre, nodo.tipo)
        return nodo.tipo
    
    def analizar_nodoAsignacion(self, nodo):
        tipo_expresion = self.analizar(nodo.expresion)
        
        if nodo.tipo:
            if nodo.tipo != tipo_expresion:
                raise Exception(f"Error semantico: Tipo de expresion ({tipo_expresion}) no coincide con el tipo de la variable ({nodo.tipo}) para '{nodo.nombre}'")
            self.tabla_actual.declarar_variable(nodo.nombre, nodo.tipo)
        else:
            tipo_variable = self.tabla_actual.obtener_tipo_variable(nodo.nombre)
            if tipo_variable != tipo_expresion:
                raise Exception(f"Error semantico: Tipo de expresion ({tipo_expresion}) no coincide con el tipo de la variable ({tipo_variable}) para '{nodo.nombre}'")
            
    def analizar_nodoIdentificador(self, nodo):
        return self.tabla_actual.obtener_tipo_variable(nodo.nombre)
    
    def analizar_nodoNumero(self, nodo):
        return "int" if "." not in nodo.valor else "float"
    
    def analizar_nodoOperacion(self, nodo):
        tipo_izquierda = self.analizar(nodo.izquierda)
        tipo_derecha = self.analizar(nodo.derecha)
        
        if tipo_izquierda != tipo_derecha:
            raise Exception(f"Error semantico: Tipos incompatibles en la operacion '{nodo.operador}' ({tipo_izquierda} y {tipo_derecha})")
        return tipo_izquierda
    
    def analizar_scanf(self, nodo_scanf):
        for var in nodo_scanf.variables:
            var_name = var.nombre
            if var_name not in self.tabla_simbolos:
                self.tabla_simbolos[var_name] = {
                    'tipo': 'int', 
                    'ambito': self.ambito_actual,
                    'declarada_en': 'scanf'
                }
            
    def analizar_nodoRetorno(self, nodo):
        if not self.funcion_actual:
            raise Exception("Error semantico: 'return' fuera de la funcion")
        
        tipo_expresion = self.analizar(nodo.expresion)
        tipo_funcion = self.tabla_global.obtener_funcion(self.funcion_actual)["tipo_retorno"]
        
        if tipo_expresion != tipo_funcion:
            raise Exception(f"Error semantico: Tipo de retorno de la funcion '{self.funcion_actual}' no coincide con el tipo de la expresion ({tipo_expresion} != {tipo_funcion})")
        return tipo_expresion
    
    def analizar_nodoIf(self, nodo):
        tipo_condicion = self.analizar(nodo.condicion)
        if tipo_condicion != "int":
            raise Exception(f"Error semantico: La condicion del if debe ser de tipo 'int', pero se encontro '{tipo_condicion}'")
        for instruccion in nodo.cuerpo:
            self.analizar(instruccion)
            
    def analizar_nodoFor(self, nodo):
        tipo_inicializacion = self.analizar(nodo.inicializacion)
        tipo_condicion = self.analizar(nodo.condicion)
        tipo_incremento = self.analizar(nodo.incremento)
        
        if tipo_condicion != "int":
            raise Exception(f"Error semantico: La condicion del for debe ser de tipo 'int', pero se encontro '{tipo_condicion}'")
        if tipo_inicializacion != tipo_incremento:
            raise Exception(f"Error semantico: Tipos incompatibles en la inicializacion y el incremento del for ({tipo_inicializacion} y {tipo_incremento})")
        
        for instruccion in nodo.cuerpo:
            self.analizar(instruccion)
            
    def analizar_nodoWhile(self, nodo):
        tipo_condicion = self.analizar(nodo.condicion)
        if tipo_condicion != "int":
            raise Exception(f"Error semantico: La condicion del while debe ser de tipo 'int', pero se encontro '{tipo_condicion}'")
        for instruccion in nodo.cuerpo:
            self.analizar(instruccion)
        
    def analizar_nodoLlamadaFuncion(self, nodo):
        try:
            info_funcion = self.tabla_global.obtener_funcion(nodo.nombre)
        except Exception as e:
            raise Exception(f"Error semantico: Funcion '{nodo.nombre}' no declarada")
        
        if len(nodo.argumentos) != len(info_funcion["parametros"]):
            raise Exception(f"Error semantico: La funcion '{nodo.nombre}' espera {len(info_funcion("parametros"))} argumentos, pero se proporcionaron {len(nodo.argumentos)}")
        
        for i, (arg, (tipo_parametro, _)) in enumerate(zip(nodo.argumentos, info_funcion["parametros"])):
            tipo_argumento = self.analizar(arg)
            if tipo_argumento != tipo_parametro:
                raise Exception(f"Error semantico: El argumento {i+1} de la funcion '{nodo.nombre}' es de tipo '{tipo_argumento}', pero se esperaba '{tipo_parametro}'")
            
            return info_funcion["tipo_retorno"]
