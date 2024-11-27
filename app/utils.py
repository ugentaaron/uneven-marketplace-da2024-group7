# app/utils.py

def allowed_file(filename):
    """
    Controleert of het bestand een toegestane extensie heeft.
    :param filename: Naam van het bestand
    :return: True als toegestaan, anders False
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS