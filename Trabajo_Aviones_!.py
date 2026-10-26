# PROYECTO: Transporte Aereo
# Algoritmos: Knapsack 0/1 y Dijkstra

import tkinter as tk
from tkinter import ttk, messagebox
from itertools import combinations

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

cajas = pd.read_csv("cajas.csv")
rutas = pd.read_csv("rutas.csv")

cajas["volumen_cm3"] = (
    cajas["alto_cm"]
    * cajas["ancho_cm"]
    * cajas["profundidad_cm"]
)

grafo = nx.Graph()

for _, fila in rutas.iterrows():
    grafo.add_edge(
        fila["origen"],
        fila["destino"],
        distancia=float(fila["distancia_km"]),
        tiempo=float(fila["tiempo_horas"])
    )

coordenadas = {}

for _, fila in cajas.iterrows():
    coordenadas[fila["pais_origen"]] = (
        float(fila["lat_origen"]),
        float(fila["lon_origen"])
    )

    coordenadas[fila["pais_destino"]] = (
        float(fila["lat_destino"]),
        float(fila["lon_destino"])
    )


# Comprobar que haya coordenadas para cada pais
for pais in grafo.nodes():
    if pais not in coordenadas:
        raise ValueError(
            f"No existen coordenadas registradas para {pais}"
        )


def knapsack_01(datos, capacidad_peso, capacidad_volumen):

    mejor_seleccion = []
    mejor_cantidad = 0
    mejor_peso = 0
    mejor_volumen = 0

    ids = datos["id_caja"].tolist()

    for cantidad in range(len(ids) + 1):
        for seleccion in combinations(ids, cantidad):

            seleccion_df = datos[
                datos["id_caja"].isin(seleccion)
            ]

            peso_total = seleccion_df["peso_kg"].sum()
            volumen_total = seleccion_df["volumen_cm3"].sum()

            if (
                peso_total <= capacidad_peso
                and volumen_total <= capacidad_volumen
            ):
                if cantidad > mejor_cantidad:
                    mejor_seleccion = list(seleccion)
                    mejor_cantidad = cantidad
                    mejor_peso = peso_total
                    mejor_volumen = volumen_total

    return {
        "ids": mejor_seleccion,
        "cantidad": mejor_cantidad,
        "peso_kg": mejor_peso,
        "volumen_cm3": mejor_volumen
    }

def buscar_ruta(origen, destino, criterio):

    if origen not in grafo or destino not in grafo:
        raise ValueError("El origen o destino no existe.")

    if criterio not in ("distancia", "tiempo"):
        raise ValueError("Criterio de busqueda no valido.")

    ruta = nx.dijkstra_path(
        grafo,
        source=origen,
        target=destino,
        weight=criterio
    )

    valor = nx.dijkstra_path_length(
        grafo,
        source=origen,
        target=destino,
        weight=criterio
    )

    return ruta, valor


