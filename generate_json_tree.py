import os
import json
import uuid
from PIL import Image, PngImagePlugin
import base64
import io
from datetime import datetime
from tqdm import tqdm  # tqdm 라이브러리 임포트

def generate_json_tree(root_path):
    tree = {}
    valid_extensions = {'png', 'jpg', 'gif', 'bmp', 'tiff', 'psd', 'psb', 'webp', 'ico', 'anigif', 'jpeg'}

    def add_folder(path, name, parent_id=None):
        folder_id = name
        tree[folder_id] = {
            "id": folder_id,
            "name": name,
            "children": [],
            "parentId": parent_id,
            "parentIdList": [],
            "imageUrls": []
        }
        if parent_id:
            tree[folder_id]["parentIdList"] = tree[parent_id]["parentIdList"] + [parent_id]
        return folder_id

    def create_thumbnail(image_path):
        with Image.open(image_path) as img:
            max_size = 128
            ratio = max_size / max(img.width, img.height)
            img.thumbnail((img.width * ratio, img.height * ratio))
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            encoded_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return "data:image/png;base64," + encoded_string
    
    def encode_image_base64_with_exif(image_path):
    	with Image.open(image_path) as img:
            info = img.info.copy()
            buffer = io.BytesIO()
            pnginfo = PngImagePlugin.PngInfo()
            
            for key, value in info.items():
                if isinstance(value, bytes):
                    value = value.decode('utf-8', errors='ignore')
                    pnginfo.add_text(key, value)
                elif isinstance(value, tuple):
                    pass
                elif isinstance(value, int):
                    pass
            
            img.save(buffer, format='PNG', pnginfo=pnginfo)
            encoded_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{encoded_string}"

    # 디렉토리 탐색 및 JSON 구조 생성
    for dirpath, dirnames, filenames in os.walk(root_path):
        if dirpath == root_path:
            folder_id = add_folder(dirpath, os.path.basename(root_path))
        else:
            parent_id = os.path.basename(os.path.dirname(dirpath))
            folder_id = add_folder(dirpath, os.path.basename(dirpath), parent_id)
        
        if 'parentId' in tree[folder_id] and tree[folder_id]['parentId']:
            tree[tree[folder_id]['parentId']]['children'].append(folder_id)
        
        # tqdm으로 파일 처리 진행률 표시
        for filename in tqdm(filenames, desc=f"[Processing files in {dirpath}", unit="file]"):
            ext = filename.split('.')[-1].lower()
            if ext in valid_extensions:
                image_path = os.path.join(dirpath, filename)
                image_data = {
                    "original": encode_image_base64_with_exif(image_path),
                    "thumbnail": create_thumbnail(image_path),
                    "uuid": str(uuid.uuid4())
                }
                tree[folder_id]["imageUrls"].append(image_data)
    
    return tree

def save_json(data, filename):
    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    target_directory = os.path.join(os.getcwd(), 'generated-bulk-json-files')
    os.makedirs(target_directory, exist_ok=True)
    full_file_path = os.path.join(target_directory, f'{filename}-{current_time}.json')
    with open(full_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
