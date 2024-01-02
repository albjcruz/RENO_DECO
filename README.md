# Repositorio para cambios en RENO

Este repositorio contiene todos los cambios que se realizaron en el sistema RENO

## decoder_API.py

Servicio API desarrollado en flask que libera a la RPI del trabajo de parsear los datos que envían los dataloggers

## serverAN.py

Servicio que levanta un sniffer para escuchar los mensajes enviados por los dataloggers. Para su correcto funcionamiento se debe configurar la dirección IP a la que apuntan los dataloggers (debe ser la misma del dispositivo que va a correr este servicio) y la red debe poder conectarse a los servidores de SOLIS.

## datos_codificadosAN.txt

Mensaje en crudo (bytes) capturado para poder hacer pruebas con el decoder.

## todos al mismo tiempo.xlsx

Archivo excel donde se realiza un análisis de los tiempos de llegada de cada paquete hacia los servidores.