def visualizar_ruta(ruta, criterio, valor):

    posiciones = {
        pais: (
            coordenadas[pais][1],
            coordenadas[pais][0]
        )
        for pais in grafo.nodes()
    }

    aristas_ruta = list(zip(ruta, ruta[1:]))

    plt.figure(figsize=(14, 9))

    # Todas las conexiones
    nx.draw_networkx_edges(
        grafo,
        posiciones,
        edge_color="lightgray",
        width=2
    )

    # Ruta seleccionada
    nx.draw_networkx_edges(
        grafo,
        posiciones,
        edgelist=aristas_ruta,
        edge_color="red",
        width=4
    )

    # Colores de los paises
    colores = []

    for pais in grafo.nodes():
        if pais == ruta[0]:
            colores.append("green")
        elif pais == ruta[-1]:
            colores.append("orange")
        elif pais in ruta:
            colores.append("yellow")
        else:
            colores.append("skyblue")

    nx.draw_networkx_nodes(
        grafo,
        posiciones,
        node_color=colores,
        node_size=2500
    )

    # Nombre y coordenadas
    etiquetas = {}

    for pais in grafo.nodes():
        latitud, longitud = coordenadas[pais]

        etiquetas[pais] = (
            f"{pais}\n"
            f"Lat: {latitud:.3f}\n"
            f"Lon: {longitud:.3f}"
        )

    nx.draw_networkx_labels(
        grafo,
        posiciones,
        labels=etiquetas,
        font_size=8
    )

    # Distancia y tiempo de cada conexion
    etiquetas_aristas = {
        (u, v): (
            f"{datos['distancia']:.0f} km\n"
            f"{datos['tiempo']:.1f} h"
        )
        for u, v, datos in grafo.edges(data=True)
    }

    nx.draw_networkx_edge_labels(
        grafo,
        posiciones,
        edge_labels=etiquetas_aristas,
        font_size=8
    )

    unidad = "km" if criterio == "distancia" else "horas"
    nombre_criterio = (
        "Menor distancia"
        if criterio == "distancia"
        else "Menor tiempo"
    )

    plt.title(
        f"TRANSTIME AEREO - {nombre_criterio}\n"
        f"{' -> '.join(ruta)}\n"
        f"Total: {valor:.1f} {unidad}"
    )

    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
def consultar_ruta_envio():
    try:
        # Obtener el ID de la caja seleccionada
        id_caja = int(selector_caja_envio.get())

        # Buscar la caja en el archivo cargado
        datos_caja = cajas[
            cajas["id_caja"] == id_caja
        ]

        if datos_caja.empty:
            messagebox.showerror(
                "Error",
                "No se encontró la caja seleccionada."
            )
            return

        caja = datos_caja.iloc[0]

        # Obtener origen y destino del envío
        origen = caja["pais_origen"]
        destino = caja["pais_destino"]

        # Obtener el criterio seleccionado
        criterio = selector_criterio_envio.get()

        # Calcular la ruta mediante Dijkstra
        ruta, valor = buscar_ruta(
            origen,
            destino,
            criterio
        )

        # Mostrar información del envío
        resultado_envio.config(
            text=(
                f"Caja: {id_caja}\n"
                f"Origen: {origen}\n"
                f"Destino: {destino}\n"
                f"Recorrido: {' → '.join(ruta)}\n"
                f"{'Distancia' if criterio == 'distancia' else 'Tiempo'} "
                f"total: {valor:g} "
                f"{'km' if criterio == 'distancia' else 'horas'}"
            )
        )

        # Dibujar el recorrido del avión
        visualizar_ruta(
            ruta,
            criterio,
            valor
        )

    except ValueError as error:
        messagebox.showerror(
            "Error de datos",
            f"Verifica la caja seleccionada y los datos.\n{error}"
        )

    except nx.NetworkXNoPath:
        messagebox.showwarning(
            "Sin ruta disponible",
            "No existe una ruta entre el origen y el destino."
        )

    except nx.NodeNotFound:
        messagebox.showwarning(
            "País no encontrado",
            "El origen o destino no está registrado en el grafo."
        )

    except Exception as error:
        messagebox.showerror(
            "Error",
            f"No se pudo calcular el envío:\n{error}"
        )

# 5. FUNCION PARA MOSTRAR RESULTADOS

def calcular_recorrido():

    origen = selector_origen.get()
    destino = selector_destino.get()
    criterio = selector_criterio.get()

    if origen == destino:
        messagebox.showwarning(
            "Seleccion invalida",
            "Selecciona un origen y un destino diferentes."
        )
        return

    try:
        ruta, valor = buscar_ruta(origen, destino, criterio)

        unidad = "km" if criterio == "distancia" else "horas"

        texto = (
            f"Origen: {origen}\n"
            f"Destino: {destino}\n"
            f"Ruta: {' -> '.join(ruta)}\n"
            f"Criterio: {criterio.capitalize()}\n"
            f"Total: {valor:.1f} {unidad}"
        )

        resultado_ruta.config(text=texto)

        visualizar_ruta(ruta, criterio, valor)

    except (nx.NetworkXNoPath, nx.NodeNotFound, ValueError) as error:
        messagebox.showerror("Error al calcular la ruta", str(error))


