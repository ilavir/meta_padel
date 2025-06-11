from app import create_app


app = create_app()


# Checkhealth for Docker
@app.route('/health', methods=['GET'])
def health():
    return {'success': True}
