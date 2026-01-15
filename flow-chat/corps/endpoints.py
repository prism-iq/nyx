from flask import request
from .magie import magie_endpoint

def setup_magie_routes(app):
    @app.route('/magie', methods=['GET', 'POST'])
    def magie():
        if request.method == 'GET':
            return magie_endpoint({"action": "status"})
        else:
            return magie_endpoint(request.json or {})
    
    @app.route('/magie/cast/<sort>', methods=['POST'])  
    def cast_sort(sort):
        return magie_endpoint({
            "action": "cast",
            "sort": sort
        })
    
    @app.route('/magie/grimoire', methods=['GET'])
    def grimoire():
        return magie_endpoint({"action": "grimoire"})