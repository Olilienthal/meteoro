'''
Copyright (c) 2026 Olilienthal
  
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

from calendar import monthrange
import datetime
import csv
import gettext
from selenium.webdriver.common.by import By
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
import sys
import time

'''
Algoritmo para obtener datos metereológicos diarios de una ciudad en un intervalo
de tiempo mediante el sitio https://www.wunderground.com/ 

Nota: para otra ciudad se debe cambiar la URL
'''

WUNDERGROUND = 'https://www.wunderground.com/history/daily/co/cartagena-de-indias/SKCG'
FLAG_COLUMNAS = 0

def traducir(Text):
	'''
	Traduce los mensajes de ayuda y uso
	de argparse para español
	'''
	Text = Text.replace("usage", "uso")
	Text = Text.replace("show this help message and exit",
						"muestra el mensaje de ayuda y sale")
	Text = Text.replace("the following arguments are required:",
						"los siguientes argumentos son requeridos:")
	Text = Text.replace("expected one argument", "se espera un argumento")

	return Text

gettext.gettext = traducir


def configurar_args():
	'''
	Setea los argumentos para interactuar con el programa.

	Nota: Ya que argparse utiliza la API gettext inspirada en GNU gettext
	se puede utilizar esta API para traducir los mensajes al idioma que uno quiera.
	'''

	import argparse

	parser = argparse.ArgumentParser(
		description='Obtiene los datos metereológicos mensuales de Cartagena de Indias'
	)

	parser.add_argument(
		'-i',
		'--inic',
		type=str,
		required=True,
		help='Fecha inicial a obtener los datos metereológicos (ej: 05-10-2018)'
	)

	parser.add_argument(
		'-f',
		'--fin',
		type=str,
		required=True,
		help='Fecha final a obtener los datos metereológicos (ej: 05-10-2024)'
	)

	parser.add_argument(
		'-d',
		'--dest',
		type=str,
		required=True,
		help='Archivo que almacenará los datos metereológicos (ej: vientos.csv)'
	)

	args = parser.parse_args()
	return args


def num_dias(anio, mes):
	'''
	Función que permite saber la cantidad de días que hay
	en un mes en determinado año
	'''
	ndias = monthrange(anio, mes)[1]

	return len([datetime.date(anio, mes, dia) for dia in range(1, ndias+1)])


def convertir_a_militar(hora_estandar):
	'''
	Función que convierte la hora estándar de formato AM/PM
	a hora militar
	'''
	hora, periodo = hora_estandar.split()
	hora, minutos = map(int, hora.split(':'))

	if periodo == "AM":
		if hora == 12: 
			hora_militar = 0
		else:
			hora_militar = hora
	else: # PM
		if hora == 12: 
			hora_militar = 12
		else:
			hora_militar = hora + 12

	return f"{hora_militar:02}:{minutos:02}"


def exportar_csv(dest, fila):
	'''
	Función que permite exportar los datos metereológicos
	a una hoja de cálculo
	'''

	with open(dest, 'a+', encoding='UTF-8', newline='') as archivo:
		global FLAG_COLUMNAS

		writer = csv.writer(archivo)

		if FLAG_COLUMNAS == 0:
			writer.writerow(['Fecha',
					'temperatura (°F)',
					'punto_de_rocio (°F)',
					'humedad',
					'viento',
					'Velocidad del viento (mph)',
					'rafaga_viento (mph)',
					'presion'
					])
			FLAG_COLUMNAS = 1

		writer.writerow(fila)


def obtener_datos(fecha_inicial, fecha_final, dest):
	'''
	Navega al sitio www.wunderground.com para scrapear los datos
	metereológicos de la ciudad en un intervalo de tiempo (fecha_final - fecha_inicial)
	'''

	# Parseo los días, meses y años

	anio_actual = datetime.date.today().year

	dia_inicial, mes_inicial, anio_inicial = fecha_inicial.split('-')

	dia_inicial = int(dia_inicial)
	mes_inicial = int(mes_inicial)
	anio_inicial = int(anio_inicial)

	dia_final, mes_final, anio_final = fecha_final.split('-')

	dia_final = int(dia_final)
	mes_final = int(mes_final)
	anio_final = int(anio_final)

	# Configura el driver y navega al sitio

	options = Options()
	options.add_argument("--headless")
	driver = Firefox(options=options)
	driver.implicitly_wait(20)

	driver.get(WUNDERGROUND)

	time.sleep(5)

	# Cambia el iframe para rechazar las cookies e interactuar con el sitio

	iframe = WebDriverWait(driver, 10).until(
		EC.frame_to_be_available_and_switch_to_it((
			By.ID,
			"sp_message_iframe_1225696"))
	)

	reject_all = WebDriverWait(driver, 10).until(
		EC.element_to_be_clickable((By.CSS_SELECTOR, '.sp_choice_type_13'))
	).click()

	# Cambia al frame del sitio por defecto

	driver.switch_to.default_content()

	dia_iterando = dia_inicial
	mes_iterando = mes_inicial
	anio_iterando = anio_inicial

	while (anio_iterando <= anio_final):
		while (mes_iterando <= 12):

			ndias = num_dias(anio_iterando, mes_iterando)

			while(dia_iterando <= ndias):

				time.sleep(5)

				# Selecciona el día, mes y año y 
				# presiona el botón para obtener sus datos metereológicos

				dia = Select(WebDriverWait(driver, 10).until(
					EC.presence_of_element_located((By.CSS_SELECTOR, '#daySelection'))
				)).select_by_value(str(dia_iterando - 1) + ": " + str(dia_iterando))

				mes = Select(WebDriverWait(driver, 10).until(
					EC.presence_of_element_located((By.CSS_SELECTOR, '#monthSelection'))
				)).select_by_value(str(mes_iterando))

				anio = Select(WebDriverWait(driver, 10).until(
					EC.presence_of_element_located((By.CSS_SELECTOR, '#yearSelection'))
				)).select_by_value(str(anio_actual - anio_iterando) + ": " + str(anio_iterando))

				boton_ver = WebDriverWait(driver, 10).until(
					EC.element_to_be_clickable((By.CSS_SELECTOR, '#dateSubmit'))
				).click()

				# Obtiene las observaciones diarias

				mas_horas = True
				idx_horas = 0
				while mas_horas:

					fecha_lista_csv = []

					hora_csss = 'tr.mat-mdc-row:nth-child(' + str(idx_horas + 1) + ') > ' \
								'td:nth-child(1) > span:nth-child(1)'
					
					temperatura_csss = 'tr.mat-mdc-row:nth-child(' + str(idx_horas + 1) + ') > ' \
										'td:nth-child(2) > lib-display-unit:nth-child(1) > '     \
										'span:nth-child(1) > span:nth-child(1)'

					punto_de_rocio_csss = 'tr.mat-mdc-row:nth-child(' + str(idx_horas + 1) + ') ' \
						'> td:nth-child(3) > lib-display-unit:nth-child(1) > span:nth-child(1) > '\
						'span:nth-child(1)'
					
					humedad_csss = 'tr.mat-mdc-row:nth-child(' + str(idx_horas + 1) + ') > ' \
					 	'td:nth-child(4) > lib-display-unit:nth-child(1) > span:nth-child(1) > ' \
						'span:nth-child(1)'
					
					viento_csss = 'tr.mat-mdc-row:nth-child(' + str(idx_horas + 1) + ') > ' \
						'td:nth-child(5) > span:nth-child(1)'
					

					velocidad_viento_csss = 'tr.mat-mdc-row:nth-child(' + str(idx_horas + 1) + ')' \
					 	' > td:nth-child(6) > lib-display-unit:nth-child(1) > span:nth-child(1) ' \
						'> span:nth-child(1)'
					
					rafaga_viento_csss = 'tr.mat-mdc-row:nth-child(' + str(idx_horas + 1) + ') ' \
						' > td:nth-child(7) > lib-display-unit:nth-child(1) > span:nth-child(1) ' \
						'> span:nth-child(1)'
					
					presion_csss = 'tr.mat-mdc-row:nth-child(' + str(idx_horas + 1) + ') > ' \
						'td:nth-child(8)'

					try:

						hora = WebDriverWait(driver, 10).until(
							EC.presence_of_element_located((
								By.CSS_SELECTOR,
								hora_csss
							))
						)

						temperatura = WebDriverWait(driver, 10).until(
							EC.presence_of_element_located((
								By.CSS_SELECTOR,
								temperatura_csss
							))
						)

						punto_de_rocio = WebDriverWait(driver, 10).until(
							EC.presence_of_element_located((
								By.CSS_SELECTOR,
								punto_de_rocio_csss
							))
						)

						humedad = WebDriverWait(driver, 10).until(
							EC.presence_of_element_located((
								By.CSS_SELECTOR,
								humedad_csss
							))
						)

						viento = WebDriverWait(driver, 10).until(
							EC.presence_of_element_located((
								By.CSS_SELECTOR,
								viento_csss
							))
						)

						velocidad_viento = WebDriverWait(driver, 10).until(
							EC.presence_of_element_located((
								By.CSS_SELECTOR,
								velocidad_viento_csss
							))
						)

						rafaga_viento = WebDriverWait(driver, 10).until(
							EC.presence_of_element_located((
								By.CSS_SELECTOR,
								rafaga_viento_csss
							))
						)

						presion = WebDriverWait(driver, 10).until(
							EC.presence_of_element_located((
								By.CSS_SELECTOR,
								presion_csss
							))
						)

						hora = convertir_a_militar(hora.get_attribute("textContent"))
						fecha_iterando = "{}-{}-{}:{}".format(dia_iterando,
															mes_iterando,
															anio_iterando,
															hora)

						fecha_lista_csv.append(fecha_iterando)
						fecha_lista_csv.append(temperatura.get_attribute("textContent"))
						fecha_lista_csv.append(punto_de_rocio.get_attribute("textContent"))
						fecha_lista_csv.append(humedad.get_attribute("textContent"))
						fecha_lista_csv.append(viento.get_attribute("textContent"))
						fecha_lista_csv.append(velocidad_viento.get_attribute("textContent"))
						fecha_lista_csv.append(rafaga_viento.get_attribute("textContent"))
						fecha_lista_csv.append(presion.get_attribute("textContent"))

						# Agrega datos de la fecha al archivo destino

						exportar_csv(dest, fecha_lista_csv)

					except Exception as e:
						mas_horas = False

					idx_horas += 1

				if (dia_iterando == dia_final) and (mes_iterando == mes_final) and 			\
					(anio_iterando == anio_final):
					print("[+] Datos dumpeados exitosamente.")
					sys.exit(0)

				dia_iterando += 1

			dia_iterando = 1
			mes_iterando += 1

		mes_iterando = 1
		anio_iterando += 1

if __name__ == '__main__':

	# Verifica que se ingrese más de 1 argumento

	if (len(sys.argv) < 2):
		print ("uso: {} [-h] para obtener ayuda".format(sys.argv[0]))
		sys.exit(0)


	args = configurar_args()

	# Web scraping

	obtener_datos(args.inic, args.fin, args.dest)