# 6. FUNCION PARA CALCULAR KNAPSACK

def calcular_carga():

    try:
        capacidad_peso = float(entrada_peso.get())
        capacidad_volumen = float(entrada_volumen.get())

        if capacidad_peso < 0 or capacidad_volumen < 0:
            raise ValueError(
                "Las capacidades no pueden ser negativas."
            )

        resultado = knapsack_01(
            cajas,
            capacidad_peso,
            capacidad_volumen
        )

        seleccionadas = cajas[
            cajas["id_caja"].isin(resultado["ids"])
        ]

        texto = (
            f"Cajas seleccionadas: {resultado['cantidad']}\n"
            f"IDs: {resultado['ids']}\n"
            f"Peso utilizado: {resultado['peso_kg']:.2f} kg\n"
            f"Volumen utilizado: {resultado['volumen_cm3']:.0f} cm³"
        )

        resultado_carga.config(text=texto)

        # Mostrar detalle en una ventana
        ventana_detalle = tk.Toplevel(ventana)
        ventana_detalle.title("Detalle de cajas seleccionadas")
        ventana_detalle.geometry("850x300")

        columnas = [
            "id_caja",
            "peso_kg",
            "volumen_cm3",
            "pais_origen",
            "pais_destino"
        ]

        tabla = ttk.Treeview(
            ventana_detalle,
            columns=columnas,
            show="headings"
        )

        for columna in columnas:
            tabla.heading(columna, text=columna)
            tabla.column(columna, width=145)

        for _, fila in seleccionadas[columnas].iterrows():
            tabla.insert(
                "",
                "end",
                values=tuple(fila[columna] for columna in columnas)
            )

        tabla.pack(fill="both", expand=True)

    except ValueError as error:
        messagebox.showerror(
            "Datos invalidos",
            f"Revisa las capacidades ingresadas.\n{error}"
        )

ventana = tk.Tk()
ventana.title("Transporte de Carga Aereo - Gestion de rutas y cajas")
ventana.geometry("700x720")

titulo = ttk.Label(
    ventana,
    text="Transporte de Carga Aereo",
    font=("Arial", 20, "bold")
)
titulo.pack(pady=15)

subtitulo = ttk.Label(
    ventana,
    text="Sistema de rutas aereas y seleccion de carga"
)
subtitulo.pack(pady=5)

# Seccion de rutas

marco_rutas = ttk.LabelFrame(
    ventana,
    text="Busqueda de rutas - Dijkstra",
    padding=15
)
marco_rutas.pack(fill="x", padx=20, pady=10)

paises = sorted(grafo.nodes())

ttk.Label(
    marco_rutas,
    text="Pais de origen:"
).grid(row=0, column=0, sticky="w", pady=5)

selector_origen = ttk.Combobox(
    marco_rutas,
    values=paises,
    state="readonly",
    width=25
)
selector_origen.grid(row=0, column=1, pady=5)
selector_origen.set(
    "Colombia" if "Colombia" in paises else paises[0]
)

ttk.Label(
    marco_rutas,
    text="Pais de destino:"
).grid(row=1, column=0, sticky="w", pady=5)

selector_destino = ttk.Combobox(
    marco_rutas,
    values=paises,
    state="readonly",
    width=25
)
selector_destino.grid(row=1, column=1, pady=5)
selector_destino.set(
    "Alemania" if "Alemania" in paises else paises[-1]
)

ttk.Label(
    marco_rutas,
    text="Criterio:"
).grid(row=2, column=0, sticky="w", pady=5)

