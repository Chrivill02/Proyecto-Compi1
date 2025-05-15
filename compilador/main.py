from parsear import Parser
import analisis_lexico
import generate_ast_json


# Ejemplo de uso con múltiples funciones
texto_prueba = """
int suma(int a, int b) {
    return a + b;
}

int multiplica(int a, int b) {
    return a * b;
}

int main() {
    int resultado = 0;
    int x = 5;
    int y = 10;
    
    resultado = suma(x, y);
    print(resultado);
    
    resultado = multiplica(x, y);
    print(resultado);
    
    return 0;
}
"""

# Analisis lexico
tokens = analisis_lexico.identificar(texto_prueba)
print("tokens encontrados:")
for i in tokens:
    print(i)

# Analisis sintactico y contruccion del AST
try:
    parser = Parser(tokens)
    ast = parser.parsear()
    print("Analisis sintactico exitoso")
    json_ast = generate_ast_json.ast_a_json(ast)
    print("\n========= AST en formato JSON =========")
    print(json_ast)
    
except Exception as e:
    print("Error en el analisis sintactico:")
    print(e)
    
