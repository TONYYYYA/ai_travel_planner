import ast

from flask import Flask, request, jsonify, session, redirect, render_template,url_for,flash
from flask_cors import CORS
import json
import uuid
from datetime import datetime
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash
from speech_service import speech_to_text, audio_stream, speech_to_text1
from llm_service import generate_itinerary, analyze_budget
from map_service import get_location_info, get_route_plan, geocode_addresses, build_baidu_personal_marker_uri
from config import config
from speech_service import BytesToStream
import io
# 初始化Flask应用，指向上级目录中的 templates 和 static
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config.from_object(config)
CORS(
    app,
    supports_credentials=True,
    resources={
        r"/api/*": {
            "origins": [
                "http://127.0.0.1:5000",
                "http://localhost:5000",
                "http://localhost:63342"
            ]
        }
    }
)
# 解决跨域问题
# 初始化Supabase客户端
supabase: Client = create_client(
    config.SUPABASE['url'],
    config.SUPABASE['key']
)


# 登录验证装饰器
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "请先登录"}), 401
        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper


@app.route('/', methods=['GET', 'POST'])
def root():
    if request.method == 'GET':
        return render_template('welcome.html')
    return redirect(url_for('login'))



# 登录页（如被移除则补回）
@app.route('/login', methods=['GET'], endpoint='login')
def login_page():
    return render_template('login.html')

@app.route('/login.html', methods=['GET'])
def login_html():
    return render_template('login.html')

@app.route('/register', methods=['GET'])
@app.route('/register.html', methods=['GET'])
def register_page_html():
    return render_template('register.html')


# 页面路由
@app.route('/planner', methods=['GET'])
@app.route('/planner.html', methods=['GET'])
def planner_page():
    return render_template('planner.html')

@app.route('/expenses', methods=['GET'])
@app.route('/expenses.html', methods=['GET'])
def expenses_page():
    return render_template('expenses.html')

@app.route('/sync', methods=['GET'])
@app.route('/sync.html', methods=['GET'])
def sync_page():
    return render_template('sync.html')

@app.route('/guide', methods=['GET'])
@app.route('/guide.html', methods=['GET'])
def guide_page():
    return render_template('guide.html')
# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    try:
        # 检查用户是否已存在
        existing = supabase.table('users').select('id').eq('username', data['username']).execute()
        if existing.data:
            return jsonify({"error": "用户名已存在"}), 400

        # 创建新用户
        hashed_password = generate_password_hash(data['password'])
        response = supabase.table('users').insert({
            'username': data['username'],
            'email': data['email'],
            'password_hash': hashed_password,
            'created_at': datetime.now().isoformat()
        }).execute()

        return jsonify({
            "success": True,
            "message": "注册成功，请登录"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 用户登录
@app.route('/api/login', methods=['POST'], endpoint='api_login')
def login():
    data = request.json
    try:
        # 打印接收的登录数据（调试用）
        print("登录请求数据：", data)

        # 查询用户
        response = supabase.table('users').select('id, username, password_hash').eq('username',
                                                                                    data['username']).execute()

        # 打印 Supabase 返回的查询结果
        print("Supabase 查询结果：", response.data)

        if not response.data:
            print("登录失败：未找到用户")  # 调试信息
            return jsonify({"error": "用户名或密码错误"}), 401

        user = response.data[0]
        # 打印查询到的用户哈希密码（调试用）
        print("查询到的密码哈希：", user['password_hash'])

        # 验证密码
        password_match = check_password_hash(user['password_hash'], data['password'])
        print("密码验证结果：", password_match)  # 调试用

        if not password_match:
            print("登录失败：密码不匹配")  # 调试信息
            return jsonify({"error": "用户名或密码错误"}), 401

        # 设置会话
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({
            "success": True,
            "user": {
                "id": user['id'],
                "username": user['username']
            }
        })
    except Exception as e:
        print("登录时发生异常：", str(e))  # 打印异常详情
        return jsonify({"error": str(e)}), 500


# 语音转文字
@app.route('/api/speech-to-text', methods=['POST'])
def handle_speech():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "未提供音频文件"}), 400

        audio_file = request.files['audio']
        
        # 检查文件大小
        audio_file.seek(0, 2)  # 移动到文件末尾
        file_size = audio_file.tell()  # 获取文件大小
        audio_file.seek(0)  # 重置到文件开头
        
        if file_size == 0:
            return jsonify({"error": "音频文件为空"}), 400
            
        # 读取音频数据
        audio_data = audio_file.read()
        
        try:
            # 调用语音识别服务
            text_result = speech_to_text(audio_data)
            return jsonify({"text": text_result, "success": True})
        except Exception as speech_error:
            # 语音处理错误，但仍返回200状态码，避免前端500错误
            return jsonify({
                "text": [{"result": {"ws": [{"cw": [{"w": f"语音识别错误: {str(speech_error)[:100]}..."}]}]}}],
                "success": False,
                "error": str(speech_error)
            })
            
    except Exception as e:
        # 其他错误，返回友好的错误信息
        return jsonify({
            "text": [{"result": {"ws": [{"cw": [{"w": f"请求处理错误"}]}]}}],
            "success": False,
            "error": str(e)
        })


# 生成行程
@app.route('/api/generate-itinerary', methods=['POST'])
@login_required
def create_itinerary():
    data = request.json
    user_input = data['input']
    print(user_input)
    # 生成行程
    itinerary = generate_itinerary(user_input)
    print(itinerary)
    return jsonify({"message": itinerary})


