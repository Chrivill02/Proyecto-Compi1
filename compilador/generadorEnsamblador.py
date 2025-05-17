from nodes import *

class GeneradorEnsamblador:
    def __init__(self):
        self.codigo = []
        self.data_section = []
        self.string_literals = {}
        self.string_counter = 0
        self.current_function = None
        self.local_vars = {}
        self.param_offset = 0
        self.stack_offset = 8  # Comenzar desde 8 para evitar [rbp - 0]
        self.label_count = 0
        self.entry_point_added = False
        self.main_function_found = False
        
    def nueva_etiqueta(self):
        self.label_count += 1
        return f"ETIQUETA_{self.label_count}"
    
    def nuevo_string_literal(self, valor):
        if valor.startswith('"') and valor.endswith('"'):
            valor = valor[1:-1]
        
        for str_id, str_val in self.string_literals.items():
            if str_val == valor:
                return str_id
        
        str_id = f"string_{self.string_counter}"
        self.string_literals[str_id] = valor
        self.string_counter += 1
        return str_id
    
    def generar(self, nodo):
        if isinstance(nodo, NodoPrograma):
            self._gen_cabecera()
            for funcion in nodo.funciones:
                if funcion.nombre == 'main':
                    self.main_function_found = True
                self.generar(funcion)
            self._gen_fin()
            
        elif isinstance(nodo, NodoFuncion):
            self.current_function = nodo.nombre
            self._gen_funcion_prologo(nodo)
            for instr in nodo.cuerpo:
                self.generar(instr)
            self._gen_funcion_epilogo()
            
        elif isinstance(nodo, NodoAsignacion):
            if nodo.tipo:  
                self.local_vars[nodo.nombre] = self.stack_offset
                self.stack_offset += 8
            self.generar(nodo.expresion)
            self.codigo.append(f"    mov [rbp - {self.local_vars[nodo.nombre]}], rax")
            
        elif isinstance(nodo, NodoOperacion):
            if nodo.operador in ['==', '!=', '<', '>', '<=', '>=']:
                self._gen_comparacion(nodo)
                return
                
            self.generar(nodo.izquierda)
            self.codigo.append("    push rax")  
            self.generar(nodo.derecha)
            self.codigo.append("    mov rbx, rax")
            self.codigo.append("    pop rax")     
            
            if nodo.operador == '+':
                self.codigo.append("    add rax, rbx")  
            elif nodo.operador == '-':
                self.codigo.append("    sub rax, rbx")  
            elif nodo.operador == '*':
                self.codigo.append("    imul rax, rbx") 
            elif nodo.operador == '/':
                self.codigo.append("    mov rcx, rbx")  
                self.codigo.append("    cqo")           
                self.codigo.append("    idiv rcx")      
            elif nodo.operador == '%':
                self.codigo.append("    mov rcx, rbx")  
                self.codigo.append("    cqo")           
                self.codigo.append("    idiv rcx")      
                self.codigo.append("    mov rax, rdx")  
            elif nodo.operador == '&&':
                self.codigo.append("    and rax, rbx") 
            elif nodo.operador == '||':
                self.codigo.append("    or rax, rbx")   
                
        elif isinstance(nodo, NodoIdentificador):
            if nodo.nombre in self.local_vars:
                self.codigo.append(f"    mov rax, [rbp - {self.local_vars[nodo.nombre]}]")
            else:
                self.codigo.append(f"    mov rax, {nodo.nombre}")
                
        elif isinstance(nodo, NodoNumero):
            try:
                if isinstance(nodo.valor, str) and '.' in nodo.valor:
                    valor_entero = int(float(nodo.valor))
                    self.codigo.append(f"    mov rax, {valor_entero}")
                else:
                    self.codigo.append(f"    mov rax, {nodo.valor}")
            except ValueError:
                self.codigo.append(f"    mov rax, {nodo.valor}")
            
        elif isinstance(nodo, NodoString):
            str_id = self.nuevo_string_literal(nodo.valor)
            self.codigo.append(f"    lea rax, [{str_id}]")
            
        elif isinstance(nodo, NodoLlamadaFuncion):
            self._gen_llamada_funcion(nodo)
            
        elif isinstance(nodo, NodoPrint):
            self.generar(nodo.expresion)
            
            if isinstance(nodo.expresion, NodoString):
                self.codigo.append("    mov rdx, rax")         
                self.codigo.append("    lea rcx, [fmt_str_s]") 
            else:
                self.codigo.append("    mov rdx, rax")         
                self.codigo.append("    lea rcx, [fmt_str_d]") 
            self.codigo.append("    sub rsp, 32") 
            self.codigo.append("    call printf")
            self.codigo.append("    add rsp, 32")
            
        elif isinstance(nodo, NodoRetorno):
            self.generar(nodo.expresion)
            
        elif isinstance(nodo, NodoIf):
            self._gen_condicional(nodo)
            
        elif isinstance(nodo, NodoWhile):
            self._gen_ciclo_while(nodo)
            
        elif isinstance(nodo, NodoFor):
            self._gen_ciclo_for(nodo)
    
    def _gen_cabecera(self):
        self.data_section = [
            'section .data',
            'fmt_str_d db "%d", 0',
            'fmt_str_s db "%s", 0', 
            'fmt_newline db 10, 0',
        ]
        
    def _gen_fin(self):
        for str_id, str_val in self.string_literals.items():
            escaped_val = str_val.replace('\\n', '", 10, "')
            self.data_section.append(f'{str_id} db "{escaped_val}", 0')
            
        if not self.entry_point_added and self.main_function_found:
            self.codigo.extend([
                'global main',
                'main:',
                '    sub rsp, 40',
                '    call _main_impl',
                '    xor rcx, rcx',
                '    call ExitProcess',
                '    add rsp, 40'
            ])
            self.entry_point_added = True
        
    def _gen_funcion_prologo(self, funcion):
        func_name = '_main_impl' if funcion.nombre == 'main' else funcion.nombre
        
        self.codigo.append(f"global {func_name}")
        self.codigo.append(f"{func_name}:")
        self.codigo.append("    push rbp") 
        self.codigo.append("    mov rbp, rsp") 
        
        self.local_vars = {}
        self.stack_offset = 8  # Comenzar desde 8 para evitar [rbp - 0]
        
        for i, param in enumerate(funcion.parametros):
            if i < 4:
                self.local_vars[param.nombre] = self.stack_offset
                self.stack_offset += 8
            else:
                self.local_vars[param.nombre] = self.stack_offset
                self.stack_offset += 8
        
        if self.stack_offset < 16:
            stack_space = 16
        else:
            stack_space = ((self.stack_offset + 15) // 16) * 16
        
        self.codigo.append(f"    sub rsp, {stack_space}")
        
        for i, param in enumerate(funcion.parametros):
            if i < 4:
                reg = ['rcx', 'rdx', 'r8', 'r9'][i]
                self.codigo.append(f"    mov [rbp - {self.local_vars[param.nombre]}], {reg}")
            else:
                offset = 16 + (i-4)*8  
                self.codigo.append(f"    mov rax, [rbp + {offset}]")
                self.codigo.append(f"    mov [rbp - {self.local_vars[param.nombre]}], rax")
            
    def _gen_funcion_epilogo(self):
        self.codigo.append("    mov rsp, rbp")
        self.codigo.append("    pop rbp")
        self.codigo.append("    ret")
        
    def _gen_llamada_funcion(self, nodo):
        called_func = '_main_impl' if nodo.nombre == 'main' else nodo.nombre
        
        args_reversed = list(reversed(nodo.argumentos))
        
        if len(nodo.argumentos) > 4:
            stack_args = len(nodo.argumentos) - 4
            padding = (stack_args % 2) * 8 
            if padding > 0:
                self.codigo.append(f"    sub rsp, {padding}")
        
        for i, arg in enumerate(args_reversed):
            self.generar(arg)
            if i < 4:
                reg = ['rcx', 'rdx', 'r8', 'r9'][i]
                self.codigo.append(f"    mov {reg}, rax")
            else:
                self.codigo.append("    push rax")
        
        self.codigo.append("    sub rsp, 32")
        self.codigo.append(f"    call {called_func}")
        
        args_on_stack = max(0, len(nodo.argumentos) - 4) * 8
        total_to_add = 32 + args_on_stack
        
        if len(nodo.argumentos) > 4:
            stack_args = len(nodo.argumentos) - 4
            padding = (stack_args % 2) * 8
            total_to_add += padding
        
        if args_on_stack > 0:
            self.codigo.append(f"    add rsp, {total_to_add}")
        else:
            self.codigo.append("    add rsp, 32")
    
    def _gen_comparacion(self, nodo):
        self.generar(nodo.izquierda)
        self.codigo.append("    push rax")
        
        self.generar(nodo.derecha)
        self.codigo.append("    mov rbx, rax") 
        self.codigo.append("    pop rax")
        self.codigo.append("    cmp rax, rbx")
        
        etiq_verdadero = self.nueva_etiqueta()
        etiq_fin = self.nueva_etiqueta()
        
        if nodo.operador == "==":
            self.codigo.append(f"    je {etiq_verdadero}")
        elif nodo.operador == "!=":
            self.codigo.append(f"    jne {etiq_verdadero}")
        elif nodo.operador == "<":
            self.codigo.append(f"    jl {etiq_verdadero}")
        elif nodo.operador == ">":
            self.codigo.append(f"    jg {etiq_verdadero}")
        elif nodo.operador == "<=":
            self.codigo.append(f"    jle {etiq_verdadero}")
        elif nodo.operador == ">=":
            self.codigo.append(f"    jge {etiq_verdadero}")
        
        self.codigo.append("    mov rax, 0")
        self.codigo.append(f"    jmp {etiq_fin}")
        
        self.codigo.append(f"{etiq_verdadero}:")
        self.codigo.append("    mov rax, 1")
        
        self.codigo.append(f"{etiq_fin}:")
        
    def _gen_condicional(self, nodo):
        else_label = self.nueva_etiqueta()
        fin_label = self.nueva_etiqueta()
        
        self.generar(nodo.condicion)
        
        self.codigo.append("    test rax, rax")
        self.codigo.append(f"    jz {else_label}")
        
        for instr in nodo.cuerpo:
            self.generar(instr)
            
        if nodo.cuerpo_else:
            self.codigo.append(f"    jmp {fin_label}")
        
        self.codigo.append(f"{else_label}:")
        for instr in nodo.cuerpo_else:
            self.generar(instr)
        
        self.codigo.append(f"{fin_label}:")
        
    def _gen_ciclo_while(self, nodo):
        inicio_label = self.nueva_etiqueta()
        condicion_label = self.nueva_etiqueta()
        fin_label = self.nueva_etiqueta()
        
        self.codigo.append(f"    jmp {condicion_label}") 
        
        self.codigo.append(f"{inicio_label}:")
        for instr in nodo.cuerpo: 
            self.generar(instr)
        
        self.codigo.append(f"{condicion_label}:")
        self.generar(nodo.condicion)
        self.codigo.append("    test rax, rax")
        self.codigo.append(f"    jnz {inicio_label}") 
        
        self.codigo.append(f"{fin_label}:")
        
    def _gen_ciclo_for(self, nodo):
        inicio_label = self.nueva_etiqueta()
        condicion_label = self.nueva_etiqueta()
        incremento_label = self.nueva_etiqueta()
        fin_label = self.nueva_etiqueta()

        if nodo.inicializacion:
            self.generar(nodo.inicializacion)

        self.codigo.append(f"    jmp {condicion_label}")

        self.codigo.append(f"{inicio_label}:")
        for instr in nodo.cuerpo:
            self.generar(instr)
            
        self.codigo.append(f"{incremento_label}:")
        if nodo.incremento:
            if isinstance(nodo.incremento, NodoAsignacion):
                self.generar(nodo.incremento)
            else:
                self.generar(nodo.incremento)

        self.codigo.append(f"{condicion_label}:")
        if nodo.condicion:
            self.generar(nodo.condicion)
            self.codigo.append("    test rax, rax")
            self.codigo.append(f"    jnz {inicio_label}")
        else:
            self.codigo.append(f"    jmp {inicio_label}")

        self.codigo.append(f"{fin_label}:")
        
    def obtener_codigo(self):
        extern_section = [
            'section .text',
            'extern printf',
            'extern ExitProcess',
            'default rel'
        ]
        return '\n'.join(self.data_section + [''] + extern_section + [''] + self.codigo)
    