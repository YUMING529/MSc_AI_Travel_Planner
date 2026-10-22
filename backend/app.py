"""Local Flask API for the TripMind prototype."""
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from backend.weather import get_weather, attach_weather
from backend.planner import generate_sample
from backend.qwen import generate_qwen, PlannerError
from backend.validation import ValidationError, validate_preferences


def create_app(config=None):
    load_dotenv(Path(__file__).with_name('.env'))
    app = Flask(__name__)
    app.config.update(
        WEATHER_ENABLED=os.getenv('WEATHER_ENABLED', 'true').lower() == 'true',
        TRIP_PROVIDER=os.getenv('TRIP_PROVIDER', 'sample'),
        DASHSCOPE_API_KEY=os.getenv('DASHSCOPE_API_KEY', ''),
        QWEN_MODEL=os.getenv('QWEN_MODEL', 'qwen-plus'),
        QWEN_BASE_URL=os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
        RECORD_LLM_EXPERIMENTS=os.getenv('RECORD_LLM_EXPERIMENTS', 'false').lower() == 'true',
        EXPERIMENT_DIR=str(Path(__file__).resolve().parents[1] / 'experiments' / 'runs'),
    )
    if config:
        app.config.update(config)
    if app.config['TRIP_PROVIDER'] not in ('sample', 'qwen'):
        raise ValueError('TRIP_PROVIDER must be sample or qwen')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024

    @app.get('/api/health')
    def health():
        return jsonify(status='ok', mode=app.config['TRIP_PROVIDER'])

    @app.post('/api/trips/generate')
    def generate():
        if not request.is_json:
            return jsonify(error={'code': 'invalid_content_type', 'message': 'Use application/json.'}), 415
        try:
            preferences = validate_preferences(request.get_json(), app.config['TRIP_PROVIDER'])
        except ValidationError as error:
            return jsonify(error={'code': 'invalid_preferences', 'message': str(error)}), 400
        try:
            if app.config['TRIP_PROVIDER'] == 'qwen':
                weather = get_weather(preferences, enabled=app.config['WEATHER_ENABLED'])
                trip = generate_qwen(preferences, {**app.config, 'WEATHER_CONTEXT': weather})
                attach_weather(trip, weather)
            else:
                trip = generate_sample(preferences)
        except PlannerError as error:
            return jsonify(error={'code': error.code, 'message': error.message}), error.status
        return jsonify(trip=trip)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error={'code': error.name.lower().replace(' ', '_'), 'message': error.description}), error.code

    return app


app = create_app()
