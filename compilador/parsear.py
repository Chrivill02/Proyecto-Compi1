from nodes import *


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        
    def obtener_token_actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def coincidir(self, tipo_esperado, valor_esperado=None):
        token_actual = self.obtener_token_actual()
        if token_actual:
            if token_actual[0] != tipo_esperado:
                raise SyntaxError(f"Error sintactico: Se esperaba {tipo_esperado}, pero se encontro {token_actual}")
            if valor_esperado is not None and token_actual[1] != valor_esperado:
                raise SyntaxError(f"Error Sintactico: se esperaba {tipo_esperado} '{valor_esperado}' pero se encontro {token_actual}")
            self.pos += 1
            return token_actual
        else:
            raise SyntaxError(f"Error sintactico: Se esperaba {tipo_esperado}, pero no hay más tokens")
        
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
        
        self.coincidir("DELIMITER", "(")
        parametros = self.parametros()
        self.coincidir("DELIMITER", ")")
        self.coincidir("DELIMITER", "{")
        
        cuerpo = self.cuerpo()
        
        self.coincidir("DELIMITER", "}")
        return NodoFuncion(tipo, nombre, parametros, cuerpo)
    
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
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != "}":
            if self.obtener_token_actual()[1] == "return":
                instrucciones.append(self.declaracion())
            elif self.obtener_token_actual()[1] == "while":
                instrucciones.append(self.ciclo_while())
            elif self.obtener_token_actual()[1] == "if":
                instrucciones.append(self.condicional_if())
            elif self.obtener_token_actual()[1] == "else":
                instrucciones.append(self.condicional_else())
            elif self.obtener_token_actual()[1] == "for":
                instrucciones.append(self.ciclo_for())
            elif self.obtener_token_actual()[1] == "print":
                instrucciones.append(self.imprimir())
            elif self.obtener_token_actual()[0] == "IDENTIFIER":
                siguiente = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
                if siguiente and siguiente[1] == "(":
                    instrucciones.append(self.llamada_funcion())
                    self.coincidir("DELIMITER", ";")
                elif siguiente and siguiente[0] == "OPERATOR" and siguiente[1] in ("++", "--"):
                    instruccion = self.incremento()
                    instrucciones.append(instruccion)
                    self.coincidir("DELIMITER", ";")
                else:
                    nombre = self.coincidir("IDENTIFIER")[1]
                    self.coincidir("OPERATOR", "=")
                    expresion = self.expresion()
                    self.coincidir("DELIMITER", ";")
                    instrucciones.append(NodoAsignacion(None, nombre, expresion))
            elif self.obtener_token_actual()[0] == "KEYWORD":
                instrucciones.append(self.asignacion())
            else:
                raise SyntaxError(f"Error sintactico: instruccion inesperada {self.obtener_token_actual()}")

        return instrucciones
                    
    def llamada_funcion(self):
        nombre_token = self.coincidir("IDENTIFIER")
        nombre = nombre_token[1]
        self.coincidir("DELIMITER", "(")
        argumentos =[]
        
        if self.obtener_token_actual() and self.obtener_token_actual()[1] != ")":
            argumentos.append(self.expresion())
            
            while self.obtener_token_actual() and self.obtener_token_actual()[1] == ",":
                self.coincidir("DELIMITER", ",")
                argumentos.append(self.expresion())
                
        self.coincidir("DELIMITER", ")")
        
        return NodoLlamadaFuncion(nombre, argumentos)
        
    def asignacion(self):
        tipo_token = self.coincidir("KEYWORD")
        tipo = tipo_token[1]
        nombre_token = self.coincidir("IDENTIFIER")
        nombre = nombre_token[1]
        self.coincidir("OPERATOR")
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
        
        while self.obtener_token_actual() and self.obtener_token_actual()[1] in ('*', '/'):
            operador_token = self.coincidir('OPERATOR')
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
            self.coincidir("DELIMITER", "(")
            expresion = self.expresion()
            self.coincidir("DELIMITER", ")")
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
        self.coincidir("KEYWORD")
        self.coincidir("DELIMITER")
        condicion = self.expresion()
        self.coincidir("DELIMITER")
        
        cuerpo = []
        if self.obtener_token_actual() and self.obtener_token_actual()[1] == "{":
            self.coincidir("DELIMITER")
            cuerpo = self.cuerpo()
            self.coincidir("DELIMITER")
        else:
            cuerpo.append(self.instruccion_unica())
        
        return NodoWhile(condicion, cuerpo)
    
    def ciclo_for(self):
        self.coincidir("KEYWORD")
        self.coincidir("DELIMITER")
        
        if self.obtener_token_actual()[0] == "KEYWORD":
            inicializacion = self.asignacion()
        else:
            nombre_token = self.coincidir("IDENTIFIER")
            nombre = nombre_token[1]
            self.coincidir("OPERATOR")
            expresion = self.expresion()
            self.coincidir("DELIMITER")
            inicializacion = NodoAsignacion(None, nombre, expresion)
            
        condicion = self.expresion()
        self.coincidir("DELIMITER")
        
        incremento = self.incremento()
        self.coincidir("DELIMITER")
        
        cuerpo = []
        if self.obtener_token_actual() and self.obtener_token_actual()[1] == "{":
            self.coincidir("DELIMITER")
            cuerpo = self.cuerpo()
            self.coincidir("DELIMITER")
        else:
            cuerpo.append(self.instruccion_unica())
            
        return NodoFor(inicializacion, condicion, incremento, cuerpo)
    
    def condicional_if(self):
        self.coincidir("KEYWORD")
        self.coincidir("DELIMITER")
        condicion = self.expresion()
        self.coincidir("DELIMITER")
        
        cuerpo = []
        if self.obtener_token_actual() and self.obtener_token_actual()[1] == "{":
            self.coincidir("DELIMITER")
            cuerpo = self.cuerpo()
            self.coincidir("DELIMITER")
        else:
            cuerpo.append(self.instruccion_unica())
            
        cuerpo_else = []
        if self.obtener_token_actual() and self.obtener_token_actual()[1] == "else":
            self.coincidir("KEYWORD")
            if self.obtener_token_actual() and self.obtener_token_actual()[1] == "{":
                self.coincidir("DELIMITER")
                cuerpo_else = self.cuerpo()
                self.coincidir("DELIMITER")
            else:
                cuerpo_else.append(self.instruccion_unica())
                
        return NodoIf(condicion, cuerpo, cuerpo_else)
    
    def condicional_else(self):
        self.coincidir("KEYWORD")
        
        cuerpo = []
        if self.obtener_token_actual() and self.obtener_token_actual()[1] == "{":
            self.coincidir("DELIMITER")
            cuerpo = self.cuerpo()
            self.coincidir("DELIMITER")
        else:
            cuerpo.append(self.instruccion_unica())
            
        return NodoElse(cuerpo)
    
    def imprimir(self):
        self.coincidir("KEYWORD")
        self.coincidir("DELIMITER", "(")
        
        token_actual = self.obtener_token_actual()
        if token_actual[0] == "STRING":
            token = self.coincidir("STRING")
            expresion = NodoString(token[1])
        else:
            expresion = self.expresion()

        self.coincidir("DELIMITER", ")")
        self.coincidir("DELIMITER", ";")
        
        return NodoPrint(expresion)
    