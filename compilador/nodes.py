class NodoAST:
    def to_dict(self):
        raise NotImplementedError("Debe implementarse en las subclases")
    
    def optimizacion(self):
        return self
    
    def traducir(self):
        raise NotImplementedError("Metodo traducir() no implementado en este nodo")
    
class NodoPrograma(NodoAST):
    def __init__(self, funciones):
        self.funciones = funciones
        
    def to_dict(self):
        return {
            "tipo": "programa",
            "funciones": [funcion.to_dict() for funcion in self.funciones]
        }
        
    def tiene_main(self):
        for funcion in self.funciones:
            if funcion.nombre == "main":
                return True
        return False
    
class NodoFuncion(NodoAST):
    def __init__(self, tipo, nombre, parametros, cuerpo):
        self.tipo = tipo
        self.nombre = nombre
        self.parametros = parametros
        self.cuerpo = cuerpo
        
    def traducir(self):
        params = ".".join(p.traducir() for p in self.parametros)
        cuerpo = "\n    ".join(c.traducir() for c in self.cuerpo)
        return f"def {self.nombre}({params}):\n    {cuerpo}"
    
    def to_dict(self):
        return {
            "tipo": "funcion",
            "retorno": self.tipo,
            "nombre": self.nombre,
            "parametros": [param.to_dict() for param in self.parametros],
            "cuerpo": [instr.to_dict() for instr in self.cuerpo]
            }
        
class NodoParametro(NodoAST):
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre
        
    def traducir(self):
        return self.nombre
    
    def to_dict(self):
        return {
            "tipo": "parametro",
            "tipo_dato": self.tipo,
            "nombre": self.nombre
        }
        
class NodoAsignacion(NodoAST):
    def __init__(self, tipo, nombre, expresion):
        self.tipo = tipo
        self.nombre = nombre
        self.expresion = expresion
        
    def traducir(self):
        return f"{self.nombre} = {self.expresion.traducir()}"
    
    def to_dict(self):
        return {
            "tipo": "asignacion",
            "tipo_dato": self.tipo,
            "nombre": self.nombre,
            "expresion": self.expresion.to_dict()
        }
        
class NodoOperacion(NodoAST):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha
        
    def to_dict(self):
        return {
            "tipo": "operacion",
            "operador": self.operador,
            "izquierda": self.izquierda.to_dict(),
            "derecha": self.derecha.to_dict()
        }
        
    def traducir(self):
        if self.operador == "+":
            return f"({self.izquierda.traducir()} + {self.derecha.traducir()})"
        elif self.operador =="-":
            return f"({self.izquierda.traducir()} - {self.derecha.traducir()})"
        elif self.operador == "*":
            return f"({self.izquierda.traducir()} * {self.derecha.traducir()})"
        elif self.operador == "/":
            return f"({self.izquierda.traducir()} / {self.derecha.traducir()})"

    def optimizacion(self):
        izquierda = self.izquierda.optimizacion()
        derecha = self.derecha.optimizacion()
        
        if isinstance(izquierda, self.NodoNumero) and isinstance(derecha, self.NodoNumero):
            if self.operador == "+":
                return self.NodoNumero(float(izquierda.valor) + float(derecha.valor))
            elif self.operador == "-":
                return self.NodoNumero(float(izquierda.valor) - float(derecha.valor))
            elif self.operador == "*":
                return self.NodoNumero(float(izquierda.valor) * float(derecha.valor))
            elif self.operador == "/" and float(derecha.valor) != 0:
                return self.NodoNumero(float(izquierda.valor) / float(derecha.valor))
            
        # Simplificacion algebraica
        if self.operador == "*" and isinstance(derecha, self.NodoNumero) and float(derecha.valor) == 1:
            return izquierda
        if self.operador =="*" and isinstance(derecha, self.NodoNumero) and float(derecha.valor) == 0:
            return self.NodoNumero(0)
        if self.operador == "*" and isinstance(izquierda, self.NodoNumero) and float(izquierda.valor) == 1:
            return derecha
        if self.operador == "*" and isinstance(izquierda, self.NodoNumero) and float(izquierda.valor) == 0:
            return self.NodoNumero(0)
        if self.operador == "+" and isinstance(derecha, self.NodoNumero) and float(derecha.valor) == 0:
            return izquierda
        if self.operador == "+" and isinstance(izquierda, self.NodoNumero) and float(izquierda.valor) == 0:
            return derecha
        if self.operador == "-" and isinstance(derecha, self.NodoNumero) and float(derecha.valor) == 0:
            return izquierda
        if self.operador == "-" and isinstance(izquierda, self.NodoNumero) and float(izquierda.valor) == 0:
            return self.NodoNumero(0) - derecha
        if self.operador == "/" and isinstance(derecha, self.NodoNumero) and float(derecha.valor) == 1:
            return izquierda
        if self.operador == "/" and isinstance(izquierda, self.NodoNumero) and float(izquierda.valor) == 0:
            return self.NodoNumero(0)
        if self.operador == "/" and isinstance(izquierda, self.NodoNumero) and float(izquierda.valor) == 1:
            return self.NodoNumero(1) / derecha
        if self.operador == "/" and isinstance(derecha, self.NodoNumero) and float(derecha.valor) == 1:
            return izquierda
        if self.operador == "/" and isinstance(derecha, self.NodoNumero) and float(derecha.valor) == 0:
            raise ZeroDivisionError("Division por cero")
        
        # Si no se puede optimizar más:
        return NodoOperacion(izquierda, self.operador, derecha)  # Retornamos la misma operacion

