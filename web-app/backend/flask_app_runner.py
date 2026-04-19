"""Starts the consolidated Flask backend service."""


def main():
    from flask_service.main import create_app

    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
