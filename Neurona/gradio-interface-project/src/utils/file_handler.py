def upload_file(file):
    import pandas as pd
    from io import BytesIO

    # Read the uploaded XLSX file
    try:
        df = pd.read_excel(BytesIO(file.read()))
        return df
    except Exception as e:
        return str(e)

def save_file(file):
    with open(file.name, 'wb') as f:
        f.write(file.read())
    return f"{file.name} saved successfully."