class NodoRetorno(NodoAST):
    def __init__(self, expresion):
        self.expresion = expresion
        
    def traducir(self):
        return f"return {self.expresion.traducir()}"
    
    def to_dict(self):
        return {
            "tipo": "retorno",
            "expresion": self.expresion.to_dict()
        }
        
class NodoIdentificador(NodoAST):
    def __init__(self, nombre):
        self.nombre = nombre
        
    def traducir(self):
        return self.nombre
    
    def optimizacion(self):
        return self
    
    def to_dict(self):
        return {
            "tipo": "identificador",
            "nombre": self.nombre
        }
        
class NodoNumero(NodoAST):
    def __init__(self, valor):
        self.valor = valor
        
    def traducir(self):
        return str(self.valor)
    
    def optimizacion(self):
        return self
    
    def to_dict(self):
        return {
            "tipo": "numero",
            "valor": self.valor
        }

class NodoString(NodoAST):
    def __init__(self, valor):
        self.valor = valor
        
    def traducir(self):
        return f'"{self.valor}"'
    
    def optimizacion(self):
        return self
    
    def to_dict(self):
        return {
            "tipo": "string",
            "valor": self.valor
        }

class NodoIf(NodoAST):
    def __init__(self, condicion, cuerpo, cuerpo_else=None):
        self.condicion = condicion
        self.cuerpo = cuerpo
        self.cuerpo_else = cuerpo_else if cuerpo_else else []
        
    def traducir(self):
        cuerpo = "\n    ".join(c.traducir() for c in self.cuerpo)
        if self.cuerpo_else:
            cuerpo_else = "\n    ".join(c.traducir() for c in self.cuerpo_else)
            return f"if {self.codicion.traducir()}:\n    {cuerpo}\nelse:\n    {cuerpo_else}"
        else:
            return f"if {self.codicion.traducir()}:\n    {cuerpo}"
        
    def optimizacion(self):
        condicion = self.condicion.optimizacion()
        
        cuerpo = [inst.optimizacion() for inst in self.cuerpo if inst is not None]
        cuerpo_else = [inst.optimizacion() for inst in self.cuerpo_else if inst is not None]
        
        if isinstance(condicion, NodoNumero):
            if float(condicion.valor) != 0:
                return cuerpo
            else:
                return cuerpo_else
        
        return NodoIf(condicion, cuerpo, cuerpo_else)
    
    def to_dict(self):
        return {
            "tipo": "if",
            "condicion": self.condicion.to_dict(),
            "cuerpo": [instr.to_dict() for instr in self.cuerpo],
            "else": [instr.to_dict() for instr in self.cuerpo_else]
        }
        
