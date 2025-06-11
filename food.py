# food.py 파일 (체크박스 삭제 기능 추가 버전)

import sqlite3
import random
import os
from flask import Flask, render_template_string, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = 'foods.db' # 음식 목록을 저장할 파일 이름

# 데이터베이스 연결 함수 (이전과 동일)
def get_db():
    """데이터베이스 연결"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Flask 앱이 종료될 때 데이터베이스 연결 닫기 (이전과 동일)
@app.teardown_appcontext
def close_db(error):
    """데이터베이스 연결 닫기"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# 데이터베이스 초기화 함수 (테이블 생성) - foodapp.sql 파일 사용 (encoding='utf-8' 추가됨)
def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    with app.app_context():
        db = get_db()
        try:
            # foodapp.sql 파일을 읽어서 SQL 명령 실행 (encoding='utf-8' 추가됨)
            with app.open_resource('foodapp.sql', mode='r', encoding='utf-8') as f:
                db.cursor().executescript(f.read())
            db.commit()
            print("Database schema initialized using foodapp.sql.")
        except FileNotFoundError:
            print("Error: foodapp.sql not found! Cannot initialize database.")
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.rollback()

# Flask CLI 명령어로 데이터베이스 초기화 실행할 수 있게 등록 (이전과 동일)
@app.cli.command('initdb')
def initdb_command():
    """데이터베이스 테이블 초기화 CLI 명령어."""
    init_db()
    print('Initialized the database via CLI command.')

# ====> 라우트(페이지)들 <====

# 메인 페이지 라우트 ('/') (이전과 동일)
@app.route('/')
def index():
    html_content = """
    <!doctype html>
    <html>
    <head><title>오늘 뭐 먹지?</title></head>
    <body>
        <h1>오늘 뭐 먹지?</h1>

        <form action="{{ url_for('recommendation_result') }}" method="get">
            <button type="submit" style="font-size: 20px; padding: 10px 20px;">오늘 뭐 먹을까?</button>
        </form>
        <br>
        <p><a href="{{ url_for('list_foods') }}">등록된 음식 전체 보기</a></p>
        <p><a href="{{ url_for('add_food_form') }}">새 음식 추가하기</a></p>

    </body>
    </html>
    """
    return render_template_string(html_content)

# 추천 결과 페이지 라우트 ('/recommend') (이전과 동일)
@app.route('/recommend')
def recommendation_result():
    db = get_db()
    cursor = db.cursor()
    recommended_food = "등록된 음식이 없습니다."

    try:
        cursor.execute("SELECT name FROM foods")
        foods = cursor.fetchall()
        if foods:
            food_list = [food[0] for food in foods]
            recommended_food = random.choice(food_list)
        else:
            print("No foods found in the database for recommendation.")

    except sqlite3.OperationalError:
        print("Warning: 'foods' table not found. Database might not be initialized.")
        recommended_food = "오류: 음식 목록을 가져올 수 없습니다. 데이터베이스 초기화가 필요할 수 있습니다."

    html_content = """
    <!doctype html>
    <html>
    <head><title>오늘의 추천 메뉴</title></head>
    <body>
        <h1>오늘의 추천 메뉴는?!</h1>
        <p style="font-size: 24px; color: green;"><strong>{{ recommended_food }}</strong></p>

        <p><a href="{{ url_for('index') }}">처음으로 돌아가기</a></p>
        <p><a href="{{ url_for('recommendation_result') }}">다른 메뉴 추천받기</a></p>
    </body>
    </html>
    """
    return render_template_string(html_content, recommended_food=recommended_food)


# 등록된 음식 목록 페이지 라우트 ('/foods')
# ====> 체크박스 삭제 기능 추가를 위해 HTML 템플릿 수정! <====
@app.route('/foods')
def list_foods():
    db = get_db()
    cursor = db.cursor()
    foods = []

    try:
        # ====> id와 name을 모두 가져와야 해 <====
        cursor.execute("SELECT id, name FROM foods ORDER BY name")
        foods = cursor.fetchall()
    except sqlite3.OperationalError:
        print("Warning: 'foods' table not found. Database might not be initialized.")


    html_content = """
    <!doctype html>
    <html>
    <head><title>등록된 음식 목록</title></head>
    <body>
        <h1>등록된 음식 목록</h1>

        <!-- ====> 삭제를 위한 폼 추가! <==== -->
        <!-- 선택된 항목들을 '/delete_selected_foods' 라우트로 POST 요청 보냄 -->
        <form action="{{ url_for('delete_selected_foods') }}" method="post">
            <ul>
                {% for food in foods %}
                    <li>
                        <!-- ====> 체크박스 추가! name은 'food_ids', value는 음식의 id <==== -->
                        <input type="checkbox" name="food_ids" value="{{ food[0] }}">
                        {{ food[1] }} <!-- 음식 이름 -->
                    </li>
                {% else %}
                    <li>등록된 음식이 없습니다.</li>
                {% endfor %}
            </ul>
            <br>
            <!-- ====> 선택 항목 삭제 버튼 추가! <==== -->
            <button type="submit" style="font-size: 16px; padding: 5px 10px;">선택 항목 삭제</button>
        </form>

        <br>
        <p><a href="{{ url_for('index') }}">처음으로 돌아가기</a></p>
        <p><a href="{{ url_for('add_food_form') }}">새 음식 추가하기</a></p>
    </body>
    </html>
    """
    # foods는 [(id1, name1), (id2, name2), ...] 형태
    return render_template_string(html_content, foods=foods)

