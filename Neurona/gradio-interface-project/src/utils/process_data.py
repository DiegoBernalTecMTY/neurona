def find_age(age, available_ages):
    if age < min(available_ages):
        print(f"Warning: The requested age {age} is below the lowest available age {min(available_ages)}.")
    elif age > max(available_ages) + 12:
        print(f"Warning: The requested age {age} is greater than the highest available age {max(available_ages)} plus 12 months.")

    floor_age = max([a for a in available_ages if a <= age], default=None)

    if floor_age is not None and abs(age - floor_age) > 12:
        print(f"Warning: The difference between the requested age {age} and the nearest available age {floor_age} is greater than 12 months.")

    return floor_age

def get_scalar(edad_meses, available_ages, puntuacion, prueba, baremos):
    nearest_age = find_age(edad_meses, available_ages)
    if nearest_age is None:
        return None
    if puntuacion is None:
        print(f"No natural score provided for age {edad_meses} in test {prueba}.")
        return None

    puntuacion_escalar = baremos[(baremos['Edad (meses)'] == nearest_age) & 
                                 (baremos['Puntuación natural'] == puntuacion)][prueba].values
    if len(puntuacion_escalar) == 0:
        print(f"No scalar score found for age {edad_meses} and natural score {puntuacion} in test {prueba}.")
        return None
    return puntuacion_escalar[0]


