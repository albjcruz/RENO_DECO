import os
import csv
import requests
from conf import config
from struct import unpack_from
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
requests.packages.urllib3.disable_warnings()
 
inicio = 0
tiempo_inicial = 0
#lista para almacenar los datos de los inversores (1A, 1B, 2B, 1C)
valores_inversores = [[], [], [], []]

def verificar_inversor(numero_serial):
    if numero_serial == "140B7018B220003":
        return 0
    elif numero_serial == "140B7018B220005":
        return 1
    elif numero_serial == "140B7018B220001":
        return 2
    elif numero_serial == "140B7018B220002":
        return 3
    else:
        return None

def verificar_lista(lista_inversores):
    if len(lista_inversores) == 4:
        for lista_interna in lista_inversores:
            if len(lista_interna) < 1:
                return False
        return True
    else:
        return False

def parse_inverter_message(message):
    return {
        "numeroSerial":              message[32:48].decode("ascii").rstrip(),
        "voltajeDC":                 0.1 * unpack_from("<H", message, 50)[0],
        "corrienteDC":               0.1 * unpack_from("<H", message, 54)[0],
        "corrienteGrid":             round(0.1 * unpack_from("<H", message, 62)[0], 2),
        "voltajeGrid":               0.1 * unpack_from("<H", message, 68)[0],
        "consumoDiario":             0.01 * unpack_from("<H", message, 76)[0],
        "potenciaInstantanea":       float(unpack_from("<I", message, 116)[0]),
        "consumoMensualActual":      float(unpack_from("<I", message, 120)[0]),
        "consumoMensualAnterior":    float(unpack_from("<I", message, 124)[0]),
        "consumoAyer":               round(0.1 * unpack_from("<H", message, 128)[0], 2),
        "potenciaAparente":          float(unpack_from("<I", message, 142)[0]),
    }

def procesar_lista(lista_diccionarios):
    if lista_diccionarios:
        resultado = {"numeroSerial": lista_diccionarios[0]["numeroSerial"]}
        valores_a_promediar = ["voltajeDC", "corrienteDC", "corrienteGrid", "voltajeGrid", "potenciaInstantanea", "potenciaAparente"]
        valores_a_maximo = ["consumoDiario", "consumoMensualActual", "consumoMensualAnterior", "consumoAyer"]

        for clave in valores_a_promediar:
            valores = [diccionario[clave] for diccionario in lista_diccionarios]
            promedio = sum(valores) / len(valores) if valores else 0
            resultado[clave] = promedio

        for clave in valores_a_maximo:
            resultado[clave] = max(diccionario[clave] for diccionario in lista_diccionarios)

        return resultado
    else:
        return None

def calculos(lista_inversores):
    valores = []
    for datos in lista_inversores:
        valores.append(procesar_lista(datos))
    return valores[0], valores[1], valores[2], valores[3]

def limpiar_lista(lista_inversores):
    global inicio
    inicio = 0
    for lista in lista_inversores:
        lista.clear()

def escribir_en_csv(lista_datos):
    # Nombre del archivo CSV
    nombre_archivo = 'datos_inversores.csv'

    # Verificar si el archivo ya existe
    archivo_existe = os.path.isfile(nombre_archivo)

    # Abrir el archivo CSV en modo de escritura
    with open(nombre_archivo, mode='a', newline='') as archivo_csv:
        # Crear el escritor CSV
        escritor_csv = csv.writer(archivo_csv)

        # Escribir la cabecera solo si el archivo no existe
        if not archivo_existe:
            escritor_csv.writerow(['fecha', 'datosA1', 'datos1B', 'datos2B', 'datos1C'])
        
            # Obtener el número de elementos en cada lista interna
        num_elementos_A1 = len(lista_datos[0])
        num_elementos_1B = len(lista_datos[1])
        num_elementos_2B = len(lista_datos[2])
        num_elementos_1C = len(lista_datos[3])

        # Obtener la fecha actual en GMT-5
        fecha_actual_gmt5 = datetime.utcnow() - timedelta(hours=5)
        fecha_actual_formato = fecha_actual_gmt5.strftime("%Y-%m-%d %H:%M:%S")

        # Escribir la fila de datos
        escritor_csv.writerow([fecha_actual_formato, num_elementos_A1, num_elementos_1B, num_elementos_2B, num_elementos_1C])

        
def create_app(enviroment):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(enviroment)
    return app

enviroment = config['development']
app = create_app(enviroment)

@app.route('/api/data', methods=['POST'])
def enviar_mensaje():
    global inicio
    global tiempo_inicial
    if inicio == 0:
        inicio = 1
        tiempo_inicial = datetime.now()
    datos = parse_inverter_message(request.data)
    numero_inversor = verificar_inversor(datos["numeroSerial"])
    valores_inversores[numero_inversor].append(datos)
    todos_tienen_datos = verificar_lista(valores_inversores)
    tiempo_actual = datetime.now()
    if todos_tienen_datos or tiempo_actual - tiempo_inicial >= timedelta(minutes=5):
        inv1, inv2, inv3, inv4 = calculos(valores_inversores)
        escribir_en_csv(valores_inversores)
        limpiar_lista(valores_inversores)
        #hacer los post
        if inv1 is not None:
            try:
                requerimiento1 = requests.post('http://200.126.14.228:5030/api/sensorPanelSolar', json=inv1, verify=False)
            except requests.exceptions.RequestException as e:
                print(f"Error en el post: {e}")
        if inv2 is not None:
            try:
                requerimiento2 = requests.post('http://200.126.14.228:5030/api/sensorPanelSolar', json=inv2, verify=False)
            except requests.exceptions.RequestException as e:
                print(f"Error en el post: {e}")       
        if inv3 is not None:
            try:
                requerimiento3 = requests.post('http://200.126.14.228:5030/api/sensorPanelSolar', json=inv3, verify=False)
            except requests.exceptions.RequestException as e:
                print(f"Error en el post: {e}") 
        if inv4 is not None:
            try:
                requerimiento4 = requests.post('http://200.126.14.228:5030/api/sensorPanelSolar', json=inv4, verify=False)
            except requests.exceptions.RequestException as e:
                print(f"Error en el post: {e}")
    else:
       print("Esperando mensajes")
    return []

if __name__ == '__main__':
    #from waitress import serve
    #serve(app = app, host='0.0.0.0', port=5050)
    app.run(debug=True, port=5000)