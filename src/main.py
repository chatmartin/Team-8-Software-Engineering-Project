from flask import Flask,jsonify,request

def create_app():
    app = Flask(__name__, template_folder="templates",static_folder="static")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)