import tkinter as tk
from tkinter import ttk, messagebox
import simpy
import random

# =============================================================================
# LOGICA DE SIMULACION (BACKEND)
# =============================================================================

class Jugador:
    def __init__(self, env, nombre, edad, goles, asistencias, pases, distancia):
        self.env = env
        self.nombre = nombre
        self.edad_inicial = edad
        self.edad_actual = edad
        
        # Estadisticas actuales (estado inicial)
        self.stats = {
            "goles": goles,
            "asistencias": asistencias,
            "pases": pases,        # Porcentaje 0-100
            "distancia": distancia # Km
        }
        
        # Historico para analisis posterior (opcional)
        self.historial = []
        
        # Iniciar el proceso de evolucion en el entorno SimPy
        self.action = env.process(self.evolucionar())

    def evolucionar(self):
        """Proceso que simula el paso del tiempo y la evolucion de estadisticas."""
        while True:
            # Registrar estado actual antes de cambiar
            self.historial.append(self.stats.copy())
            
            # Esperar 1 unidad de tiempo (asumimos 1 mes)
            yield self.env.timeout(1)
            
            self.edad_actual += 1/12  # Sumar un mes a la edad
            
            # --- MOTOR DE SIMULACION ESTADISTICA ---
            # Factor de crecimiento basado en la edad (Curva de rendimiento)
            # Jugadores < 24 crecen rapido, 24-29 pico, > 30 declive
            if self.edad_actual < 24:
                factor_desarrollo = random.uniform(1.001, 1.015) # Crecimiento positivo fuerte
            elif 24 <= self.edad_actual <= 29:
                factor_desarrollo = random.uniform(0.995, 1.005) # Estabilidad (pico)
            else:
                factor_desarrollo = random.uniform(0.980, 1.000) # Declive fisico
            
            # Ruido aleatorio (lesiones leves, racha, moral)
            ruido_tecnico = random.normalvariate(0, 0.02) # Variacion en tecnica
            ruido_fisico = random.normalvariate(0, 0.05)  # Variacion en fisico (mas volatil)

            # Aplicar evolucion a cada metrica
            
            # 1. Goles y Asistencias (Tecnica + Tactica)
            self.stats["goles"] *= (factor_desarrollo + ruido_tecnico)
            self.stats["asistencias"] *= (factor_desarrollo + ruido_tecnico)
            
            # 2. Pases (Mental + Tecnica) - Topado a 100%
            self.stats["pases"] += random.uniform(-1, 1.5) if self.edad_actual < 28 else random.uniform(-1.5, 0.5)
            self.stats["pases"] = max(0, min(100, self.stats["pases"])) # Clamp 0-100
            
            # 3. Distancia (Fisico puro) - Cae mas rapido con la edad
            factor_fisico = factor_desarrollo if self.edad_actual < 28 else (factor_desarrollo - 0.005)
            self.stats["distancia"] *= (factor_fisico + (ruido_fisico * 0.1))

    def obtener_puntaje_general(self):
        """Calcula un rating global ponderado para definir al 'Mejor Prospecto'."""
        score = (
            (self.stats["goles"] * 40) +       # Goles valen mucho
            (self.stats["asistencias"] * 30) + # Asistencias valen
            (self.stats["pases"] * 0.5) +      # % de pase
            (self.stats["distancia"] * 3)      # Km recorridos
        )
        # Penalizacion por edad para fichajes a largo plazo
        if self.edad_actual > 30:
            score *= 0.9
            
        return score

# =============================================================================
# INTERFAZ GRAFICA (FRONTEND)
# =============================================================================

class ScoutingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Talento Deportivo con SimPy")
        self.root.geometry("900x700")
        
        self.jugadores_data = [] # Lista temporal de diccionarios para la GUI
        
        self._crear_interfaz()

    def _crear_interfaz(self):
        # --- Marco de Entrada de Datos ---
        frame_input = tk.LabelFrame(self.root, text="Agregar Nuevo Jugador", padx=10, pady=10)
        frame_input.pack(fill="x", padx=10, pady=5)

        # Entradas
        tk.Label(frame_input, text="Nombre:").grid(row=0, column=0)
        self.entry_nombre = tk.Entry(frame_input)
        self.entry_nombre.grid(row=0, column=1)

        tk.Label(frame_input, text="Edad:").grid(row=0, column=2)
        self.entry_edad = tk.Entry(frame_input, width=5)
        self.entry_edad.grid(row=0, column=3)

        tk.Label(frame_input, text="Goles/90min:").grid(row=0, column=4)
        self.entry_goles = tk.Entry(frame_input, width=5)
        self.entry_goles.grid(row=0, column=5)

        tk.Label(frame_input, text="Asist./90min:").grid(row=1, column=0)
        self.entry_asist = tk.Entry(frame_input, width=5)
        self.entry_asist.grid(row=1, column=1)

        tk.Label(frame_input, text="% Pase (0-100):").grid(row=1, column=2)
        self.entry_pase = tk.Entry(frame_input, width=5)
        self.entry_pase.grid(row=1, column=3)

        tk.Label(frame_input, text="Distancia (km):").grid(row=1, column=4)
        self.entry_dist = tk.Entry(frame_input, width=5)
        self.entry_dist.grid(row=1, column=5)

        # --- BOTON DE AGREGAR ---
        btn_agregar = tk.Button(frame_input, text="Anadir a Lista", command=self.agregar_jugador, bg="#4CAF50", fg="white")
        btn_agregar.grid(row=2, columnspan=6, pady=10, sticky="we")

        # --- Tabla de Jugadores Cargados ---
        frame_lista = tk.LabelFrame(self.root, text="Jugadores en Analisis", padx=10, pady=10)
        frame_lista.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("nombre", "edad", "goles", "asist", "pase", "dist")
        self.tree = ttk.Treeview(frame_lista, columns=columns, show="headings", height=5)
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("edad", text="Edad")
        self.tree.heading("goles", text="Goles")
        self.tree.heading("asist", text="Asistencias")
        self.tree.heading("pase", text="% Pase")
        self.tree.heading("dist", text="Distancia")
        self.tree.pack(fill="both", expand=True)

        # --- Configuracion de Simulacion ---
        frame_sim = tk.Frame(self.root, pady=10)
        frame_sim.pack(fill="x", padx=10)

        tk.Label(frame_sim, text="Tiempo a simular (meses):", font=("Arial", 10, "bold")).pack(side="left")
        self.entry_tiempo = tk.Entry(frame_sim, width=10)
        self.entry_tiempo.insert(0, "12") # Default 1 año
        self.entry_tiempo.pack(side="left", padx=5)

        btn_simular = tk.Button(frame_sim, text="EJECUTAR SIMULACION TEMPORAL", command=self.ejecutar_simulacion, bg="#2196F3", fg="white", font=("Arial", 11, "bold"))
        btn_simular.pack(side="left", padx=20)
        
        btn_limpiar_todo = tk.Button(frame_sim, text="Limpiar Lista Completa", command=self.limpiar_datos, bg="#f44336", fg="white")
        btn_limpiar_todo.pack(side="right")

        # --- Resultados ---
        frame_res = tk.LabelFrame(self.root, text="Resultados del Scouting (Prediccion)", padx=10, pady=10)
        frame_res.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.text_resultados = tk.Text(frame_res, height=12, font=("Consolas", 10))
        self.text_resultados.pack(fill="both", expand=True)

    def limpiar_entradas(self):
        """Borra solo el texto de los cuadros de entrada."""
        self.entry_nombre.delete(0, 'end')
        self.entry_edad.delete(0, 'end')
        self.entry_goles.delete(0, 'end')
        self.entry_asist.delete(0, 'end')
        self.entry_pase.delete(0, 'end')
        self.entry_dist.delete(0, 'end')
        # Pone el cursor en el nombre para escribir rapido de nuevo
        self.entry_nombre.focus()

    def agregar_jugador(self):
        try:
            nombre = self.entry_nombre.get()
            if not nombre: raise ValueError("Falta el nombre")
            
            data = {
                "nombre": nombre,
                "edad": float(self.entry_edad.get()),
                "goles": float(self.entry_goles.get()),
                "asistencias": float(self.entry_asist.get()),
                "pases": float(self.entry_pase.get()),
                "distancia": float(self.entry_dist.get())
            }
            self.jugadores_data.append(data)
            
            # Actualizar tabla visual
            self.tree.insert("", "end", values=(data['nombre'], data['edad'], data['goles'], data['asistencias'], data['pases'], data['distancia']))
            
            # Limpiar entradas automaticamente despues de agregar
            self.limpiar_entradas()
            
        except ValueError:
            messagebox.showerror("Error", "Por favor ingresa valores numericos validos en las estadisticas.")

    def limpiar_datos(self):
        """Borra la lista de jugadores y los resultados."""
        self.jugadores_data = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.text_resultados.delete(1.0, tk.END)

    def ejecutar_simulacion(self):
        if not self.jugadores_data:
            messagebox.showwarning("Atencion", "No hay jugadores para analizar.")
            return

        try:
            tiempo_simulacion = int(self.entry_tiempo.get())
        except ValueError:
            messagebox.showerror("Error", "El tiempo debe ser un numero entero (meses).")
            return

        # 1. Configurar entorno SimPy
        env = simpy.Environment()
        objetos_jugadores = []

        # 2. Instanciar procesos de jugadores
        for data in self.jugadores_data:
            j = Jugador(
                env, 
                data['nombre'], 
                data['edad'], 
                data['goles'], 
                data['asistencias'], 
                data['pases'], 
                data['distancia']
            )
            objetos_jugadores.append(j)

        # 3. Correr Simulacion
        env.run(until=tiempo_simulacion)

        # 4. Analizar Resultados
        self.mostrar_analisis(objetos_jugadores, tiempo_simulacion)

    def mostrar_analisis(self, jugadores, meses):
        self.text_resultados.delete(1.0, tk.END)
        
        header = f"--- REPORTE DE SCOUTING --- (Proyeccion a {meses} meses)\n"
        header += "Nota: Basado en simulacion estocastica de crecimiento/declive.\n\n"
        self.text_resultados.insert(tk.END, header)

        # Buscar los mejores en cada categoria
        mejor_goleador = max(jugadores, key=lambda x: x.stats['goles'])
        mejor_asistidor = max(jugadores, key=lambda x: x.stats['asistencias'])
        mejor_pasador = max(jugadores, key=lambda x: x.stats['pases'])
        mejor_fisico = max(jugadores, key=lambda x: x.stats['distancia'])
        mejor_prospecto = max(jugadores, key=lambda x: x.obtener_puntaje_general())

        res = ""
        res += f"SI BUSCAS GOLES: Ficha a {mejor_goleador.nombre}\n"
        res += f"   - Proyeccion: {mejor_goleador.stats['goles']:.2f} goles/90min (Edad futura: {mejor_goleador.edad_actual:.1f})\n\n"

        res += f"SI BUSCAS ASISTENCIAS: Ficha a {mejor_asistidor.nombre}\n"
        res += f"   - Proyeccion: {mejor_asistidor.stats['asistencias']:.2f} asist/90min\n\n"

        res += f"SI BUSCAS POSESION (PASES): Ficha a {mejor_pasador.nombre}\n"
        res += f"   - Proyeccion: {mejor_pasador.stats['pases']:.1f}% de efectividad\n\n"

        res += f"SI BUSCAS INTENSIDAD (FISICO): Ficha a {mejor_fisico.nombre}\n"
        res += f"   - Proyeccion: {mejor_fisico.stats['distancia']:.2f} km/partido\n\n"

        res += f"MEJOR PROSPECTO GENERAL (Balance Calidad/Edad): {mejor_prospecto.nombre}\n"
        res += f"   - Este jugador ofrece el mejor retorno de inversion basado en su curva de desarrollo.\n"
        
        res += "\n" + "="*60 + "\nDETALLE FINAL DE TODOS LOS JUGADORES:\n"
        
        for j in jugadores:
            res += f"> {j.nombre} ({j.edad_actual:.1f} anos): G:{j.stats['goles']:.2f} | A:{j.stats['asistencias']:.2f} | P:{j.stats['pases']:.1f}% | D:{j.stats['distancia']:.2f}km\n"

        self.text_resultados.insert(tk.END, res)

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = ScoutingApp(root)
    root.mainloop()