class NodoWhile(NodoAST):
    def __init__(self, condicion, cuerpo):
        self.condicion = condicion
        self.cuerpo = cuerpo
        
    def traducir(self):
        cuerpo = "\n    ".join(c.traducir() for c in self.cuerpo)
        return f"while {self.condicion.traducir()}:\n    {cuerpo}"
    
    def optimizacion(self):
        condicion = self.condicion.optimizacion()
        
        cuerpo = [inst.optimizacion() for inst in self.cuerpo if inst is not None]
        if isinstance(condicion, NodoNumero):
            if float(condicion.valor) != 0:
                return cuerpo
            else:
                return []
            
        return NodoWhile(condicion, cuerpo)
    
    def to_dict(self):
        return {
            "tipo": "while",
            "condicion": self.condicion.to_dict(),
            "cuerpo": [instr.to_dict() for instr in self.cuerpo]
        }
    
class NodoFor(NodoAST):
    def __init__(self, inicializacion, condicion, incremento, cuerpo):
        self.inicializacion = inicializacion
        self.condicion = condicion
        self.incremento = incremento
        self.cuerpo = cuerpo
        
    def traducir(self):
        inicializacion = self.inicializacion.traducir()
        condicion = self.condicion.traducir()
        incremento = self.incremento.traducir()
        
        cuerpo = "\n    ".join(c.traducir() for c in self.cuerpo)
        return f"for {inicializacion}; {condicion}; {incremento}:\n    {cuerpo}"
    
    def optimizacion(self):
        inicializacion = self.inicializacion.optimizacion()
        condicion = self.condicion.optimizacion()
        incremento = self.incremento.optimizacion()
        
        cuerpo = [inst.optimizacion() for inst in self.cuerpo if inst is not None]
        if isinstance(condicion, NodoNumero):
            if float(condicion.valor) != 0:
                return cuerpo
            else:
                return []
            
        return NodoFor(inicializacion, condicion, incremento, cuerpo)
    
    def to_dict(self):
        return {
            "tipo": "for",
            "incializacion": self.inicializacion.to_dict(),
            "condicion": self.condicion.to_dict(),
            "incremento": self.incremento.to_dict(),
            "cuerpo": [instr.to_dict() for instr in self.cuerpo]
        }
        
class NodoIncremento(NodoAST):
    def __init__(self, nombre, operador):
        self.nombre = nombre
        self.operador = operador
        
    def to_dict(self):
        return {
            "tipo": "incremento",
            "nombre": self.nombre,
            "operador": self.operador
        }
        
class NodoPrint(NodoAST):
    def __init__(self, expresion):
        self.expresion = expresion
        
    def traducir(self):
        return f'print("{self.expresion.traducir()}")'

    def to_dict(self):
        return {
            "tipo": "print",
            "expresion": self.expresion.to_dict()
        }

class NodoElse(NodoAST):
    def __init__(self, cuerpo):
        self.cuerpo = cuerpo

    def traducir(self):
        cuerpo = "\n    ".join(c.traducir() for c in self.cuerpo)
        return f"else:\n    {cuerpo}"
    def to_dict(self):
        return {
            "tipo": "else",
            "cuerpo": [instr.to_dict() for instr in self.cuerpo]
        }
        
class NodoLlamadaFuncion(NodoAST):
    def __init__(self, nombre, argumentos):
        self.nombre = nombre
        self.argumentos = argumentos
        
    def traducir(self):
        argumentos = ", ".join(a.traducir() for a in self.argumentos)
        return f"{self.nombre}({argumentos})"
    
    def to_dict(self):
        return {
            "tipo": "llamada_funcion",
            "nombre": self.nombre,
            "argumentos": [arg.to_dict() for arg in self.argumentos]
        }
        