
import os

def try_read_pdf():
    file_path = 'states.pdf'
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            content = f.read(1000) # Read first 1000 bytes
            print(content)

if __name__ == "__main__":
    try_read_pdf()
