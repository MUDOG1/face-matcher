import os
import face_recognition
import sqlite3
import numpy as np
from flask import Flask, render_template, request, redirect, url_for

# Initialisierung der Flask-Anwendung
app = Flask(__name__)

# Ordner und Datenbankpfade
db_path = "faces.db"
UPLOAD_FOLDER = 'uploads'
KNOWN_FACES_FOLDER = os.path.join(UPLOAD_FOLDER, 'knownfaces')
UNKNOWN_FACES_FOLDER = os.path.join(UPLOAD_FOLDER, 'unknownfaces')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Sicherstellen, dass die Ordner existieren
os.makedirs(KNOWN_FACES_FOLDER, exist_ok=True)
os.makedirs(UNKNOWN_FACES_FOLDER, exist_ok=True)

# Funktion, um eine Datenbank zu erstellen, falls sie noch nicht existiert
def create_database():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    encoding BLOB)''')
    conn.commit()
    conn.close()

# Funktion, um das Gesicht zu kodieren
def encode_face(image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    return encodings[0] if encodings else None

# Funktion, um Gesichter in die Datenbank zu speichern
def store_face_in_db(filename, encoding):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO faces (name, encoding) VALUES (?, ?)", (filename, encoding.tobytes()))
    conn.commit()
    conn.close()

# Funktion, um alle Gesichter aus der Datenbank zu laden
def load_faces_from_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name, encoding FROM faces")
    faces = [(name, np.frombuffer(enc, dtype=np.float64)) for name, enc in c.fetchall()]
    conn.close()
    return faces

def is_face_in_db(encoding):
    """
    Überprüft, ob das Gesicht mit dieser Kodierung bereits in der Datenbank existiert.
    """
    known_faces = load_faces_from_db()
    for _, known_encoding in known_faces:
        # Vergleich der Gesichter
        match = face_recognition.compare_faces([known_encoding], encoding)[0]
        if match:
            return True
    return False


# Startseite mit zwei Buttons
@app.route('/')
def index():
    return render_template('index.html')



# Seite für das Hochladen von bekannten Gesichtern
@app.route('/upload_known', methods=['GET', 'POST'])
def upload_known():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            filename = os.path.join(KNOWN_FACES_FOLDER, file.filename)
            file.save(filename)

            # Gesicht kodieren
            encoding = encode_face(filename)

            if encoding is not None and encoding.size > 0:
                # Überprüfen, ob das Gesicht schon in der Datenbank ist
                if is_face_in_db(encoding):
                    return render_template('success_error_redirect.html',title =f"Error" ,message=f"Das Gesicht im Bild {file.filename} existiert bereits in der Datenbank.")
                
                # Wenn das Gesicht nicht vorhanden ist, speichern wir es
                store_face_in_db(file.filename, encoding)
                return render_template('success_error_redirect.html',title =f"Success", message=f"Gesicht {file.filename} wurde erfolgreich hochgeladen!")
            else:
                return f"Kein Gesicht im Bild {file.filename} gefunden."
    return render_template('upload.html', title='Upload Known Faces')


# Seite für das Hochladen von unbekannten Gesichtern und Vergleich
@app.route('/upload_unknown', methods=['GET', 'POST'])
def upload_unknown():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            filename = os.path.join(UNKNOWN_FACES_FOLDER, file.filename)
            file.save(filename)

            # Gesicht kodieren
            unknown_encoding = encode_face(filename)
            if unknown_encoding is None:
                return f"Kein Gesicht im Bild {file.filename} gefunden."

            # Gesichter vergleichen
            known_faces = load_faces_from_db()
            for name, known_encoding in known_faces:
                match = face_recognition.compare_faces([known_encoding], unknown_encoding)[0]
                if match:
                    return render_template('success_error_redirect.html',title = f"Success", message=f"Das Bild {file.filename} stimmt mit {name} überein.")
            return f"Das Bild {file.filename} stimmt mit keinem bekannten Gesicht überein."
    return render_template('upload.html', title='Upload Unknown Faces')

if __name__ == "__main__":
    create_database()
    app.run(debug=True)
