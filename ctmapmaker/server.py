import traceback
from io import BytesIO

from flask import Flask, jsonify, request, send_file, make_response

from ctmapmaker.draw import render
from ctmapmaker.error import MapmakerError


app = Flask(__name__)


@app.route('/', methods=['POST'])
def endpoint():
    data = request.get_json()
    try:
        img_io = BytesIO()
        image, tiles = render(data['season'], data['predicate'], data['team'])
        image.save(img_io, 'PNG')
        img_io.seek(0)

        response = make_response(send_file(img_io, mimetype='image/png'))
        response.headers['X-Tiles'] = ','.join(tiles)
        return response
    except MapmakerError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'{type(e).__name__}: {e}'}), 500
