from nodes import NodoPrograma, NodoFuncion, NodoParametro
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
        
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != "}":
            pass