selector_criterio = ttk.Combobox(
    marco_rutas,
    values=["distancia", "tiempo"],
    state="readonly",
    width=25
)
selector_criterio.grid(row=2, column=1, pady=5)
selector_criterio.set("distancia")

boton_ruta = ttk.Button(
    marco_rutas,
    text="Calcular y visualizar ruta",
    command=calcular_recorrido
)
boton_ruta.grid(
    row=3, column=0, columnspan=2, pady=12
)

resultado_ruta = ttk.Label(
    marco_rutas,
    text="Selecciona los paises para comenzar.",
    justify="left",
    wraplength=550
)
resultado_ruta.grid(
    row=4, column=0, columnspan=2, sticky="w", pady=5
)

# Seccion de carga

marco_carga = ttk.LabelFrame(
    ventana,
    text="Seleccion de carga - Knapsack 0/1",
    padding=15
)
marco_carga.pack(fill="x", padx=20, pady=10)

ttk.Label(
    marco_carga,
    text="Capacidad maxima de peso (kg):"
).grid(row=0, column=0, sticky="w", pady=5)

entrada_peso = ttk.Entry(marco_carga, width=20)
entrada_peso.grid(row=0, column=1, pady=5)
entrada_peso.insert(0, "50")

ttk.Label(
    marco_carga,
    text="Capacidad maxima de volumen (cm³):"
).grid(row=1, column=0, sticky="w", pady=5)

entrada_volumen = ttk.Entry(marco_carga, width=20)
entrada_volumen.grid(row=1, column=1, pady=5)
entrada_volumen.insert(0, "250000")

boton_carga = ttk.Button(
    marco_carga,
    text="Seleccionar cajas",
    command=calcular_carga
)
boton_carga.grid(
    row=2, column=0, columnspan=2, pady=12
)

resultado_carga = ttk.Label(
    marco_carga,
    text="Ingresa las capacidades para seleccionar las cajas.",
    justify="left",
    wraplength=550
)
resultado_carga.grid(
    row=3, column=0, columnspan=2, sticky="w", pady=5
)

# Sección para visualizar la ruta de un envío
marco_envio = ttk.LabelFrame(
    ventana,
    text="Visualizar ruta de un envío"
)
marco_envio.pack(
    fill="x",
    padx=10,
    pady=10
)

# Selección de caja
ttk.Label(
    marco_envio,
    text="Seleccionar caja:"
).grid(row=0, column=0, padx=5, pady=5)

selector_caja_envio = ttk.Combobox(
    marco_envio,
    values=cajas["id_caja"].tolist(),
    state="readonly",
    width=15
)
selector_caja_envio.grid(
    row=0,
    column=1,
    padx=5,
    pady=5
)

if not cajas.empty:
    selector_caja_envio.current(0)

# Criterio para calcular la ruta
ttk.Label(
    marco_envio,
    text="Optimizar por:"
).grid(row=1, column=0, padx=5, pady=5)

selector_criterio_envio = ttk.Combobox(
    marco_envio,
    values=["distancia", "tiempo"],
    state="readonly",
    width=15
)
selector_criterio_envio.grid(
    row=1,
    column=1,
    padx=5,
    pady=5
)
selector_criterio_envio.current(0)

# Botón para calcular y visualizar
ttk.Button(
    marco_envio,
    text="Visualizar recorrido del avión",
    command=consultar_ruta_envio
).grid(
    row=2,
    column=0,
    columnspan=2,
    padx=5,
    pady=10
)

# Resultado del envío
resultado_envio = ttk.Label(
    marco_envio,
    text="Selecciona una caja para consultar su recorrido.",
    justify="left"
)
resultado_envio.grid(
    row=3,
    column=0,
    columnspan=2,
    padx=5,
    pady=5,
    sticky="w"
)

# 8. INICIAR LA APLICACION

ventana.mainloop()
