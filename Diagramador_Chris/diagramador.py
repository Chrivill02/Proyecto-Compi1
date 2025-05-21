import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QGraphicsView, QGraphicsScene,
    QGraphicsPathItem, QGraphicsTextItem, QInputDialog, QMenu, QGraphicsLineItem,
    QGraphicsPolygonItem, QDockWidget, QListWidget, QVBoxLayout, QWidget,
    QLabel, QColorDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QPointF, QLineF
from PyQt5.QtGui import (
    QBrush, QPen, QColor, QPainterPath, QPainter, QPolygonF, QFont
)

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
        self.text = text
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

        self.text_item = QGraphicsTextItem(text, self)
        self.center_text()
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.text_item.setDefaultTextColor(Qt.black)
        font = QFont()
        font.setPointSize(10)
        self.text_item.setFont(font)

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
        new_text, ok = QInputDialog.getText(None, 'Editar texto', 'Nuevo texto:', text=self.text)
        if ok:
            self.text = new_text
            self.text_item.setPlainText(new_text)
            self.center_text()

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
                
                text = node.text.strip()
                
                if node.shape_type == "start":
                    add_line("// Programa generado automáticamente")
                    add_line("#include <stdio.h>")
                    add_line("")
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
                    # Verificar si es una asignación simple
                    if "=" in text or text.endswith(";"):
                        add_line(text if text.endswith(";") else f"{text};")
                    else:
                        add_line(f"{text};")
                        
                elif node.shape_type == "input":
                    # Determinar el tipo de entrada basado en el texto
                    if " " in text:
                        var_name, var_type = text.split(" ", 1)
                        if var_type.lower() in ["int", "entero"]:
                            add_line(f'scanf("%d", &{var_name});')
                        elif var_type.lower() in ["float", "flotante"]:
                            add_line(f'scanf("%f", &{var_name});')
                        else:  # Por defecto string
                            add_line(f'scanf("%s", {var_name});')
                    else:
                        add_line(f'scanf("%s", &{text});')
                        
                elif node.shape_type == "decision":
                    condition = text
                    # Limpiar la condición si tiene signos de interrogación
                    condition = condition.replace("?", "").strip()
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

            # Mostrar el código en un cuadro de diálogo
            code_text = "\n".join(code_lines)
            
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Código C Generado")
            dlg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            dlg.setText(f"<pre>{code_text}</pre>")
            dlg.setStandardButtons(QMessageBox.Ok)
            dlg.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al generar el código:\n{str(e)}")

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