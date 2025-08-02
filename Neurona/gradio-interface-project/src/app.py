import sys
import subprocess
import os
import webbrowser  # Import webbrowser module
import signal  # Import signal module for stopping the script
from dateutil.relativedelta import relativedelta  # Import relativedelta



# try:
#     subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "../requirements.txt"])
# except Exception as e:
#     print(f"Error installing requirements: {e}")
#     sys.exit(1)

from gradio import Interface, File, Textbox, Button  # Import necessary components from gradio
import pandas as pd
from utils.process_data import get_scalar

baremos = pd.read_csv('gradio-interface-project/src/utils/baremos_wisc_escalares.csv')
baremos_idx = pd.read_csv('gradio-interface-project/src/utils/baremoswisc_indices.csv')


def process_file(file):
    form = pd.read_excel(file)
    birth_date = pd.to_datetime(f"{form.at[1,3]}-{form.at[1,2]}-{form.at[1,1]}")
    print(f'Fecha de nacimiento: {birth_date.strftime("%Y-%m-%d")}')
    test_date = pd.to_datetime(f"{form.at[2,3]}-{form.at[2,2]}-{form.at[2,1]}")
    print(f'Fecha de la prueba: {test_date.strftime("%Y-%m-%d")}')
    age_at_test = (test_date.year - birth_date.year) * 12 + (test_date.month - birth_date.month)  # Convert days to months
    age_complete = relativedelta(test_date, birth_date)
    print(f"Edad en meses al momento de la prueba: {age_at_test} meses")
    print(f"Edad en años, meses y días: {age_complete.years} años, {age_complete.months} meses, {age_complete.days} días")
        
    messages = []
    messages.append(f'Fecha de nacimiento: {birth_date.strftime("%Y-%m-%d")}')
    messages.append(f'Fecha de la prueba: {test_date.strftime("%Y-%m-%d")}')
    messages.append(f"Edad en años, meses y días: {age_complete.years} años, {age_complete.months} meses, {age_complete.days} días")
    messages.append(f"Edad en meses al momento de la prueba: {age_at_test} meses")
    results, messages = all_tests(wisc_tests.items(), baremos, form, age_at_test, messages)
    indexes, messages = wisc_indexes(results, baremos_idx, messages)
    for test, scalar in results.items():
        messages.append(f"Test: {test}, Puntuación escalar: {scalar}")
    for index, value in indexes.items():
        messages.append(f"{index}: {value}")
    return "\n".join(messages)



wisc_tests = {
    'Semejanzas': ['SE', [7, 1]],
    'Vocabulario': ['VB', [7, 2]],
    'Comprensión': ['CM', [7, 3]],
    'Información': ['IN', [7, 4]],
    'Diseño con cubos': ['DC', [7, 5]],
    'Conceptos con dibujos': ['CD', [7, 6]],
    'Matrices': ['MT', [7, 7]],
    'Figuras incompletas': ['FI', [7, 8]],
    'Retención de dígitos': ['RD', ([7, 9], [7, 10])],
    'Letras y números': ['NL', [7, 11]],
    'Aritmética': ['AR', [7, 12]],
    'Claves' : ['CL', [7, 13]],
    'Búsqueda de símbolos': ['BS', [7, 14]],
}

def all_tests(tests, baremos, form, age_at_test=None, messages=None):
    results = {}

    for test, test_info in tests:
        if test_info[0] not in baremos.columns:
            messages.append(f"Prueba {test} no encontrada en los baremos.")
        
            continue
        if isinstance(test_info[1], list):
            puntuacion = form.at[test_info[1][0],test_info[1][1] ]  # Assuming the natural score is in the second row
        elif isinstance(test_info[1], tuple):
            puntuacion = form.at[test_info[1][0][0], test_info[1][0][1],] + form.at[test_info[1][1][0], test_info[1][1][1]]
        if pd.isna(puntuacion):
            messages.append(f"No se proporcionó puntuación natural para la prueba {test}.")
            continue
        scalar = get_scalar(age_at_test, baremos['Edad (meses)'].unique(), puntuacion, test_info[0], baremos)
        if scalar is not None:
            results[test] = scalar
    return results, messages

