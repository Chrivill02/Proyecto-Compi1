from nodes import NodoPrograma, NodoFuncion, NodoParametro, NodoAsignacion, NodoOperacion, NodoRetorno, NodoIdentificador, NodoNumero, NodoString, NodoIf, NodoWhile, NodoFor, NodoIncremento, NodoPrint, NodoElse, NodoLlamadaFuncion
import json


def ast_a_json(ast):
    return json.dumps(ast.to_dict(), indent=4)

def imprimir_ast(nodo, nivel=0):
    prefijo = "  " * nivel
    
    if isinstance(nodo, NodoPrograma):
        print(f"{prefijo}Programa:")
        for funcion in nodo.funciones:
            imprimir_ast(funcion, nivel + 1)
        print(f'{prefijo}Tiene funcion main?: {"Si" if nodo.tiene_main() else "No"}')

    elif isinstance(nodo, NodoFuncion):
        print(f"{prefijo}Funcion: {nodo.nombre} (Tipo de retorno: {nodo.tipo})")
        print(f"{prefijo}Parametros:")
        for param in nodo.parametros:
            imprimir_ast(param, nivel + 1)
        print(f"{prefijo}Cuerpo:")
        for instr in nodo.cuerpo:
            imprimir_ast(instr, nivel + 1)
            
    elif isinstance(nodo, NodoParametro):
        print(f"{prefijo}Parametro: {nodo.nombre} (Tipo: {nodo.tipo})")
        
    elif isinstance(nodo, NodoAsignacion):
        tipo_str = f"(Tipo: {nodo.tipo})" if nodo.tipo else ""
        print(f"{prefijo}Asignacion: {nodo.nombre} {tipo_str}")
        print(f"{prefijo} Valor:")
        imprimir_ast(nodo.expresion, nivel + 2)
    
    elif isinstance(nodo, NodoOperacion):
        print(f"{prefijo}Operacion: {nodo.operador}")
        print(f"{prefijo} Operando izquierdo:")
        imprimir_ast(nodo.izquierda, nivel + 2)
        print(f"{prefijo} Operando derecho:")
        imprimir_ast(nodo.derecha, nivel + 2)
        
    elif isinstance(nodo, NodoRetorno):
        print(f"{prefijo}Retorno:")
        imprimir_ast(nodo.expreison, nivel + 1)
        
    elif isinstance(nodo, NodoIdentificador):
        print(f"{prefijo}Identificador: {nodo.nombre}")
    
    elif isinstance(nodo, NodoNumero):
        print(f"{prefijo}Numero: {nodo.valor}")
    
    elif isinstance(nodo, NodoString):
        print(f"{prefijo}Cadena: {nodo.valor}")
    
    elif isinstance(nodo, NodoIf):
        print(f"{prefijo}If:")
        print(f"{prefijo} Condicion:")
        imprimir_ast(nodo.condicion, nivel + 2)
        print(f"{prefijo} Cuerpo:")
        for instr in nodo.cuerpo:
            imprimir_ast(instr, nivel + 2)
    
    elif isinstance(nodo, NodoFor):
        print(f"{prefijo}For:")
        print(f"{prefijo} Inicializacion:")
        imprimir_ast(nodo.inicializacion, nivel + 2)
        print(f"{prefijo} Condicion:")
        imprimir_ast(nodo.condicion, nivel + 2)
        print(f"{prefijo} Incremento:")
        imprimir_ast(nodo.incremento, nivel + 2)
        print(f"{prefijo} Cuerpo:")
        for instr in nodo.cuerpo:
            imprimir_ast(instr, nivel + 2)
    
    elif isinstance(nodo, NodoIncremento):
        pass
    
    elif isinstance(nodo, NodoWhile):
        pass
    
    elif isinstance(nodo, NodoPrint):
        pass
    
    elif isinstance(nodo, NodoElse):
        pass
    
    elif isinstance(nodo, NodoLlamadaFuncion):
        pass
    
    else:
        print(f"{prefijo}Nodo desconocido: {type(nodo)}")