from PIL import Image
import os

def convert_png_to_ico(png_path, ico_path, sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]):
    try:
        img = Image.open(png_path)
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        img.save(ico_path, format='ICO', sizes=sizes)
        print(f"成功转换: {png_path} -> {ico_path}")
        print(f"包含尺寸: {sizes}")
        return True
    except Exception as e:
        print(f"转换失败: {e}")
        return False

if __name__ == "__main__":
    png_file = r"E:\AIcoding\桌面计时器\1.6.png"
    ico_file = r"E:\AIcoding\桌面计时器\icon.ico"
    
    convert_png_to_ico(png_file, ico_file)
