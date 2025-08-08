# run.py
from app import create_app
from app.utils import load_master_data

app = create_app()

# --- マスターデータの読み込み ---
with app.app_context():
    master_data = load_master_data()
    app.config['MASTER_DATA'] = master_data
    print("マスターデータを正常に読み込み、アプリケーションコンフィグに設定しました。")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