# 새 음식 추가 폼 페이지 라우트 ('/add') (이전과 동일)
@app.route('/add')
def add_food_form():
    html_content = """
    <!doctype html>
    <html>
    <head><title>새 음식 추가</title></head>
    <body>
        <h1>새 음식 추가하기</h1>
        <form action="{{ url_for('add_food') }}" method="post">
            음식 이름: <input type="text" name="food_name" required>
            <button type="submit">추가</button>
        </form>
        <br>
        <p><a href="{{ url_for('index') }}">처음으로 돌아가기</a></p>
        <p><a href="{{ url_for('list_foods') }}">등록된 음식 전체 보기</a></p>
    </body>
    </html>
    """
    return render_template_string(html_content)


# 음식 추가 처리 라우트 ('/add_food') (이전과 동일)
@app.route('/add_food', methods=['POST'])
def add_food():
    food_name = request.form.get('food_name', '').strip()
    if food_name:
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO foods (name) VALUES (?)", (food_name,))
            if cursor.rowcount > 0:
                db.commit()
                print(f"Successfully added food: '{food_name}'")
            else:
                print(f"Food '{food_name}' already exists and was ignored.")
        except Exception as e:
             print(f"Error adding food '{food_name}': {e}")
             db.rollback()
    return redirect(url_for('list_foods'))

# ====> 새로운 라우트 추가! 선택된 음식들 삭제 처리 라우트 ('/delete_selected_foods') <====
# 목록 페이지에서 '선택 항목 삭제' 버튼을 누르면 이 라우트로 POST 요청이 와.
@app.route('/delete_selected_foods', methods=['POST'])
def delete_selected_foods():
    # ====> 체크된 체크박스들의 'value'(음식 id) 값들을 리스트로 가져와! <====
    # request.form.getlist('food_ids')는 'food_ids' 이름으로 온 모든 값들을 리스트로 반환해줘.
    selected_food_ids = request.form.getlist('food_ids')
    # print(f"Selected food IDs for deletion: {selected_food_ids}") # 디버깅용

    if selected_food_ids: # 선택된 음식 ID가 하나라도 있다면
        db = get_db()
        cursor = db.cursor()
        try:
            # ====> 선택된 모든 ID에 해당하는 음식들을 데이터베이스에서 삭제! <====
            # SQL의 IN 절을 사용해서 여러 개를 한 번에 삭제할 수 있어.
            # (?, ?, ...) 부분은 selected_food_ids 리스트의 길이만큼 자동으로 만들어져.
            placeholders = ','.join('?' * len(selected_food_ids))
            sql_query = f"DELETE FROM foods WHERE id IN ({placeholders})"
            # print(f"Executing delete query: {sql_query} with IDs {selected_food_ids}") # 디버깅용
            cursor.execute(sql_query, selected_food_ids)

            deleted_count = cursor.rowcount # 실제로 삭제된 행의 개수
            db.commit()
            print(f"Successfully deleted {deleted_count} selected foods.")

        except Exception as e:
            print(f"Error deleting selected foods: {e}")
            db.rollback() # 에러 발생 시 되돌리기

    # ====> 삭제 처리 후, 등록된 음식 목록 페이지로 리다이렉트! <====
    return redirect(url_for('list_foods'))


# 앱 실행 부분 (이전과 동일)
if __name__ == '__main__':
    # 앱 실행 전에 데이터베이스 파일이 없으면 초기화 (테이블 생성 및 초기 데이터 삽입)
    # foods.db 파일 삭제 후 처음 실행할 때 이 부분이 작동해야 해!
    if not os.path.exists(DATABASE):
        print(f"Database file '{DATABASE}' not found. Initializing database...")
        init_db() # foodapp.sql 실행 (encoding='utf-8' 적용)
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            # initial_foods 리스트는 각 음식이름마다 튜플()로 감싸져 있어야 해!
            initial_foods = [
                ('짜장면',), ('김치찌개',), ('치킨',), ('파스타',), ('피자',),
                ('족발',), ('보쌈',), ('초밥',), ('스테이크',)
            ]
            cursor.executemany("INSERT OR IGNORE INTO foods (name) VALUES (?)", initial_foods)
            db.commit()
            print("Initial foods added (if they didn't exist).")
    else:
        print(f"Database file '{DATABASE}' found. Skipping initialization.")

    app.run(debug=True)