def wisc_indexes(results, baremos_idx, messages):
    #icv = semejanzas + vocab + compren
    icv_1 = [results.get('Semejanzas', 0), results.get('Vocabulario', 0), results.get('Comprensión', 0)]
    min_icv = min(icv_1)
    max_icv = max(icv_1)
    if max_icv - min_icv > 4:
        messages.append(f"Advertencia: La diferencia entre el ICV máximo {max_icv} y el ICV mínimo {min_icv} es mayor que 4. Cambiando el mínimo por el valor de información")
        icv_2 = icv_1.copy()
        icv_2[icv_1.index(min_icv)] = results.get('Información', 0)  # Replace the minimum with the value of 'Información'
        min_icv = min(icv_2)
        max_icv = max(icv_2)
        if max_icv - min_icv > 4:
            messages.append(f"Advertencia: La diferencia entre el ICV máximo {max_icv} y el ICV mínimo {min_icv} sigue siendo mayor que 4. Cambiando el máximo por el valor de información")
            icv_3 = icv_2.copy()
            icv_3[icv_2.index(max_icv)] = results.get('Información', 0)
            min_icv = min(icv_3)
            max_icv = max(icv_3)
            if max_icv - min_icv > 4:
                messages.append(f"Advertencia: La diferencia entre el ICV máximo {max_icv} y el ICV mínimo {min_icv} sigue siendo mayor que 4. Retornando el cálculo normal.")
                icv = icv_1
            else:
                icv = icv_3
        else:
            icv = icv_2
    else:
        icv = icv_1
    icv = sum(icv)  # Sum the values for ICV
    #irp = diseño con cubos + conceptos con dibujos + matrices
    irp = [results.get('Diseño con cubos', 0), results.get('Conceptos con dibujos', 0), results.get('Matrices', 0)]
    min_irp = min(irp)
    max_irp = max(irp)
    if max_irp - min_irp > 4:
        messages.append(f"Advertencia: La diferencia entre el IRP máximo {max_irp} y el IRP mínimo {min_irp} es mayor que 4. Cambiando el mínimo por el valor de Figuras incompletas")
        irp_2 = irp.copy()
        irp_2[irp.index(min_irp)] = results.get('Figuras incompletas', 0)
        min_irp = min(irp_2)
        max_irp = max(irp_2)
        if max_irp - min_irp > 4:
            messages.append(f"Advertencia: La diferencia entre el IRP máximo {max_irp} y el IRP mínimo {min_irp} sigue siendo mayor que 4. Cambiando el máximo por el valor de Figuras incompletas")
            irp_3 = irp_2.copy()
            irp_3[irp_2.index(max_irp)] = results.get('Figuras incompletas', 0)
            min_irp = min(irp_3)
            max_irp = max(irp_3)
            if max_irp - min_irp > 4:
                messages.append(f"Advertencia: La diferencia entre el IRP máximo {max_irp} y el IRP mínimo {min_irp} sigue siendo mayor que 4. Retornando el cálculo normal.")
                irp = irp
            else:
                irp = irp_3
        else:
            irp = irp_2
    else:
        irp = irp
    irp = sum(irp)  # Sum the values for IRP
    #imt = retención de dígitos  + letras y números
    imt = [results.get('Retención de dígitos', 0), results.get('Letras y números', 0)]
    min_imt = min(imt)
    max_imt = max(imt)
    if max_imt - min_imt > 4:
        messages.append(f"Advertencia: La diferencia entre el IMT máximo {max_imt} y el IMT mínimo {min_imt} es mayor que 4. Cambiando el mínimo por el valor de Aritmética")
        imt_2 = imt.copy()
        imt_2[imt.index(min_imt)] = results.get('Aritmética', 0)
        min_imt = min(imt_2)
        max_imt = max(imt_2)
        if max_imt - min_imt > 4:
            messages.append(f"Advertencia: La diferencia entre el IMT máximo {max_imt} y el IMT mínimo {min_imt} sigue siendo mayor que 4. Cambiando el máximo por el valor de Aritmética")
            imt_3 = imt_2.copy()
            imt_3[imt_2.index(max_imt)] = results.get('Aritmética', 0)
            min_imt = min(imt_3)
            max_imt = max(imt_3)
            if max_imt - min_imt > 4:
                messages.append(f"Advertencia: La diferencia entre el IMT máximo {max_imt} y el IMT mínimo {min_imt} sigue siendo mayor que 4. Retornando el cálculo normal.")
                imt = imt
            else:
                imt = imt_3
        else:
            imt = imt_2
    else:
        imt = imt
    imt = sum(imt)  # Sum the values for IMT
    #icd = claves + búsqueda de símbolos
    ivp = [results.get('Claves', 0), results.get('Búsqueda de símbolos', 0)]
    min_ivp = min(ivp)
    max_ivp = max(ivp)
    if max_ivp - min_ivp > 4:
        messages.append(f"Advertencia: La diferencia entre el ICD máximo {max_ivp} y el ICD mínimo {min_ivp} es mayor que 4. Se requiere el valor de registros.")
    ivp = sum(ivp)  # Sum the values for ICD
    cit = icv + irp + imt + ivp
    indexes = {
        'ICV': baremos_idx[baremos_idx['Puntuación escalar']== icv]['ICV'].values[0],
        'IRP': baremos_idx[baremos_idx['Puntuación escalar']== irp]['IRP'].values[0],
        'IMT': baremos_idx[baremos_idx['Puntuación escalar']== imt]['IMT'].values[0],
        'IVP': baremos_idx[baremos_idx['Puntuación escalar']== ivp]['IVP'].values[0],
        'CIT': baremos_idx[baremos_idx['Suma puntuaciones escalares']== cit]['CIT'].values[0]
    }
    messages.append(f"ICV: {indexes['ICV']}, IRP: {indexes['IRP']}, IMT: {indexes['IMT']}, IVP: {indexes['IVP']}, CIT: {indexes['CIT']}")
    messages.append(f'ICV - Rango percentil: {baremos_idx[baremos_idx["Puntuación escalar"] == icv]["Rango percentil_ICV"].values[0]}')
    messages.append(f'ICV - Confianza 95: {baremos_idx[baremos_idx["Puntuación escalar"] == icv]["Confianza 95_ICV"].values[0]}')
    messages.append(f'IRP - Rango percentil: {baremos_idx[baremos_idx["Puntuación escalar"] == irp]["Rango percentil_IRP"].values[0]}')
    messages.append(f'IRP - Confianza 95: {baremos_idx[baremos_idx["Puntuación escalar"] == irp]["Confianza 95_IRP"].values[0]}')
    messages.append(f'IMT - Rango percentil: {baremos_idx[baremos_idx["Puntuación escalar"] == imt]["Rango percentil_IMT"].values[0]}')
    messages.append(f'IMT - Confianza 95: {baremos_idx[baremos_idx["Puntuación escalar"] == imt]["Confianza 95_IMT"].values[0]}')
    messages.append(f'IVP - Rango percentil: {baremos_idx[baremos_idx["Puntuación escalar"] == ivp]["Rango percentil_IVP"].values[0]}')
    messages.append(f'IVP - Confianza 95: {baremos_idx[baremos_idx["Puntuación escalar"] == ivp]["Confianza 95_IVP"].values[0]}')
    messages.append(f'CIT - Rango percentil: {baremos_idx[baremos_idx["Suma puntuaciones escalares"] == cit]["Rango percentil_CIT"].values[0]}')
    messages.append(f'CIT - Confianza 95: {baremos_idx[baremos_idx["Suma puntuaciones escalares"] == cit]["Confianza 95_CIT"].values[0]}')
    return indexes, messages

def stop_app(dummy_input):
    print("Stopping the app...")
    os.kill(os.getpid(), signal.SIGTERM)  # Terminate the script
    return "App stopped."



iface = Interface(
    fn=process_file,
    inputs=File(label="Sube un archivo XLSX con los datos de la prueba"),
    outputs=Textbox(label="Resultados"),
    title="Neurona - Calculadora de valores escalares",
    description="Sube un archivo XLSX con los datos de la pruebas neuropsicologicas para calcular los valores escalares.",
    theme='shivi/calm_seafoam'  # Link to the custom CSS file
)
stop_iface = Interface(
    fn=stop_app,
    inputs="button",  # Corrected input type for Button
    outputs=Textbox(label="Status"),
    title="Stop App",
    description="Click the button to stop the app."
)

if __name__ == "__main__":
    url = 'http://127.0.0.1:7860'
    webbrowser.open(url)  # Force open the interface URL in the default browser
    iface.launch(share=False)  # Launch the interface locally
    