# 获取/创建用户行程
@app.route('/api/itineraries', methods=['GET', 'POST'])
@login_required
def get_itineraries():
    try:
        if request.method == 'GET':
            response = supabase.table('itineraries').select(
                'id, title, created_at'
            ).eq('user_id', session['user_id']).order('created_at', desc=True).execute()
            return jsonify(response.data)
        else:
            data = request.get_json(force=True) or {}
            itinerary_id = str(uuid.uuid4())
            # 确保 itinerary_data 可序列化为 JSON（jsonb）
            itinerary_data = data.get('itinerary_data')
            try:
                # 通过一次序列化+反序列化来校验/净化
                itinerary_data = json.loads(json.dumps(itinerary_data))
            except Exception:
                # 退回原始字符串
                itinerary_data = str(itinerary_data) if itinerary_data is not None else {}
            supabase.table('itineraries').insert({
                'id': itinerary_id,
                'user_id': session['user_id'],
                'title': data.get('title', ''),
                'input_text': data.get('input_text', ''),
                'itinerary_data': itinerary_data,
                'created_at': datetime.now().isoformat()
            }).execute()
            return jsonify({"success": True, "id": itinerary_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 获取单个行程详情
@app.route('/api/itineraries/<itinerary_id>', methods=['GET'])
@login_required
def get_itinerary_detail(itinerary_id):
    try:
        resp = supabase.table('itineraries').select(
            'id, title, input_text, itinerary_data, created_at'
        ).eq('id', itinerary_id).eq('user_id', session['user_id']).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return jsonify({"error": "未找到行程"}), 404
        return jsonify(rows[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 删除行程
@app.route('/api/itineraries/<itinerary_id>', methods=['DELETE'])
@login_required
def delete_itinerary(itinerary_id):
    try:
        # 仅删除当前登录用户的行程
        supabase.table('itineraries').delete().eq('id', itinerary_id).eq('user_id', session['user_id']).execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取地理位置信息
@app.route('/api/location-info', methods=['GET'])
def get_location():
    address = request.args.get('address')
    city = request.args.get('city')
    country = request.args.get('country')
    if not address:
        return jsonify({"error": "请提供地址"}), 400

    print(f"[API] /api/location-info 请求: address={address}, city={city}, country={country}")
    info = get_location_info(address, city=city, country=country)
    print(f"[API] /api/location-info 响应: success={info.get('success')}, error={info.get('error', '')}")
    return jsonify(info)


# 获取路线规划
@app.route('/api/route-plan', methods=['GET'])
def get_route():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    if not origin or not destination:
        return jsonify({"error": "请提供起点和终点"}), 400

    route = get_route_plan(origin, destination)
    return jsonify(route)


# 生成百度个人地图URI（标记景点并可唤起App）
@app.route('/api/schema/personal-map', methods=['POST'])
def build_personal_map_uri():
    try:
        data = request.get_json(force=True) or {}
        # 接受形如 { title, points: [{ name, city?, country? }, ...] }
        raw_points = data.get('points') or []
        names = []
        for p in raw_points:
            if isinstance(p, dict):
                name = (p.get('name') or '').strip()
                city = (p.get('city') or '').strip() or None
                country = (p.get('country') or '').strip() or None
                if name:
                    parts = [name]
                    if city:
                        parts.append(city)
                    if country:
                        parts.append(country)
                    names.append(", ".join(parts))
            else:
                text = str(p).strip()
                if text:
                    names.append(text)

        if not names:
            return jsonify({"error": "请提供至少一个景点名称"}), 400

        # 提取默认城市和国家（从第一个点或数据中获取）
        default_city = None
        default_country = None
        if raw_points and isinstance(raw_points[0], dict):
            default_city = raw_points[0].get('city')
            default_country = raw_points[0].get('country')
        
        coded = geocode_addresses(raw_points, city=default_city, country=default_country)
        if not coded:
            return jsonify({"error": "无法解析任何景点位置"}), 400

        uri_result = build_baidu_personal_marker_uri(coded)
        if not uri_result:
            return jsonify({"error": "URI 生成失败"}), 500

        return jsonify({
            "success": True,
            "uri": uri_result.get('uri'),
            "web_url": uri_result.get('web'),
            "count": len(coded),
            "points": coded
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 添加费用记录
@app.route('/api/expenses', methods=['POST'])
@login_required
def add_expense():
    data = request.json
    try:
        expense_id = str(uuid.uuid4())
        supabase.table('expenses').insert({
            'id': expense_id,
            'itinerary_id': data['itinerary_id'],
            'user_id': session['user_id'],
            'amount': data['amount'],
            'category': data['category'],
            'description': data['description'],
            'created_at': datetime.now().isoformat()
        }).execute()

        return jsonify({"success": True, "expense_id": expense_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 获取行程费用记录
@app.route('/api/expenses/<itinerary_id>', methods=['GET'])
@login_required
def get_expenses(itinerary_id):
    try:
        response = supabase.table('expenses').select('*').eq(
            'itinerary_id', itinerary_id
        ).eq('user_id', session['user_id']).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 预算分析
@app.route('/api/analyze-budget', methods=['POST'])
@login_required
def analyze_budget_route():
    data = request.json
    # 可选语音识别备注
    note = data.get('note')
    analysis = analyze_budget(
        data['itinerary_id'],
        data['expenses'],
        data['original_budget'],
        note=note
    )
    # 回传备注以便前端确认已传达
    if note is not None and isinstance(analysis, dict):
        analysis['note'] = note
    return jsonify(analysis)


# 登出
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
