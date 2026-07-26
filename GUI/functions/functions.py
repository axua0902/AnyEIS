# IMPORT PACKAGES AND MODULES
# ///////////////////////////////////////////////////////////////
import os

# APP FUNCTIONS
# ///////////////////////////////////////////////////////////////
class Functions:
    # GET ERROR ICON PATH
    # ///////////////////////////////////////////////////////////////
    def get_error_icon(self):
        """返回错误图标的路径"""
        app_path = os.path.abspath(os.getcwd())
        error_icon = os.path.normpath(os.path.join(app_path, "images", "IconError.svg"))
        return error_icon

    # VALIDATE FILE PATH
    # ///////////////////////////////////////////////////////////////
    def validate_file_path(file_name, folder_path):
        """验证文件路径是否有效"""
        # 检查文件名是否为空或None
        if not file_name or file_name.strip() == "":
            print("错误: 文件名为空或None")
            return Functions.get_error_icon()
        
        # 构建完整路径
        full_path = os.path.normpath(os.path.join(folder_path, file_name))
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            print(f"错误: 指定的文件 '{file_name}' 不存在于路径 '{folder_path}'")
            return Functions.get_error_icon()
        
        # 检查是否为文件
        if not os.path.isfile(full_path):
            print(f"错误: '{full_path}' 不是一个有效的文件")
            return Functions.get_error_icon()
        
        return full_path

    # SET SVG ICON
    # ///////////////////////////////////////////////////////////////
    def set_svg_icon(icon_name):
        app_path = os.path.abspath(os.getcwd())
        folder = "images/svg_icons/"
        path = os.path.join(app_path, folder)
        return Functions.validate_file_path(icon_name, path)

    # SET SVG IMAGE
    # ///////////////////////////////////////////////////////////////
    def set_svg_image(icon_name):
        app_path = os.path.abspath(os.getcwd())
        folder = "images/svg_images/"
        path = os.path.join(app_path, folder)
        return Functions.validate_file_path(icon_name, path)

    # SET IMAGE
    # ///////////////////////////////////////////////////////////////
    def set_image(image_name):
        app_path = os.path.abspath(os.getcwd())
        folder = "images/images/"
        path = os.path.join(app_path, folder)
        return Functions.validate_file_path(image_name, path)