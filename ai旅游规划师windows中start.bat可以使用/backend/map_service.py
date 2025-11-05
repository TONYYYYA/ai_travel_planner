import requests
from config import config


def get_location_info(address, city: str = None, country: str = None):
    """使用百度地理编码API，根据地址（可包含城市、国家）获取经纬度信息。
    通过组合 address + city + country 提高准确性，严格限制在指定区域范围内。
    """
    try:
        base = "https://api.map.baidu.com/geocoding/v3/"
        
        # 构建查询地址：优先使用单独的地址名称，避免过度组合
        # 百度API的address参数应该主要是地点名称
        query_address = address.strip() if address else ""
        
        params = {
            "address": query_address,
            "output": "json",
            "ak": config.BAIDU['ak'],
            "ret_coordtype": "bd09ll"  # 返回百度坐标系
        }
        
        # region 参数用于限定搜索范围
        # 百度API的region可以接受：省、市、区，或国家名称
        if city:
            params["region"] = city
        elif country:
            # 对于国外地址，使用国家作为region
            params["region"] = country
        
        print(f"[百度地理编码] 查询地址: {query_address}, region: {params.get('region', '未指定')}")
        print(f"[百度地理编码] 请求URL: {base}?address={query_address}&region={params.get('region', '')}&ak=***")
        
        response = requests.get(base, params=params, timeout=10)
        result = response.json()
        
        print(f"[百度地理编码] API响应: status={result.get('status')}, message={result.get('message', '')}")

        # 百度API: status=0表示成功
        if result.get('status') == 0 and result.get('result'):
            result_data = result['result']
            
            # 检查是否有location信息
            if result_data.get('location'):
                loc = result_data['location']  # {lng, lat}
                formatted_addr = result_data.get('formatted_address') or result_data.get('level') or query_address
                
                print(f"[百度地理编码] 成功获取: {formatted_addr}, 坐标: {loc['lng']}, {loc['lat']}")
                
                # 如果指定了非中国的国家，但返回的地址明显是中国境内的，认为匹配错误，改用备用方案
                if country and country.lower() not in ['中国', 'china', 'cn', '']:
                    # 检查返回地址是否明显是中国地址
                    china_keywords = ['中国', 'china', '北京', '上海', '广东', '深圳', '香港', '澳门', '台湾', 
                                    'beijing', 'shanghai', 'guangdong', 'shenzhen', 'hong kong', 'hongkong']
                    addr_lower = formatted_addr.lower()
                    if any(keyword.lower() in addr_lower for keyword in china_keywords):
                        print(f"[百度地理编码] 检测到错误匹配：期望国家={country}，但返回中国地址={formatted_addr}，改用国际备用方案...")
                        # 改为直接使用高德（禁用Nominatim）
                        amap_result = get_location_info_amap(address, city, country)
                        if amap_result.get('success'):
                            return amap_result
                        # 如果都失败，只能返回百度结果（可能不准确）
                        print("[百度地理编码] 备用方案失败（已禁用Nominatim），返回可能不准确的百度结果")
                
                # 对于国内地址，只在国内且指定了城市时才做验证
                if city and country and ('中国' in country or 'China' in country or 'china' in country.lower()):
                    addr_lower = formatted_addr.lower()
                    city_match = city.lower() in addr_lower if city else True
                    if not city_match:
                        print(f"[百度地理编码] 城市不匹配: 期望={city}, 实际={formatted_addr}")
                        # 对于国内地址，如果城市不匹配，尝试不限制region再次查询
                        return {"success": False, "error": f"地址不在指定城市({city})内: {address}"}
                
                return {
                    "success": True,
                    "address": formatted_addr,
                    "location": f"{loc['lng']},{loc['lat']}",
                    "city": city or '',
                    "country": country or ''
                }
            else:
                print(f"[百度地理编码] API返回无location信息: {result_data}")
                return {"success": False, "error": "API返回无位置信息"}
        else:
            # 错误信息处理
            status = result.get('status')
            message = result.get('message') or result.get('msg') or "未知错误"
            print(f"[百度地理编码] API错误: status={status}, message={message}")
            
            # 常见错误码说明
            error_map = {
                1: "服务器内部错误",
                2: "请求参数非法",
                3: "权限校验失败",
                4: "配额校验失败",
                5: "AK不存在或非法",
                200: "无权限",
                201: "无权限（IP白名单）",
                240: "APP服务被禁用",  # 需要启用地理编码服务
            }
            
            error_msg = error_map.get(status, message)
            
            # 如果百度不可用：使用高德地图作为唯一备用（已禁用Nominatim）
            if status in [240, 200, 201, 3, 5]:
                print(f"[百度地理编码] 百度API不可用(status={status})，尝试使用高德地图作为备用...")
                return get_location_info_amap(address, city, country)
            
            return {"success": False, "error": f"百度API错误({status}): {error_msg}"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时，请稍后重试"}
    except requests.exceptions.RequestException as e:
        print(f"[百度地理编码] 网络请求异常: {e}")
        return {"success": False, "error": f"网络请求失败: {str(e)}"}
    except Exception as e:
        import traceback
        print(f"[百度地理编码] 异常: {e}\n{traceback.format_exc()}")
        return {"success": False, "error": str(e)}


def get_location_info_nominatim(address, city: str = None, country: str = None):
    """使用 OpenStreetMap Nominatim 作为国际备用方案，支持重试与备用端点，返回BD-09坐标。"""
    try:
        # 构造查询字符串
        def build_query(addr, cty, ctry):
            parts = []
            if addr:
                parts.append(addr)
            if cty:
                parts.append(cty)
            if ctry:
                parts.append(ctry)
            return ", ".join([p for p in parts if p])

        # 依次尝试的端点与语言组合
        providers = [
            ("https://nominatim.openstreetmap.org/search", "zh-CN,en"),
            ("https://nominatim.openstreetmap.org/search", "en"),
            ("https://geocode.maps.co/search", "en"),
        ]

        headers = {"User-Agent": "ai_travel2/1.0 (contact: support@example.com)"}

        # 逐个端点尝试，且在每个端点上做重试与降级（去掉city，保留country）
        for base, lang in providers:
            for attempt in range(3):
                q = build_query(address, city, country)
                params = {
                    "q": q,
                    "format": "jsonv2",
                    "limit": 1,
                    "accept-language": lang
                }
                timeout_sec = 8 + attempt * 4  # 递增超时：8s,12s,16s
                try:
                    print(f"[Nominatim] 第{attempt+1}次尝试 {base} 语言={lang} 查询: {q}")
                    resp = requests.get(base, params=params, headers=headers, timeout=timeout_sec)
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        item = data[0]
                        lat = float(item.get('lat'))
                        lon = float(item.get('lon'))
                        display_name = item.get('display_name') or q

                        # WGS84 -> GCJ-02 -> BD-09
                        gcj_lng, gcj_lat = wgs84_to_gcj02(lon, lat)
                        bd_lng, bd_lat = gcj02_to_bd09(gcj_lng, gcj_lat)

                        print(f"[Nominatim] 成功: {display_name}, WGS84({lon},{lat}) -> BD09({bd_lng},{bd_lat})")
                        return {
                            "success": True,
                            "address": display_name,
                            "location": f"{bd_lng},{bd_lat}",
                            "city": city or '',
                            "country": country or ''
                        }
                    else:
                        # 第一次失败后，降级去掉城市，仅用地址+国家
                        if attempt == 0 and (city or country):
                            city = None
                            print("[Nominatim] 未找到结果，降级为仅地址+国家后重试")
                        else:
                            print("[Nominatim] 未找到匹配结果，继续重试/切换端点")
                except Exception as e:
                    import traceback
                    print(f"[Nominatim] 端点 {base} 尝试失败({attempt+1})：{e}\n{traceback.format_exc()}")
                    continue

        return {"success": False, "error": "Nominatim及备用端点均未找到匹配或超时"}
    except Exception as e:
        import traceback
        print(f"[Nominatim] 异常: {e}\n{traceback.format_exc()}")
        return {"success": False, "error": f"Nominatim失败: {str(e)}"}


def get_location_info_amap(address, city: str = None, country: str = None):
    """使用高德地图地理编码API作为备用方案"""
    try:
        # 检查是否有高德地图配置
        if not hasattr(config, 'AMAP') or not config.AMAP.get('key') or config.AMAP.get('key') == '你的高德地图key':
            return {"success": False, "error": "高德地图API Key未配置，无法使用备用方案"}
        
        base = "https://restapi.amap.com/v3/geocode/geo"
        
        # 构建查询地址
        query_address = address.strip() if address else ""
        if city and city not in query_address:
            query_address = f"{query_address},{city}"
        if country and country not in query_address:
            query_address = f"{query_address},{country}"
        
        params = {
            "address": query_address,
            "output": "json",
            "key": config.AMAP['key']
        }
        
        # 高德地图的city参数用于限定搜索范围
        if city:
            params["city"] = city
        elif country:
            params["city"] = country
        
        print(f"[高德地理编码] 查询地址: {query_address}, city: {params.get('city', '未指定')}")
        
        response = requests.get(base, params=params, timeout=10)
        result = response.json()
        
        print(f"[高德地理编码] API响应: status={result.get('status')}, info={result.get('info', '')}")
        
        # 高德API: status='1'表示成功
        if result.get('status') == '1' and result.get('geocodes') and len(result['geocodes']) > 0:
            geocode = result['geocodes'][0]
            location_str = geocode.get('location')  # 格式: "lng,lat"
            
            if location_str:
                print(f"[高德地理编码] 成功获取: {geocode.get('formatted_address', query_address)}, 坐标: {location_str}")
                
                # 高德返回的是GCJ-02坐标系，需要转换为百度坐标系(BD-09)供前端使用
                lng_str, lat_str = location_str.split(',')
                lng = float(lng_str)
                lat = float(lat_str)
                
                # 转换为百度坐标系
                bd_lng, bd_lat = gcj02_to_bd09(lng, lat)
                
                return {
                    "success": True,
                    "address": geocode.get('formatted_address') or geocode.get('formatted_address', query_address),
                    "location": f"{bd_lng},{bd_lat}",  # 返回百度坐标系
                    "city": city or geocode.get('city', ''),
                    "country": country or ''
                }
            else:
                return {"success": False, "error": "高德API返回无位置信息"}
        else:
            info = result.get('info', '未知错误')
            print(f"[高德地理编码] API错误: {info}")
            return {"success": False, "error": f"高德API错误: {info}"}
    except Exception as e:
        import traceback
        print(f"[高德地理编码] 异常: {e}\n{traceback.format_exc()}")
        return {"success": False, "error": f"高德地图备用方案失败: {str(e)}"}


def gcj02_to_bd09(lng, lat):
    """将GCJ-02坐标系（高德）转换为BD-09坐标系（百度）"""
    try:
        import math
        
        z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * math.pi * 3000.0 / 180.0)
        theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * math.pi * 3000.0 / 180.0)
        bd_lng = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        
        return bd_lng, bd_lat
    except Exception:
        # 如果转换失败，返回原始坐标（可能有误差但不会报错）
        return lng, lat


