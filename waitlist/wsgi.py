from app import app as application  # gunicorn entry point: gunicorn -w 2 -b 127.0.0.1:8787 wsgi:application

if __name__ == "__main__":
    application.run()
