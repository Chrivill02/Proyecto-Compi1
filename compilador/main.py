
import json
import platform
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QGraphicsView, QGraphicsScene,
    QGraphicsPathItem, QGraphicsTextItem, QInputDialog, QMenu, QGraphicsLineItem,
    QDockWidget, QListWidget, QVBoxLayout, QWidget, QLabel, 
    QColorDialog, QMessageBox, QDialog, QFileDialog, QTextEdit, QPushButton
            
)
from PyQt5.QtCore import Qt, QPointF, QLineF
from PyQt5.QtGui import (
    QBrush, QPen, QColor, QPainterPath, QPainter, QPolygonF, QFont
)

from parsear import Parser
import analisis_lexico
import generate_ast_json
from analisis_semantico import AnalizadorSemantico
from generadorEnsamblador import GeneradorEnsamblador
import subprocess
import os

global codigo_c
codigo_c = "" 

class Connection(QGraphicsLineItem):
    def __init__(self, start_item, end_item, parent=None):
        super().__init__(parent)
        self.start_item = start_item
        self.end_item = end_item
        self.setPen(QPen(Qt.black, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setZValue(-1)
        self.update_position()
    
    def update_position(self):
        if self.start_item and self.end_item:
            start_center = self.start_item.pos() + QPointF(
                self.start_item.boundingRect().width() / 2,
                self.start_item.boundingRect().height() / 2
            )
            end_center = self.end_item.pos() + QPointF(
                self.end_item.boundingRect().width() / 2,
                self.end_item.boundingRect().height() / 2
            )
            self.setLine(QLineF(start_center, end_center))

class FlowchartItem(QGraphicsPathItem):
    def __init__(self, x, y, width, height, shape_type="process", text=""):
        super().__init__()
        self.shape_type = shape_type
        self._text = text  # Propiedad texto privada
        self.width = width
        self.height = height
        self.connections = []

        self.normal_brush = QBrush(QColor(200, 230, 255))
        self.selected_brush = QBrush(QColor(255, 200, 200))
        self.setBrush(self.normal_brush)
        self.setPen(QPen(Qt.black, 2))

        self.setFlag(QGraphicsPathItem.ItemIsMovable)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable)
        self.setFlag(QGraphicsPathItem.ItemSendsGeometryChanges)

        self.create_shape()
        self.setPos(x, y)

        # Crear el elemento de texto gráfico
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPlainText(text)  # Establecer el texto inicial
        self.center_text()
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.text_item.setDefaultTextColor(Qt.black)
        font = QFont()
        font.setPointSize(10)
        self.text_item.setFont(font)
        
        # Señal para actualizar el texto interno cuando cambia el editor
        self.text_item.document().contentsChanged.connect(self.update_text_from_item)

    @property
    def text(self):
        return self.text_item.toPlainText()
    
    @text.setter
    def text(self, value):
        self._text = value
        if self.text_item.toPlainText() != value:
            self.text_item.setPlainText(value)
        self.center_text()
    
    def update_text_from_item(self):
        self._text = self.text_item.toPlainText()
        print(f"Texto actualizado a: '{self._text}'")  # Para depuración
        self.center_text()

    def center_text(self):
        text_width = self.text_item.boundingRect().width()
        text_height = self.text_item.boundingRect().height()
        
        if self.shape_type == "decision":
            center_x = (self.width - text_width) / 2
            center_y = (self.height - text_height) / 2 - 5
        else:
            center_x = (self.width - text_width) / 2
            center_y = (self.height - text_height) / 2
        
        self.text_item.setPos(center_x, center_y)

    def create_shape(self):
        path = QPainterPath()
        if self.shape_type == "process":
            path.addRoundedRect(0, 0, self.width, self.height, 10, 10)
        elif self.shape_type == "decision":
            polygon = QPolygonF([
                QPointF(self.width/2, 0),
                QPointF(self.width, self.height/2),
                QPointF(self.width/2, self.height),
                QPointF(0, self.height/2)
            ])
            path.addPolygon(polygon)
        elif self.shape_type in ["terminator", "start", "end"]:
            path.addEllipse(0, 0, self.width, self.height)
        elif self.shape_type == "input":
            path.moveTo(self.width/4, 0)
            path.lineTo(3*self.width/4, 0)
            path.lineTo(self.width, self.height/2)
            path.lineTo(3*self.width/4, self.height)
            path.lineTo(self.width/4, self.height)
            path.lineTo(0, self.height/2)
            path.closeSubpath()
        self.setPath(path)

    def add_connection(self, connection):
        self.connections.append(connection)

    def remove_connection(self, connection):
        if connection in self.connections:
            self.connections.remove(connection)

    def itemChange(self, change, value):
        if change == QGraphicsPathItem.ItemSelectedChange:
            self.setBrush(self.selected_brush if value else self.normal_brush)
        elif change == QGraphicsPathItem.ItemPositionHasChanged:
            for connection in self.connections:
                connection.update_position()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        current_text = self.text_item.toPlainText()
        new_text, ok = QInputDialog.getText(None, 'Editar texto', 'Nuevo texto:', text=current_text)
        if ok:
            # Actualizar texto grafico
            self.text_item.setPlainText(new_text)
            print(f"Texto establecido a: '{new_text}' por doble clic")  # Depuracion

    def contextMenuEvent(self, event):
        menu = QMenu()
        color_action = menu.addAction("Cambiar color")
        edit_text_action = menu.addAction("Editar texto")
        delete_action = menu.addAction("Eliminar")
        action = menu.exec_(event.screenPos())

        if action == color_action:
            self.change_color()
        elif action == edit_text_action:
            self.mouseDoubleClickEvent(None)
        elif action == delete_action:
            self.delete_item()

    def change_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.normal_brush = QBrush(color)
            if not self.isSelected():
                self.setBrush(self.normal_brush)

    def delete_item(self):
        for connection in self.connections[:]:
            if connection.start_item == self:
                connection.end_item.remove_connection(connection)
            else:
                connection.start_item.remove_connection(connection)
            self.scene().removeItem(connection)
        self.scene().removeItem(self)
        
    def get_raw_text(self):
        """Get the raw text content without any HTML interpretation"""
        return self.text

class FlowchartView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 2000, 2000)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        self.connecting = False
        self.start_item = None
        self.temp_line = None

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setInteractive(True)

    def start_connection_mode(self):
        self.connecting = True
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.CrossCursor)

    def cancel_connection_mode(self):
        self.connecting = False
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setCursor(Qt.ArrowCursor)
        if self.temp_line:
            self.scene.removeItem(self.temp_line)
            self.temp_line = None
        self.start_item = None

    def mousePressEvent(self, event):
        if self.connecting and event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if isinstance(item, FlowchartItem):
                self.start_item = item
                self.temp_line = QGraphicsLineItem()
                self.temp_line.setPen(QPen(Qt.black, 2, Qt.DashLine))
                self.temp_line.setZValue(-1)
                self.scene.addItem(self.temp_line)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.connecting and self.start_item and self.temp_line:
            start_pos = self.start_item.pos() + QPointF(
                self.start_item.boundingRect().width() / 2,
                self.start_item.boundingRect().height() / 2
            )
            end_pos = self.mapToScene(event.pos())
            self.temp_line.setLine(QLineF(start_pos, end_pos))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.connecting and self.start_item and event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if isinstance(item, FlowchartItem) and item != self.start_item:
                connection = Connection(self.start_item, item)
                self.scene.addItem(connection)
                self.start_item.add_connection(connection)
                item.add_connection(connection)
            if self.temp_line:
                self.scene.removeItem(self.temp_line)
                self.temp_line = None
            self.start_item = None
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        zoom_factor = 1.2
        if event.angleDelta().y() < 0:
            zoom_factor = 1 / zoom_factor
        self.scale(zoom_factor, zoom_factor)

class FlowchartEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Editor de Diagramas de Flujo Profesional")
        self.setGeometry(100, 100, 1200, 800)
        self.view = FlowchartView()
        self.setCentralWidget(self.view)
        self.create_toolbar()
        self.create_side_panel()
        self.statusBar().showMessage("Listo")

    def create_toolbar(self):
        toolbar = self.addToolBar("Herramientas")
        toolbar.setMovable(False)

        select_action = QAction("Seleccionar (S)", self)
        select_action.setShortcut("S")
        select_action.triggered.connect(
            lambda: self.view.setDragMode(QGraphicsView.RubberBandDrag)
        )
        toolbar.addAction(select_action)

        shapes = [
            ("Inicio (N)", "start", "N"),
            ("Proceso (P)", "process", "P"),
            ("Decisión (D)", "decision", "D"),
            ("Fin (F)", "end", "F"),
            ("Entrada/Salida (I)", "input", "I"),
        ]

        for name, shape, shortcut in shapes:
            action = QAction(name, self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked, s=shape: self.create_item(s))
            toolbar.addAction(action)

        toolbar.addSeparator()

        connect_action = QAction("Conectar (C)", self)
        connect_action.setShortcut("C")
        connect_action.triggered.connect(self.view.start_connection_mode)
        toolbar.addAction(connect_action)

        cancel_connect_action = QAction("Cancelar Conexión (Esc)", self)
        cancel_connect_action.setShortcut("Esc")
        cancel_connect_action.triggered.connect(self.view.cancel_connection_mode)
        toolbar.addAction(cancel_connect_action)

        toolbar.addSeparator()

        generate_code_action = QAction("Generar Código C", self)
        generate_code_action.triggered.connect(self.generate_c_code)
        toolbar.addAction(generate_code_action)

        delete_action = QAction("Eliminar (Del)", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected)
        toolbar.addAction(delete_action)

        clear_action = QAction("Limpiar Todo", self)
        clear_action.triggered.connect(self.clear_scene)
        toolbar.addAction(clear_action)

        save_json_action = QAction("Guardar JSON", self)
        save_json_action.triggered.connect(self.save_ast_json)
        toolbar.addAction(save_json_action)

        load_json_action = QAction("Abrir JSON", self)
        load_json_action.triggered.connect(self.load_diagram_from_json)
        toolbar.addAction(load_json_action)
        
    def generate_c_code(self):
        try:
            items = [item for item in self.view.scene.items() if isinstance(item, FlowchartItem)]
            connections = [item for item in self.view.scene.items() if isinstance(item, Connection)]

            # Construir el grafo de conexiones
            graph = {}
            for item in items:
                graph[item] = []
            
            for conn in connections:
                if conn.start_item in graph and conn.end_item in graph:
                    graph[conn.start_item].append(conn.end_item)

            visited = set()
            code_lines = []
            indent_level = 0

            def add_line(text):
                code_lines.append("    " * indent_level + text)

            def generate_code(node):
                nonlocal indent_level
                if node in visited:
                    return
                visited.add(node)
                
                # Obtener texto
                raw_text = node.text_item.toPlainText().strip()
                print(f"Generando código para nodo: '{raw_text}'")
                
                if node.shape_type == "start":
                    add_line("int main() {")
                    indent_level += 1
                    # Procesar siguiente nodo
                    for next_node in graph.get(node, []):
                        generate_code(next_node)
                    indent_level -= 1
                    add_line("}")
                    return
                    
                elif node.shape_type == "end":
                    add_line("return 0;")
                    return
                    
                elif node.shape_type == "process":
                    processed_text = raw_text
                    if not processed_text.endswith(";"):
                        processed_text += ";"
                    add_line(processed_text)
                        
                elif node.shape_type == "input":
                    var_name = raw_text.split(" ")[0]
                    add_line(f'scanf("%d", &{var_name});')
                        
                elif node.shape_type == "decision":
                    condition = raw_text.replace("?", "").strip()
                    print(f"Decision condition: '{condition}'")
                    add_line(f"if ({condition}) {{")
                    indent_level += 1
                    # Procesar rama verdadera (primera conexión)
                    if graph.get(node, []) and len(graph[node]) > 0:
                        generate_code(graph[node][0])
                    indent_level -= 1
                    
                    # Procesar rama falsa (segunda conexión si existe)
                    if graph.get(node, []) and len(graph[node]) > 1:
                        add_line("} else {")
                        indent_level += 1
                        generate_code(graph[node][1])
                        indent_level -= 1
                    add_line("}")
                    return
                    
                # Procesar siguientes nodos (para nodos que no son decisiones)
                for next_node in graph.get(node, []):
                    generate_code(next_node)

            # Encontrar el nodo de inicio
            start_nodes = [item for item in items if item.shape_type == "start"]
            if start_nodes:
                generate_code(start_nodes[0])
            else:
                add_line("// No se encontró un nodo inicial (Inicio)")
                add_line("int main() {")
                add_line("    // Tu código aquí")
                add_line("    return 0;")
                add_line("}")

            # Generador de codigo
            code_text = "\n".join(code_lines)
            global codigo_c
            codigo_c = code_text
            
        
            dlg = QDialog(self)
            dlg.setWindowTitle("Código C Generado")
            dlg.setMinimumSize(600, 400)
            
            layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setPlainText(code_text)  # Plain para interpretar HTML
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            buttons_layout = QVBoxLayout()
            
            btn_copy = QPushButton("Copiar al Portapapeles")
            btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(code_text))
            buttons_layout.addWidget(btn_copy)
            
            btn_close = QPushButton("Ejecutar")
            btn_close.clicked.connect(dlg.accept)
            buttons_layout.addWidget(btn_close)
            
            layout.addLayout(buttons_layout)
            dlg.setLayout(layout)
            dlg.exec_()
            
            ######## Aquí comienza la logica de la implementación de el compilador ##########
            texto_prueba = ""
            texto_prueba = codigo_c

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
                btn_save_ast = QPushButton("Guardar AST")
                btn_save_ast.clicked.connect(lambda: self.save_ast_file(json_ast))
                buttons_layout.addWidget(btn_save_ast)
                
                def save_ast_file(self, ast_json):
                    filename, _ = QFileDialog.getSaveFileName(
                        self, "Guardar AST", "", "JSON Files (*.json)"
                    )
                    if filename:
                        with open(filename, 'w') as f:
                            f.write(ast_json)
                try:
                    self.compilar(ast)
                    self.execute_code()
                except:
                    print("Error al compilar o ejecutar el codigo")
                    
            except Exception as e:
                print("Error en el analisis sintactico:")
                print(e)

        ########## Aquí finaliza la logica del compilador #############
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Ocurrió un error al generar el código:\n{str(e)}\n\nDetalles:\n{tb}")

    def execute_code(self):
        try:
            if platform.system() == "Windows":
                subprocess.Popen(f'start cmd /k "salida.exe"', shell=True)
            else:
                print("Este método está diseñado para ejecutarse en Windows.")
                return False
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar: {e}")
            return False
    
    def compilar(self, ast, archivo_salida ="salida"):
        extensiones = [".asm", ".exe", ".obj"]
        for ext in extensiones:
            ruta = f"{archivo_salida}{ext}"
            if os.path.exists(ruta):
                try:
                    os.remove(ruta)
                    print(f"Archivo eliminado: {ruta}")
                except Exception as e:
                    print(f"No se pudo eliminar {ruta}: {e}")
            else:
                print(f"No existe archivo: {ruta}")
            
        generador = GeneradorEnsamblador()
        generador.generar(ast)
        with open('salida.asm', 'w') as f:
            f.write(generador.obtener_codigo())
            print(f"Archivo {archivo_salida}.asm generado correctamente")
        try:
            print("Ensamblado con NASM...")
            try:
                subprocess.run(["nasm", "-f", "win64", f"{archivo_salida}.asm", "-o", f"{archivo_salida}.obj"], check=True, capture_output=True, text=True)
                print("Ensamblado completo")
            except subprocess.CalledProcessError as e:
                print("Error al ejecutar NASM: ")
                print("STDOUT:", e.stdout)
                print("STDERR:", e.stderr)
                return False
            
            subprocess.run(["gcc", f"{archivo_salida}.obj", "-o", f"{archivo_salida}.exe"])
            print("Enlazado completo")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error durante la compilación (código {e.returncode}): {e}")
            if e.stdout:
                print("Salida estándar:", e.stdout.decode())
            if e.stderr:
                print("Error estándar:", e.stderr.decode())
            return False
        except FileNotFoundError:
            print("Error: NASM o link.exe no están instalados o no están en el PATH")
            print("Asegúrate de que:")
            print("1. NASM esté instalado y en el PATH")
            print("2. Visual Studio o las herramientas de compilación de C++ estén instaladas")
            return False
    
    def save_ast_json(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Diagrama", "", "JSON Files (*.json)"
        )
        if filename:
            data = {
                "nodes": [],
                "connections": []
            }
            
            # Guardar nodos
            items = [item for item in self.view.scene.items() 
                    if isinstance(item, FlowchartItem)]
            for item in items:
                data["nodes"].append({
                    "type": item.shape_type,
                    "x": item.x(),
                    "y": item.y(),
                    "text": item.text,
                    "color": item.brush().color().name(),
                    "width": item.width,
                    "height": item.height
                })
            
            # Guardar conexiones
            connections = [conn for conn in self.view.scene.items() 
                        if isinstance(conn, Connection)]
            for conn in connections:
                data["connections"].append({
                    "start": items.index(conn.start_item),
                    "end": items.index(conn.end_item)
                })
                
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)

    def load_diagram_from_json(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir Diagrama", "", "JSON Files (*.json)"
        )
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)
            
        self.view.scene.clear()
        
        # Cargar nodos
        items = []
        for node in data["nodes"]:
            item = FlowchartItem(
                node["x"],
                node["y"],
                node["width"],
                node["height"],
                node["type"],
                node["text"]
            )
            item.setBrush(QColor(node["color"]))
            self.view.scene.addItem(item)
            items.append(item)

        # Cargar conexiones
        for conn in data["connections"]:
            start = items[conn["start"]]
            end = items[conn["end"]]
            connection = Connection(start, end)
            self.view.scene.addItem(connection)
            start.add_connection(connection)
            end.add_connection(connection)
            
    def save_code_to_file(self, code_text):
        filename, _ = QDialog.getSaveFileName(self, "Guardar Código C", "", "Archivos C (*.c);;Todos los archivos (*)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(code_text)
                QMessageBox.information(self, "Éxito", f"Código guardado exitosamente en:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar el archivo:\n{str(e)}")

    def create_side_panel(self):
        dock = QDockWidget("Elementos", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        content = QWidget()
        layout = QVBoxLayout()
        self.elements_list = QListWidget()
        self.elements_list.itemDoubleClicked.connect(self.focus_element)
        layout.addWidget(QLabel("Elementos en el diagrama:"))
        layout.addWidget(self.elements_list)
        self.stats_label = QLabel("Total: 0 elementos, 0 conexiones")
        layout.addWidget(self.stats_label)
        content.setLayout(layout)
        dock.setWidget(content)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.view.scene.changed.connect(self.update_side_panel)

    def update_side_panel(self):
        self.elements_list.clear()
        items = [item for item in self.view.scene.items() if isinstance(item, FlowchartItem)]
        connections = [item for item in self.view.scene.items() if isinstance(item, Connection)]
        for item in items:
            self.elements_list.addItem(f"{item.shape_type}: {item.text}")
        self.stats_label.setText(f"Total: {len(items)} elementos, {len(connections)} conexiones")

    def focus_element(self, list_item):
        items = [item for item in self.view.scene.items() if isinstance(item, FlowchartItem)]
        index = self.elements_list.row(list_item)
        if 0 <= index < len(items):
            item = items[index]
            self.view.centerOn(item)
            item.setSelected(True)

    def create_item(self, shape_type):
        default_texts = {
            "start": "Inicio",
            "end": "Fin",
            "process": "Procesar",
            "decision": "¿Condición?",
            "input": "variable tipo"
        }
        item = FlowchartItem(100, 100, 120, 70, shape_type, default_texts.get(shape_type, shape_type.capitalize()))
        self.view.scene.addItem(item)
        item.setSelected(True)
        self.view.centerOn(item)
        self.statusBar().showMessage(f"Elemento {shape_type} creado", 2000)

    def delete_selected(self):
        for item in self.view.scene.selectedItems():
            if isinstance(item, FlowchartItem):
                item.delete_item()
            elif isinstance(item, Connection):
                if hasattr(item, 'start_item') and hasattr(item, 'end_item'):
                    item.start_item.remove_connection(item)
                    item.end_item.remove_connection(item)
                self.view.scene.removeItem(item)

    def clear_scene(self):
        self.view.scene.clear()
        self.statusBar().showMessage("Diagrama limpiado", 2000)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Salir',
            '¿Estás seguro de que quieres salir? Se perderán los cambios no guardados.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = FlowchartEditor()
    editor.show()
    sys.exit(app.exec_())