def out_of_china(lng, lat):
    return not (73.66 <= lng <= 135.05 and 3.86 <= lat <= 53.55)


def wgs84_to_gcj02(lng, lat):
    """WGS84 -> GCJ-02（仅中国境内转换，境外原样返回）"""
    try:
        if out_of_china(lng, lat):
            return lng, lat
        import math
        a = 6378245.0
        ee = 0.00669342162296594323

        def transform_lat(x, y):
            ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
            ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
            ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
            ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
            return ret

        def transform_lng(x, y):
            ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
            ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
            ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
            ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
            return ret

        dlat = transform_lat(lng - 105.0, lat - 35.0)
        dlng = transform_lng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * math.pi
        magic = math.sin(radlat)
        magic = 1 - ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
        dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return mglng, mglat
    except Exception:
        return lng, lat


def get_route_plan(origin, destination):
    """获取两地之间的路线规划"""
    try:
        # 先将地址转换为经纬度（百度）
        origin_loc = get_location_info(origin)
        dest_loc = get_location_info(destination)

        if not origin_loc['success'] or not dest_loc['success']:
            return {"success": False, "error": "地址解析失败"}

        # 简化：此处暂不调用百度路线规划，返回两点坐标，前端可自行绘制
        return {
            "success": True,
            "origin": origin_loc.get('location'),
            "destination": dest_loc.get('location')
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def geocode_addresses(address_list, city: str = None, country: str = None):
    """批量地理编码，支持传递city/country提高准确性，返回[{name, lng, lat}]（成功的条目）。"""
    results = []
    for addr_item in address_list:
        # 支持字符串或字典格式
        if isinstance(addr_item, dict):
            name = addr_item.get('name', '')
            addr_city = addr_item.get('city') or city
            addr_country = addr_item.get('country') or country
        else:
            name = str(addr_item)
            addr_city = city
            addr_country = country
        
        if not name:
            continue
            
        info = get_location_info(name, city=addr_city, country=addr_country)
        if info.get("success") and info.get("location"):
            try:
                lng_str, lat_str = info["location"].split(",")
                results.append({
                    "name": name,
                    "lng": float(lng_str),
                    "lat": float(lat_str),
                    "city": info.get('city', ''),
                    "country": info.get('country', '')
                })
            except Exception:
                continue
    return results


def build_baidu_personal_marker_uri(named_points):
    """基于多个点构建百度地图URI，支持在App中查看并标记多个景点。
    使用百度地图URI Scheme：baidumap://map/marker?...
    文档参考：https://lbsyun.baidu.com/index.php?title=uri/api/android
    """
    if not named_points:
        return None
    
    try:
        import urllib.parse
        
        # 构建Web版备用URL（所有点）
        web_markers = []
        for p in named_points:
            try:
                lat = p['lat']
                lng = p['lng']
                name = urllib.parse.quote(p.get('name', '景点'))
                web_markers.append(f"location={lat},{lng}&title={name}")
            except KeyError:
                continue
        
        web_url = None
        if web_markers:
            # Web版使用百度地图API的marker页面
            if len(web_markers) == 1:
                web_url = f"https://api.map.baidu.com/marker?{web_markers[0]}&output=html&src=ai_travel2"
            else:
                # 多个点，使用第一个点作为中心，其他点通过自定义地图展示
                web_url = f"https://api.map.baidu.com/marker?{web_markers[0]}&output=html&src=ai_travel2"
        
        # App版URI Scheme
        if len(named_points) > 1:
            # 多点标记：使用 markers 参数
            markers = []
            for p in named_points:
                try:
                    lat = p['lat']
                    lng = p['lng']
                    name = p.get('name', '景点')
                    # 百度多点格式：lat,lng,name|lat,lng,name
                    markers.append(f"{lat},{lng},{urllib.parse.quote(name)}")
                except KeyError:
                    continue
            
            if not markers:
                return None
            
            markers_str = "|".join(markers)
            uri = f"baidumap://map/marker?markers={markers_str}&src=ai_travel2"
        else:
            # 单个点
            p = named_points[0]
            lng = p['lng']
            lat = p['lat']
            title = urllib.parse.quote(p.get('name', '目的地'))
            uri = f"baidumap://map/marker?location={lat},{lng}&title={title}&src=ai_travel2"
        
        return {"uri": uri, "web": web_url}
    except Exception as e:
        import traceback
        print(f"生成百度地图URI出错: {e}\n{traceback.format_exc()}")
        return None