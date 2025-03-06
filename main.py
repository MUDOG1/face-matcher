import os
import face_recognition
import sqlite3
import numpy as np

db_path = "faces.db"
input_folder = "knownfaces"
compare_folder = "unknownfaces"

def create_database():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    encoding BLOB)''')
    conn.commit()
    conn.close()

def encode_face(image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    return encodings[0] if encodings else None

def store_faces():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for file in os.listdir(input_folder):
        path = os.path.join(input_folder, file)
        encoding = encode_face(path)
        if encoding is not None:
            # Überprüfen, ob der Name bereits in der Datenbank existiert
            c.execute("SELECT 1 FROM faces WHERE name = ?", (file,))
            if c.fetchone() is None:  # Wenn der Name nicht gefunden wird, füge ihn hinzu
                c.execute("INSERT INTO faces (name, encoding) VALUES (?, ?)", (file, encoding.tobytes()))
                print(f"Gesicht {file} wurde hinzugefügt.")
            else:
                print(f"Gesicht {file} existiert bereits und wird übersprungen.")
    conn.commit()
    conn.close()

def load_faces():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name, encoding FROM faces")
    faces = [(name, np.frombuffer(enc, dtype=np.float64)) for name, enc in c.fetchall()]
    conn.close()
    return faces

def compare_faces():
    known_faces = load_faces()
    for file in os.listdir(compare_folder):
        path = os.path.join(compare_folder, file)
        unknown_encoding = encode_face(path)
        if unknown_encoding is None:
            continue
        for name, known_encoding in known_faces:
            match = face_recognition.compare_faces([known_encoding], unknown_encoding)[0]
            if match:
                print(f"{file} matches {name}")
            else:
                print(f"{file} does not match {name}")

if __name__ == "__main__":
    create_database()
    store_faces()
    compare_faces()
