from nodes import NodoPrograma, NodoFuncion, NodoParametro, NodoLlamadaFuncion, NodoAsignacion, NodoRetorno, NodoOperacion, NodoNumero, NodoIdentificador, NodoIncremento, NodoFor, NodoWhile, NodoIf, NodoElse, NodoString, NodoPrint
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        
    def obtener_token_actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def coincidir(self, tipo_esperado):
        token_actual = self.obtener_token_actual()
        if token_actual and token_actual[0] == tipo_esperado:
            self.pos += 1
            return token_actual
        else:
            raise SyntaxError(f"Error Sintactico: Se esperaba {tipo_esperado} pero se encontró {token_actual}")
        
    def parsear(self):
        funciones = []
        
        while self.pos < len(self.tokens):
            funciones.append(self.funcion())
        programa = NodoPrograma(funciones)
        
        if not programa.tiene_main:
            raise SyntaxError("Error Sintactico: Se esperaba una función main")
        return programa
    
    def funcion(self):
        tipo_token = self.coincidir("KEYWORD")
        tipo = tipo_token[1].lower()
        nombre_token = self.coincidir("IDENTIFIER")
        nombre = nombre_token[1]
        
        self.coincidir("DELIMITER")
        paramentros = self.paramentros()
        self.coincidir("DELIMITER")
        self.coincidir("DELIMITER")
        
        cuerpo = self.cuerpo()
        
        self.coincidir("DELIMITER")
        return NodoFuncion(tipo, nombre, paramentros, cuerpo)
    
    def parametros(self):
        parametros = []
        
        if self.obtener_token_actual() and self.obtener_token_actual()[1] != ")":
            tipo_token = self.coincidir("KEYWORD")
            tipo = tipo_token[1].lower()
            nombre_token = self.coincidir("IDENTIFIER")
            nombre = nombre_token[1]
            
            parametros.append(NodoParametro(tipo, nombre))
            
            while self.obtener_token_actual() and self.obtener_token_actual()[1] == ",":
                self.coincidir("DELIMITER")
                tipo_token = self.coincidir("KEYWORD")
                tipo = tipo_token[1].lower()
                nombre_token = self.coincidir("IDENTIFIER")
                nombre = nombre_token[1]
                
                parametros.append(NodoParametro(tipo, nombre))
                
        return parametros
    
    def cuerpo(self):
        instrucciones = []
        token_actual = self.obtener_token_actual()
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != "}":
            if token_actual[1] == "return":
                instrucciones.append(self.declaracion())
            elif token_actual[1] == "while":
                instrucciones.append(self.ciclo_while())
            elif token_actual[1] == "if":
                instrucciones.append(self.condicional_if())
            elif token_actual[1] == "else":
                instrucciones.append(self.condicional_else())
            elif token_actual[1] == "for":
                instrucciones.append(self.ciclo_for())
            elif token_actual[1] == "print":
                instrucciones.append(self.imprimir())
            elif token_actual[1] == "IDENTIFIER":
                siguiente = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
                if siguiente and siguiente[1] == "(":
                    instrucciones.append(self.llamada_funcion())
                    self.coincidir("DELIMITER")
                elif siguiente and siguiente[0] == "OPERATOR":
                    instruccion = self.incremento()
                    instrucciones.append(instruccion)
                    self.coincidir("DELIMITER")
                else:
                    nombre_token = self.coincidir("IDENTIFIER")
                    nombre = nombre_token[1]
                    self.coincidir("OPERATOR")
                    expresion = self.expresion()
                    self.coincidir("DELIMITER")
                    instrucciones.append(NodoAsignacion(None, nombre, expresion))
            elif token_actual[0] == "KEYWORD":
                instrucciones.append(self.asignacion())
            else:
                raise SyntaxError(f"Error sintactico: instruccion inesperada {token_actual}")
                    
    def llamada_funcion(self):
        nombre_token = self.coincidir('IDENTIFIER')
        nombre = nombre_token[1]
        self.coincidir('DELIMITER')
        argumentos =[]
        
        if self.obtener_token_actual() and self.obtener_token_actual()[1] != ")":
            argumentos.append(self.expresion())
            
            while self.obtener_token_actual() and self.obtener_token_actual()[1] == ",":
                self.coincidir("DELIMITER")
                argumentos.append(self.expresion())
                
        self.coincidir("DELIMITER")
        
        return NodoLlamadaFuncion(nombre, argumentos)
        
    def asignacion(self):
        tipo_token = self.coincidir("KEYWORD")
        tipo = tipo_token[1]
        nombre_token = self.coincidir("IDENTIFIER")
        nombre = nombre_token[1]
        self.coincidir("OPERADOR")
        expresion = self.expresion()
        self.coincidir("DELIMITER")
        
        return NodoAsignacion(tipo, nombre, expresion)
    
    def declaracion(self):
        self.coincidir("KEYWORD")
        expresion = self.expresion()
        self.coincidir("DELIMITER")
        return NodoRetorno(expresion)
    
    def expresion(self):
        izquierda = self.termino()
        while self.obtener_token_actual() and self.obtener_token_actual()[1] in ('+', '-', '==', '!=', '<', '>', '<=', '>=', '&&', '||'):
            operador_token = self.coincidir("OPERATOR")
            operador = operador_token[1]
            derecha = self.termino()
            izquierda = NodoOperacion(izquierda, operador, derecha)
        
        return izquierda
    
    def termino(self):
        izquierda = self.factor()
        
        while self.obtener_token_actual()[0] == "OPERATOR":
            operador_token = self.coincidir("OPERATOR")
            operador = operador_token[1]
            derecha = self.factor()
            izquierda = NodoOperacion(izquierda, operador, derecha)
            
            return izquierda
        
    def factor(self):
        token_actual = self.obtener_token_actual()
        
        if token_actual[0] == "NUMBER":
            token = self.coincidir("NUMBER")
            return NodoNumero(token[1])
        elif token_actual[0] == "IDENTIFIER":
            siguiente = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if siguiente and siguiente[1] == "(":
                return self.llamada_funcion()
            else:
                token = self.coincidir("IDENTIFIER")
                return NodoIdentificador(token[1])
        elif token_actual[1] == "(":
            self.coincidir("DELIMITER")
            expresion = self.expreison()
            self.coincidir("DELIMITER")
            return expresion
        else:
            raise SyntaxError(f"Error sintactico en factor: token inesperado {token_actual}")
        
    def incremento(self):
        nombre_token = self.coincidir("IDENTIFIER")
        nombre = nombre_token[1]
        operador_token = self.coincidir("OPERATOR")
        operador = operador_token[1]
        
        return NodoIncremento(nombre, operador)
    
    def instruccion_unica(self):
        token_actual = self.obtener_token_actual()
        if not token_actual:
            raise SyntaxError("Error sintactico: se esperaba una instruccion")
        
        if token_actual[0] == "KEYWORD":
            if token_actual[1] == "return":
                return self.declaracion()
            elif token_actual[1] == "while":
                return self.ciclo_while()
            elif token_actual[1] == "if":
                return self.condicional_if()
            elif token_actual[1] == "else":
                return self.condicional_else()
            elif token_actual[1] == "for":
                return self.ciclo_for()
            elif token_actual[1] == "print":
                return self.imprimir()
            else:
                return self.asignacion()
        elif token_actual[0] == "IDENTIFIER":
            siguiente = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if siguiente and siguiente[1] == "(":
                instruccion = self.llamada_funcion()
                self.coincidir("DELIMITER")
                return instruccion
            else:
                return self.asignacion()
        else:
            raise SyntaxError(f"Error sintactico: instruccion inesperada {token_actual}")
            
    
    def ciclo_while(self):
        pass
    
    def ciclo_for(self):
        pass
    
    def condicional_if(self):
        pass
    
    def condicional_else(self):
        pass
    
    def imprimir(self):
        pass
    