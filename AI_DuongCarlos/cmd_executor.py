import ctypes
import subprocess
import os
import re

LOCAL_SOFTWARE = {
    "7zip": "7zip.install",
    "unikey": "unikey",
    "firefox": "firefox",
    "chrome": "googlechrome",
    "zalo": "zalo",
    "git": "git",
    "vscode": "visualstudiocode",
    "photoshop": "photoshop"
}
SOFTWARE_NAMES = list(LOCAL_SOFTWARE.keys())

CHOCO_PATH = r"C:\ProgramData\chocolatey\bin\choco.exe"
if not os.path.exists(CHOCO_PATH):
    CHOCO_PATH = "choco" 

def run_live_search(query):
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        result = subprocess.run(
            f'"{CHOCO_PATH}" search "{query}" --id-only', 
            shell=True, capture_output=True, text=True, creationflags=creation_flags,
            timeout=20 
        )
        output = result.stdout if result.stdout else result.stderr
        if "is not recognized" in output or "không được nhận dạng" in output:
            return "❌ Hệ thống không tìm thấy lõi Chocolatey."
            
        output = output.replace("Chocolatey", "Yoh").replace("chocolatey", "yoh").replace("choco", "yoh").replace("Choco", "Yoh")
        return output.strip()
    except subprocess.TimeoutExpired:
        return "⏳ Quá thời gian chờ. Máy chủ kho phần mềm đang phản hồi chậm."
    except Exception as e:
        return f"Lỗi thực thi lệnh: {e}"

def get_exact_package_for_install(query):
    version_match = re.search(r'\d+(\.\d+)+', query)
    version = version_match.group(0) if version_match else None
    base_query = query.replace(version, '').strip() if version else query
    base_query = re.sub(r'[\s\.\-\_v]+$', '', base_query).strip()

    if not base_query: return None, None

    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        result = subprocess.run(
            f'"{CHOCO_PATH}" search "{base_query}" --id-only', 
            shell=True, capture_output=True, text=True, creationflags=creation_flags,
            timeout=15
        )
        
        lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        valid_packages = []
        for line in lines:
            if "|" in line or line.startswith("Chocolatey") or line.startswith("Yoh v") or "packages found" in line.lower(): continue
            if line.startswith("Title:") or line.startswith("Progress:") or line.lower().startswith("warning:") or line.lower().startswith("error:"): continue
            
            pkg_name = line.split()[0]
            if pkg_name.lower() not in ["failed", "error", "warning"]:
                valid_packages.append(pkg_name)

        if not valid_packages: return None, None

        # LOGIC TÌM KIẾM TUYỆT ĐỐI
        # 1. Tìm gói khớp chính xác 100% ID
        for pkg in valid_packages:
            if pkg.lower() == base_query.lower():
                return pkg, version
        
        # 2. Tìm gói có đuôi .install
        for pkg in valid_packages:
            if pkg.lower() == f"{base_query.lower()}.install":
                return pkg, version

        # 3. Trả về gói khả dĩ nhất
        return valid_packages[0], version
    except:
        return None, None

def install_software_as_admin(package_name, version=None):
    cmd = f'"{CHOCO_PATH}" install {package_name} -y'
    if version: cmd += f' --version {version}'
    command = f"/c {cmd}"
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", command, None, 1)
        return True
    except Exception:
        return False

def uninstall_software_as_admin(package_name, version=None):
    cmd = f'"{CHOCO_PATH}" uninstall {package_name} -y'
    if version: cmd += f' --version {version}'
    command = f"/c {cmd}"
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", command, None, 1)
        return True
    except Exception:
        return False