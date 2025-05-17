from parsear import Parser
import analisis_lexico
import generate_ast_json
from analisis_semantico import AnalizadorSemantico
from generadorEnsamblador import GeneradorEnsamblador

# Ejemplo de uso con múltiples funciones
texto_prueba = """
int main() {
    for (int i = 1; i <= 5; i++) {
        print(i);
    }

    return 0;
}
"""

# Analisis lexico
tokens = analisis_lexico.identificar(texto_prueba)
print("tokens encontrados:")
for i in tokens:
    print(i)
print("\n")

# Analisis sintactico y contruccion del AST
try:
    parser = Parser(tokens)
    ast = parser.parsear()
    print("Analisis sintactico exitoso")
    # Imprimir el AST (cuando este completo) en esta linea
    analizador = AnalizadorSemantico()
    analizador.analizar(ast)
    print("Analisis semantico exitoso")
    # Mostrar tabla de simbolos (variable y funciones) en esta linea
    json_ast = generate_ast_json.ast_a_json(ast)
    print("\n========= AST en formato JSON =========")
    print(json_ast)
    generador = GeneradorEnsamblador()
    generador.generar(ast)
    with open('salida.asm', 'w') as f:
        f.write(generador.obtener_codigo())
    
except Exception as e:
    print("Error en el analisis sintactico:")
    print(e)